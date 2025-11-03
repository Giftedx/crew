"""Enhanced multi-provider router using LiteLLM with intelligent failover and cost optimization.

This service extends the existing OpenRouter functionality with LiteLLM's multi-provider
routing capabilities, providing automatic failover, cost optimization, and unified API
access to 100+ LLM providers.
"""

from __future__ import annotations

import asyncio
import copy
import logging
import time
from dataclasses import dataclass
from platform.cache.semantic_cache import get_semantic_cache
from platform.config.configuration import get_config
from platform.http.http_utils import REQUEST_TIMEOUT_SECONDS
from platform.observability import metrics
from platform.observability.langsmith_integration import get_enhanced_observability
from platform.rl.learning_engine import LearningEngine
from typing import TYPE_CHECKING, Any, Protocol, cast, runtime_checkable

from app.config.settings import Settings
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant

from .cache import RedisLLMCache, make_key
from .prompt_engine import PromptEngine
from .token_meter import TokenMeter


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from platform.core.step_result import StepResult

    from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry

    from .logging_utils import AnalyticsStore


class LLMCacheProto(Protocol):
    def get(self, key: str) -> StepResult: ...

    def set(self, key: str, value: dict[str, Any]) -> StepResult: ...


@runtime_checkable
class _LiteLLMMsg(Protocol):
    content: str | None


@runtime_checkable
class _LiteLLMChoice(Protocol):
    message: _LiteLLMMsg


@runtime_checkable
class _LiteLLMResponse(Protocol):
    choices: Sequence[_LiteLLMChoice]


def _extract_content(resp: Any) -> StepResult:
    """Best-effort extraction of response text from a LiteLLM completion.

    Handles both standard response objects exposing ``choices[0].message.content``
    and fallback attributes; never raises and always returns a string for
    downstream token counting.
    """
    try:
        if isinstance(resp, _LiteLLMResponse) and resp.choices:
            msg = resp.choices[0].message
            if msg and getattr(msg, "content", None) is not None:
                return str(msg.content)
        direct = getattr(resp, "content", None)
        if direct is not None:
            return str(direct)
    except Exception:
        pass
    return ""


litellm: Any
_completion_cost: Callable[..., float] | None = None
try:
    import litellm as _litellm
    from litellm import completion as _completion

    try:
        from litellm.cost_calculator import completion_cost as _cc

        _completion_cost = _cc
    except Exception:
        _completion_cost = None
    litellm = _litellm
    LITELLM_AVAILABLE = True
except Exception:
    litellm = None
    _completion = None
    LITELLM_AVAILABLE = False
logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for a specific LLM provider."""

    name: str
    models: list[str]
    priority: int = 1
    max_retries: int = 3
    timeout: float = 30.0
    cost_multiplier: float = 1.0
    enabled: bool = True


@dataclass
class RouterStats:
    """Runtime statistics for the enhanced router."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_requests: int = 0
    fallback_requests: int = 0
    total_cost: float = 0.0
    average_latency: float = 0.0


