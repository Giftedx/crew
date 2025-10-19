"""LLM request/response caching with Redis backend and TTL support.

This module provides a caching layer for LLM requests to improve performance
and reduce costs by avoiding duplicate API calls.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from typing import Any

from .dependencies import (
    check_dependency,
    get_fallback_cache,
    get_with_fallback,
    is_feature_enabled,
)

logger = logging.getLogger(__name__)

# Try to import Redis with fallback
try:
    redis = get_with_fallback("redis", get_fallback_cache)
except Exception:
    redis = get_fallback_cache()


class LLMCache:
    """Redis-backed cache for LLM requests and responses.

    This class provides a high-performance caching layer for LLM API calls
    with configurable TTL, namespace isolation, and cache statistics.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        namespace: str = "llm_cache",
        default_ttl: int = 3600,  # 1 hour
        max_key_length: int = 250,  # Redis key limit
    ) -> None:
        """Initialize the LLM cache.

        Args:
            redis_url: Redis connection URL. If None, uses environment variable or defaults to localhost
            namespace: Cache namespace for key isolation
            default_ttl: Default time-to-live in seconds
            max_key_length: Maximum key length (Redis limit is 512MB, but we use 250 for safety)
        """
        self.namespace = namespace
        self.default_ttl = default_ttl
        self.max_key_length = max_key_length

        # Initialize Redis connection
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # Check if Redis caching is enabled and available
        if not is_feature_enabled("redis_cache") or not check_dependency("redis"):
            # Use fallback cache
            self.redis_client = None
            self._fallback_cache = get_fallback_cache()
            self.enabled = True
            logger.info("Using fallback in-memory cache (Redis disabled or unavailable)")
        else:
            # Try to use Redis
            try:
                # Import Redis only when needed
                from redis import Redis

                self.redis_client: Redis[str] | None = Redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                self.enabled = True
                logger.info("Using Redis cache backend")
            except Exception as e:
                # Fallback to in-memory cache if Redis is unavailable
                self.redis_client = None
                self._fallback_cache = get_fallback_cache()
                self.enabled = True
                logger.warning(f"Redis unavailable, using fallback cache: {e}")

    def _generate_cache_key(self, request_data: dict[str, Any]) -> str:
        """Generate a cache key from request data.

        Args:
            request_data: The request data to hash

        Returns:
            str: Cache key
        """
        # Create a deterministic hash of the request
        request_str = json.dumps(request_data, sort_keys=True, separators=(",", ":"))
        hash_obj = hashlib.sha256(request_str.encode("utf-8"))
        hash_hex = hash_obj.hexdigest()

        # Create the full key with namespace
        full_key = f"{self.namespace}:{hash_hex}"

        # Ensure key doesn't exceed max length
        if len(full_key) > self.max_key_length:
            # Truncate namespace if needed
            max_hash_length = self.max_key_length - len(f"{self.namespace}:")
            if max_hash_length > 0:
                full_key = f"{self.namespace}:{hash_hex[:max_hash_length]}"
            else:
                # Fallback to just the hash if namespace is too long
                full_key = hash_hex[: self.max_key_length]

        return full_key

    def _get_memory_cache_entry(self, key: str) -> dict[str, Any] | None:
        """Get entry from in-memory cache.

        Args:
            key: Cache key

        Returns:
            Optional cache entry or None if not found/expired
        """
        if key not in self._memory_cache:
            return None

        entry = self._memory_cache[key]
        if entry["expires_at"] < time.time():
            del self._memory_cache[key]
            return None

        return entry

    def _set_memory_cache_entry(self, key: str, value: Any, ttl: int) -> None:
        """Set entry in in-memory cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        self._memory_cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time(),
        }

    async def get(self, request_data: dict[str, Any]) -> dict[str, Any] | None:
        """Get cached response for a request.

        Args:
            request_data: The request data to look up

        Returns:
            Cached response data or None if not found
        """
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(request_data)

        try:
            if self.redis_client:
                # Redis backend
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    result = json.loads(cached_data)
                    if isinstance(result, dict):
                        return result
            else:
                # In-memory fallback
                entry = self._get_memory_cache_entry(cache_key)
                if entry and isinstance(entry["value"], dict):
                    return entry["value"]
        except Exception:
            # Log error but don't fail the request
            pass

        return None

    async def set(
        self,
        request_data: dict[str, Any],
        response_data: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Cache a response for a request.

        Args:
            request_data: The request data
            response_data: The response data to cache
            ttl: Time to live in seconds (uses default if None)
        """
        if not self.enabled:
            return

        cache_key = self._generate_cache_key(request_data)
        ttl = ttl or self.default_ttl

        # Add metadata to cached data
        cache_entry = {
            "response": response_data,
            "cached_at": time.time(),
            "ttl": ttl,
            "request_hash": cache_key,
        }

        try:
            if self.redis_client:
                # Redis backend
                self.redis_client.setex(cache_key, ttl, json.dumps(cache_entry, separators=(",", ":")))
            else:
                # In-memory fallback
                self._set_memory_cache_entry(cache_key, cache_entry, ttl)
        except Exception:
            # Log error but don't fail the request
            pass

    async def delete(self, request_data: dict[str, Any]) -> bool:
        """Delete a cached response.

        Args:
            request_data: The request data to delete from cache

        Returns:
            True if deleted, False if not found
        """
        if not self.enabled:
            return False

        cache_key = self._generate_cache_key(request_data)

        try:
            if self.redis_client:
                # Redis backend
                return bool(self.redis_client.delete(cache_key))
            else:
                # In-memory fallback
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                    return True
        except Exception:
            pass

        return False

    async def clear_namespace(self) -> int:
        """Clear all cache entries in the namespace.

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            if self.redis_client:
                # Redis backend - use pattern matching
                pattern = f"{self.namespace}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                # In-memory fallback
                keys_to_delete = [k for k in self._memory_cache.keys() if k.startswith(f"{self.namespace}:")]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                return len(keys_to_delete)
        except Exception:
            pass

        return 0

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            if self.redis_client:
                # Redis backend
                pattern = f"{self.namespace}:*"
                keys = self.redis_client.keys(pattern)
                total_keys = len(keys)

                # Get memory usage
                memory_usage = 0
                for key in keys:
                    memory_usage += self.redis_client.memory_usage(key)

                return {
                    "enabled": True,
                    "backend": "redis",
                    "namespace": self.namespace,
                    "total_keys": total_keys,
                    "memory_usage_bytes": memory_usage,
                    "default_ttl": self.default_ttl,
                }
            else:
                # In-memory fallback
                namespace_keys = [k for k in self._memory_cache.keys() if k.startswith(f"{self.namespace}:")]
                return {
                    "enabled": True,
                    "backend": "memory",
                    "namespace": self.namespace,
                    "total_keys": len(namespace_keys),
                    "memory_usage_bytes": len(str(self._memory_cache)),
                    "default_ttl": self.default_ttl,
                }
        except Exception:
            return {"enabled": False, "error": "Failed to get stats"}

    async def health_check(self) -> dict[str, Any]:
        """Check cache health.

        Returns:
            Health status dictionary
        """
        if not self.enabled:
            return {"healthy": False, "reason": "Cache disabled"}

        try:
            if self.redis_client:
                # Redis backend
                self.redis_client.ping()
                return {"healthy": True, "backend": "redis"}
            else:
                # In-memory fallback
                return {"healthy": True, "backend": "memory"}
        except Exception as e:
            return {"healthy": False, "reason": str(e)}


# Global cache instance
_llm_cache: LLMCache | None = None


def get_llm_cache() -> LLMCache:
    """Get the global LLM cache instance.

    Returns:
        LLMCache: The global cache instance
    """
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = LLMCache()
    return _llm_cache


async def cache_llm_request(
    request_data: dict[str, Any],
    response_data: dict[str, Any],
    ttl: int | None = None,
) -> None:
    """Cache an LLM request/response.

    Args:
        request_data: The request data
        response_data: The response data to cache
        ttl: Time to live in seconds
    """
    cache = get_llm_cache()
    await cache.set(request_data, response_data, ttl)


async def get_cached_llm_response(request_data: dict[str, Any]) -> dict[str, Any] | None:
    """Get cached LLM response.

    Args:
        request_data: The request data to look up

    Returns:
        Cached response or None if not found
    """
    cache = get_llm_cache()
    return await cache.get(request_data)


__all__ = [
    "LLMCache",
    "get_llm_cache",
    "cache_llm_request",
    "get_cached_llm_response",
]
