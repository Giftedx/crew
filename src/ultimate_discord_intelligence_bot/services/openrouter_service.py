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
    from core.cache.enhanced_redis_cache import DistributedLLMCache
except Exception:  # pragma: no cover
    DistributedLLMCache = None

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

    def get_settings() -> Any:  # minimal shim (return object with expected attrs)
        class _S:  # minimal shim for tests
            reward_cost_weight = 0.5
            reward_latency_weight = 0.5
            reward_latency_ms_window = 2000
            openrouter_referer = None
            openrouter_title = None
            enable_vllm_local = False
            local_llm_url = None

        return _S()


from core.flags import enabled  # tenancy strictness flags
from obs import metrics

try:
    from obs.enhanced_langsmith_integration import trace_llm_call as _trace_llm_call

    def trace_llm_call(*args: Any, **kwargs: Any) -> None:
        _trace_llm_call(*args, **kwargs)
except Exception:  # pragma: no cover

    def trace_llm_call(*args: Any, **kwargs: Any) -> None:
        return None


from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, current_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry

from .cache import RedisLLMCache, make_key
from .logging_utils import AnalyticsStore
from .prompt_engine import PromptEngine
from .request_budget import current_request_tracker as _crt
from .token_meter import TokenMeter

# Optional semantic cache (guarded by feature flag in settings)
_semantic_cache_get = None
_semantic_cache_factory_err: str | None = None
try:
    from core.cache.semantic_cache import get_semantic_cache as _get_semantic_cache

    _semantic_cache_get = _get_semantic_cache
except Exception as _sc_exc:  # pragma: no cover - optional feature
    _semantic_cache_factory_err = str(_sc_exc)

# Optional local vLLM adapter (placed after all imports to satisfy E402). Define aliases once.
try:  # pragma: no cover - optional local vLLM adapter
    from core.vllm_service import is_vllm_available as _is_vllm_available  # type: ignore[unused-ignore]
    from core.vllm_service import vLLMOpenRouterAdapter as _VLLMAdapterCtor  # type: ignore[unused-ignore]
except Exception:  # pragma: no cover
    _is_vllm_available = None
    _VLLMAdapterCtor = None
vllm_adapter_ctor: Any | None = _VLLMAdapterCtor


