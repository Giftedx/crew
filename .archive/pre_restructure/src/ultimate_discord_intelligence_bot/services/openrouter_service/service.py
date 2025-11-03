"""Primary OpenRouterService class with modular workflow delegation."""

from __future__ import annotations

import copy
import logging
import os as _os
import sys
from typing import TYPE_CHECKING, Any


# Optional dependencies (graceful degradation if unavailable)
try:  # pragma: no cover - optional distributed cache
    from core.cache.enhanced_redis_cache import DistributedLLMCache
except Exception:  # pragma: no cover
    DistributedLLMCache = None

from ai.litellm_router import LLMRouterSingleton
from core.learning_engine import LearningEngine
from core.secure_config import get_config

from core.cache.bounded_cache import BoundedLRUCache
from core.cache.unified_config import get_unified_cache_config
from obs import metrics

from .adaptive_routing import AdaptiveRoutingManager
from .tenant_semantic_cache import TenantSemanticCache


try:
    from src.core.settings import get_settings  # type: ignore
except Exception:
    try:
        from ultimate_discord_intelligence_bot.settings import Settings  # type: ignore

        def get_settings():
            return Settings()
    except Exception:  # pragma: no cover - fallback when pydantic/settings unavailable

        def _get_settings_fallback() -> Any:
            class _S:
                reward_cost_weight = 0.5
                reward_latency_weight = 0.5
                reward_latency_ms_window = 2000
                reward_quality_weight = 0.0
                openrouter_referer = None
                openrouter_title = None
                enable_vllm_local = False
                local_llm_url = None

            return _S()

        get_settings = _get_settings_fallback  # type: ignore[assignment]

from ultimate_discord_intelligence_bot.cache import (
    ENABLE_CACHE_V2,
    UnifiedCache,
    get_unified_cache,
)
from ultimate_discord_intelligence_bot.settings import ENABLE_RL_MODEL_ROUTING

from ..openrouter_helpers import (
    choose_model_from_map as _choose_model_from_map_helper,
)
from ..openrouter_helpers import (
    ctx_or_fallback as _ctx_or_fallback_helper,
)
from ..openrouter_helpers import (
    deep_merge as _deep_merge_helper,
)
from ..openrouter_helpers import (
    update_shadow_hit_ratio as _update_shadow_hit_ratio_helper,
)
from ..prompt_engine import PromptEngine
from ..rl_model_router import RLModelRouter
from ..token_meter import TokenMeter


_MODULE_NAMES = (
    "ultimate_discord_intelligence_bot.services.openrouter_service",
    "src.ultimate_discord_intelligence_bot.services.openrouter_service",
)

# Optional semantic cache (guarded by feature flag in settings)
try:  # pragma: no cover - optional dependency
    from core.cache.semantic_cache import (
        get_semantic_cache as _default_semantic_cache_get,
    )
except Exception as _sc_exc:  # pragma: no cover
    _default_semantic_cache_get = None
    _semantic_cache_factory_err: str | None = str(_sc_exc)
else:
    _semantic_cache_factory_err = None


def _resolve_semantic_cache_factory() -> Any | None:
    module = None
    for name in _MODULE_NAMES:
        module = sys.modules.get(name)
        if module is not None:
            break
    override = getattr(module, "_semantic_cache_get", None) if module else None
    if override is not None:
        return override
    return _default_semantic_cache_get


log = logging.getLogger(__name__)


if TYPE_CHECKING:  # pragma: no cover - type hints only
    from collections.abc import Mapping

    from ultimate_discord_intelligence_bot.tenancy.context import TenantContext
    from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry

    from ..logging_utils import AnalyticsStore
    from .state import RouteState


