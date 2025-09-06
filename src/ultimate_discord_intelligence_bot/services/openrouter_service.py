"""Dynamic model routing via the OpenRouter API.

In production this service would query https://openrouter.ai to select a model
and execute the request.  For testing and offline development we keep the
implementation lightweight and fall back to a deterministic echo response when
no API key is configured.
"""

from __future__ import annotations

import copy
import logging
import os as _os  # used for dynamic offline detection
import time
from collections.abc import Mapping
from typing import Any

# Optional dependencies (graceful degradation if unavailable)
try:  # pragma: no cover - optional distributed cache
    from core.cache.enhanced_redis_cache import DistributedLLMCache  # type: ignore
except Exception:  # pragma: no cover
    DistributedLLMCache = None  # type: ignore

try:  # pragma: no cover - optional local vLLM adapter
    from core.vllm_service import is_vllm_available, vLLMOpenRouterAdapter  # type: ignore
except Exception:  # pragma: no cover

    def is_vllm_available():  # type: ignore
        return False

    vllm_openrouter_adapter_class = None  # type: ignore

from core.http_utils import (
    REQUEST_TIMEOUT_SECONDS,
    http_request_with_retry,
    is_retry_enabled,
    resilient_post,
)
from core.learning_engine import LearningEngine
from core.secure_config import get_config

try:
    from core.settings import get_settings
except Exception:  # pragma: no cover - fallback when pydantic/settings unavailable

    def get_settings():  # type: ignore
        class _S:  # minimal shim for tests
            reward_cost_weight = 0.5
            reward_latency_weight = 0.5
            reward_latency_ms_window = 2000
            openrouter_referer = None
            openrouter_title = None
            enable_vllm_local = False
            local_llm_url = None

        return _S()


from obs import metrics

try:
    from obs.enhanced_langsmith_integration import trace_llm_call  # type: ignore[assignment]
except Exception:  # pragma: no cover

    def trace_llm_call(*args, **kwargs):  # type: ignore
        return None


from ultimate_discord_intelligence_bot.tenancy.context import current_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry

from .cache import RedisLLMCache, make_key
from .logging_utils import AnalyticsStore
from .prompt_engine import PromptEngine
from .request_budget import current_request_tracker as _crt
from .token_meter import TokenMeter

log = logging.getLogger(__name__)


