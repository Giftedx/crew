"""Resource pooling system for efficient management of external service connections.

This module provides connection pooling for external services like OpenRouter API,
Qdrant vector database, and other network resources to improve performance
and reduce connection overhead.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)


T = TypeVar("T")  # Type of resource being pooled


@dataclass
class PoolStats:
    """Statistics for resource pool performance."""

    total_created: int = 0
    total_destroyed: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_creations: int = 0
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def utilization_rate(self) -> float:
        """Calculate pool utilization rate."""
        total = self.active_connections + self.idle_connections
        return self.active_connections / total if total > 0 else 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class ResourceFactory(ABC, Generic[T]):
    """Abstract factory for creating pooled resources."""

    @abstractmethod
    async def create_resource(self) -> T:
        """Create a new resource instance."""
        pass

    @abstractmethod
    async def destroy_resource(self, resource: T) -> None:
        """Destroy a resource instance."""
        pass

    @abstractmethod
    def is_resource_valid(self, resource: T) -> bool:
        """Check if a resource is still valid for use."""
        pass

    @abstractmethod
    async def validate_resource(self, resource: T) -> bool:
        """Perform validation on a resource before reuse."""
        pass


class ConnectionPool(Generic[T]):
    """Generic connection pool for managing reusable resources."""

    def __init__(
        self,
        factory: ResourceFactory[T],
        *,
        min_size: int = 1,
        max_size: int = 10,
        max_idle_time: float = 300.0,  # 5 minutes
        validation_interval: float = 60.0,  # 1 minute
        enable_metrics: bool = True,
    ):
        self.factory = factory
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.validation_interval = validation_interval
        self.enable_metrics = enable_metrics

        # Pool state
        self._pool: deque[T] = deque()
        self._active: set[T] = set()
        self._lock = threading.RLock()
        self._stats = PoolStats()

        # Background maintenance
        self._maintenance_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

        # Metrics
        self._pool_name = f"{self.__class__.__name__}_{id(self)}"

    async def start(self) -> None:
        """Start the connection pool and initialize minimum connections."""
        # Initialize minimum connections
        await self._ensure_min_connections()

        # Start background maintenance
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())

        logger.info(f"Connection pool {self._pool_name} started (min: {self.min_size}, max: {self.max_size})")

    async def stop(self) -> None:
        """Stop the connection pool and cleanup resources."""
        # Signal shutdown
        self._shutdown_event.set()

        # Cancel maintenance task
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass

        # Destroy all connections
        await self._destroy_all_connections()

        logger.info(f"Connection pool {self._pool_name} stopped")

    async def acquire(self, timeout: float = 30.0) -> T:
        """Acquire a resource from the pool."""
        if self.enable_metrics:
            self._stats.total_requests += 1

        # start_time could be used for latency tracking
        _ = time.time()

        try:
            # Try to get from pool first
            resource = await self._try_acquire_from_pool()
            if resource:
                if self.enable_metrics:
                    self._stats.cache_hits += 1
                return resource

            # Pool empty, need to create new resource
            if self.enable_metrics:
                self._stats.cache_misses += 1

            resource = await self._create_resource()
            if resource:
                self._active.add(resource)
                return resource

            # Creation failed
            raise RuntimeError("Failed to acquire resource from pool")

        except Exception as e:
            logger.error(f"Failed to acquire resource from pool: {e}")
            raise

    async def release(self, resource: T) -> None:
        """Release a resource back to the pool."""
        with self._lock:
            if resource in self._active:
                self._active.remove(resource)

                # Check if resource is still valid
                if self.factory.is_resource_valid(resource):
                    # Check if pool is not at max capacity
                    if len(self._pool) < self.max_size:
                        self._pool.append(resource)
                        return

                # Resource invalid or pool full, destroy it
                await self._destroy_resource(resource)

    async def _try_acquire_from_pool(self) -> T | None:
        """Try to acquire a resource from the pool."""
        with self._lock:
            while self._pool:
                resource = self._pool.popleft()

                # Validate resource before returning
                try:
                    if await self.factory.validate_resource(resource):
                        self._active.add(resource)
                        return resource
                    else:
                        # Resource failed validation, destroy it
                        await self._destroy_resource(resource)
                except Exception as e:
                    logger.warning(f"Resource validation failed: {e}")
                    await self._destroy_resource(resource)

            return None

    async def _create_resource(self) -> T | None:
        """Create a new resource."""
        try:
            with self._lock:
                if len(self._active) + len(self._pool) >= self.max_size:
                    return None  # Pool at capacity

            resource = await self.factory.create_resource()
            self._stats.total_created += 1
            return resource

        except Exception as e:
            logger.error(f"Failed to create resource: {e}")
            self._stats.failed_creations += 1
            return None

    async def _destroy_resource(self, resource: T) -> None:
        """Destroy a resource."""
        try:
            await self.factory.destroy_resource(resource)
            self._stats.total_destroyed += 1
        except Exception as e:
            logger.error(f"Error destroying resource: {e}")

    async def _destroy_all_connections(self) -> None:
        """Destroy all connections in the pool."""
        with self._lock:
            # Destroy active connections
            for resource in list(self._active):
                await self._destroy_resource(resource)
            self._active.clear()

            # Destroy idle connections
            for resource in list(self._pool):
                await self._destroy_resource(resource)
            self._pool.clear()

    async def _ensure_min_connections(self) -> None:
        """Ensure minimum number of connections are available."""
        with self._lock:
            current_total = len(self._active) + len(self._pool)

            for _ in range(self.min_size - current_total):
                resource = await self._create_resource()
                if resource:
                    self._pool.append(resource)

    async def _maintenance_loop(self) -> None:
        """Background maintenance loop for pool health."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.validation_interval)
                await self._perform_maintenance()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in pool maintenance: {e}")

    async def _perform_maintenance(self) -> None:
        """Perform periodic maintenance on the pool."""
        current_time = time.time()

        with self._lock:
            # Remove expired idle connections
            expired_resources = []
            for resource in list(self._pool):
                # Check if connection has been idle too long
                # (This would need to be implemented per resource type)
                if current_time - getattr(resource, "_last_used", 0) > self.max_idle_time:
                    expired_resources.append(resource)

            for resource in expired_resources:
                self._pool.remove(resource)
                await self._destroy_resource(resource)

            # Ensure minimum connections
            await self._ensure_min_connections()

    def get_stats(self) -> PoolStats:
        """Get current pool statistics."""
        with self._lock:
            return PoolStats(
                total_created=self._stats.total_created,
                total_destroyed=self._stats.total_destroyed,
                active_connections=len(self._active),
                idle_connections=len(self._pool),
                failed_creations=self._stats.failed_creations,
                total_requests=self._stats.total_requests,
                cache_hits=self._stats.cache_hits,
                cache_misses=self._stats.cache_misses,
            )


