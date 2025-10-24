# ruff: noqa: I001
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
from typing import Any, Protocol, runtime_checkable, cast, TYPE_CHECKING

from core.cache.semantic_cache import get_semantic_cache
from core.http_utils import REQUEST_TIMEOUT_SECONDS
from core.learning_engine import LearningEngine
from core.secure_config import get_config
from obs import metrics
from obs.langsmith_integration import get_enhanced_observability
from .prompt_engine import PromptEngine
from .token_meter import TokenMeter
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant

from .cache import RedisLLMCache, make_key

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Callable
    from .logging_utils import AnalyticsStore
    from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry
    from ultimate_discord_intelligence_bot.step_result import StepResult


class LLMCacheProto(Protocol):  # minimal structural type used in this module
    def get(self, key: str) -> StepResult: ...
    def set(self, key: str, value: dict[str, Any]) -> StepResult: ...


# --- LiteLLM response shape (duck-typed) -------------------------------------
@runtime_checkable
class _LiteLLMMsg(Protocol):  # pragma: no cover - structural typing only
    content: str | None


@runtime_checkable
class _LiteLLMChoice(Protocol):  # pragma: no cover
    message: _LiteLLMMsg


@runtime_checkable
class _LiteLLMResponse(Protocol):  # pragma: no cover
    choices: Sequence[_LiteLLMChoice]


def _extract_content(resp: Any) -> StepResult:
    """Best-effort extraction of response text from a LiteLLM completion.

    Handles both standard response objects exposing ``choices[0].message.content``
    and fallback attributes; never raises and always returns a string for
    downstream token counting.
    """
    try:
        if isinstance(resp, _LiteLLMResponse):  # structural check
            if resp.choices:
                msg = resp.choices[0].message
                if msg and getattr(msg, "content", None) is not None:
                    return str(msg.content)
        # Fallbacks: streaming wrappers may expose ``content`` directly
        direct = getattr(resp, "content", None)
        if direct is not None:
            return str(direct)
    except Exception:  # pragma: no cover - defensive
        pass
    return ""


litellm: Any  # runtime module if available; used under guards
_completion_cost: Callable[..., float] | None = None
try:
    import litellm as _litellm
    from litellm import completion as _completion

    try:
        from litellm.cost_calculator import completion_cost as _cc

        _completion_cost = _cc  # assign only if import succeeds
    except Exception:  # pragma: no cover
        _completion_cost = None
    litellm = _litellm
    LITELLM_AVAILABLE = True
