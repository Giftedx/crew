"""Memory Pool System for Resource Optimization.

This module provides intelligent memory pooling and resource management
to optimize memory usage across the Ultimate Discord Intelligence Bot.
"""

from __future__ import annotations

import gc
import time
import tracemalloc
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

import psutil


T = TypeVar("T")


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    current_memory_mb: float
    peak_memory_mb: float
    memory_usage_percent: float
    available_memory_mb: float
    total_memory_mb: float
    objects_count: int
    gc_collections: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class PooledResource:
    """A pooled resource with metadata."""

    resource: Any
    resource_type: str
    created_at: float
    last_used: float
    use_count: int = 0
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self):
        """Update usage information."""
        self.last_used = time.time()
        self.use_count += 1


class MemoryPool:
    """Intelligent memory pool for resource management."""

    def __init__(
        self,
        max_pool_size: int = 100,
        cleanup_interval: float = 300.0,  # 5 minutes
        max_idle_time: float = 600.0,  # 10 minutes
        enable_gc_optimization: bool = True,
    ):
        """Initialize the memory pool."""
        self.max_pool_size = max_pool_size
        self.cleanup_interval = cleanup_interval
        self.max_idle_time = max_idle_time
        self.enable_gc_optimization = enable_gc_optimization

        self._pools: dict[str, list[PooledResource]] = defaultdict(list)
        self._active_resources: dict[str, PooledResource] = {}
        self._resource_factories: dict[str, Callable[[], Any]] = {}
        self._last_cleanup = time.time()

        # Memory tracking
        self._memory_stats: list[MemoryStats] = []
        self._peak_memory = 0.0

        # Start memory tracking if enabled
        if self.enable_gc_optimization:
            tracemalloc.start()

    def register_resource_factory(self, resource_type: str, factory: Callable[[], Any]):
        """Register a factory function for creating resources."""
        self._resource_factories[resource_type] = factory

    def get_resource(self, resource_type: str, *args, **kwargs) -> Any:
        """Get a resource from the pool or create a new one."""
        # Check if we have an available resource in the pool
        if self._pools.get(resource_type):
            pooled_resource = self._pools[resource_type].pop()
            pooled_resource.touch()
            pooled_resource.is_active = True
            self._active_resources[id(pooled_resource.resource)] = pooled_resource
            return pooled_resource.resource

        # Create a new resource
        if resource_type not in self._resource_factories:
            raise ValueError(f"No factory registered for resource type: {resource_type}")

        factory = self._resource_factories[resource_type]
        resource = factory(*args, **kwargs)

        # Wrap in pooled resource
        pooled_resource = PooledResource(
            resource=resource,
            resource_type=resource_type,
            created_at=time.time(),
            last_used=time.time(),
        )

        self._active_resources[id(resource)] = pooled_resource
        return resource

    def return_resource(self, resource: Any) -> bool:
        """Return a resource to the pool."""
        resource_id = id(resource)

        if resource_id not in self._active_resources:
            return False

        pooled_resource = self._active_resources[resource_id]
        pooled_resource.is_active = False

        # Check if pool is full
        if len(self._pools[pooled_resource.resource_type]) >= self.max_pool_size:
            # Remove oldest resource
            oldest = min(self._pools[pooled_resource.resource_type], key=lambda r: r.last_used)
            self._pools[pooled_resource.resource_type].remove(oldest)

        # Add to pool
        self._pools[pooled_resource.resource_type].append(pooled_resource)
        del self._active_resources[resource_id]

        # Periodic cleanup
        self._cleanup_if_needed()
        return True

    def _cleanup_if_needed(self):
        """Clean up idle resources if needed."""
        current_time = time.time()
        if current_time - self._last_cleanup < self.cleanup_interval:
            return

        self._last_cleanup = current_time
        self._cleanup_idle_resources()
        self._optimize_memory()

    def _cleanup_idle_resources(self):
        """Remove idle resources from pools."""
        for resource_type, pool in self._pools.items():
            idle_resources = [r for r in pool if current_time - r.last_used > self.max_idle_time]

            for resource in idle_resources:
                pool.remove(resource)
                # Clean up the resource if it has a cleanup method
                if hasattr(resource.resource, "cleanup"):
                    resource.resource.cleanup()

    def _optimize_memory(self):
        """Optimize memory usage."""
        if not self.enable_gc_optimization:
            return

        # Force garbage collection
        collected = gc.collect()

        # Update memory stats
        self._update_memory_stats()

        # Log optimization if significant
        if collected > 0:
            print(f"Memory optimization: collected {collected} objects")

    def _update_memory_stats(self):
        """Update memory usage statistics."""
        process = psutil.Process()
        memory_info = process.memory_info()

        current_memory_mb = memory_info.rss / 1024 / 1024
        self._peak_memory = max(self._peak_memory, current_memory_mb)

        # Get system memory info
        system_memory = psutil.virtual_memory()

        stats = MemoryStats(
            current_memory_mb=current_memory_mb,
            peak_memory_mb=self._peak_memory,
            memory_usage_percent=system_memory.percent,
            available_memory_mb=system_memory.available / 1024 / 1024,
            total_memory_mb=system_memory.total / 1024 / 1024,
            objects_count=len(gc.get_objects()),
            gc_collections=sum(stat["collections"] for stat in gc.get_stats()),
        )

        self._memory_stats.append(stats)

        # Keep only recent stats (last 100)
        if len(self._memory_stats) > 100:
            self._memory_stats = self._memory_stats[-100:]

    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        self._update_memory_stats()
        return self._memory_stats[-1] if self._memory_stats else None

    def get_pool_stats(self) -> dict[str, Any]:
        """Get pool statistics."""
        total_pooled = sum(len(pool) for pool in self._pools.values())
        total_active = len(self._active_resources)

        return {
            "total_pooled_resources": total_pooled,
            "total_active_resources": total_active,
            "pool_utilization": total_pooled / self.max_pool_size * 100 if self.max_pool_size > 0 else 0,
            "resource_types": {resource_type: len(pool) for resource_type, pool in self._pools.items()},
            "memory_stats": self.get_memory_stats().__dict__ if self.get_memory_stats() else None,
        }

    def clear_pools(self):
        """Clear all resource pools."""
        for pool in self._pools.values():
            for resource in pool:
                if hasattr(resource.resource, "cleanup"):
                    resource.resource.cleanup()

        self._pools.clear()
        self._active_resources.clear()

        # Force garbage collection
        if self.enable_gc_optimization:
            gc.collect()

    def optimize_memory(self) -> dict[str, Any]:
        """Perform comprehensive memory optimization."""
        initial_stats = self.get_memory_stats()

        # Clean up idle resources
        self._cleanup_idle_resources()

        # Force garbage collection
        collected = gc.collect()

        # Update stats
        final_stats = self.get_memory_stats()

        return {
            "initial_memory_mb": initial_stats.current_memory_mb if initial_stats else 0,
            "final_memory_mb": final_stats.current_memory_mb if final_stats else 0,
            "memory_saved_mb": (initial_stats.current_memory_mb - final_stats.current_memory_mb)
            if initial_stats and final_stats
            else 0,
            "objects_collected": collected,
            "pool_stats": self.get_pool_stats(),
        }


