from __future__ import annotations
import contextlib
import copy
import logging
from collections.abc import Mapping
from typing import Any
from platform.flags import enabled
from platform.observability.metrics import get_metrics
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, current_tenant
log = logging.getLogger(__name__)

def ctx_or_fallback(component: str) -> TenantContext:
    """Return current tenant or fallback/default according to flags.

    If strict tenancy is enabled and no context is set, raise. Otherwise,
    log a warning, increment the tenancy fallback metric, and return a
    default context ("default:main").
    """
    ctx = current_tenant()
    if ctx is not None:
        return ctx
    if enabled('ENABLE_TENANCY_STRICT', False) or enabled('ENABLE_INGEST_STRICT', False):
        raise RuntimeError('TenantContext required but not set (strict mode)')
    else:
        logging.getLogger('tenancy').warning("TenantContext missing; defaulting to 'default:main' namespace (non-strict mode)")
    with contextlib.suppress(Exception):
        m = get_metrics()
        m.counter('tenancy_fallbacks_total', labels={'component': component}).inc()
    return TenantContext('default', 'main')

def deep_merge(base: dict[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge ``overrides`` into ``base`` and return ``base``.

    This mirrors the previous OpenRouterService._deep_merge behavior.
    """
    for key, value in overrides.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, Mapping):
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base

def update_shadow_hit_ratio(labels: dict[str, str], is_hit: bool) -> None:
    """Update the semantic cache shadow mode hit ratio metric (best-effort)."""
    with contextlib.suppress(Exception):
        m = get_metrics()
        m.gauge('semantic_cache_shadow_hit_ratio', labels=labels).set(1.0 if is_hit else 0.0)

def choose_model_from_map(task_type: str, models_map: dict[str, list[str]], learning) -> str:
    """Pick a model for a given task type from the provided map using learning engine."""
    candidates = models_map.get(task_type) or models_map.get('general') or []
    if candidates:
        if len(candidates) > 1:
            try:
                return learning.select_model(task_type, candidates)
            except Exception:
                return candidates[0]
        return candidates[0]
    return 'openai/gpt-4o-mini'
__all__ = ['choose_model_from_map', 'ctx_or_fallback', 'deep_merge', 'update_shadow_hit_ratio']