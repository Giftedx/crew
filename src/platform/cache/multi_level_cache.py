"""Multi-level caching system for expensive ML/AI operations."""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
import time
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using memory-only cache")


class MultiLevelCache:
    """Multi-level cache with memory → Redis → disk fallback."""

    def __init__(
        self,
        redis_url: str | None = None,
        max_memory_size: int = 1000,
        default_ttl: int = 3600,
        enable_disk_cache: bool = False,
        disk_cache_path: str = "/tmp/cache",
    ):
        """Initialize multi-level cache.

        Args:
            redis_url: Redis connection URL (optional)
            max_memory_size: Maximum number of items in memory cache
            default_ttl: Default TTL in seconds
            enable_disk_cache: Whether to enable disk caching
            disk_cache_path: Path for disk cache storage
        """
        self.max_memory_size = max_memory_size
        self.default_ttl = default_ttl
        self.enable_disk_cache = enable_disk_cache
        self.disk_cache_path = disk_cache_path
        self.memory_cache: dict[str, dict[str, Any]] = {}
        self.memory_access_times: dict[str, float] = {}
        self.redis_client: redis.Redis | None = None
        self.redis_available = False
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=False)
                self.redis_client.ping()
                self.redis_available = True
                logger.info("Multi-level cache connected to Redis")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.redis_client = None
        if self.enable_disk_cache:
            import os

            os.makedirs(self.disk_cache_path, exist_ok=True)

    def _generate_key(self, operation: str, inputs: dict[str, Any], tenant: str = "", workspace: str = "") -> str:
        """Generate cache key from operation and inputs."""
        inputs_str = json.dumps(inputs, sort_keys=True)
        inputs_hash = hashlib.sha256(inputs_str.encode()).hexdigest()[:16]
        namespace = f"{tenant}:{workspace}" if tenant and workspace else "default"
        return f"cache:{namespace}:{operation}:{inputs_hash}"

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            if isinstance(value, (str, int, float, bool, list, dict)):
                return json.dumps(value).encode()
        except (TypeError, ValueError):
            pass
        return pickle.dumps(value)

    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            return json.loads(data.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        return pickle.loads(data)

    def _is_expired(self, timestamp: float, ttl: int) -> bool:
        """Check if cache entry is expired."""
        return time.time() - timestamp > ttl

    def _evict_lru(self) -> None:
        """Evict least recently used item from memory cache."""
        if len(self.memory_cache) < self.max_memory_size:
            return
        lru_key = min(self.memory_access_times.keys(), key=lambda k: self.memory_access_times[k])
        if lru_key in self.memory_cache:
            del self.memory_cache[lru_key]
        if lru_key in self.memory_access_times:
            del self.memory_access_times[lru_key]

    def get(self, operation: str, inputs: dict[str, Any], tenant: str = "", workspace: str = "") -> Any | None:
        """Get value from cache.

        Args:
            operation: Operation name (e.g., 'transcription', 'embedding')
            inputs: Input parameters for the operation
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            Cached value or None if not found/expired
        """
        key = self._generate_key(operation, inputs, tenant, workspace)
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if not self._is_expired(entry["timestamp"], entry["ttl"]):
                self.memory_access_times[key] = time.time()
                logger.debug(f"Cache hit (memory): {operation}")
                return entry["value"]
            else:
                del self.memory_cache[key]
                if key in self.memory_access_times:
                    del self.memory_access_times[key]
        if self.redis_available and self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    entry = self._deserialize_value(data)
                    if not self._is_expired(entry["timestamp"], entry["ttl"]):
                        self._evict_lru()
                        self.memory_cache[key] = entry
                        self.memory_access_times[key] = time.time()
                        logger.debug(f"Cache hit (Redis): {operation}")
                        return entry["value"]
                    else:
                        self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis cache get error: {e}")
        if self.enable_disk_cache:
            try:
                import os

                disk_path = os.path.join(self.disk_cache_path, f"{key}.cache")
                if os.path.exists(disk_path):
                    with open(disk_path, "rb") as f:
                        data = f.read()
                    entry = self._deserialize_value(data)
                    if not self._is_expired(entry["timestamp"], entry["ttl"]):
                        self._evict_lru()
                        self.memory_cache[key] = entry
                        self.memory_access_times[key] = time.time()
                        logger.debug(f"Cache hit (disk): {operation}")
                        return entry["value"]
                    else:
                        os.remove(disk_path)
            except Exception as e:
                logger.warning(f"Disk cache get error: {e}")
        logger.debug(f"Cache miss: {operation}")
        return None

    def set(
        self,
        operation: str,
        inputs: dict[str, Any],
        value: Any,
        ttl: int | None = None,
        tenant: str = "",
        workspace: str = "",
    ) -> bool:
        """Set value in cache.

        Args:
            operation: Operation name
            inputs: Input parameters
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            True if successfully cached
        """
        key = self._generate_key(operation, inputs, tenant, workspace)
        ttl = ttl or self.default_ttl
        timestamp = time.time()
        entry = {"value": value, "timestamp": timestamp, "ttl": ttl}
        self._evict_lru()
        self.memory_cache[key] = entry
        self.memory_access_times[key] = timestamp
        if self.redis_available and self.redis_client:
            try:
                data = self._serialize_value(entry)
                self.redis_client.setex(key, ttl, data)
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")
        if self.enable_disk_cache:
            try:
                import os

                disk_path = os.path.join(self.disk_cache_path, f"{key}.cache")
                data = self._serialize_value(entry)
                with open(disk_path, "wb") as f:
                    f.write(data)
            except Exception as e:
                logger.warning(f"Disk cache set error: {e}")
        logger.debug(f"Cache set: {operation}")
        return True

    def delete(self, operation: str, inputs: dict[str, Any], tenant: str = "", workspace: str = "") -> bool:
        """Delete value from cache.

        Args:
            operation: Operation name
            inputs: Input parameters
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            True if successfully deleted
        """
        key = self._generate_key(operation, inputs, tenant, workspace)
        deleted = False
        if key in self.memory_cache:
            del self.memory_cache[key]
            deleted = True
        if key in self.memory_access_times:
            del self.memory_access_times[key]
        if self.redis_available and self.redis_client:
            try:
                if self.redis_client.delete(key):
                    deleted = True
            except Exception as e:
                logger.warning(f"Redis cache delete error: {e}")
        if self.enable_disk_cache:
            try:
                import os

                disk_path = os.path.join(self.disk_cache_path, f"{key}.cache")
                if os.path.exists(disk_path):
                    os.remove(disk_path)
                    deleted = True
            except Exception as e:
                logger.warning(f"Disk cache delete error: {e}")
        return deleted

    def clear(self, tenant: str = "", workspace: str = "") -> bool:
        """Clear cache for tenant/workspace or all.

        Args:
            tenant: Tenant identifier (empty for all)
            workspace: Workspace identifier (empty for all)

        Returns:
            True if successfully cleared
        """
        cleared = False
        if tenant and workspace:
            namespace = f"{tenant}:{workspace}"
            keys_to_remove = [k for k in self.memory_cache if f"cache:{namespace}:" in k]
        else:
            keys_to_remove = list(self.memory_cache.keys())
        for key in keys_to_remove:
            if key in self.memory_cache:
                del self.memory_cache[key]
            if key in self.memory_access_times:
                del self.memory_access_times[key]
            cleared = True
        if self.redis_available and self.redis_client:
            try:
                pattern = f"cache:{tenant}:{workspace}:*" if tenant and workspace else "cache:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    cleared = True
            except Exception as e:
                logger.warning(f"Redis cache clear error: {e}")
        if self.enable_disk_cache:
            try:
                import glob
                import os

                if tenant and workspace:
                    pattern = os.path.join(self.disk_cache_path, f"cache:{tenant}:{workspace}:*.cache")
                else:
                    pattern = os.path.join(self.disk_cache_path, "cache:*.cache")
                for file_path in glob.glob(pattern):
                    os.remove(file_path)
                    cleared = True
            except Exception as e:
                logger.warning(f"Disk cache clear error: {e}")
        return cleared

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "memory_cache_size": len(self.memory_cache),
            "redis_available": self.redis_available,
            "disk_cache_enabled": self.enable_disk_cache,
        }
        if self.redis_available and self.redis_client:
            try:
                redis_info = self.redis_client.info()
                stats["redis_used_memory"] = redis_info.get("used_memory", 0)
                stats["redis_connected_clients"] = redis_info.get("connected_clients", 0)
            except Exception as e:
                stats["redis_error"] = str(e)
        return stats

    def health_check(self) -> StepResult:
        """Check cache health."""
        try:
            self.set("test", {"test": True}, "test_value", ttl=1)
            result = self.get("test", {"test": True})
            if result != "test_value":
                return StepResult.fail("Memory cache health check failed")
            if self.redis_available and self.redis_client:
                self.redis_client.ping()
            return StepResult.ok(data={"status": "healthy", "stats": self.get_stats()})
        except Exception as e:
            return StepResult.fail(f"Cache health check failed: {e}")


