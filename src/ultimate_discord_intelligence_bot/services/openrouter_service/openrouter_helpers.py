"""Helper functions for OpenRouter service.

This module contains shared helper functions used by the OpenRouter service
and its components.
"""

from __future__ import annotations
import contextlib
import copy
from typing import TYPE_CHECKING, Any
from platform.observability import metrics
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext

if TYPE_CHECKING:
    from core.learning_engine import LearningEngine


def ctx_or_fallback(component: str) -> TenantContext | None:
    """Get tenant context with fallback logic."""
    try:
        from ultimate_discord_intelligence_bot.tenancy.context import current_tenant

        ctx = current_tenant()
        if ctx is not None:
            return ctx
        from core.flags import enabled

        if enabled("ENABLE_TENANCY_STRICT", False):
            raise RuntimeError(f"TenantContext required for {component} but not set (strict mode)")
        return TenantContext("default", "main")
    except Exception:
        return None


def deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries."""
    result = copy.deepcopy(base)
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def choose_model_from_map(task_type: str, models_map: dict[str, list[str]], learning_engine: LearningEngine) -> str:
    """Choose model from map using learning engine."""
    available_models = models_map.get(task_type, models_map.get("general", []))
    if not available_models:
        return "openai/gpt-4o-mini"
    try:
        return learning_engine.select_model(task_type, available_models)
    except AttributeError:
        return available_models[0] if available_models else "openai/gpt-4o-mini"


def update_shadow_hit_ratio(labels: dict[str, str], is_hit: bool) -> None:
    """Update shadow hit ratio metrics."""
    with contextlib.suppress(Exception):
        if is_hit:
            metrics.SEMANTIC_CACHE_SHADOW_HITS.labels(**labels).inc()
        else:
            metrics.SEMANTIC_CACHE_SHADOW_MISSES.labels(**labels).inc()