class HTTPConnectionFactory(ResourceFactory[Any]):
    """Factory for creating HTTP connections with session reuse."""

    def __init__(self, base_url: str, headers: dict[str, str] | None = None):
        self.base_url = base_url
        self.headers = headers or {}

    async def create_resource(self) -> Any:
        """Create a new HTTP session."""
        import aiohttp

        # Create session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=100,  # Max connections per host
            limit_per_host=10,  # Max connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
        )

        session = aiohttp.ClientSession(
            connector=connector, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)
        )

        # Mark creation time
        session._created_at = time.time()
        session._pool_factory = self

        return session

    async def destroy_resource(self, resource: Any) -> None:
        """Close HTTP session."""
        if hasattr(resource, "close"):
            await resource.close()

    def is_resource_valid(self, resource: Any) -> bool:
        """Check if HTTP session is still valid."""
        if not hasattr(resource, "closed") or resource.closed:
            return False

        # Check if session is too old
        if hasattr(resource, "_created_at"):
            age = time.time() - resource._created_at
            if age > 3600:  # 1 hour max age
                return False

        return True

    async def validate_resource(self, resource: Any) -> bool:
        """Validate HTTP session health."""
        if not self.is_resource_valid(resource):
            return False

        # Could add a simple HEAD request here to test connectivity
        # For now, just check if session is not closed
        return not getattr(resource, "closed", True)


