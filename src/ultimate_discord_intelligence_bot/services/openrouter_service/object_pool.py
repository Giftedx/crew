"""Object pooling for memory optimization in OpenRouter service.

This module provides object pooling capabilities to reduce memory
allocation overhead and improve performance for frequently created objects.
"""

from __future__ import annotations
import logging
import threading
import time
from collections import deque
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags

if TYPE_CHECKING:
    from .service import OpenRouterService
log = logging.getLogger(__name__)
T = TypeVar("T")


class ObjectPool(Generic[T]):
    """Generic object pool for reusing objects."""

    def __init__(
        self, factory: callable[[], T], max_size: int = 10, reset_func: callable[[T], None] | None = None
    ) -> None:
        """Initialize object pool.

        Args:
            factory: Function to create new objects
            max_size: Maximum number of objects in the pool
            reset_func: Function to reset objects before reuse
        """
        self._factory = factory
        self._max_size = max_size
        self._reset_func = reset_func
        self._pool: deque[T] = deque()
        self._lock = threading.RLock()
        self._created_count = 0
        self._reused_count = 0
        self._stats = {
            "objects_created": 0,
            "objects_reused": 0,
            "pool_hits": 0,
            "pool_misses": 0,
            "current_pool_size": 0,
        }

    def get(self) -> T:
        """Get an object from the pool or create a new one.

        Returns:
            Object from the pool or newly created
        """
        with self._lock:
            if self._pool:
                obj = self._pool.popleft()
                self._stats["objects_reused"] += 1
                self._stats["pool_hits"] += 1
                self._stats["current_pool_size"] = len(self._pool)
                if self._reset_func:
                    try:
                        self._reset_func(obj)
                    except Exception as e:
                        log.debug("Object reset failed: %s", e)
                log.debug("Reused object from pool (pool size: %d)", len(self._pool))
                return obj
            else:
                obj = self._factory()
                self._created_count += 1
                self._stats["objects_created"] += 1
                self._stats["pool_misses"] += 1
                log.debug("Created new object (total created: %d)", self._created_count)
                return obj

    def put(self, obj: T) -> None:
        """Return an object to the pool.

        Args:
            obj: Object to return to the pool
        """
        with self._lock:
            if len(self._pool) < self._max_size:
                self._pool.append(obj)
                self._stats["current_pool_size"] = len(self._pool)
                log.debug("Returned object to pool (pool size: %d)", len(self._pool))
            else:
                log.debug("Pool is full, discarding object")

    def clear(self) -> None:
        """Clear all objects from the pool."""
        with self._lock:
            self._pool.clear()
            self._stats["current_pool_size"] = 0
            log.debug("Cleared object pool")

    def get_stats(self) -> dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary with pool statistics
        """
        with self._lock:
            total_objects = self._stats["objects_created"] + self._stats["objects_reused"]
            reuse_rate = self._stats["objects_reused"] / total_objects * 100 if total_objects > 0 else 0
            return {**self._stats, "reuse_rate_percent": round(reuse_rate, 2), "max_pool_size": self._max_size}

    def reset_stats(self) -> None:
        """Reset pool statistics."""
        with self._lock:
            self._stats = {
                "objects_created": 0,
                "objects_reused": 0,
                "pool_hits": 0,
                "pool_misses": 0,
                "current_pool_size": len(self._pool),
            }


class RouteStatePool:
    """Object pool for RouteState objects."""

    def __init__(self, max_size: int = 20) -> None:
        """Initialize RouteState pool.

        Args:
            max_size: Maximum number of RouteState objects in the pool
        """
        self._pool = ObjectPool(factory=self._create_route_state, max_size=max_size, reset_func=self._reset_route_state)
        self._feature_flags = FeatureFlags()

    def _create_route_state(self) -> Any:
        """Create a new RouteState object."""
        from .state import RouteState

        return RouteState()

    def _reset_route_state(self, state: Any) -> None:
        """Reset a RouteState object for reuse."""
        try:
            for attr in dir(state):
                if not attr.startswith("_") and (not callable(getattr(state, attr))):
                    setattr(state, attr, None)
        except Exception as e:
            log.debug("RouteState reset failed: %s", e)

    def get_route_state(self) -> Any:
        """Get a RouteState object from the pool."""
        if self._feature_flags.ENABLE_OPENROUTER_OBJECT_POOLING:
            return self._pool.get()
        else:
            return self._create_route_state()

    def return_route_state(self, state: Any) -> None:
        """Return a RouteState object to the pool."""
        if self._feature_flags.ENABLE_OPENROUTER_OBJECT_POOLING:
            self._pool.put(state)

    def get_stats(self) -> dict[str, Any]:
        """Get RouteState pool statistics."""
        return self._pool.get_stats()


class RequestResponsePool:
    """Object pool for request/response dictionaries."""

    def __init__(self, max_size: int = 50) -> None:
        """Initialize request/response pool.

        Args:
            max_size: Maximum number of dictionaries in the pool
        """
        self._pool = ObjectPool(
            factory=self._create_response_dict, max_size=max_size, reset_func=self._reset_response_dict
        )
        self._feature_flags = FeatureFlags()

    def _create_response_dict(self) -> dict[str, Any]:
        """Create a new response dictionary."""
        return {"status": "success", "model": "", "response": "", "tokens": 0, "provider": {}, "cached": False}

    def _reset_response_dict(self, response_dict: dict[str, Any]) -> None:
        """Reset a response dictionary for reuse."""
        try:
            response_dict.clear()
            response_dict.update(
                {"status": "success", "model": "", "response": "", "tokens": 0, "provider": {}, "cached": False}
            )
        except Exception as e:
            log.debug("Response dict reset failed: %s", e)

    def get_response_dict(self) -> dict[str, Any]:
        """Get a response dictionary from the pool."""
        if self._feature_flags.ENABLE_OPENROUTER_OBJECT_POOLING:
            return self._pool.get()
        else:
            return self._create_response_dict()

    def return_response_dict(self, response_dict: dict[str, Any]) -> None:
        """Return a response dictionary to the pool."""
        if self._feature_flags.ENABLE_OPENROUTER_OBJECT_POOLING:
            self._pool.put(response_dict)

    def get_stats(self) -> dict[str, Any]:
        """Get response dictionary pool statistics."""
        return self._pool.get_stats()


class MetricsPool:
    """Object pool for metrics dictionaries."""

    def __init__(self, max_size: int = 30) -> None:
        """Initialize metrics pool.

        Args:
            max_size: Maximum number of metrics dictionaries in the pool
        """
        self._pool = ObjectPool(
            factory=self._create_metrics_dict, max_size=max_size, reset_func=self._reset_metrics_dict
        )
        self._feature_flags = FeatureFlags()

    def _create_metrics_dict(self) -> dict[str, Any]:
        """Create a new metrics dictionary."""
        return {
            "timestamp": time.time(),
            "latency_ms": 0.0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost": 0.0,
            "success": False,
            "model": "",
            "task_type": "",
        }

    def _reset_metrics_dict(self, metrics_dict: dict[str, Any]) -> None:
        """Reset a metrics dictionary for reuse."""
        try:
            metrics_dict.clear()
            metrics_dict.update(
                {
                    "timestamp": time.time(),
                    "latency_ms": 0.0,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "cost": 0.0,
                    "success": False,
                    "model": "",
                    "task_type": "",
                }
            )
        except Exception as e:
            log.debug("Metrics dict reset failed: %s", e)

    def get_metrics_dict(self) -> dict[str, Any]:
        """Get a metrics dictionary from the pool."""
        if self._feature_flags.ENABLE_OPENROUTER_OBJECT_POOLING:
            return self._pool.get()
        else:
            return self._create_metrics_dict()

    def return_metrics_dict(self, metrics_dict: dict[str, Any]) -> None:
        """Return a metrics dictionary to the pool."""
        if self._feature_flags.ENABLE_OPENROUTER_OBJECT_POOLING:
            self._pool.put(metrics_dict)

    def get_stats(self) -> dict[str, Any]:
        """Get metrics dictionary pool statistics."""
        return self._pool.get_stats()


class ObjectPoolManager:
    """Manages all object pools for the OpenRouter service."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize object pool manager.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._feature_flags = FeatureFlags()
        self._route_state_pool = RouteStatePool()
        self._request_response_pool = RequestResponsePool()
        self._metrics_pool = MetricsPool()
        self._stats = {"total_objects_created": 0, "total_objects_reused": 0, "memory_savings_estimate": 0.0}

    def get_route_state(self) -> Any:
        """Get a RouteState object from the pool."""
        return self._route_state_pool.get_route_state()

    def return_route_state(self, state: Any) -> None:
        """Return a RouteState object to the pool."""
        self._route_state_pool.return_route_state(state)

    def get_response_dict(self) -> dict[str, Any]:
        """Get a response dictionary from the pool."""
        return self._request_response_pool.get_response_dict()

    def return_response_dict(self, response_dict: dict[str, Any]) -> None:
        """Return a response dictionary to the pool."""
        self._request_response_pool.return_response_dict(response_dict)

    def get_metrics_dict(self) -> dict[str, Any]:
        """Get a metrics dictionary from the pool."""
        return self._metrics_pool.get_metrics_dict()

    def return_metrics_dict(self, metrics_dict: dict[str, Any]) -> None:
        """Return a metrics dictionary to the pool."""
        self._metrics_pool.return_metrics_dict(metrics_dict)

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive pool statistics.

        Returns:
            Dictionary with all pool statistics
        """
        route_stats = self._route_state_pool.get_stats()
        response_stats = self._request_response_pool.get_stats()
        metrics_stats = self._metrics_pool.get_stats()
        total_created = (
            route_stats["objects_created"] + response_stats["objects_created"] + metrics_stats["objects_created"]
        )
        total_reused = (
            route_stats["objects_reused"] + response_stats["objects_reused"] + metrics_stats["objects_reused"]
        )
        total_objects = total_created + total_reused
        overall_reuse_rate = total_reused / total_objects * 100 if total_objects > 0 else 0
        memory_savings_kb = total_reused * 1.0
        return {
            "overall_stats": {
                "total_objects_created": total_created,
                "total_objects_reused": total_reused,
                "overall_reuse_rate_percent": round(overall_reuse_rate, 2),
                "memory_savings_kb": round(memory_savings_kb, 2),
                "object_pooling_enabled": self._feature_flags.ENABLE_OPENROUTER_OBJECT_POOLING,
            },
            "route_state_pool": route_stats,
            "response_dict_pool": response_stats,
            "metrics_dict_pool": metrics_stats,
        }

    def reset_stats(self) -> None:
        """Reset all pool statistics."""
        self._route_state_pool.reset_stats()
        self._request_response_pool.reset_stats()
        self._metrics_pool.reset_stats()

    def clear_all_pools(self) -> None:
        """Clear all object pools."""
        self._route_state_pool.clear()
        self._request_response_pool.clear()
        self._metrics_pool.clear()
        log.debug("Cleared all object pools")


_object_pool_manager: ObjectPoolManager | None = None


def get_object_pool_manager(service: OpenRouterService) -> ObjectPoolManager:
    """Get or create object pool manager for the service.

    Args:
        service: The OpenRouter service instance

    Returns:
        ObjectPoolManager instance
    """
    global _object_pool_manager
    if _object_pool_manager is None:
        _object_pool_manager = ObjectPoolManager(service)
    return _object_pool_manager


def close_object_pool_manager() -> None:
    """Close the global object pool manager."""
    global _object_pool_manager
    if _object_pool_manager:
        _object_pool_manager.clear_all_pools()
        _object_pool_manager = None