class OpenRouterService:
    """Route prompts to the best available provider via OpenRouter."""

    def __init__(
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
        config = get_config()
        settings = get_settings()
        env_general = config.get_setting("openrouter_general_model")
        env_analysis = config.get_setting("openrouter_analysis_model")
        default_map = {
            "general": [env_general or "openai/gpt-4o-mini"],
            "analysis": [env_analysis or env_general or "openai/gpt-4o-mini"],
        }
        if models_map:
            default_map.update(models_map)
        self.models_map = default_map
        self.learning = learning_engine or LearningEngine()
        if api_key is not None:
            self.api_key = api_key or None
        else:
            cand = getattr(config, "openrouter_api_key", None)
            if cand and _os.getenv("OPENROUTER_API_KEY") is None:
                cand = None
            if isinstance(cand, str) and not cand.strip():
                cand = None
            self.api_key = cand
        self.offline_mode = not bool(self.api_key)
        self.prompt_engine = PromptEngine()
        self.token_meter = token_meter or TokenMeter()
        truthy = {"1", "true", "yes", "on"}
        env_ax = (_os.getenv("ENABLE_AX_ROUTING") or "").lower()
        ax_enabled = bool(getattr(settings, "enable_ax_routing", False))
        if env_ax:
            ax_enabled = env_ax in truthy
        self.adaptive_routing = AdaptiveRoutingManager(enabled=ax_enabled)
        self.cache = None
        self.unified_cache: UnifiedCache | None = None
        if cache is not None:
            self.cache = cache
        else:
            try:
                cfg = get_config()
                if ENABLE_CACHE_V2:
                    self.unified_cache = get_unified_cache()
                elif getattr(cfg, "enable_cache_global", True) and getattr(cfg, "rate_limit_redis_url", None):
                    if DistributedLLMCache is not None:
                        try:
                            ctx_cache = OpenRouterService._ctx_or_fallback("openrouter_service")
                            tenant_id = (getattr(ctx_cache, "tenant_id", None) or "default") if ctx_cache else "default"
                            workspace_id = (getattr(ctx_cache, "workspace_id", None) or "main") if ctx_cache else "main"
                            cache_ctor: Any = DistributedLLMCache
                            self.cache = cache_ctor(
                                url=str(cfg.rate_limit_redis_url),
                                ttl=get_unified_cache_config().get_ttl_for_domain("llm"),
                                tenant=tenant_id,
                                workspace=workspace_id,
                            )
                        except Exception as dist_exc:  # pragma: no cover
                            log.debug(
                                "Falling back to in-memory cache (Distributed init failed): %s",
                                dist_exc,
                            )
                            self.cache = None
                    if self.cache is None:
                        self.cache = BoundedLRUCache(
                            max_size=int(getattr(cfg, "cache_max_entries", 1000)),
                            ttl=get_unified_cache_config().get_ttl_for_domain("llm"),
                            name="openrouter",
                        )
            except Exception as cache_root_exc:  # pragma: no cover
                log.debug(
                    "Cache configuration unavailable, disabling cache: %s",
                    cache_root_exc,
                )
                self.cache = None
                self.unified_cache = None
        self.provider_opts = copy.deepcopy(provider_opts or {})
        self.logger = logger
        self.tenant_registry = tenant_registry
        self.semantic_cache = None
        self.semantic_cache_mode = "disabled"
        self.semantic_cache_gptcache_enabled = False
        self.semantic_cache_shadow_task_types: set[str] = set()
        try:
            enabled_sem = bool(getattr(settings, "enable_semantic_cache", False))
            if not enabled_sem:
                raw = (_os.getenv("ENABLE_SEMANTIC_CACHE") or "").lower()
                enabled_sem = raw in ("1", "true", "yes", "on")
            factory = _resolve_semantic_cache_factory()

            gptcache_flag = bool(getattr(settings, "enable_gptcache", False))
            if not gptcache_flag:
                raw_gpt = (_os.getenv("ENABLE_GPTCACHE") or "").lower()
                gptcache_flag = raw_gpt in ("1", "true", "yes", "on")
            self.semantic_cache_gptcache_enabled = gptcache_flag

            if gptcache_flag:
                try:
                    cache_root = getattr(get_config(), "cache_dir", "./cache")
                    threshold = float(getattr(settings, "semantic_cache_threshold", 0.8) or 0.8)
                    cache_config = get_unified_cache_config()
                    ttl = cache_config.semantic.ttl if cache_config.semantic.enabled else 3600
                    self.semantic_cache = TenantSemanticCache(
                        cache_root=str(cache_root),
                        similarity_threshold=threshold,
                        fallback_ttl_seconds=ttl,
                    )
                    self.semantic_cache_mode = "tenant"
                    enabled_sem = True
                except Exception as tenant_cache_exc:  # pragma: no cover - best effort init
                    log.warning(
                        "Tenant semantic cache init failed (%s); falling back to global cache",
                        tenant_cache_exc,
                    )
                    self.semantic_cache = None

            if self.semantic_cache is None and enabled_sem and factory:
                try:
                    self.semantic_cache = factory()
                    self.semantic_cache_mode = "global"
                except Exception as global_sem_exc:  # pragma: no cover
                    log.debug(
                        "Global semantic cache initialisation failed: %s",
                        global_sem_exc,
                    )
                    self.semantic_cache = None

            enabled_shadow = bool(getattr(settings, "enable_semantic_cache_shadow", False))
            if not enabled_shadow:
                raw_shadow = (_os.getenv("ENABLE_SEMANTIC_CACHE_SHADOW") or "").lower()
                enabled_shadow = raw_shadow in ("1", "true", "yes", "on")
            self.semantic_cache_shadow_mode = enabled_shadow
            if enabled_shadow and not enabled_sem and self.semantic_cache is None and factory:
                try:
                    self.semantic_cache = factory()
                    self.semantic_cache_mode = "global"
                except Exception:  # pragma: no cover - skip on failure
                    self.semantic_cache = None

            shadow_tasks: set[str] = set()

            tasks_setting = getattr(settings, "semantic_cache_shadow_tasks", None)
            if tasks_setting:
                if isinstance(tasks_setting, str):
                    candidates = tasks_setting.replace(";", ",").split(",")
                elif isinstance(tasks_setting, (list, tuple, set)):
                    candidates = list(tasks_setting)
                else:
                    candidates = []
                for item in candidates:
                    if item is None:
                        continue
                    name = str(item).strip()
                    if name:
                        shadow_tasks.add(name.lower())

            env_tasks = _os.getenv("SEMANTIC_CACHE_SHADOW_TASKS")
            if env_tasks:
                for item in env_tasks.replace(";", ",").split(","):
                    name = item.strip()
                    if name:
                        shadow_tasks.add(name.lower())

            analysis_shadow_flag = bool(getattr(settings, "enable_gptcache_analysis_shadow", False))
            if not analysis_shadow_flag:
                raw_analysis = (_os.getenv("ENABLE_GPTCACHE_ANALYSIS_SHADOW") or "").lower()
                analysis_shadow_flag = raw_analysis in ("1", "true", "yes", "on")
            if analysis_shadow_flag:
                shadow_tasks.add("analysis")

            self.semantic_cache_shadow_task_types = shadow_tasks

            promote_flag = bool(getattr(settings, "enable_semantic_cache_promotion", False))
            if not promote_flag:
                raw_promote = (_os.getenv("ENABLE_SEMANTIC_CACHE_PROMOTION") or "").lower()
                promote_flag = raw_promote in ("1", "true", "yes", "on")
            self.semantic_cache_promotion_enabled = promote_flag

            thr = getattr(settings, "semantic_cache_promotion_threshold", None)
            if thr is None:
                env_thr = _os.getenv("SEMANTIC_CACHE_PROMOTION_THRESHOLD")
                try:
                    thr = float(env_thr) if env_thr is not None and env_thr.strip() != "" else 0.9
                except Exception:
                    thr = 0.9
            try:
                self.semantic_cache_promotion_threshold = float(thr)
            except Exception:
                self.semantic_cache_promotion_threshold = 0.9

        except Exception:
            self.semantic_cache = None
            self.semantic_cache_mode = "disabled"
            self.semantic_cache_gptcache_enabled = False
            self.semantic_cache_shadow_mode = False
            self.semantic_cache_promotion_enabled = False
            self.semantic_cache_promotion_threshold = 0.9
            self.semantic_cache_shadow_task_types = set()

        # Initialize RL Model Router if enabled
        self.rl_router = None
        if ENABLE_RL_MODEL_ROUTING:
            try:
                self.rl_router = RLModelRouter()
                log.info("RL Model Router enabled - adaptive model selection active")
            except Exception as rl_exc:  # pragma: no cover
                log.warning(
                    "RL Model Router initialization failed, falling back to standard routing: %s",
                    rl_exc,
                )
                self.rl_router = None

        # Initialize LiteLLM Router if enabled
        self.litellm_router = None
        if LLMRouterSingleton.is_enabled():
            try:
                self.litellm_router = LLMRouterSingleton.get()
                if self.litellm_router is not None:
                    log.info("LiteLLM Router enabled - multi-provider routing active")
            except Exception as lite_exc:  # pragma: no cover
                log.warning(
                    "LiteLLM Router initialization failed, falling back to standard routing: %s",
                    lite_exc,
                )
                self.litellm_router = None

    @staticmethod
    def _ctx_or_fallback(component: str) -> TenantContext | None:
        return _ctx_or_fallback_helper(component)

    @staticmethod
    def _deep_merge(base: dict[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
        return _deep_merge_helper(base, overrides)

    def _update_shadow_hit_ratio(self, labels: dict[str, str], is_hit: bool) -> None:
        _update_shadow_hit_ratio_helper(labels, is_hit)

    def _choose_model_from_map(self, task_type: str, models_map: dict[str, list[str]]) -> str:
        return _choose_model_from_map_helper(task_type, models_map, self.learning)

    def route(
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
        compress: bool = True,
    ) -> dict[str, Any]:
        from .workflow import route_prompt

        result = route_prompt(
            self,
            prompt,
            task_type=task_type,
            model=model,
            provider_opts=provider_opts,
            compress=compress,
        )
        self._adaptive_flush_events()
        return result

    def _adaptive_record_outcome(
        self,
        state: RouteState,
        *,
        reward: float,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        # Record outcome for RL Router if available
        rl_router = getattr(self, "rl_router", None)
        if rl_router is not None and state.rl_router_selection is not None:
            try:
                rl_router.update_reward(state.rl_router_selection, reward)
                log.debug(f"RL Router reward updated: {reward} for model {state.chosen_model}")
            except Exception as rl_exc:  # pragma: no cover
                log.warning(f"RL Router reward update failed: {rl_exc}")

        # Record outcome for adaptive routing manager
        manager = getattr(self, "adaptive_routing", None)
        if manager is None or not getattr(manager, "enabled", False):
            return
        trial_index = getattr(state, "adaptive_trial_index", None)
        if trial_index is None:
            return
        suggested = getattr(state, "adaptive_suggested_model", None)
        record_metadata: dict[str, Any] = {
            "status": status,
            "model": state.chosen_model,
            "chosen_model": state.chosen_model,
            "suggested_model": suggested,
            "requested_model": state.requested_model,
            "provider_family": state.provider_family,
            "override": bool(suggested and suggested != state.chosen_model),
            "rl_router_used": state.rl_router_selection is not None,
        }
        if state.adaptive_candidates:
            record_metadata.setdefault("candidates", list(state.adaptive_candidates))
        if metadata:
            record_metadata.update(metadata)
        try:
            manager.observe(state.task_type, trial_index, float(reward), record_metadata)
        except Exception:  # pragma: no cover - observation best effort
            log.debug("adaptive routing observe failed", exc_info=True)
        finally:
            state.adaptive_trial_index = None
            state.adaptive_recorded = True
            try:
                labels = state.labels()
                metrics.ACTIVE_BANDIT_POLICY.labels(
                    tenant=labels.get("tenant", "unknown"),
                    workspace=labels.get("workspace", "unknown"),
                    domain=state.task_type,
                    policy="ax_adaptive",
                ).set(0.0)
            except Exception:  # pragma: no cover - metrics optional
                pass

    def _adaptive_flush_events(self) -> None:
        manager = getattr(self, "adaptive_routing", None)
        if manager is None or not getattr(manager, "enabled", False):
            return
        try:
            events = manager.drain_events()
        except Exception:  # pragma: no cover - defensive
            events = []
        if not events:
            return
        if self.logger and hasattr(self.logger, "log_bandit_event"):
            for event in events:
                try:
                    self.logger.log_bandit_event(event)
                except Exception:  # pragma: no cover - logging best effort
                    log.debug("bandit event logging failed", exc_info=True)
