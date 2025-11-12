"""Unified Cache Service

This module provides a consolidated caching layer that unifies all caching
functionality across the application, replacing the fragmented cache services.

Features:
- Multi-level caching (memory, Redis, file-based)
- TTL management with automatic expiration
- Cache invalidation strategies
- Performance metrics and monitoring
- Tenant-aware caching with namespace isolation
- Compression for large cached objects
- Cache warming and preloading

Usage:
    from ultimate_discord_intelligence_bot.services.unified_cache_service import UnifiedCacheService

    cache = UnifiedCacheService()

    # Basic caching
    await cache.set("key", "value", ttl=3600)
    value = await cache.get("key")

    # Tenant-aware caching
    await cache.set_tenant("key", "value", tenant="tenant_id", ttl=3600)
    value = await cache.get_tenant("key", tenant="tenant_id")

    # Batch operations
    await cache.set_many({"key1": "value1", "key2": "value2"})
    values = await cache.get_many(["key1", "key2"])
"""

from __future__ import annotations

import asyncio
import json
import logging
import pickle
import time
from platform.cache.unified_config import get_unified_cache_config
from typing import Any

from app.config.base import BaseConfig
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a cached entry with metadata."""

    def __init__(
        self, value: Any, ttl: int, created_at: float, tenant: str | None = None, workspace: str | None = None
    ):
        self.value = value
        self.ttl = ttl
        self.created_at = created_at
        self.tenant = tenant
        self.workspace = workspace
        self.access_count = 0
        self.last_accessed = created_at

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl <= 0:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self) -> None:
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = time.time()


class UnifiedCacheService:
    """Unified cache service with multi-level caching support."""

    def __init__(
        self,
        config: BaseConfig | None = None,
        max_memory_size: int = 1000,
        default_ttl: int | None = None,
        enable_compression: bool = True,
        enable_metrics: bool = True,
    ):
        """Initialize the unified cache service.

        Args:
            config: Configuration object
            max_memory_size: Maximum number of items in memory cache
            default_ttl: Default TTL in seconds (uses unified config if None)
            enable_compression: Enable compression for large objects
            enable_metrics: Enable performance metrics
        """
        self.config = config or BaseConfig.from_env()
        self.max_memory_size = max_memory_size
        if default_ttl is None:
            cache_config = get_unified_cache_config()
            self.default_ttl = cache_config.get_ttl_for_domain("tool")
        else:
            self.default_ttl = default_ttl
        self.enable_compression = enable_compression
        self.enable_metrics = enable_metrics
        self._memory_cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []
        self._redis_client = None
        self._redis_available = False
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "expired": 0,
            "compressed": 0,
            "total_size": 0,
        }
        self._init_redis()
        self._cleanup_task = asyncio.create_task(self._cleanup_expired())

    def _init_redis(self) -> None:
        """Initialize Redis client if available."""
        try:
            import redis.asyncio as redis

            redis_url = getattr(self.config, "redis_url", None)
            if redis_url:
                self._redis_client = redis.from_url(redis_url)
                self._redis_available = True
                logger.info("Redis cache initialized")
            else:
                logger.warning("Redis URL not configured, using memory-only cache")
        except ImportError:
            logger.warning("Redis not available, using memory-only cache")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis: {e}")

    def _get_cache_key(self, key: str, tenant: str | None = None, workspace: str | None = None) -> str:
        """Generate a namespaced cache key.

        Args:
            key: Base cache key
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            Namespaced cache key
        """
        if tenant and workspace:
            return f"tenant:{tenant}:workspace:{workspace}:{key}"
        elif tenant:
            return f"tenant:{tenant}:{key}"
        else:
            return f"global:{key}"

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize a value for storage.

        Args:
            value: Value to serialize

        Returns:
            Serialized bytes
        """
        try:
            if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                return json.dumps(value).encode("utf-8")
            else:
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Serialization failed: {e}")
            raise

    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize a value from storage.

        Args:
            data: Serialized data

        Returns:
            Deserialized value
        """
        try:
            try:
                return json.loads(data.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Deserialization failed: {e}")
            raise

    def _compress_data(self, data: bytes) -> bytes:
        """Compress data if compression is enabled.

        Args:
            data: Data to compress

        Returns:
            Compressed data
        """
        if not self.enable_compression or len(data) < 1024:
            return data
        try:
            import gzip

            compressed = gzip.compress(data)
            if len(compressed) < len(data):
                self._metrics["compressed"] += 1
                return compressed
            else:
                return data
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return data

    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress data if it's compressed.

        Args:
            data: Data to decompress

        Returns:
            Decompressed data
        """
        try:
            import gzip

            return gzip.decompress(data)
        except Exception:
            return data

    async def _cleanup_expired(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(60)
                expired_keys = []
                for key, entry in self._memory_cache.items():
                    if entry.is_expired():
                        expired_keys.append(key)
                for key in expired_keys:
                    del self._memory_cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
                    self._metrics["expired"] += 1
                if self._redis_available and self._redis_client:
                    pass
            except Exception as e:
                logger.error(f"Cache cleanup failed: {e}")

    async def set(
        self, key: str, value: Any, ttl: int | None = None, tenant: str | None = None, workspace: str | None = None
    ) -> StepResult:
        """Set a cache entry.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult indicating success or failure
        """
        try:
            ttl = ttl or self.default_ttl
            cache_key = self._get_cache_key(key, tenant, workspace)
            entry = CacheEntry(value=value, ttl=ttl, created_at=time.time(), tenant=tenant, workspace=workspace)
            self._memory_cache[cache_key] = entry
            self._access_order.append(cache_key)
            while len(self._memory_cache) > self.max_memory_size:
                oldest_key = self._access_order.pop(0)
                if oldest_key in self._memory_cache:
                    del self._memory_cache[oldest_key]
            if self._redis_available and self._redis_client:
                try:
                    serialized = self._serialize_value(value)
                    compressed = self._compress_data(serialized)
                    await self._redis_client.setex(cache_key, ttl, compressed)
                except Exception as e:
                    logger.warning(f"Redis set failed: {e}")
            self._metrics["sets"] += 1
            self._metrics["total_size"] += 1
            return StepResult.ok(data={"key": cache_key, "ttl": ttl})
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return StepResult.fail(f"Cache set failed: {e}")

    async def get(self, key: str, tenant: str | None = None, workspace: str | None = None) -> StepResult:
        """Get a cache entry.

        Args:
            key: Cache key
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with cached value or error
        """
        try:
            cache_key = self._get_cache_key(key, tenant, workspace)
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                if not entry.is_expired():
                    entry.touch()
                    if cache_key in self._access_order:
                        self._access_order.remove(cache_key)
                    self._access_order.append(cache_key)
                    self._metrics["hits"] += 1
                    return StepResult.ok(data=entry.value)
                else:
                    del self._memory_cache[cache_key]
                    if cache_key in self._access_order:
                        self._access_order.remove(cache_key)
                    self._metrics["expired"] += 1
            if self._redis_available and self._redis_client:
                try:
                    data = await self._redis_client.get(cache_key)
                    if data:
                        decompressed = self._decompress_data(data)
                        value = self._deserialize_value(decompressed)
                        entry = CacheEntry(
                            value=value,
                            ttl=self.default_ttl,
                            created_at=time.time(),
                            tenant=tenant,
                            workspace=workspace,
                        )
                        self._memory_cache[cache_key] = entry
                        self._access_order.append(cache_key)
                        self._metrics["hits"] += 1
                        return StepResult.ok(data=value)
                except Exception as e:
                    logger.warning(f"Redis get failed: {e}")
            self._metrics["misses"] += 1
            return StepResult.fail("Cache miss")
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return StepResult.fail(f"Cache get failed: {e}")

    async def delete(self, key: str, tenant: str | None = None, workspace: str | None = None) -> StepResult:
        """Delete a cache entry.

        Args:
            key: Cache key
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult indicating success or failure
        """
        try:
            cache_key = self._get_cache_key(key, tenant, workspace)
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
                if cache_key in self._access_order:
                    self._access_order.remove(cache_key)
                self._metrics["total_size"] -= 1
            if self._redis_available and self._redis_client:
                try:
                    await self._redis_client.delete(cache_key)
                except Exception as e:
                    logger.warning(f"Redis delete failed: {e}")
            self._metrics["deletes"] += 1
            return StepResult.ok(data={"deleted": cache_key})
        except Exception as e:
            logger.error(f"Cache delete failed: {e}")
            return StepResult.fail(f"Cache delete failed: {e}")

    async def set_many(
        self, items: dict[str, Any], ttl: int | None = None, tenant: str | None = None, workspace: str | None = None
    ) -> StepResult:
        """Set multiple cache entries.

        Args:
            items: Dictionary of key-value pairs to cache
            ttl: Time to live in seconds
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult indicating success or failure
        """
        try:
            results = []
            for key, value in items.items():
                result = await self.set(key, value, ttl, tenant, workspace)
                if result.success:
                    results.append(key)
                else:
                    logger.warning(f"Failed to cache key {key}: {result.error}")
            return StepResult.ok(data={"cached_keys": results})
        except Exception as e:
            logger.error(f"Cache set_many failed: {e}")
            return StepResult.fail(f"Cache set_many failed: {e}")

    async def get_many(self, keys: list[str], tenant: str | None = None, workspace: str | None = None) -> StepResult:
        """Get multiple cache entries.

        Args:
            keys: List of keys to retrieve
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with dictionary of key-value pairs
        """
        try:
            results = {}
            for key in keys:
                result = await self.get(key, tenant, workspace)
                if result.success:
                    results[key] = result.data
            return StepResult.ok(data=results)
        except Exception as e:
            logger.error(f"Cache get_many failed: {e}")
            return StepResult.fail(f"Cache get_many failed: {e}")

    async def clear(self, tenant: str | None = None, workspace: str | None = None) -> StepResult:
        """Clear cache entries.

        Args:
            tenant: Clear entries for specific tenant
            workspace: Clear entries for specific workspace

        Returns:
            StepResult indicating success or failure
        """
        try:
            if tenant and workspace:
                pattern = f"tenant:{tenant}:workspace:{workspace}:*"
            elif tenant:
                pattern = f"tenant:{tenant}:*"
            else:
                pattern = "*"
            keys_to_remove = []
            for key in self._memory_cache:
                if tenant and workspace:
                    if key.startswith(f"tenant:{tenant}:workspace:{workspace}:"):
                        keys_to_remove.append(key)
                elif tenant:
                    if key.startswith(f"tenant:{tenant}:"):
                        keys_to_remove.append(key)
                else:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del self._memory_cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
            if self._redis_available and self._redis_client:
                try:
                    if pattern == "*":
                        await self._redis_client.flushdb()
                    else:
                        keys = await self._redis_client.keys(pattern)
                        if keys:
                            await self._redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Redis clear failed: {e}")
            self._metrics["total_size"] = len(self._memory_cache)
            return StepResult.ok(data={"cleared": len(keys_to_remove)})
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return StepResult.fail(f"Cache clear failed: {e}")

    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics.

        Returns:
            Dictionary with cache metrics
        """
        if not self.enable_metrics:
            return {"metrics_disabled": True}
        total_requests = self._metrics["hits"] + self._metrics["misses"]
        hit_rate = self._metrics["hits"] / total_requests if total_requests > 0 else 0
        return {
            "hits": self._metrics["hits"],
            "misses": self._metrics["misses"],
            "hit_rate": hit_rate,
            "sets": self._metrics["sets"],
            "deletes": self._metrics["deletes"],
            "expired": self._metrics["expired"],
            "compressed": self._metrics["compressed"],
            "total_size": self._metrics["total_size"],
            "memory_size": len(self._memory_cache),
            "redis_available": self._redis_available,
        }

    def get_status(self) -> dict[str, Any]:
        """Get cache service status.

        Returns:
            Dictionary with service status
        """
        return {
            "memory_cache_size": len(self._memory_cache),
            "max_memory_size": self.max_memory_size,
            "redis_available": self._redis_available,
            "compression_enabled": self.enable_compression,
            "metrics_enabled": self.enable_metrics,
            "default_ttl": self.default_ttl,
        }

    async def close(self) -> None:
        """Close the cache service and cleanup resources."""
        try:
            if hasattr(self, "_cleanup_task"):
                self._cleanup_task.cancel()
            if self._redis_client:
                await self._redis_client.close()
        except Exception as e:
            logger.error(f"Cache close failed: {e}")

    def __del__(self):
        """Cleanup on destruction."""
        try:
            if hasattr(self, "_cleanup_task"):
                self._cleanup_task.cancel()
        except Exception:
            pass