class EnhancedOpenRouterService:
    """Enhanced LLM router with LiteLLM multi-provider support and intelligent failover."""

    def __init__(
        self,
        models_map: dict[str, list[str]] | None = None,
        learning_engine: LearningEngine | None = None,
        provider_configs: list[ProviderConfig] | None = None,
        cache: LLMCacheProto | None = None,
        token_meter: TokenMeter | None = None,
        tenant_registry: TenantRegistry | None = None,
        logger: AnalyticsStore | None = None,
        fallback_to_openrouter: bool = True,
    ):
        """Initialize the enhanced router with LiteLLM integration.

        Args:
            models_map: Task-to-model mapping for routing decisions
            learning_engine: RL-based model selection engine
            provider_configs: List of provider configurations with priorities
            cache: LLM response cache implementation
            token_meter: Token usage and cost tracking
            tenant_registry: Multi-tenant configuration registry
            logger: Analytics and logging store
            fallback_to_openrouter: Whether to fallback to original OpenRouter service
        """
        self.config = get_config()
        self.settings = Settings()
        self.provider_configs = provider_configs or self._create_default_providers()
        self._validate_litellm_availability()
        self.learning = learning_engine or LearningEngine()
        self.prompt_engine = PromptEngine()
        self.token_meter = token_meter or TokenMeter()
        self.tenant_registry = tenant_registry
        self.logger = logger
        self.fallback_to_openrouter = fallback_to_openrouter
        self.models_map = self._build_enhanced_model_map(models_map)
        self.cache = cache or self._setup_cache()
        try:
            self.semantic_cache = (
                get_semantic_cache() if getattr(self.settings, "enable_semantic_cache", False) else None
            )
        except Exception:
            self.semantic_cache = None
        self.observability = get_enhanced_observability()
        self.stats = RouterStats()
        self._configure_litellm()
        if self.fallback_to_openrouter:
            from .openrouter_service import OpenRouterService

            self._fallback_service: OpenRouterService | None = OpenRouterService(
                models_map=models_map,
                learning_engine=learning_engine,
                cache=cache,
                token_meter=token_meter,
                tenant_registry=tenant_registry,
                logger=logger,
            )
        else:
            self._fallback_service = None

    def _validate_litellm_availability(self):
        """Validate that LiteLLM is available and configured properly."""
        if not LITELLM_AVAILABLE:
            logger.warning("LiteLLM not available - falling back to basic routing")
            if not self.fallback_to_openrouter:
                raise ImportError("LiteLLM required but not available")

    def _create_default_providers(self) -> StepResult:
        """Create default provider configurations with intelligent prioritization."""
        providers = [
            ProviderConfig(
                name="openai", models=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"], priority=1, cost_multiplier=1.0
            ),
            ProviderConfig(
                name="anthropic",
                models=["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
                priority=2,
                cost_multiplier=0.9,
            ),
            ProviderConfig(
                name="google", models=["gemini-1.5-pro", "gemini-1.5-flash"], priority=3, cost_multiplier=0.8
            ),
            ProviderConfig(
                name="azure", models=["azure/gpt-4o", "azure/gpt-35-turbo"], priority=4, cost_multiplier=1.1
            ),
            ProviderConfig(name="openrouter", models=["openrouter/auto"], priority=5, cost_multiplier=1.2),
        ]
        enabled_providers = []
        for provider in providers:
            try:
                if provider.name == "openai":
                    key = self.config.get_api_key("openai")
                elif provider.name == "anthropic":
                    key = self.config.get_api_key("anthropic")
                elif provider.name == "google":
                    key = self.config.get_api_key("google")
                elif provider.name == "azure":
                    key = self.config.get_api_key("azure")
                elif provider.name == "openrouter":
                    key = self.config.get_api_key("openrouter")
                else:
                    continue
                if key:
                    enabled_providers.append(provider)
                    logger.info(f"Provider {provider.name} enabled with API key")
            except Exception as e:
                logger.debug(f"Provider {provider.name} not configured: {e}")
        return enabled_providers or [ProviderConfig(name="openrouter", models=["openai/gpt-4o-mini"], priority=1)]

    def _build_enhanced_model_map(self, models_map: dict[str, list[str]] | None) -> StepResult:
        """Build enhanced model mapping with provider prefixes."""
        base_map = {
            "general": ["openai/gpt-4o-mini", "anthropic/claude-3-haiku-20240307", "google/gemini-1.5-flash"],
            "analysis": ["openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022", "google/gemini-1.5-pro"],
            "creative": ["anthropic/claude-3-5-sonnet-20241022", "openai/gpt-4o", "google/gemini-1.5-pro"],
            "fast": ["openai/gpt-4o-mini", "google/gemini-1.5-flash", "anthropic/claude-3-haiku-20240307"],
        }
        if models_map:
            base_map.update(models_map)
        return base_map

    def _setup_cache(self) -> StepResult:
        """Set up intelligent caching with semantic similarity."""
        try:
            if getattr(self.config, "enable_cache_global", True) and getattr(self.config, "rate_limit_redis_url", None):
                return RedisLLMCache(
                    url=str(self.config.rate_limit_redis_url), ttl=int(getattr(self.config, "cache_ttl_llm", 3600))
                )
        except Exception as e:
            logger.warning(f"Failed to setup cache: {e}")
        return None

    def _configure_litellm(self):
        """Configure LiteLLM with provider-specific settings."""
        if not LITELLM_AVAILABLE:
            return
        litellm.set_verbose = False
        litellm.drop_params = True
        litellm.success_callback = [self._on_litellm_success]
        litellm.failure_callback = [self._on_litellm_failure]
        litellm.num_retries = 3
        litellm.request_timeout = REQUEST_TIMEOUT_SECONDS

    def _on_litellm_success(self, kwargs, completion_response, start_time, end_time):
        """Handle successful LiteLLM completion."""
        latency_ms = (end_time - start_time) * 1000
        model = kwargs.get("model", "unknown")
        metrics.LLM_LATENCY.labels(**metrics.label_ctx()).observe(latency_ms)
        self.stats.successful_requests += 1
        try:
            if _completion_cost is not None and completion_response is not None:
                cost = _completion_cost(completion_response, model)
                self.stats.total_cost += cost
                metrics.LLM_ESTIMATED_COST.labels(
                    **metrics.label_ctx(), model=model, provider=self._extract_provider_from_model(model)
                ).observe(cost)
        except Exception as e:
            logger.debug(f"Failed to calculate cost: {e}")

    def _on_litellm_failure(self, kwargs, completion_response, start_time, end_time):
        """Handle failed LiteLLM completion."""
        self.stats.failed_requests += 1
        model = kwargs.get("model", "unknown")
        provider = self._extract_provider_from_model(model)
        metrics.LLM_MODEL_SELECTED.labels(**metrics.label_ctx(), task="error", model=model, provider=provider).inc()

    def _extract_provider_from_model(self, model: str) -> StepResult:
        """Extract provider name from model string."""
        if "/" in model:
            return model.split("/")[0]
        return "unknown"

    def _get_fallback_candidates(self, task_type: str) -> StepResult:
        """Get fallback model candidates for a task type."""
        candidates = self.models_map.get(task_type, self.models_map.get("general", []))
        if self.tenant_registry:
            ctx = current_tenant()
            if ctx:
                allowed = self.tenant_registry.get_allowed_models(ctx)
                if allowed:
                    filtered = [c for c in candidates if any(a.lower() in c.lower() for a in allowed)]
                    if filtered:
                        candidates = filtered
        return candidates

    async def route_async(
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.8,
    ) -> StepResult:
        """Asynchronous routing with LiteLLM integration."""
        start_time = time.perf_counter()
        self.stats.total_requests += 1
        with self.observability.trace_llm_call(
            model=model or "auto-select",
            provider="multi-provider",
            task_type=task_type,
            metadata={
                "max_tokens": max_tokens,
                "temperature": temperature,
                **{k: v for k, v in (provider_opts or {}).items() if isinstance(v, str | int | float | bool)},
            },
        ) as trace_context:
            try:
                chosen_model = model or self._select_model(task_type)
                provider = self._extract_provider_from_model(chosen_model)
                trace_context.update({"model": chosen_model, "provider": provider})
                ns = None
                try:
                    ctx = current_tenant()
                    if ctx:
                        ns = f"{ctx.tenant_id}:{ctx.workspace_id}"
                except Exception:
                    ns = None
                semantic_cached = None
                if self.semantic_cache is not None:
                    semantic_cached = await self.semantic_cache.get(
                        prompt=prompt, model=chosen_model, temperature=temperature, max_tokens=max_tokens, namespace=ns
                    )
                if semantic_cached is not None:
                    self.stats.cached_requests += 1
                    metrics.LLM_CACHE_HITS.labels(**metrics.label_ctx(), model=chosen_model, provider=provider).inc()
                    result = dict(semantic_cached)
                    result["cached"] = True
                    result["cache_type"] = "semantic"
                    return result
                else:
                    try:
                        provider = self._extract_provider_from_model(chosen_model)
                        metrics.LLM_CACHE_MISSES.labels(
                            **metrics.label_ctx(), model=chosen_model, provider=provider
                        ).inc()
                    except Exception:
                        pass
                cache_key = None
                if self.cache is not None:
                    cache_key = self._build_cache_key(prompt, chosen_model, provider_opts)
                    cached = self.cache.get(cache_key)
                    if cached:
                        self.stats.cached_requests += 1
                        metrics.LLM_CACHE_HITS.labels(
                            **metrics.label_ctx(), model=chosen_model, provider=provider
                        ).inc()
                        result = dict(cached)
                        result["cached"] = True
                        result["cache_type"] = "traditional"
                        return result
                tokens_in = self.prompt_engine.count_tokens(prompt, chosen_model)
                projected_cost = self.token_meter.estimate_cost(tokens_in, chosen_model)
                if not self._check_budget_limits(projected_cost, task_type):
                    return {
                        "status": "error",
                        "error": "projected cost exceeds budget limit",
                        "model": chosen_model,
                        "tokens": tokens_in,
                    }
                messages = [{"role": "user", "content": prompt}]
                if LITELLM_AVAILABLE:
                    result = await self._call_litellm(
                        model=chosen_model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        task_type=task_type,
                    )
                elif self._fallback_service:
                    result = self._fallback_service.route(
                        prompt=prompt, task_type=task_type, model=model, provider_opts=provider_opts
                    )
                else:
                    raise RuntimeError("No LLM routing service available")
                if result.get("status") == "success":
                    if self.semantic_cache is not None:
                        await self.semantic_cache.set(
                            prompt=prompt,
                            model=chosen_model,
                            response=result,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            namespace=ns,
                        )
                    if self.cache is not None and cache_key:
                        self.cache.set(cache_key, result)
                    tokens_out = result.get("tokens_out", 0)
                    actual_cost = result.get("cost", projected_cost)
                    self.observability.log_llm_interaction(
                        run_context=trace_context,
                        prompt=prompt,
                        response=result.get("response", ""),
                        tokens_input=tokens_in,
                        tokens_output=tokens_out,
                        cost=actual_cost,
                    )
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    if result.get("status") == "success":
                        reward = self._calculate_reward(projected_cost, latency_ms)
                        self.learning.update(task_type, chosen_model, reward=reward)
                    result["cached"] = False
                    return result
            except Exception as e:
                logger.error(f"Enhanced router failed: {e}")
                self.stats.failed_requests += 1
                if self._fallback_service:
                    self.stats.fallback_requests += 1
                    return self._fallback_service.route(
                        prompt=prompt, task_type=task_type, model=model, provider_opts=provider_opts
                    )
                return {
                    "status": "error",
                    "error": str(e),
                    "model": chosen_model if "chosen_model" in locals() else "unknown",
                }
        return {"status": "error", "error": "unreachable - no result from router"}

    async def _call_litellm(
        self, model: str, messages: list[dict], max_tokens: int, temperature: float, task_type: str
    ) -> StepResult:
        """Call LiteLLM with intelligent fallback."""
        fallback_models = self._get_fallback_candidates(task_type)
        models_to_try = [model] + [m for m in fallback_models if m != model]
        for attempt_model in models_to_try[:3]:
            try:
                if _completion is None:
                    raise RuntimeError("LiteLLM completion unavailable")
                response = _completion(
                    model=attempt_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    fallbacks=[m for m in models_to_try if m != attempt_model][:2],
                )
                content = _extract_content(response)
                tokens_in = sum(self.prompt_engine.count_tokens(m["content"], attempt_model) for m in messages)
                tokens_out = self.prompt_engine.count_tokens(content, attempt_model) if content else 0
                cost = 0.0
                try:
                    if _completion_cost is not None:
                        cost = _completion_cost(cast("Any", response), attempt_model)
                except Exception as e:
                    logger.debug(f"Cost calculation failed: {e}")
                return {
                    "status": "success",
                    "model": attempt_model,
                    "response": content,
                    "tokens": tokens_in,
                    "tokens_out": tokens_out,
                    "cost": cost,
                    "provider": self._extract_provider_from_model(attempt_model),
                }
            except Exception as e:
                logger.warning(f"Model {attempt_model} failed: {e}")
                continue
        raise RuntimeError("All model attempts failed")

    def _select_model(self, task_type: str) -> StepResult:
        """Select optimal model using learning engine."""
        candidates = self._get_fallback_candidates(task_type)
        if not candidates:
            return "openai/gpt-4o-mini"
        return self.learning.select_model(task_type, candidates)

    def _build_cache_key(self, prompt: str, model: str, provider_opts: dict | None) -> StepResult:
        """Build semantic cache key."""
        norm_prompt = prompt
        opts_str = str(sorted(provider_opts.items())) if provider_opts else ""
        return make_key(f"{norm_prompt}|opts={opts_str}", model)

    def _check_budget_limits(self, projected_cost: float, task_type: str) -> StepResult:
        """Check if request is within budget limits."""
        max_cost = self.token_meter.max_cost_per_request or float("inf")
        if self.tenant_registry:
            ctx = current_tenant()
            if ctx:
                tenant_limit = self.tenant_registry.get_per_request_limit(ctx, task_type)
                if tenant_limit is not None:
                    max_cost = min(max_cost, tenant_limit)
        return projected_cost <= max_cost

    def _calculate_reward(self, cost: float, latency_ms: float) -> StepResult:
        """Calculate reward for learning engine."""
        cost_norm = min(1.0, cost / 0.01)
        latency_norm = min(1.0, latency_ms / 2000.0)
        return max(0.0, 1.0 - 0.5 * cost_norm - 0.5 * latency_norm)

    def route(
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
    ) -> StepResult:
        """Synchronous wrapper for route_async."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.route_async(prompt, task_type, model, provider_opts))
        except RuntimeError:
            return asyncio.run(self.route_async(prompt, task_type, model, provider_opts))

    def get_stats(self) -> StepResult:
        """Get router runtime statistics."""
        return copy.deepcopy(self.stats)

    def get_available_models(self) -> StepResult:
        """Get list of available models across all providers."""
        models = []
        for provider in self.provider_configs:
            if provider.enabled:
                models.extend(provider.models)
        return models
