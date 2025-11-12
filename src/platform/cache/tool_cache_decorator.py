"""Reusable cache decorator for BaseTool implementations.

This module provides a decorator for caching expensive tool operations using
the multi-level cache infrastructure (memory + Redis + disk) with optional
semantic similarity matching for improved cache hit rates.

Example:
    @cache_tool_result(namespace="tool:sentiment", ttl=7200)
    def _run(self, text: str) -> StepResult:
        # Expensive sentiment analysis here
        return StepResult.ok(data={...})
"""

from __future__ import annotations

import functools
import hashlib
import inspect
import json
import logging
import os
from collections.abc import Callable
from platform.cache.multi_level_cache import MultiLevelCache
from platform.cache.semantic_cache_service import get_semantic_cache_service
from platform.cache.semantic_cache_warmer import get_tool_cache_warmer
from typing import Any, TypeVar

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Callable[..., StepResult])


def cache_tool_result(
    namespace: str,
    ttl: int = 3600,
    cache_key_fn: Callable[..., str] | None = None,
    enabled_env_var: str = "ENABLE_TOOL_RESULT_CACHING",
    enable_semantic_cache: bool = False,
    semantic_similarity_threshold: float = 0.85,
    semantic_text_fn: Callable[..., str] | None = None,
    enable_warming: bool = False,
    warming_patterns: list[dict[str, Any]] | None = None,
) -> Callable[[T], T]:
    """Decorator to cache tool execution results using multi-level cache with optional semantic similarity.

    Args:
        namespace: Cache namespace (e.g., "tool:enhanced_analysis")
        ttl: Time-to-live in seconds (default: 1 hour)
        cache_key_fn: Optional function to generate cache key from args
        enabled_env_var: Environment variable to check if caching is enabled
        enable_semantic_cache: Whether to enable semantic similarity matching
        semantic_similarity_threshold: Similarity threshold for semantic cache hits (0.0-1.0)
        semantic_text_fn: Optional function to extract text for semantic comparison from args
        enable_warming: Whether to enable proactive cache warming for this tool
        warming_patterns: Optional list of input patterns to use for cache warming

    Returns:
        Decorated function with automatic caching

    Example:
        @cache_tool_result(namespace="tool:sentiment", ttl=7200)
        def _run(self, text: str) -> StepResult:
            # Expensive sentiment analysis here
            return StepResult.ok(data={"sentiment": "positive"})

        # With semantic caching
        @cache_tool_result(
            namespace="tool:sentiment",
            ttl=7200,
            enable_semantic_cache=True,
            semantic_text_fn=lambda text: text
        )
        def _run(self, text: str) -> StepResult:
            return StepResult.ok(data={"sentiment": "positive"})

        # With cache warming
        @cache_tool_result(
            namespace="tool:sentiment",
            ttl=7200,
            enable_warming=True,
            warming_patterns=[
                {"text": "I love this product!"},
                {"text": "This is terrible."},
                {"text": "It's okay, nothing special."}
            ]
        )
        def _run(self, text: str) -> StepResult:
            return StepResult.ok(data={"sentiment": "positive"})
    """
    # Check if caching is enabled via environment variable
    cache = MultiLevelCache(
        redis_url=os.getenv("REDIS_URL"),
        max_memory_size=int(os.getenv("CACHE_MEMORY_SIZE", "1000")),
        default_ttl=ttl,
    )

    # Initialize cache warmer if enabled
    tool_warmer = None
    if enable_warming:
        try:
            tool_warmer = get_tool_cache_warmer()
            if warming_patterns:
                tool_warmer.register_tool_patterns(namespace, warming_patterns)
            logger.info(f"Enabled cache warming for namespace: {namespace}")
        except Exception as e:
            logger.warning(f"Failed to initialize cache warmer for {namespace}: {e}")
            enable_warming = False

    metrics = get_metrics()
    hit_counter = metrics.counter("tool_cache_hits_total", labels={"namespace": namespace})
    miss_counter = metrics.counter("tool_cache_misses_total", labels={"namespace": namespace})
    semantic_hit_counter = metrics.counter("tool_semantic_cache_hits_total", labels={"namespace": namespace})

    def _should_attempt_warming() -> bool:
        """Determine if cache warming should be attempted (throttled to avoid overhead)."""
        import random

        # Only attempt warming on ~10% of cache misses to avoid performance impact
        return random.random() < 0.1

    async def _perform_warming_if_enabled(tenant: str, workspace: str) -> None:
        """Perform cache warming if enabled and conditions are met."""
        if enable_warming and tool_warmer and _should_attempt_warming():
            try:
                # Create a data fetcher that calls the original function
                async def data_fetcher(pattern: dict[str, Any]) -> Any:  # noqa: ARG001
                    # This would need to be implemented to call the original function
                    # For now, we'll skip actual warming to avoid recursion
                    return None

                # Only warm if we have registered patterns
                if warming_patterns:
                    await tool_warmer.warm_tool_cache(
                        namespace, data_fetcher, tenant, workspace, use_registered_patterns=True
                    )
            except Exception as e:
                logger.debug(f"Cache warming failed for {namespace}: {e}")

    def decorator(func: T) -> T:
        is_coroutine = inspect.iscoroutinefunction(func)

        # Initialize semantic cache if enabled (only for async functions)
        semantic_cache = None
        semantic_cache_enabled = enable_semantic_cache
        if enable_semantic_cache and is_coroutine:
            try:
                semantic_cache = get_semantic_cache_service(
                    similarity_threshold=semantic_similarity_threshold,
                    cache_ttl=ttl,
                )
                logger.info(f"Enabled semantic caching for namespace: {namespace}")
            except Exception as e:
                logger.warning(f"Failed to initialize semantic cache for {namespace}: {e}")
                semantic_cache_enabled = False
        elif enable_semantic_cache and not is_coroutine:
            logger.warning(f"Semantic caching disabled for sync function {namespace} - requires async")
            semantic_cache_enabled = False
        signature = inspect.signature(func)
        use_cache_param_index: int | None = None
        if "use_cache" in signature.parameters:
            use_cache_param_index = list(signature.parameters.keys()).index("use_cache")

        def _is_enabled() -> bool:
            return os.getenv(enabled_env_var, "true").lower() == "true"

        def _is_cache_disabled(call_args: tuple[Any, ...], call_kwargs: dict[str, Any]) -> bool:
            if "use_cache" in call_kwargs:
                return call_kwargs["use_cache"] is False
            if use_cache_param_index is not None and use_cache_param_index < len(call_args):
                return call_args[use_cache_param_index] is False
            return False

        def _compute_cache_key(call_args: tuple[Any, ...], call_kwargs: dict[str, Any]) -> str:
            if cache_key_fn:
                try:
                    key = cache_key_fn(*call_args, **call_kwargs)
                    return str(key)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("Custom cache_key_fn failed for %s: %s", namespace, exc)
            payload = {"args": call_args[1:], "kwargs": call_kwargs}
            try:
                serialized = json.dumps(payload, sort_keys=True, default=str)
            except (TypeError, ValueError):
                logger.debug("Falling back to repr serialization for cache key in %s", namespace)
                serialized = repr(payload)
            return hashlib.sha256(serialized.encode()).hexdigest()[:16]

        def _resolve_scope(call_args: tuple[Any, ...], call_kwargs: dict[str, Any]) -> tuple[str | None, str | None]:
            tenant = call_kwargs.get("tenant")
            workspace = call_kwargs.get("workspace")
            if (tenant is None or workspace is None) and call_args:
                candidate = call_args[0]
                tenant = tenant or getattr(candidate, "tenant", None)
                workspace = workspace or getattr(candidate, "workspace", None)
            return tenant or "global", workspace or "global"

        def _augment_metadata(
            result: StepResult, *, cache_hit: bool, cache_key: str, tenant: str, workspace: str
        ) -> StepResult:
            existing = dict(result.metadata or {})
            existing.update(
                {
                    "cache_hit": cache_hit,
                    "cache_key": cache_key,
                    "namespace": namespace,
                    "cache_tenant": tenant,
                    "cache_workspace": workspace,
                }
            )
            return result.with_metadata(existing)

        def _deserialize_cached(value: Any) -> StepResult | None:
            try:
                return StepResult.from_dict(value)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to deserialize cached result for %s: %s", namespace, exc)
                return None

        def _cache_inputs(cache_key: str) -> dict[str, str]:
            return {"cache_key": cache_key}

        def _extract_semantic_text(call_args: tuple[Any, ...], call_kwargs: dict[str, Any]) -> str | None:
            """Extract text for semantic comparison from function arguments."""
            if semantic_text_fn:
                try:
                    return semantic_text_fn(*call_args, **call_kwargs)
                except Exception as e:
                    logger.debug(f"Failed to extract semantic text for {namespace}: {e}")
                    return None

            # Default: try to find text-like arguments
            for arg in call_args[1:]:  # Skip 'self'
                if isinstance(arg, str) and len(arg) > 10:  # Reasonable text length
                    return arg
            for value in call_kwargs.values():
                if isinstance(value, str) and len(value) > 10:
                    return value
            return None

        def _to_step_result(value: Any) -> StepResult:
            if isinstance(value, StepResult):
                return value
            return StepResult.from_dict(value)

        def _cache_set(operation: str, inputs: dict[str, str], payload: Any, *, tenant: str, workspace: str) -> None:
            try:
                cache.set(operation, inputs, payload, ttl=ttl, tenant=tenant, workspace=workspace)
                logger.debug("Cached result for %s: %s", namespace, inputs["cache_key"][:8])
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Cache set error for %s: %s", namespace, exc)

        def _cache_get(operation: str, inputs: dict[str, str], *, tenant: str, workspace: str) -> StepResult | None:
            try:
                cached_payload = cache.get(operation, inputs, tenant=tenant, workspace=workspace)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Cache get error for %s: %s", namespace, exc)
                return None
            if cached_payload is None:
                return None
            return _deserialize_cached(cached_payload)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> StepResult:
            if not _is_enabled() or _is_cache_disabled(args, kwargs):
                return func(*args, **kwargs)

            cache_key = _compute_cache_key(args, kwargs)
            tenant, workspace = _resolve_scope(args, kwargs)
            inputs = _cache_inputs(cache_key)

            # Try exact match first
            cached_result = _cache_get(namespace, inputs, tenant=tenant, workspace=workspace)

            if cached_result is not None:
                hit_counter.inc()
                logger.debug("Cache hit for %s: %s", namespace, cache_key[:8])
                return _augment_metadata(
                    cached_result,
                    cache_hit=True,
                    cache_key=cache_key,
                    tenant=tenant,
                    workspace=workspace,
                )

            # Semantic caching disabled for sync functions
            miss_counter.inc()
            logger.debug("Cache miss for %s: %s", namespace, cache_key[:8])

            # Attempt cache warming if enabled
            if enable_warming and tool_warmer:
                # For sync context, we can't await, so skip warming
                pass

            result = _to_step_result(func(*args, **kwargs))
            if not result.success:
                return result

            # Store in exact cache
            _cache_set(namespace, inputs, result.to_dict(), tenant=tenant, workspace=workspace)

            # Semantic cache storage disabled for sync functions
            return _augment_metadata(
                result,
                cache_hit=False,
                cache_key=cache_key,
                tenant=tenant,
                workspace=workspace,
            )

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> StepResult:
            if not _is_enabled() or _is_cache_disabled(args, kwargs):
                return await func(*args, **kwargs)

            cache_key = _compute_cache_key(args, kwargs)
            tenant, workspace = _resolve_scope(args, kwargs)
            inputs = _cache_inputs(cache_key)

            # Try exact match first
            cached_result = _cache_get(namespace, inputs, tenant=tenant, workspace=workspace)

            if cached_result is not None:
                hit_counter.inc()
                logger.debug("Cache hit for %s: %s", namespace, cache_key[:8])
                return _augment_metadata(
                    cached_result,
                    cache_hit=True,
                    cache_key=cache_key,
                    tenant=tenant,
                    workspace=workspace,
                )

            # Try semantic match if enabled
            semantic_result = None
            if semantic_cache_enabled and semantic_cache:
                semantic_text = _extract_semantic_text(args, kwargs)
                if semantic_text:
                    semantic_result = await semantic_cache.get_semantic_match(
                        semantic_text, namespace, tenant, workspace
                    )
                    if semantic_result:
                        semantic_hit_counter.inc()
                        logger.debug(
                            "Semantic cache hit for %s: similarity=%.3f",
                            namespace,
                            semantic_result.get("similarity", 0),
                        )
                        cached_result = _deserialize_cached(semantic_result["result"])
                        if cached_result:
                            return _augment_metadata(
                                cached_result,
                                cache_hit=True,
                                cache_key=f"semantic:{cache_key}",
                                tenant=tenant,
                                workspace=workspace,
                            )

            miss_counter.inc()
            logger.debug("Cache miss for %s: %s", namespace, cache_key[:8])

            # Attempt cache warming if enabled
            if enable_warming and tool_warmer:
                await _perform_warming_if_enabled(tenant, workspace)

            result = _to_step_result(await func(*args, **kwargs))
            if not result.success:
                return result

            # Store in exact cache
            _cache_set(namespace, inputs, result.to_dict(), tenant=tenant, workspace=workspace)

            # Store in semantic cache if enabled
            if semantic_cache_enabled and semantic_cache and semantic_text:
                try:
                    await semantic_cache.store_semantic_entry(
                        semantic_text, result.to_dict(), namespace, tenant, workspace, cache_key
                    )
                except Exception as e:
                    logger.debug(f"Failed to store semantic cache entry for {namespace}: {e}")

            return _augment_metadata(
                result,
                cache_hit=False,
                cache_key=cache_key,
                tenant=tenant,
                workspace=workspace,
            )

        wrapper = async_wrapper if is_coroutine else sync_wrapper

        return wrapper  # type: ignore

    return decorator