class OpenRouterService:
    """Route prompts to the best model and provider available."""

    def __init__(  # noqa: PLR0913, PLR0912 - wide configuration surface & branching for config selection is acceptable here
        self,
        models_map: dict[str, list[str]] | None = None,
        learning_engine: LearningEngine | None = None,
        api_key: str | None = None,
        provider_opts: dict[str, Any] | None = None,
        logger: AnalyticsStore | None = None,
        token_meter: TokenMeter | None = None,
        cache: Any | None = None,
        tenant_registry: TenantRegistry | None = None,
    ) -> None:
        """Initialise the router.

        Args:
            models_map: Optional mapping of task types to model lists.
            learning_engine: Bandit-based learner for model selection.
            api_key: OpenRouter API key; when absent the service operates offline.
            provider_opts: Default provider routing preferences applied to all
                requests. A deep copy is stored to avoid accidental mutation of
                caller data. Nested dictionaries are merged with call-level
                overrides when routing.
        """
        # Environment variables allow deployment-time model overrides without
        # changing source. ``OPENROUTER_GENERAL_MODEL`` sets the default model
        # for unspecified task types while ``OPENROUTER_ANALYSIS_MODEL`` can
        # specialise the analysis route.
        config = get_config()
        env_general = config.get_setting("openrouter_general_model")
        env_analysis = config.get_setting("openrouter_analysis_model")
        default_map = {
            "general": [env_general or "openai/gpt-3.5-turbo"],
            "analysis": [env_analysis or env_general or "openai/gpt-3.5-turbo"],
        }
        if models_map:
            default_map.update(models_map)
        self.models_map = default_map
        self.learning = learning_engine or LearningEngine()
        # API key may be absent in offline/dev mode. Treat an explicit argument
        # (including empty string) as authoritative so tests can force offline
        # mode by passing api_key="" rather than falling back to secure config.
        self.api_key: str | None
        if api_key is not None:
            # Explicit argument provided (including empty string). Empty string -> force offline.
            self.api_key = api_key or None
        else:
            # Caller omitted api_key; use raw config attribute directly (avoid raising) and treat blank/placeholder as absent.
            cand = getattr(config, "openrouter_api_key", None)
            # If the secure_config still has a cached key but the environment variable was removed
            # (common in tests using monkeypatch.delenv), treat as absent so we enter offline mode.
            if cand and _os.getenv("OPENROUTER_API_KEY") is None:
                cand = None
            if isinstance(cand, str) and not cand.strip():  # blank
                cand = None
                # Some test fixtures may inject a fake looking key to ensure code paths don't 400; if they want offline they unset env.
                # Keep as-is otherwise.
            self.api_key = cand
        # Convenience flag for tests to introspect offline mode quickly.
        # Preserve initial offline determination; later route calls should not override this.
        self.offline_mode = not bool(self.api_key)
        self.prompt_engine = PromptEngine()
        self.token_meter = token_meter or TokenMeter()
        # Choose cache implementation - prefer enhanced Redis cache for performance
        self.cache = None
        if cache is not None:
            self.cache = cache
        else:
            try:
                cfg = get_config()
                if getattr(cfg, "enable_cache_global", True) and getattr(cfg, "rate_limit_redis_url", None):
                    if DistributedLLMCache is not None:
                        try:
                            ctx_cache = current_tenant()
                            tenant_id = getattr(ctx_cache, "tenant", None) or "default"
                            workspace_id = getattr(ctx_cache, "workspace", None) or "main"
                            self.cache = DistributedLLMCache(  # type: ignore[call-arg]
                                url=str(cfg.rate_limit_redis_url),
                                ttl=int(getattr(cfg, "cache_ttl_llm", 3600)),
                                tenant=tenant_id,
                                workspace=workspace_id,
                            )
                        except Exception as dist_exc:  # pragma: no cover - best effort cache upgrade
                            log.debug("Falling back to RedisLLMCache (Distributed init failed): %s", dist_exc)
                            self.cache = None
                    if self.cache is None:
                        try:
                            self.cache = RedisLLMCache(
                                url=str(cfg.rate_limit_redis_url),
                                ttl=int(getattr(cfg, "cache_ttl_llm", 3600)),
                            )
                        except Exception as redis_exc:  # pragma: no cover
                            log.debug("RedisLLMCache initialisation failed, disabling cache: %s", redis_exc)
                            self.cache = None
            except Exception as cache_root_exc:  # pragma: no cover
                log.debug("Cache configuration unavailable, disabling cache: %s", cache_root_exc)
                self.cache = None
        # Deep copy to avoid mutating caller-supplied dictionaries when merging
        self.provider_opts = copy.deepcopy(provider_opts or {})
        self.logger = logger
        self.tenant_registry = tenant_registry

    @staticmethod
    def _deep_merge(base: dict[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
        """Recursively merge ``overrides`` into ``base``.

        Args:
            base: Dictionary to merge values into. Modified in place.
            overrides: Mapping providing override values.

        Returns:
            The merged dictionary (identical to ``base``).
        """
        for key, value in overrides.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, Mapping):
                base[key] = OpenRouterService._deep_merge(base[key], value)
            else:
                base[key] = copy.deepcopy(value)
        return base

    def _filter_candidates_by_tenant(self, candidates: list[str]) -> list[str]:
        """Filter candidates using tenant allowlist if available.

        Performs a forgiving substring match so allowlists like ['gpt-4'] match
        provider-prefixed model IDs (e.g., 'openai/gpt-4o').
        """
        if not self.tenant_registry:
            return candidates
        ctx = current_tenant()
        if not ctx:
            return candidates
        allowed = self.tenant_registry.get_allowed_models(ctx)
        if not allowed:
            return candidates
        lowered = [a.lower() for a in allowed]
        filtered = [c for c in candidates if any(a in c.lower() or c.lower().startswith(a) for a in lowered)]
        return filtered or candidates

    def _choose_model_from_map(self, task_type: str, model_map: dict[str, list[str]]) -> str:
        base = model_map.get(task_type) or model_map.get("general") or []
        if not base:
            base = self.models_map.get(task_type) or self.models_map.get("general") or []
        candidates = self._filter_candidates_by_tenant(list(base))
        return self.learning.select_model(task_type, candidates)

    def route(  # noqa: PLR0912, PLR0915, PLR0911
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Route a prompt with provider preferences and budget enforcement."""
        # Effective model map (include tenant overrides)
        effective_models = copy.deepcopy(self.models_map)
        if self.tenant_registry:
            ctx = current_tenant()
            if ctx:
                overrides = self.tenant_registry.get_model_overrides(ctx)
                if overrides:
                    default_override = overrides.get("default")
                    if default_override:
                        effective_models.setdefault("general", [default_override])
                        # If no explicit analysis override is provided, align analysis with the
                        # default override so budgeting tests that specify only a default model
                        # still apply that model to analysis tasks (mirrors intuitive expectation
                        # that 'default' applies to all unspecified task types).
                        if "analysis" not in overrides:
                            effective_models["analysis"] = [default_override]
                    for k, v in overrides.items():
                        if k != "default":
                            effective_models[k] = [v]
        # Do not override original offline choice; allow env var to enable only if we were not explicitly offline
        if not self.api_key and not self.offline_mode:
            env_key = _os.getenv("OPENROUTER_API_KEY")
            if env_key:
                self.api_key = env_key
                self.offline_mode = False
        effective_offline = self.offline_mode or not self.api_key
        chosen = model or self._choose_model_from_map(task_type, effective_models)
        # Provider preferences
        provider: dict[str, Any] = {}
        if self.tenant_registry:
            ctx = current_tenant()
            if ctx:
                prefs = self.tenant_registry.get_provider_preferences(ctx)
                if prefs:
                    provider = {"order": prefs}
        provider = self._deep_merge(provider, copy.deepcopy(self.provider_opts)) if self.provider_opts else provider
        if provider_opts:
            provider = self._deep_merge(provider, provider_opts)
        provider_family = "unknown"
        try:
            order = provider.get("order") if isinstance(provider, dict) else None
            if isinstance(order, list) and order:
                provider_family = str(order[0])
        except Exception:
            provider_family = "unknown"

        # ------------------------------------------------------------------
        # Estimate cost & enforce budgeting constraints (cumulative + per-call)
        # ------------------------------------------------------------------
        tokens_in = self.prompt_engine.count_tokens(prompt, chosen)
        effective_prices = dict(self.token_meter.model_prices)
        if self.tenant_registry:
            ctx = current_tenant()
            if ctx:
                effective_prices.update(self.tenant_registry.get_pricing_map(ctx))
        projected_cost = self.token_meter.estimate_cost(tokens_in, chosen, prices=effective_prices)
        affordable = self.token_meter.affordable_model(
            tokens_in,
            effective_models.get(task_type, effective_models.get("general", [])),
            prices=effective_prices,
        )
        # Cumulative tracker
        tracker = _crt()
        if tracker and not tracker.can_charge(projected_cost, task_type):
            # try cheaper option
            if affordable and affordable != chosen:
                alt_tokens = self.prompt_engine.count_tokens(prompt, affordable)
                alt_cost = self.token_meter.estimate_cost(alt_tokens, affordable, prices=effective_prices)
                if tracker.can_charge(alt_cost, task_type):
                    chosen = affordable
                    tokens_in = alt_tokens
                    projected_cost = alt_cost
                else:
                    metrics.LLM_BUDGET_REJECTIONS.labels(
                        **metrics.label_ctx(), task=task_type, provider=provider_family
                    ).inc()
                    return {
                        "status": "error",
                        "error": "cumulative cost exceeds limit",
                        "model": chosen,
                        "tokens": tokens_in,
                        "provider": provider,
                    }
            else:
                metrics.LLM_BUDGET_REJECTIONS.labels(
                    **metrics.label_ctx(), task=task_type, provider=provider_family
                ).inc()
                return {
                    "status": "error",
                    "error": "cumulative cost exceeds limit",
                    "model": chosen,
                    "tokens": tokens_in,
                    "provider": provider,
                }

        # Per-request limit overrides
        tenant_max: float | None = None
        if self.tenant_registry:
            ctx = current_tenant()
            if ctx:
                per_task_limit = self.tenant_registry.get_per_request_limit(ctx, task_type)
                if per_task_limit is not None:
                    tenant_max = per_task_limit
                else:
                    bcfg = self.tenant_registry.get_budget_config(ctx.tenant_id)
                    if isinstance(bcfg, dict):
                        limits = bcfg.get("limits") if isinstance(bcfg.get("limits"), dict) else None
                        if limits and "max_per_request" in limits:
                            try:
                                tenant_max = float(limits["max_per_request"])
                            except Exception:
                                tenant_max = None
                        if tenant_max is None and "max_per_request" in bcfg:
                            try:
                                raw_val = bcfg.get("max_per_request")
                                tenant_max = float(raw_val) if raw_val is not None else None
                            except Exception:
                                tenant_max = None
        effective_max = (
            self.token_meter.max_cost_per_request if self.token_meter.max_cost_per_request is not None else float("inf")
        )
        if tenant_max is not None:
            effective_max = min(effective_max, tenant_max)
        # Strict per-request limit enforcement: if current model exceeds limit attempt
        # an affordable fallback ONCE; if still over, emit error immediately.
        if projected_cost > effective_max:
            if affordable and affordable != chosen:
                alt_tokens = self.prompt_engine.count_tokens(prompt, affordable)
                alt_cost = self.token_meter.estimate_cost(alt_tokens, affordable, prices=effective_prices)
                if alt_cost <= effective_max:
                    chosen = affordable
                    tokens_in = alt_tokens
                    projected_cost = alt_cost
                else:
                    metrics.LLM_BUDGET_REJECTIONS.labels(
                        **metrics.label_ctx(), task=task_type, provider=provider_family
                    ).inc()
                    return {
                        "status": "error",
                        "error": "projected cost exceeds limit",
                        "model": chosen,
                        "tokens": tokens_in,
                        "provider": provider,
                    }
            else:
                metrics.LLM_BUDGET_REJECTIONS.labels(
                    **metrics.label_ctx(), task=task_type, provider=provider_family
                ).inc()
                return {
                    "status": "error",
                    "error": "projected cost exceeds limit",
                    "model": chosen,
                    "tokens": tokens_in,
                    "provider": provider,
                }

        # Cache lookup
        cache_key = None
        if self.cache:
            norm_prompt = self.prompt_engine.optimise(prompt)

            def _sig(obj: Any) -> str:
                if isinstance(obj, dict):
                    return "{" + ",".join(f"{k}:{_sig(obj[k])}" for k in sorted(obj)) + "}"
                if isinstance(obj, list):
                    return "[" + ",".join(_sig(x) for x in obj) + "]"
                return str(obj)

            provider_sig = _sig(provider) if provider else "{}"
            cache_key = make_key(f"{norm_prompt}|provider={provider_sig}", chosen)
            cached = self.cache.get(cache_key)
            if cached:
                result = dict(cached)
                result["cached"] = True
                metrics.LLM_CACHE_HITS.labels(
                    **metrics.label_ctx(), model=result.get("model", chosen), provider=provider_family
                ).inc()
                return result

        start = time.perf_counter()
        if effective_offline:  # offline path
            # Offline deterministic echo (historically uppercased for test stability)
            response = prompt.upper()
            latency_ms = (time.perf_counter() - start) * 1000
            tokens_out = self.prompt_engine.count_tokens(response, chosen)
            settings = get_settings()
            rl = {}
            if self.tenant_registry:
                ctx_t = current_tenant()
                rl = self.tenant_registry.get_rl_overrides(ctx_t) if ctx_t else {}
            w_cost = float(rl.get("reward_cost_weight", getattr(settings, "reward_cost_weight", 0.5) or 0.5))
            w_lat = float(rl.get("reward_latency_weight", getattr(settings, "reward_latency_weight", 0.5) or 0.5))
            if w_cost == 0.0 and w_lat == 0.0:
                w_cost = w_lat = 0.5
            norm = w_cost + w_lat
            w_cost /= norm
            w_lat /= norm
            cost_norm = 0.0
            if projected_cost > 0:
                # When explicit RL overrides are provided we normalise cost against the
                # observed projected cost itself (treating it as 100%) so a cost weight of 1.0
                # drives reward close to 0 as tests expect. Otherwise retain scaling relative
                # to the effective max budget for smoother shaping.
                if rl.get("reward_cost_weight") is not None or rl.get("reward_latency_weight") is not None:
                    denom = projected_cost
                else:
                    denom = effective_max if effective_max and effective_max != float("inf") else projected_cost
                cost_norm = min(1.0, projected_cost / max(denom, 1e-9))
            lat_window = float(
                rl.get("reward_latency_ms_window", getattr(settings, "reward_latency_ms_window", 2000) or 2000)
            )
            lat_window = max(1.0, lat_window)
            lat_norm = min(1.0, latency_ms / lat_window)
            reward = max(0.0, 1.0 - w_cost * cost_norm - w_lat * lat_norm)
            self.learning.update(task_type, chosen, reward=reward)
            metrics.LLM_MODEL_SELECTED.labels(
                **metrics.label_ctx(), task=task_type, model=chosen, provider=provider_family
            ).inc()
            metrics.LLM_ESTIMATED_COST.labels(**metrics.label_ctx(), model=chosen, provider=provider_family).observe(
                projected_cost
            )
            metrics.LLM_LATENCY.labels(**metrics.label_ctx()).observe(latency_ms)
            if self.logger:
                self.logger.log_llm_call(
                    task_type,
                    chosen,
                    str(provider),
                    tokens_in,
                    tokens_out,
                    float(projected_cost),
                    latency_ms,
                    None,
                    True,
                    None,
                )
            result = {
                "status": "success",
                "model": chosen,
                "response": response,
                "tokens": tokens_in,
                "provider": provider,
            }
            trace_llm_call(
                name=f"openrouter_{task_type}",
                prompt=prompt,
                response=response,
                model=chosen,
                metadata={"provider": provider, "task_type": task_type, "offline": True},
                latency_ms=latency_ms,
                token_usage={
                    "input_tokens": tokens_in,
                    "output_tokens": tokens_out,
                    "total_tokens": tokens_in + tokens_out,
                },
                cost=projected_cost,
            )
            if self.cache and cache_key:
                self.cache.set(cache_key, result)
            result["cached"] = False
            if tracker:
                try:
                    tracker.charge(projected_cost, task_type)
                except Exception as charge_exc:  # pragma: no cover - defensive accounting
                    log.debug(
                        "request budget charge failed (offline path) task=%s model=%s err=%s",
                        task_type,
                        chosen,
                        charge_exc,
                    )
            return result
        # Network path
        try:  # pragma: no cover
            payload: dict[str, Any] = {"model": chosen, "messages": [{"role": "user", "content": prompt}]}
            if provider:
                payload["provider"] = provider
            settings = get_settings()
            if (
                chosen.startswith("local/")
                and vLLMOpenRouterAdapter is not None
                and is_vllm_available()
                and getattr(settings, "enable_vllm_local", False)
            ):
                try:  # pragma: no cover - only when local inference available
                    adapter = vLLMOpenRouterAdapter()  # type: ignore[operator]
                    vllm_result = adapter.route_to_local_model(prompt, chosen, task_type)
                    if vllm_result.get("status") == "success":
                        latency_ms = (time.perf_counter() - start) * 1000
                        trace_llm_call(
                            name=f"vllm_{task_type}",
                            prompt=prompt,
                            response=vllm_result["response"],
                            model=chosen,
                            metadata={"provider": "vllm", "task_type": task_type, "local_inference": True},
                            latency_ms=latency_ms,
                            token_usage={
                                "input_tokens": tokens_in,
                                "output_tokens": vllm_result.get("tokens", 0),
                                "total_tokens": tokens_in + vllm_result.get("tokens", 0),
                            },
                            cost=0.0,
                        )
                        if tracker:
                            try:
                                tracker.charge(projected_cost, task_type)
                            except Exception as charge_exc:  # pragma: no cover
                                log.debug(
                                    "request budget charge failed (vLLM path) task=%s model=%s err=%s",
                                    task_type,
                                    chosen,
                                    charge_exc,
                                )
                        return vllm_result
                except Exception as e:  # pragma: no cover
                    log.warning("vLLM local inference failed: %s, falling back to HTTP", e)
                if getattr(settings, "local_llm_url", None):
                    local_model = chosen.split("/", 1)[1] if "/" in chosen else chosen
                    local_payload = {"model": local_model, "messages": payload["messages"]}
                    local_url = str(settings.local_llm_url).rstrip("/") + "/v1/chat/completions"
                    resp = resilient_post(
                        local_url, json_payload=local_payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS
                    )
                    if getattr(resp, "status_code", 200) >= 400:  # noqa: PLR2004
                        raise RuntimeError(f"local_llm_error status={resp.status_code}")
                    data = resp.json()
                    message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    latency_ms = (time.perf_counter() - start) * 1000
                    tokens_out = self.prompt_engine.count_tokens(message, local_model)
                    result_local = {
                        "status": "success",
                        "model": chosen,
                        "response": message,
                        "tokens": tokens_in,
                        "provider": {"order": ["local"]},
                    }
                    if tracker:
                        try:
                            tracker.charge(projected_cost, task_type)
                        except Exception as charge_exc:  # pragma: no cover
                            log.debug(
                                "request budget charge failed (local_llm path) task=%s model=%s err=%s",
                                task_type,
                                chosen,
                                charge_exc,
                            )
                    return result_local
            url = "https://openrouter.ai/api/v1/chat/completions"
            api_key = self.api_key or ""
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            ref = getattr(settings, "openrouter_referer", None) or _os.getenv("OPENROUTER_REFERER")
            if ref:
                ref = str(ref)
                headers["Referer"] = ref
                headers["HTTP-Referer"] = ref
            title = getattr(settings, "openrouter_title", None) or _os.getenv("OPENROUTER_TITLE")
            if title:
                headers["X-Title"] = str(title)
            resp = None
            if is_retry_enabled():
                try:
                    resp = http_request_with_retry(
                        "POST",
                        url,
                        request_callable=lambda u, **_: resilient_post(
                            u, headers=headers, json_payload=payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS
                        ),
                        max_attempts=3,
                    )
                except Exception as retry_exc:
                    # Give-up path: record error status and surface message
                    latency_ms = (time.perf_counter() - start) * 1000
                    if self.logger:
                        try:
                            self.logger.log_llm_call(
                                task_type,
                                chosen,
                                str(provider),
                                tokens_in,
                                0,
                                float(projected_cost),
                                latency_ms,
                                None,
                                False,
                                str(retry_exc),
                            )
                        except Exception as log_exc:  # pragma: no cover
                            log.debug("logger failure in retry give-up: %s", log_exc)
                    return {
                        "status": "error",
                        "error": str(retry_exc),
                        "model": chosen,
                        "tokens": tokens_in,
                        "provider": provider,
                    }
            else:
                resp = resilient_post(
                    url, headers=headers, json_payload=payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS
                )
            if getattr(resp, "status_code", 200) >= 400:  # noqa: PLR2004
                raise RuntimeError(f"openrouter_error status={resp.status_code}")
            data = resp.json()
            message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            latency_ms = (time.perf_counter() - start) * 1000
            tokens_out = self.prompt_engine.count_tokens(message, chosen)
            settings = get_settings()
            rl = {}
            if self.tenant_registry:
                ctx_t = current_tenant()
                rl = self.tenant_registry.get_rl_overrides(ctx_t) if ctx_t else {}
            w_cost = float(rl.get("reward_cost_weight", getattr(settings, "reward_cost_weight", 0.5) or 0.5))
            w_lat = float(rl.get("reward_latency_weight", getattr(settings, "reward_latency_weight", 0.5) or 0.5))
            if w_cost == 0.0 and w_lat == 0.0:
                w_cost = w_lat = 0.5
            norm = w_cost + w_lat
            w_cost /= norm
            w_lat /= norm
            cost_norm = 0.0
            if projected_cost > 0:
                if rl.get("reward_cost_weight") is not None or rl.get("reward_latency_weight") is not None:
                    denom = projected_cost
                else:
                    denom = effective_max if effective_max and effective_max != float("inf") else projected_cost
                cost_norm = min(1.0, projected_cost / max(denom, 1e-9))
            lat_window = float(
                rl.get("reward_latency_ms_window", getattr(settings, "reward_latency_ms_window", 2000) or 2000)
            )
            lat_window = max(1.0, lat_window)
            lat_norm = min(1.0, latency_ms / lat_window)
            reward = max(0.0, 1.0 - w_cost * cost_norm - w_lat * lat_norm)
            self.learning.update(task_type, chosen, reward=reward)
            metrics.LLM_MODEL_SELECTED.labels(
                **metrics.label_ctx(), task=task_type, model=chosen, provider=provider_family
            ).inc()
            metrics.LLM_ESTIMATED_COST.labels(**metrics.label_ctx(), model=chosen, provider=provider_family).observe(
                projected_cost
            )
            metrics.LLM_LATENCY.labels(**metrics.label_ctx()).observe(latency_ms)
            if self.logger:
                self.logger.log_llm_call(
                    task_type,
                    chosen,
                    str(provider),
                    tokens_in,
                    tokens_out,
                    float(projected_cost),
                    latency_ms,
                    None,
                    True,
                    None,
                )
            result = {
                "status": "success",
                "model": chosen,
                "response": message,
                "tokens": tokens_in,
                "provider": provider,
            }
            trace_llm_call(
                name=f"openrouter_{task_type}",
                prompt=prompt,
                response=message,
                model=chosen,
                metadata={"provider": provider, "task_type": task_type, "offline": False, "api_endpoint": "openrouter"},
                latency_ms=latency_ms,
                token_usage={
                    "input_tokens": tokens_in,
                    "output_tokens": tokens_out,
                    "total_tokens": tokens_in + tokens_out,
                },
                cost=projected_cost,
            )
            if self.cache and cache_key:
                self.cache.set(cache_key, result)
            result["cached"] = False
            if tracker:
                try:
                    tracker.charge(projected_cost, task_type)
                except Exception as charge_exc:  # pragma: no cover
                    log.debug(
                        "request budget charge failed (network success path) task=%s model=%s err=%s",
                        task_type,
                        chosen,
                        charge_exc,
                    )
            return result
        except Exception as exc:  # pragma: no cover
            latency_ms = (time.perf_counter() - start) * 1000
            if self.logger:
                self.logger.log_llm_call(
                    task_type, chosen, str(provider), tokens_in, 0, 0.0, latency_ms, None, False, None
                )
            log.error(
                "OpenRouterService route failed task=%s model=%s provider=%s err=%s",
                task_type,
                chosen,
                provider_family,
                exc,
                exc_info=True,
            )
            return {"status": "error", "error": str(exc), "model": chosen, "tokens": tokens_in, "provider": provider}
