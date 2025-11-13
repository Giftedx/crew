"""Enhanced Redis cache with pipeline optimization, distributed coordination, and acceleration.

This module provides high-performance caching for LLM responses and retrieval results
with features designed for the multi-tenant Ultimate Discord Intelligence Bot.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from platform.config.configuration import get_config
from typing import TYPE_CHECKING, Any, cast


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)
try:
    import redis
    import redis.connection
    from redis.cluster import RedisCluster

    try:
        import importlib.util as _ils

        HIREDIS_AVAILABLE = _ils.find_spec("hiredis") is not None
        if HIREDIS_AVAILABLE:
            logger.info("Enhanced Redis cache using hiredis parser for 40% faster performance")
        else:
            logger.debug("hiredis not available or incompatible version, using standard parser")
    except Exception:
        HIREDIS_AVAILABLE = False
        logger.debug("hiredis detection failed, using standard parser")
except ImportError:
    redis = None
    RedisCluster = None
    HIREDIS_AVAILABLE = False


@dataclass
class EnhancedRedisCache:
    """High-performance Redis cache with pipeline optimization and clustering support."""

    url: str
    namespace: str = "enhanced_llm"
    ttl: int = 3600
    pipeline_size: int = 100
    enable_clustering: bool = False
    timeout: float = 5.0
    retry_attempts: int = 3

    def __post_init__(self) -> None:
        """Initialize Redis connection with optimizations."""
        if redis is None:
            raise RuntimeError("redis package not installed - run: pip install redis")
        connection_kwargs = {
            "decode_responses": True,
            "socket_connect_timeout": self.timeout,
            "socket_timeout": self.timeout,
            "retry_on_timeout": True,
            "health_check_interval": 30,
        }
        try:
            exc_mod = getattr(redis, "exceptions", None) if redis is not None else None
            BusyLoadingError = getattr(exc_mod, "BusyLoadingError", None) if exc_mod is not None else None
            ConnectionError = getattr(exc_mod, "ConnectionError", None) if exc_mod is not None else None
            if BusyLoadingError is not None and ConnectionError is not None:
                cast("dict[str, Any]", connection_kwargs)["retry_on_error"] = [BusyLoadingError, ConnectionError]
        except Exception:
            pass
        conn_mod = getattr(redis, "connection", None) if redis is not None else None
        hiredis_conn_cls = getattr(conn_mod, "HiredisConnection", None) if conn_mod is not None else None
        if HIREDIS_AVAILABLE and hiredis_conn_cls is not None:
            connection_kwargs["connection_class"] = hiredis_conn_cls
        self._r: Any
        if self.enable_clustering:
            if RedisCluster is not None:
                self._r = RedisCluster.from_url(self.url, **connection_kwargs)
                logger.info(f"Enhanced Redis cache connected to cluster: {self.url}")
            else:
                raise RuntimeError("Redis cluster requested but redis package not available")
        else:
            self._r = redis.Redis.from_url(self.url, **cast("Any", connection_kwargs))
            logger.info(f"Enhanced Redis cache connected: {self.url}")
        try:
            self._r.ping()
            logger.info("Enhanced Redis cache connection verified")
        except Exception as e:
            logger.error(f"Enhanced Redis cache connection failed: {e}")
            raise

    def _make_key(self, key: str) -> str:
        """Generate namespaced cache key."""
        return f"{self.namespace}:{key}"

    def _make_hash_key(self, prompt: str, model: str, provider_sig: str = "") -> str:
        """Generate deterministic cache key for LLM prompts."""
        content = f"{prompt}|model={model}|provider={provider_sig}"
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        return self._make_key(f"llm:{model}:{digest}")

    def get(self, key: str, track_access: bool = True) -> dict[str, Any] | None:
        """Get cached value with automatic retry and error handling."""
        cache_key = self._make_key(key)
        for attempt in range(self.retry_attempts):
            try:
                raw = cast("str | None", self._r.get(cache_key))
                if raw is None:
                    return None
                data = json.loads(raw)
                if isinstance(data, dict):
                    if track_access:
                        self.track_access_pattern(key)
                    return data
                logger.warning(f"Invalid cache data type for key {key}: {type(data)}")
                return None
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode cached JSON for key: {key}")
                try:
                    self._r.delete(cache_key)
                except Exception:
                    logger.debug("Failed to delete corrupted cache entry")
                return None
            except Exception as e:
                is_redis_error = redis is not None and isinstance(e, getattr(redis, "RedisError", Exception))
                if is_redis_error and attempt < self.retry_attempts - 1:
                    logger.warning(f"Redis error on attempt {attempt + 1}/{self.retry_attempts}: {e}")
                    time.sleep(0.1 * 2**attempt)
                    continue
                elif is_redis_error:
                    logger.error(f"Redis get failed after {self.retry_attempts} attempts: {e}")
                else:
                    logger.error(f"Unexpected error getting cache key {key}: {e}")
                return None
        return None

    def set(self, key: str, value: dict[str, Any], ttl: int | None = None) -> bool:
        """Set cached value with pipeline optimization for batch operations."""
        cache_key = self._make_key(key)
        effective_ttl = ttl or self.ttl
        try:
            serialized = json.dumps(value, separators=(",", ":"))
            self._r.setex(cache_key, effective_ttl, serialized)
            return True
        except Exception as e:
            if redis is not None and isinstance(e, getattr(redis, "RedisError", Exception)):
                logger.error(f"Redis set failed for key {key}: {e}")
                return False
            else:
                logger.error(f"Unexpected error setting cache key {key}: {e}")
                return False

    def mget(self, keys: list[str]) -> dict[str, dict[str, Any] | None]:
        """Batch get multiple cache keys with pipeline optimization."""
        if not keys:
            return {}
        cache_keys = [self._make_key(k) for k in keys]
        try:
            pipeline = self._r.pipeline()
            for cache_key in cache_keys:
                pipeline.get(cache_key)
            raw_values = pipeline.execute()
            result: dict[str, dict[str, Any] | None] = {}
            for _i, (original_key, raw_value) in enumerate(zip(keys, raw_values, strict=False)):
                if raw_value is None:
                    result[original_key] = None
                    continue
                try:
                    data = json.loads(raw_value)
                    if isinstance(data, dict):
                        result[original_key] = data
                    else:
                        logger.warning(f"Invalid cache data type for key {original_key}: {type(data)}")
                        result[original_key] = None
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode cached JSON for key: {original_key}")
                    result[original_key] = None
            return result
        except Exception as e:
            if redis is not None and isinstance(e, getattr(redis, "RedisError", Exception)):
                logger.error(f"Redis mget failed for {len(keys)} keys: {e}")
                return dict.fromkeys(keys)
            else:
                logger.error(f"Unexpected error in mget for {len(keys)} keys: {e}")
                return dict.fromkeys(keys)

    def mset(self, data: dict[str, dict[str, Any]], ttl: int | None = None) -> int:
        """Batch set multiple cache keys with pipeline optimization."""
        if not data:
            return 0
        effective_ttl = ttl or self.ttl
        success_count = 0
        try:
            pipeline = self._r.pipeline()
            for key, value in data.items():
                try:
                    cache_key = self._make_key(key)
                    serialized = json.dumps(value, separators=(",", ":"))
                    pipeline.setex(cache_key, effective_ttl, serialized)
                except Exception as e:
                    logger.warning(f"Failed to prepare cache entry for key {key}: {e}")
                    continue
            results = pipeline.execute()
            success_count = sum(1 for result in results if result is True)
            logger.debug(f"Batch cached {success_count}/{len(data)} entries")
            return success_count
        except Exception as e:
            if redis is not None and isinstance(e, getattr(redis, "RedisError", Exception)):
                logger.error(f"Redis mset failed for {len(data)} keys: {e}")
                return 0
            else:
                logger.error(f"Unexpected error in mset for {len(data)} keys: {e}")
                return 0

    def delete(self, key: str) -> bool:
        """Delete cache entry."""
        cache_key = self._make_key(key)
        try:
            result = self._r.delete(cache_key)
            return bool(result)
        except Exception as e:
            if redis is not None and isinstance(e, getattr(redis, "RedisError", Exception)):
                logger.error(f"Redis delete failed for key {key}: {e}")
                return False
            else:
                logger.error(f"Unexpected error deleting cache key {key}: {e}")
                return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern (use with caution in production)."""
        cache_pattern = self._make_key(pattern)
        try:
            keys = list(self._r.scan_iter(match=cache_pattern))
            if not keys:
                return 0
            pipeline = self._r.pipeline()
            for key in keys:
                pipeline.delete(key)
            results = pipeline.execute()
            deleted_count = sum(1 for result in results if result > 0)
            logger.info(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")
            return deleted_count
        except Exception as e:
            if redis is not None and isinstance(e, getattr(redis, "RedisError", Exception)):
                logger.error(f"Redis pattern invalidation failed for pattern {pattern}: {e}")
                return 0
            else:
                logger.error(f"Unexpected error in pattern invalidation for pattern {pattern}: {e}")
                return 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        try:
            info = self._r.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0)
                / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
                * 100,
                "hiredis_enabled": HIREDIS_AVAILABLE,
                "clustering_enabled": self.enable_clustering,
            }
        except Exception:
            return {"error": "Unable to fetch Redis stats"}

    def track_access_pattern(self, key: str) -> None:
        """Track access patterns for cache warming optimization."""
        try:
            access_key = f"{self.namespace}:access:{key}"
            self._r.incr(access_key)
            self._r.expire(access_key, 86400)
        except Exception as e:
            logger.debug(f"Failed to track access pattern for key {key}: {e}")

    def get_frequent_keys(self, limit: int = 100) -> list[tuple[str, int]]:
        """Get most frequently accessed keys for cache warming."""
        try:
            pattern = f"{self.namespace}:access:*"
            keys = list(self._r.scan_iter(match=pattern))
            if not keys:
                return []
            pipeline = self._r.pipeline()
            for key in keys:
                pipeline.get(key)
            counts = pipeline.execute()
            key_counts = []
            for key, count in zip(keys, counts, strict=False):
                if count is not None:
                    original_key = key.replace(f"{self.namespace}:access:", "")
                    key_counts.append((original_key, int(count)))
            key_counts.sort(key=lambda x: x[1], reverse=True)
            return key_counts[:limit]
        except Exception as e:
            logger.error(f"Failed to get frequent keys: {e}")
            return []

    def warm_cache(self, keys: list[str], data_fetcher: Callable[[str], dict[str, Any] | None]) -> int:
        """Warm the cache for a list of keys using a provided fetcher.

        Returns the number of keys successfully written to Redis.
        """
        warmed_count = 0
        try:
            pipeline = self._r.pipeline()
            for key in keys:
                try:
                    data = data_fetcher(key)
                    if data is not None:
                        cache_key = self._make_key(key)
                        serialized = json.dumps(data, separators=(",", ":"))
                        pipeline.setex(cache_key, self.ttl, serialized)
                        warmed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to warm cache for key {key}: {e}")
                    continue
            if warmed_count > 0:
                results = pipeline.execute()
                success_count = sum(1 for result in results if result is True)
                logger.info(f"Cache warming completed: {success_count}/{warmed_count} keys warmed")
                return success_count
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
        return 0

    def get_cache_efficiency_score(self) -> float:
        """Calculate cache efficiency score based on hit rate and memory usage."""
        try:
            stats = self.get_stats()
            if "error" in stats:
                return 0.0
            hit_rate = stats.get("hit_rate", 0.0)
            efficiency = hit_rate / 100.0 * 0.8
            memory_efficiency = 0.2
            return min(1.0, efficiency + memory_efficiency)
        except Exception as e:
            logger.error(f"Failed to calculate cache efficiency: {e}")
            return 0.0


