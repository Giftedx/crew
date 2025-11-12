"""Caching decorators for ML/AI operations."""

from __future__ import annotations

import functools
import json
import logging
from typing import TYPE_CHECKING, Any, TypeVar

from .multi_level_cache import get_cache


if TYPE_CHECKING:
    from collections.abc import Callable

    from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)
T = TypeVar("T")


def cached_operation(
    operation_name: str,
    ttl: int | None = None,
    tenant_param: str = "tenant",
    workspace_param: str = "workspace",
    key_params: list[str] | None = None,
    exclude_params: list[str] | None = None,
):
    """Decorator for caching expensive operations.

    Args:
        operation_name: Name of the operation for cache key
        ttl: Time to live in seconds (None for default)
        tenant_param: Parameter name for tenant
        workspace_param: Parameter name for workspace
        key_params: Specific parameters to include in cache key
        exclude_params: Parameters to exclude from cache key
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cache = get_cache()
            tenant = kwargs.get(tenant_param, "")
            workspace = kwargs.get(workspace_param, "")
            cache_inputs = {}
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            if key_params:
                for param in key_params:
                    if param in bound_args.arguments:
                        cache_inputs[param] = bound_args.arguments[param]
            else:
                exclude_set = set(exclude_params or [])
                for param, value in bound_args.arguments.items():
                    if param not in exclude_set and param not in [tenant_param, workspace_param]:
                        try:
                            json.dumps(value)
                            cache_inputs[param] = value
                        except (TypeError, ValueError):
                            continue
            cached_result = cache.get(operation_name, cache_inputs, tenant, workspace)
            if cached_result is not None:
                logger.debug(f"Cache hit for {operation_name}")
                return cached_result
            logger.debug(f"Cache miss for {operation_name}, executing function")
            result = func(*args, **kwargs)
            cache.set(operation_name, cache_inputs, result, ttl, tenant, workspace)
            return result

        return wrapper

    return decorator


def cached_step_result(
    operation_name: str,
    ttl: int | None = None,
    tenant_param: str = "tenant",
    workspace_param: str = "workspace",
    key_params: list[str] | None = None,
    exclude_params: list[str] | None = None,
):
    """Decorator for caching StepResult operations.

    Args:
        operation_name: Name of the operation for cache key
        ttl: Time to live in seconds (None for default)
        tenant_param: Parameter name for tenant
        workspace_param: Parameter name for workspace
        key_params: Specific parameters to include in cache key
        exclude_params: Parameters to exclude from cache key
    """

    def decorator(func: Callable[..., StepResult]) -> Callable[..., StepResult]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> StepResult:
            cache = get_cache()
            tenant = kwargs.get(tenant_param, "")
            workspace = kwargs.get(workspace_param, "")
            cache_inputs = {}
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            if key_params:
                for param in key_params:
                    if param in bound_args.arguments:
                        cache_inputs[param] = bound_args.arguments[param]
            else:
                exclude_set = set(exclude_params or [])
                for param, value in bound_args.arguments.items():
                    if param not in exclude_set and param not in [tenant_param, workspace_param]:
                        try:
                            json.dumps(value)
                            cache_inputs[param] = value
                        except (TypeError, ValueError):
                            continue
            cached_result = cache.get(operation_name, cache_inputs, tenant, workspace)
            if cached_result is not None:
                logger.debug(f"Cache hit for {operation_name}")
                return cached_result
            logger.debug(f"Cache miss for {operation_name}, executing function")
            result = func(*args, **kwargs)
            if result.success:
                cache.set(operation_name, cache_inputs, result, ttl, tenant, workspace)
            return result

        return wrapper

    return decorator


def cache_invalidate(
    operation_name: str,
    tenant_param: str = "tenant",
    workspace_param: str = "workspace",
    key_params: list[str] | None = None,
    exclude_params: list[str] | None = None,
):
    """Decorator for invalidating cache entries.

    Args:
        operation_name: Name of the operation to invalidate
        tenant_param: Parameter name for tenant
        workspace_param: Parameter name for workspace
        key_params: Specific parameters to include in cache key
        exclude_params: Parameters to exclude from cache key
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cache = get_cache()
            tenant = kwargs.get(tenant_param, "")
            workspace = kwargs.get(workspace_param, "")
            cache_inputs = {}
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            if key_params:
                for param in key_params:
                    if param in bound_args.arguments:
                        cache_inputs[param] = bound_args.arguments[param]
            else:
                exclude_set = set(exclude_params or [])
                for param, value in bound_args.arguments.items():
                    if param not in exclude_set and param not in [tenant_param, workspace_param]:
                        try:
                            json.dumps(value)
                            cache_inputs[param] = value
                        except (TypeError, ValueError):
                            continue
            result = func(*args, **kwargs)
            cache.delete(operation_name, cache_inputs, tenant, workspace)
            return result

        return wrapper

    return decorator


def cache_clear(tenant: str = "", workspace: str = ""):
    """Clear cache for tenant/workspace or all.

    Args:
        tenant: Tenant identifier (empty for all)
        workspace: Workspace identifier (empty for all)
    """
    cache = get_cache()
    return cache.clear(tenant, workspace)


def cache_stats() -> dict[str, Any]:
    """Get cache statistics."""
    cache = get_cache()
    return cache.get_stats()


def cache_health() -> StepResult:
    """Check cache health."""
    cache = get_cache()
    return cache.health_check()