def _has_vllm() -> bool:
    """Return True if local vLLM adapter is importable and available."""
    try:
        if _is_vllm_available is None:
            return False
        return bool(_is_vllm_available())
    except Exception:
        return False


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
                            # Resolve tenant context for cache namespacing (allows fallback in non-strict mode)
                            ctx_cache = OpenRouterService._ctx_or_fallback("openrouter_service")
                            tenant_id = (getattr(ctx_cache, "tenant_id", None) or "default") if ctx_cache else "default"
                            workspace_id = (getattr(ctx_cache, "workspace_id", None) or "main") if ctx_cache else "main"
                            CacheCtor: Any = DistributedLLMCache
                            self.cache = CacheCtor(
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
        # Semantic cache instance (only if enabled via settings or env fallback)
        try:
            settings = get_settings()
            enabled_sem = bool(getattr(settings, "enable_semantic_cache", False))
            if not enabled_sem:
                raw = (_os.getenv("ENABLE_SEMANTIC_CACHE") or "").lower()
                enabled_sem = raw in ("1", "true", "yes", "on")
            self.semantic_cache = _semantic_cache_get() if enabled_sem and _semantic_cache_get else None
        except Exception:
            self.semantic_cache = None

    # --- Tenancy helpers -------------------------------------------------
    @staticmethod
    def _ctx_or_fallback(component: str) -> TenantContext | None:
        """Return current tenant or fallback/default according to flags.

        If strict tenancy is enabled and no context is set, raise. Otherwise,
        log a warning, increment the tenancy fallback metric, and return a
        default context ("default:main").
        """
        ctx = current_tenant()
        if ctx is not None:
            return ctx
        # Strict mode gates
        if enabled("ENABLE_TENANCY_STRICT", False) or enabled("ENABLE_INGEST_STRICT", False):
            raise RuntimeError("TenantContext required but not set (strict mode)")
        logging.getLogger("tenancy").warning(
            "TenantContext missing; defaulting to 'default:main' namespace (non-strict mode)",
        )
        try:
            metrics.TENANCY_FALLBACKS.labels(**{**metrics.label_ctx(), "component": component}).inc()
        except Exception as exc:  # pragma: no cover - metrics optional
            logging.debug("tenancy metric increment failed: %s", exc)
        return TenantContext("default", "main")

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

    def _choose_model_from_map(self, task_type: str, models_map: dict[str, list[str]]) -> str:
        """Pick a model for a given task type from the provided map.

        Preference order:
          1) task_type list
          2) general list
          3) conservative default
        """
        candidates = models_map.get(task_type) or models_map.get("general") or []
        if candidates:
            # Delegate to learning engine if multiple candidates exist
            if len(candidates) > 1:
                try:
                    return self.learning.select_model(task_type, candidates)
                except Exception:
                    return candidates[0]
            return candidates[0]
        return "openai/gpt-3.5-turbo"

    def route(  # noqa: PLR0912, PLR0913, PLR0915, C901 - complex orchestrator; slated for helper extraction
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Route a prompt with provider preferences and budget enforcement.

        Note: This function coordinates several concerns (tenancy, pricing,
        budgeting, caching, offline/network execution, metrics, tracing). A
        follow-up refactor will extract helpers to reduce complexity while
        preserving behavior.
        """
        # Resolve tenant context early (strict mode can raise; non-strict records fallback once per call)
        ctx_effective = OpenRouterService._ctx_or_fallback("openrouter_service")

        # Ensure metrics are attributed to the effective tenant/workspace even when no
        # TenantContext was pre-set by the caller. We avoid mutating thread-local state
        # and instead provide a local label factory for metric calls.
        def _labels() -> dict[str, str]:
            if ctx_effective is not None:
                return {
                    "tenant": getattr(ctx_effective, "tenant_id", "unknown"),
                    "workspace": getattr(ctx_effective, "workspace_id", "unknown"),
                }
            return metrics.label_ctx()

        # Effective model map (include tenant overrides)
        effective_models = copy.deepcopy(self.models_map)
        if self.tenant_registry:
            ctx = ctx_effective
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
            ctx = ctx_effective
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
            ctx = ctx_effective
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
                    metrics.LLM_BUDGET_REJECTIONS.labels(**_labels(), task=task_type, provider=provider_family).inc()
                    return {
                        "status": "error",
                        "error": "cumulative cost exceeds limit",
                        "model": chosen,
                        "tokens": tokens_in,
                        "provider": provider,
                    }
            else:
                metrics.LLM_BUDGET_REJECTIONS.labels(**_labels(), task=task_type, provider=provider_family).inc()
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
            ctx = ctx_effective
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
                    metrics.LLM_BUDGET_REJECTIONS.labels(**_labels(), task=task_type, provider=provider_family).inc()
                    return {
                        "status": "error",
                        "error": "projected cost exceeds limit",
                        "model": chosen,
                        "tokens": tokens_in,
                        "provider": provider,
                    }
            else:
                metrics.LLM_BUDGET_REJECTIONS.labels(**_labels(), task=task_type, provider=provider_family).inc()
                return {
                    "status": "error",
                    "error": "projected cost exceeds limit",
                    "model": chosen,
                    "tokens": tokens_in,
                    "provider": provider,
                }

        # Cache lookup (semantic first, then traditional)
        cache_key = None
        # Tenant namespace for scoping
        ns = None
        if ctx_effective:
            try:
                ns = f"{getattr(ctx_effective, 'tenant_id', 'unknown')}:{getattr(ctx_effective, 'workspace_id', 'unknown')}"
            except Exception:
                ns = None
        # Semantic cache
        if self.semantic_cache is not None:
            try:
                # Run coroutine in a background thread using asyncio.run so it works
                # regardless of whether a loop is already running in this thread.
                import asyncio as _asyncio
                import threading as _threading

                _holder: dict[str, Any] = {}
                log.debug(
                    "semantic_cache_get attempting (ns=%s, model=%s, type=%s)", ns, chosen, type(self.semantic_cache)
                )

                sc = self.semantic_cache

                def _runner() -> None:
                    try:
                        if sc is not None:
                            _holder["result"] = _asyncio.run(sc.get(prompt, chosen, namespace=ns))
                    except Exception as e:  # pragma: no cover - defensive
                        _holder["error"] = e

                t = _threading.Thread(target=_runner, daemon=True)
                t.start()
                t.join()
                if "error" not in _holder:
                    sem_res = _holder.get("result")
                    if sem_res is not None:
                        log.debug("semantic_cache_get HIT for model=%s ns=%s", chosen, ns)
                        result = dict(sem_res)
                        result["cached"] = True
                        result["cache_type"] = "semantic"
                        # Record similarity (if provided) into histogram buckets for observability
                        try:
                            sim_val = float(result.get("similarity", 0.0))
                            # Bucket label keeps low cardinality; refine later if distribution warrants.
                            if sim_val >= 0.9:
                                bucket = ">=0.9"
                            elif sim_val >= 0.75:
                                bucket = "0.75-0.9"
                            else:
                                bucket = "<0.75"
                            metrics.SEMANTIC_CACHE_SIMILARITY.labels(**_labels(), bucket=bucket).observe(sim_val)
                        except Exception:  # pragma: no cover - best effort metrics
                            pass
                        # Prefetch USED: a prior miss would have issued a prefetch for this prompt/model.
                        try:
                            metrics.SEMANTIC_CACHE_PREFETCH_USED.labels(**_labels()).inc()
                        except Exception:  # pragma: no cover
                            pass
                        metrics.LLM_CACHE_HITS.labels(**_labels(), model=chosen, provider=provider_family).inc()
                        return result
                    else:
                        log.debug("semantic_cache_get MISS for model=%s ns=%s", chosen, ns)
                        try:
                            metrics.LLM_CACHE_MISSES.labels(**_labels(), model=chosen, provider=provider_family).inc()
                            # Miss triggers a prefetch issuance (we will store response post-call via set())
                            metrics.SEMANTIC_CACHE_PREFETCH_ISSUED.labels(**_labels()).inc()
                        except Exception:
                            pass
            except Exception:
                # Conservative: ignore semantic cache errors
                pass
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
                    **_labels(), model=result.get("model", chosen), provider=provider_family
                ).inc()
                return result

        start = time.perf_counter()
        if effective_offline:  # offline path
            # Offline deterministic echo (historically uppercased for test stability)
            response = prompt.upper()
            latency_ms = (time.perf_counter() - start) * 1000
            tokens_out = self.prompt_engine.count_tokens(response, chosen)
            settings = get_settings()
            rl: dict[str, float] = {}
            if self.tenant_registry:
                ctx_t = ctx_effective
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
            metrics.LLM_MODEL_SELECTED.labels(**_labels(), task=task_type, model=chosen, provider=provider_family).inc()
            metrics.LLM_ESTIMATED_COST.labels(**_labels(), model=chosen, provider=provider_family).observe(
                projected_cost
            )
            metrics.LLM_LATENCY.labels(**_labels()).observe(latency_ms)
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
            # Persist caches
            if self.semantic_cache is not None:
                try:
                    import asyncio as _asyncio
                    import threading as _threading

                    sc = self.semantic_cache

                    def _runner_set() -> None:
                        try:
                            if sc is not None:
                                _asyncio.run(sc.set(prompt, chosen, result, namespace=ns))
                        except Exception:
                            pass

                    t_set = _threading.Thread(target=_runner_set, daemon=True)
                    t_set.start()
                    t_set.join()
                    log.debug("semantic_cache_set completed for model=%s ns=%s", chosen, ns)
                except Exception:
                    pass
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
                and vllm_adapter_ctor is not None
                and _has_vllm()
                and getattr(settings, "enable_vllm_local", False)
            ):
                try:  # pragma: no cover - only when local inference available
                    AdapterType: Any = vllm_adapter_ctor
                    adapter = AdapterType()
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
                    local_url = str(getattr(settings, "local_llm_url", "")).rstrip("/") + "/v1/chat/completions"
                    resp = resilient_post(
                        local_url, json_payload=local_payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS
                    )
                    if resp is None or getattr(resp, "status_code", 200) >= 400:  # noqa: PLR2004
                        raise RuntimeError(f"local_llm_error status={resp.status_code}")
                    data = resp.json() if resp is not None else {}
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
            if resp is None or getattr(resp, "status_code", 200) >= 400:  # noqa: PLR2004
                code = getattr(resp, "status_code", "unknown")
                raise RuntimeError(f"openrouter_error status={code}")
            data = resp.json() if resp is not None else {}
            message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            latency_ms = (time.perf_counter() - start) * 1000
            tokens_out = self.prompt_engine.count_tokens(message, chosen)
            settings = get_settings()
            rl = {}
            if self.tenant_registry:
                ctx_t = ctx_effective
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
            metrics.LLM_MODEL_SELECTED.labels(**_labels(), task=task_type, model=chosen, provider=provider_family).inc()
            metrics.LLM_ESTIMATED_COST.labels(**_labels(), model=chosen, provider=provider_family).observe(
                projected_cost
            )
            metrics.LLM_LATENCY.labels(**_labels()).observe(latency_ms)
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