class DistributedLLMCache:
    """LLM cache with distributed coordination and tenant-aware namespacing."""

    def __init__(self, url: str, ttl: int = 3600, tenant: str = "default", workspace: str = "main") -> None:
        self.tenant = tenant
        self.workspace = workspace
        self.namespace = f"llm_cache:{tenant}:{workspace}"
        self.cache = EnhancedRedisCache(
            url=url, namespace=self.namespace, ttl=ttl, pipeline_size=100, enable_clustering=False
        )

    def make_key(self, prompt: str, model: str, provider_sig: str = "") -> str:
        """Generate cache key compatible with existing LLMCache interface."""
        return self.cache._make_hash_key(prompt, model, provider_sig)

    def get(self, key: str, track_access: bool = True) -> dict[str, Any] | None:
        """Get cached LLM response."""
        return self.cache.get(key, track_access=track_access)

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Set cached LLM response."""
        self.cache.set(key, value)

    def invalidate_tenant_cache(self) -> int:
        """Invalidate all cache entries for the current tenant."""
        pattern = f"llm_cache:{self.tenant}:*"
        return self.cache.invalidate_pattern(pattern)


def create_enhanced_llm_cache(tenant: str = "default", workspace: str = "main") -> DistributedLLMCache | None:
    """Factory function to create enhanced Redis LLM cache if configured."""
    try:
        config = get_config()
        redis_url = getattr(config, "rate_limit_redis_url", None) or getattr(config, "redis_url", None)
        if not redis_url or redis is None:
            logger.info("Enhanced Redis cache not available - no Redis URL configured or redis package missing")
            return None
        cache_ttl = int(getattr(config, "cache_ttl_llm", 3600))
        return DistributedLLMCache(url=str(redis_url), ttl=cache_ttl, tenant=tenant, workspace=workspace)
    except Exception as e:
        logger.error(f"Failed to create enhanced Redis LLM cache: {e}")
        return None