_cache_instance: MultiLevelCache | None = None


def get_cache() -> MultiLevelCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MultiLevelCache()
    return _cache_instance


def cache_result(
    operation: str, inputs: dict[str, Any], value: Any, ttl: int | None = None, tenant: str = "", workspace: str = ""
) -> bool:
    """Convenience function to cache a result."""
    cache = get_cache()
    return cache.set(operation, inputs, value, ttl, tenant, workspace)


def get_cached_result(operation: str, inputs: dict[str, Any], tenant: str = "", workspace: str = "") -> Any | None:
    """Convenience function to get a cached result."""
    cache = get_cache()
    return cache.get(operation, inputs, tenant, workspace)


class _KeyValueAsyncAdapter:
    """Async key-value facade over MultiLevelCache.

    This adapter maps simple key operations onto the existing operation/inputs
    interface and provides async-compatible methods expected by CacheService
    and APICacheMiddleware. Dependency APIs are no-ops in this lightweight
    shim; they can be extended later without breaking callers.
    """

    def __init__(self, cache: MultiLevelCache, namespace: str = "kv") -> None:
        self._cache = cache
        self._ns = namespace or "kv"

    async def get(self, key: str) -> Any | None:
        return self._cache.get(self._ns, {"key": key})

    async def set(self, key: str, value: Any, dependencies: set[str] | None = None) -> bool:
        return self._cache.set(self._ns, {"key": key}, value)

    async def delete(self, key: str, cascade: bool = True) -> bool:
        return self._cache.delete(self._ns, {"key": key})

    async def get_dependencies(self, key: str) -> set[str]:
        return set()

    async def get_dependents(self, key: str) -> set[str]:
        return set()

    def get_stats(self) -> dict[str, Any]:
        return self._cache.get_stats()


def get_multi_level_cache(name: str, _l2_cache: Any | None = None, _enable_dependency_tracking: bool = True):
    """Factory compatible with CacheService expectations.

    Returns an async key-value adapter backed by the process-wide
    MultiLevelCache instance. The parameters are accepted for forward
    compatibility with enhanced implementations.
    """
    base = get_cache()
    return _KeyValueAsyncAdapter(base, namespace=name)


# CacheEntry placeholder for backward compatibility
class CacheEntry:
    """Placeholder cache entry class."""

    def __init__(self, key: str, value: Any, ttl: int | None = None):
        self.key = key
        self.value = value
        self.ttl = ttl


__all__ = [
    "CacheEntry",
    "MultiLevelCache",
    "get_cache",
    "get_multi_level_cache",
]
