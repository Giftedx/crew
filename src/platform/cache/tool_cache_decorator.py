"""Reusable cache decorator for BaseTool implementations.

This module provides a decorator for caching expensive tool operations using
the multi-level cache infrastructure (memory + Redis + disk).

Example:
    @cache_tool_result(namespace="tool:sentiment", ttl=7200)
    def _run(self, text: str) -> StepResult:
        # Expensive sentiment analysis here
        return StepResult.ok(data={...})
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import os
from collections.abc import Callable
from platform.cache.multi_level_cache import MultiLevelCache
from platform.core.step_result import StepResult
from typing import Any, TypeVar

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics


logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Callable[..., StepResult])


def cache_tool_result(
    namespace: str,
    ttl: int = 3600,
    cache_key_fn: Callable[..., str] | None = None,
    enabled_env_var: str = "ENABLE_TOOL_RESULT_CACHING",
) -> Callable[[T], T]:
    """Decorator to cache tool execution results using multi-level cache.

    Args:
        namespace: Cache namespace (e.g., "tool:enhanced_analysis")
        ttl: Time-to-live in seconds (default: 1 hour)
        cache_key_fn: Optional function to generate cache key from args
        enabled_env_var: Environment variable to check if caching is enabled

    Returns:
        Decorated function with automatic caching

    Example:
        @cache_tool_result(namespace="tool:sentiment", ttl=7200)
        def _run(self, text: str) -> StepResult:
            # Expensive sentiment analysis here
            return StepResult.ok(data={"sentiment": "positive"})
    """
    # Check if caching is enabled via environment variable
    cache_enabled = os.getenv(enabled_env_var, "true").lower() == "true"

    # Initialize cache (singleton pattern - reuse across decorators)
    cache = MultiLevelCache(
        redis_url=os.getenv("REDIS_URL"),
        max_memory_size=int(os.getenv("CACHE_MEMORY_SIZE", "1000")),
        default_ttl=ttl,
    )
    metrics = get_metrics()

    def decorator(func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> StepResult:
            # If caching is disabled, execute function directly
            if not cache_enabled:
                return func(*args, **kwargs)

            # Generate cache key
            if cache_key_fn:
                cache_key = cache_key_fn(*args, **kwargs)
            else:
                # Default: hash function args (skip self)
                # Extract meaningful args (skip self at index 0)
                cache_args = {"args": args[1:], "kwargs": kwargs}
                try:
                    key_str = json.dumps(cache_args, sort_keys=True, default=str)
                    cache_key = hashlib.sha256(key_str.encode()).hexdigest()[:16]
                except (TypeError, ValueError) as e:
                    logger.warning(f"Failed to generate cache key: {e}, using fallback")
                    cache_key = hashlib.sha256(str(cache_args).encode()).hexdigest()[:16]

            operation = f"{namespace}:{cache_key}"

            # Check cache
            try:
                cached_value = cache.get(operation, {})
                if cached_value is not None:
                    metrics.counter("tool_cache_hits_total", labels={"namespace": namespace}).inc()
                    logger.debug(f"Cache hit for {namespace}: {cache_key[:8]}")

                    # Return cached data with cache metadata
                    return StepResult(
                        success=True,
                        data=cached_value,
                        metadata={
                            "cache_hit": True,
                            "cache_key": cache_key,
                            "namespace": namespace,
                        },
                    )
            except Exception as e:
                logger.warning(f"Cache get error for {namespace}: {e}")
                # Continue to execute function on cache error

            # Cache miss - execute function
            metrics.counter("tool_cache_misses_total", labels={"namespace": namespace}).inc()
            logger.debug(f"Cache miss for {namespace}: {cache_key[:8]}")

            result = func(*args, **kwargs)

            # Preserve error state if result failed
            if not result.success:
                return result

            # Store successful results in cache
            if result.data:
                try:
                    cache.set(operation, {}, result.data, ttl=ttl)
                    logger.debug(f"Cached result for {namespace}: {cache_key[:8]}")
                except Exception as e:
                    logger.warning(f"Cache set error for {namespace}: {e}")

            # Add cache metadata to result
            return StepResult(
                success=True,
                data=result.data,
                metadata={
                    **result.metadata,
                    "cache_hit": False,
                    "cache_key": cache_key,
                    "namespace": namespace,
                },
            )

        return wrapper  # type: ignore

    return decorator