class OpenRouterConnectionFactory(HTTPConnectionFactory):
    """Specialized factory for OpenRouter API connections."""

    def __init__(self, api_key: str | None = None):
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        headers["Content-Type"] = "application/json"

        super().__init__("https://openrouter.ai/api/v1", headers)

    async def create_resource(self) -> Any:
        """Create OpenRouter session."""
        session = await super().create_resource()

        # Add OpenRouter-specific configuration
        session._is_openrouter = True

        return session


class QdrantConnectionFactory(ResourceFactory[Any]):
    """Factory for Qdrant vector database connections."""

    def __init__(self, url: str, api_key: str | None = None):
        self.url = url
        self.api_key = api_key

    async def create_resource(self) -> Any:
        """Create Qdrant client."""
        from qdrant_client import QdrantClient

        # Create client with connection pooling
        client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=30,
        )

        # Mark creation time
        client._created_at = time.time()
        client._pool_factory = self

        return client

    async def destroy_resource(self, resource: Any) -> None:
        """Close Qdrant client."""
        # Qdrant client doesn't have explicit close method
        # Just mark as closed
        if hasattr(resource, "close"):
            resource.close()

    def is_resource_valid(self, resource: Any) -> bool:
        """Check if Qdrant client is valid."""
        # Check if client is too old
        if hasattr(resource, "_created_at"):
            age = time.time() - resource._created_at
            if age > 3600:  # 1 hour max age
                return False

        return True

    async def validate_resource(self, resource: Any) -> bool:
        """Validate Qdrant client health."""
        if not self.is_resource_valid(resource):
            return False

        # Test connectivity with a simple operation
        try:
            # Try to get collections (lightweight operation)
            resource.get_collections()
            return True
        except Exception:
            return False


# Global connection pools
_connection_pools: dict[str, ConnectionPool] = {}
_pools_lock = threading.Lock()


def get_connection_pool(pool_name: str, factory: ResourceFactory, **pool_kwargs) -> ConnectionPool:
    """Get or create a connection pool by name."""
    with _pools_lock:
        if pool_name not in _connection_pools:
            _connection_pools[pool_name] = ConnectionPool(factory, **pool_kwargs)
        return _connection_pools[pool_name]


def get_openrouter_pool(api_key: str | None = None) -> ConnectionPool:
    """Get OpenRouter connection pool."""
    factory = OpenRouterConnectionFactory(api_key)
    return get_connection_pool(
        "openrouter",
        factory,
        min_size=2,
        max_size=20,
        max_idle_time=300.0,
        validation_interval=60.0,
    )


def get_qdrant_pool(url: str, api_key: str | None = None) -> ConnectionPool:
    """Get Qdrant connection pool."""
    factory = QdrantConnectionFactory(url, api_key)
    return get_connection_pool(
        "qdrant",
        factory,
        min_size=1,
        max_size=10,
        max_idle_time=600.0,  # Longer idle time for vector DB
        validation_interval=120.0,
    )


async def initialize_connection_pools() -> None:
    """Initialize all connection pools."""
    logger.info("Initializing connection pools...")

    # Start all pools
    for pool_name, pool in _connection_pools.items():
        await pool.start()

    logger.info(f"Initialized {len(_connection_pools)} connection pools")


async def shutdown_connection_pools() -> None:
    """Shutdown all connection pools."""
    logger.info("Shutting down connection pools...")

    # Stop all pools
    for pool_name, pool in _connection_pools.items():
        await pool.stop()

    _connection_pools.clear()
    logger.info("All connection pools shut down")


def get_pool_stats() -> dict[str, PoolStats]:
    """Get statistics for all connection pools."""
    return {name: pool.get_stats() for name, pool in _connection_pools.items()}


__all__ = [
    "ResourceFactory",
    "ConnectionPool",
    "PoolStats",
    "HTTPConnectionFactory",
    "OpenRouterConnectionFactory",
    "QdrantConnectionFactory",
    "get_connection_pool",
    "get_openrouter_pool",
    "get_qdrant_pool",
    "initialize_connection_pools",
    "shutdown_connection_pools",
    "get_pool_stats",
]