class ResourceManager:
    """High-level resource manager with automatic pooling."""

    def __init__(self, memory_pool: MemoryPool | None = None):
        """Initialize the resource manager."""
        self.memory_pool = memory_pool or MemoryPool()
        self._context_managers: dict[str, Any] = {}

    def register_resource_type(self, resource_type: str, factory: Callable[[], Any]):
        """Register a resource type with its factory."""
        self.memory_pool.register_resource_factory(resource_type, factory)

    def get_resource(self, resource_type: str, *args, **kwargs) -> Any:
        """Get a resource with automatic pooling."""
        return self.memory_pool.get_resource(resource_type, *args, **kwargs)

    def return_resource(self, resource: Any) -> bool:
        """Return a resource to the pool."""
        return self.memory_pool.return_resource(resource)

    def with_resource(self, resource_type: str, *args, **kwargs):
        """Context manager for automatic resource management."""
        return ResourceContext(self, resource_type, *args, **kwargs)

    def optimize_memory(self) -> dict[str, Any]:
        """Optimize memory usage."""
        return self.memory_pool.optimize_memory()

    def get_stats(self) -> dict[str, Any]:
        """Get resource manager statistics."""
        return self.memory_pool.get_pool_stats()


class ResourceContext:
    """Context manager for automatic resource pooling."""

    def __init__(self, manager: ResourceManager, resource_type: str, *args, **kwargs):
        """Initialize the resource context."""
        self.manager = manager
        self.resource_type = resource_type
        self.args = args
        self.kwargs = kwargs
        self.resource = None

    def __enter__(self):
        """Enter the context and get a resource."""
        self.resource = self.manager.get_resource(self.resource_type, *self.args, **self.kwargs)
        return self.resource

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and return the resource."""
        if self.resource is not None:
            self.manager.return_resource(self.resource)


# Global resource manager instance
_global_resource_manager = ResourceManager()


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance."""
    return _global_resource_manager


def register_resource_type(resource_type: str, factory: Callable[[], Any]):
    """Register a resource type with the global manager."""
    manager = get_resource_manager()
    manager.register_resource_type(resource_type, factory)


def get_pooled_resource(resource_type: str, *args, **kwargs) -> Any:
    """Get a pooled resource from the global manager."""
    manager = get_resource_manager()
    return manager.get_resource(resource_type, *args, **kwargs)


def return_pooled_resource(resource: Any) -> bool:
    """Return a resource to the global pool."""
    manager = get_resource_manager()
    return manager.return_resource(resource)


def with_pooled_resource(resource_type: str, *args, **kwargs):
    """Context manager for pooled resources."""
    manager = get_resource_manager()
    return manager.with_resource(resource_type, *args, **kwargs)


def optimize_memory() -> dict[str, Any]:
    """Optimize memory usage using the global manager."""
    manager = get_resource_manager()
    return manager.optimize_memory()


def get_memory_stats() -> dict[str, Any]:
    """Get memory statistics from the global manager."""
    manager = get_resource_manager()
    return manager.get_stats()