except Exception:  # pragma: no cover
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

        # Initialize provider configurations
        self.provider_configs = provider_configs or self._create_default_providers()
        self._validate_litellm_availability()

        # Core components
        self.learning = learning_engine or LearningEngine()
        self.prompt_engine = PromptEngine()
        self.token_meter = token_meter or TokenMeter()
        self.tenant_registry = tenant_registry
        self.logger = logger
        self.fallback_to_openrouter = fallback_to_openrouter

        # Model mapping with enhanced defaults
        self.models_map = self._build_enhanced_model_map(models_map)

        # Cache setup (both traditional and semantic)
        self.cache = cache or self._setup_cache()
        # Semantic cache behind explicit feature flag
        try:
            self.semantic_cache = (
                get_semantic_cache() if getattr(self.settings, "enable_semantic_cache", False) else None
            )
        except Exception:
            self.semantic_cache = None

        # Enhanced observability
        self.observability = get_enhanced_observability()

        # Runtime statistics
        self.stats = RouterStats()

        # Initialize LiteLLM configuration
        self._configure_litellm()

        # Original OpenRouter service for fallback
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
                name="openai",
                models=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                priority=1,
                cost_multiplier=1.0,
            ),
            ProviderConfig(
                name="anthropic",
                models=["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
                priority=2,
                cost_multiplier=0.9,
            ),
            ProviderConfig(
                name="google",
                models=["gemini-1.5-pro", "gemini-1.5-flash"],
                priority=3,
                cost_multiplier=0.8,
            ),
            ProviderConfig(
                name="azure",
                models=["azure/gpt-4o", "azure/gpt-35-turbo"],
                priority=4,
                cost_multiplier=1.1,
            ),
            ProviderConfig(
                name="openrouter",
                models=["openrouter/auto"],
                priority=5,
                cost_multiplier=1.2,
            ),
        ]

        # Filter providers based on available API keys
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
            "general": [
                "openai/gpt-4o-mini",
                "anthropic/claude-3-haiku-20240307",
                "google/gemini-1.5-flash",
            ],
            "analysis": [
                "openai/gpt-4o",
                "anthropic/claude-3-5-sonnet-20241022",
                "google/gemini-1.5-pro",
            ],
            "creative": [
                "anthropic/claude-3-5-sonnet-20241022",
                "openai/gpt-4o",
                "google/gemini-1.5-pro",
            ],
            "fast": [
                "openai/gpt-4o-mini",
                "google/gemini-1.5-flash",
                "anthropic/claude-3-haiku-20240307",
            ],
        }

        if models_map:
            base_map.update(models_map)

        return base_map

    def _setup_cache(self) -> StepResult:
        """Set up intelligent caching with semantic similarity."""
        try:
            if getattr(self.config, "enable_cache_global", True) and getattr(self.config, "rate_limit_redis_url", None):
                return RedisLLMCache(
                    url=str(self.config.rate_limit_redis_url),
                    ttl=int(getattr(self.config, "cache_ttl_llm", 3600)),
                )
        except Exception as e:
            logger.warning(f"Failed to setup cache: {e}")
        return None

    def _configure_litellm(self):
        """Configure LiteLLM with provider-specific settings."""
        if not LITELLM_AVAILABLE:
            return

        # Set global configuration
        litellm.set_verbose = False  # Reduce noise in logs
        litellm.drop_params = True  # Allow extra parameters
        litellm.success_callback = [self._on_litellm_success]
        litellm.failure_callback = [self._on_litellm_failure]

        # Configure retries and timeouts
        litellm.num_retries = 3
        litellm.request_timeout = REQUEST_TIMEOUT_SECONDS

    def _on_litellm_success(self, kwargs, completion_response, start_time, end_time):
        """Handle successful LiteLLM completion."""
        latency_ms = (end_time - start_time) * 1000
        model = kwargs.get("model", "unknown")

        # Update metrics
        metrics.LLM_LATENCY.labels(**metrics.label_ctx()).observe(latency_ms)
        self.stats.successful_requests += 1

        # Calculate cost if available
        try:
            if _completion_cost is not None and completion_response is not None:
                cost = _completion_cost(completion_response, model)
                self.stats.total_cost += cost
                metrics.LLM_ESTIMATED_COST.labels(
                    **metrics.label_ctx(),
                    model=model,
                    provider=self._extract_provider_from_model(model),
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

        # Filter by tenant allowlist if applicable
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

        # Start comprehensive tracing
        with self.observability.trace_llm_call(
            model=model or "auto-select",
            provider="multi-provider",
            task_type=task_type,
            metadata={
                "max_tokens": max_tokens,
                "temperature": temperature,
                **({k: v for k, v in (provider_opts or {}).items() if isinstance(v, str | int | float | bool)}),
            },
        ) as trace_context:
            try:
                # Model selection
                chosen_model = model or self._select_model(task_type)
                provider = self._extract_provider_from_model(chosen_model)

                # Update trace context with selected model
                trace_context.update({"model": chosen_model, "provider": provider})

                # Check semantic cache first (higher priority)
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
                        prompt=prompt,
                        model=chosen_model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        namespace=ns,
                    )
                if semantic_cached is not None:  # Semantic cache hit path
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

                # Check traditional cache as fallback
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

                # Cost estimation and budget checks
                tokens_in = self.prompt_engine.count_tokens(prompt, chosen_model)
                projected_cost = self.token_meter.estimate_cost(tokens_in, chosen_model)

                if not self._check_budget_limits(projected_cost, task_type):
                    return {
                        "status": "error",
                        "error": "projected cost exceeds budget limit",
                        "model": chosen_model,
                        "tokens": tokens_in,
                    }

                # Prepare LiteLLM request
                messages = [{"role": "user", "content": prompt}]

                if LITELLM_AVAILABLE:
                    # Use LiteLLM for intelligent routing
                    result = await self._call_litellm(
                        model=chosen_model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        task_type=task_type,
                    )
                # Fallback to original OpenRouter service
                elif self._fallback_service:
                    result = self._fallback_service.route(
                        prompt=prompt,
                        task_type=task_type,
                        model=model,
                        provider_opts=provider_opts,
                    )
                else:
                    raise RuntimeError("No LLM routing service available")

                # Cache successful response in both caches
                if result.get("status") == "success":
                    # Store in semantic cache (higher priority)
                    if self.semantic_cache is not None:
                        await self.semantic_cache.set(
                            prompt=prompt,
                            model=chosen_model,
                            response=result,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            namespace=ns,
                        )

                    # Store in traditional cache as backup
                    if self.cache is not None and cache_key:
                        self.cache.set(cache_key, result)

                    # Log comprehensive LLM interaction data
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

                    # Update learning engine with reward
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    if result.get("status") == "success":
                        reward = self._calculate_reward(projected_cost, latency_ms)
                        self.learning.update(task_type, chosen_model, reward=reward)

                    result["cached"] = False
                    return result

            except Exception as e:
                logger.error(f"Enhanced router failed: {e}")
                self.stats.failed_requests += 1

                # Try fallback to original service
                if self._fallback_service:
                    self.stats.fallback_requests += 1
                    return self._fallback_service.route(
                        prompt=prompt,
                        task_type=task_type,
                        model=model,
                        provider_opts=provider_opts,
                    )

                return {
                    "status": "error",
                    "error": str(e),
                    "model": chosen_model if "chosen_model" in locals() else "unknown",
                }
        # Should not reach here; provide defensive error contract for type-checkers
        return {"status": "error", "error": "unreachable - no result from router"}

    async def _call_litellm(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        task_type: str,
    ) -> StepResult:
        """Call LiteLLM with intelligent fallback."""
        fallback_models = self._get_fallback_candidates(task_type)

        # Try primary model first, then fallbacks
        models_to_try = [model] + [m for m in fallback_models if m != model]

        for attempt_model in models_to_try[:3]:  # Limit to 3 attempts
            try:
                # Async completion with LiteLLM
                if _completion is None:
                    raise RuntimeError("LiteLLM completion unavailable")
                # _completion may be synchronous; call directly (wrapped in async context for uniform interface)
                response = _completion(
                    model=attempt_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    fallbacks=[m for m in models_to_try if m != attempt_model][:2],
                )
                # Extract response content safely
                content = _extract_content(response)

                # Calculate tokens and cost
                tokens_in = sum(self.prompt_engine.count_tokens(m["content"], attempt_model) for m in messages)
                tokens_out = self.prompt_engine.count_tokens(content, attempt_model) if content else 0

                cost = 0.0
                try:
                    if _completion_cost is not None:
                        # Cast to silence mypy; runtime function can handle flexible shapes
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
            return "openai/gpt-4o-mini"  # Ultimate fallback

        return self.learning.select_model(task_type, candidates)

    def _build_cache_key(self, prompt: str, model: str, provider_opts: dict | None) -> StepResult:
        """Build semantic cache key."""
        norm_prompt = prompt
        opts_str = str(sorted(provider_opts.items())) if provider_opts else ""
        # Use canonical key function for compatibility with RedisLLMCache/BoundedLRUCache
        return make_key(f"{norm_prompt}|opts={opts_str}", model)

    def _check_budget_limits(self, projected_cost: float, task_type: str) -> StepResult:
        """Check if request is within budget limits."""
        max_cost = self.token_meter.max_cost_per_request or float("inf")

        # Check tenant-specific limits
        if self.tenant_registry:
            ctx = current_tenant()
            if ctx:
                tenant_limit = self.tenant_registry.get_per_request_limit(ctx, task_type)
                if tenant_limit is not None:
                    max_cost = min(max_cost, tenant_limit)

        return projected_cost <= max_cost

    def _calculate_reward(self, cost: float, latency_ms: float) -> StepResult:
        """Calculate reward for learning engine."""
        # Normalize cost and latency for reward calculation
        cost_norm = min(1.0, cost / 0.01)  # $0.01 normalization
        latency_norm = min(1.0, latency_ms / 2000.0)  # 2s normalization

        # Higher reward for lower cost and latency
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
            # No event loop running, create new one
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
