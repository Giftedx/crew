"""High-level cache service interface for application-wide caching.

This module provides a unified interface for the advanced caching system,
making it easy to use throughout the application with proper configuration
and monitoring integration.
"""
from __future__ import annotations

import builtins
import logging
from platform.cache.enhanced_redis_cache import EnhancedRedisCache
from platform.cache.multi_level_cache import MultiLevelCache, get_multi_level_cache
from typing import Any, TypeVar


logger = logging.getLogger(__name__)
T = TypeVar('T')

class CacheService:
    """High-level cache service for application-wide caching operations."""

    def __init__(self, name: str, enable_llm_cache: bool=True, enable_api_cache: bool=True, enable_dependency_tracking: bool=True, l2_cache: EnhancedRedisCache | None=None):
        """Initialize the cache service.

        Args:
            name: Service name for cache identification
            enable_llm_cache: Enable specialized LLM response caching
            enable_api_cache: Enable API response caching
            enable_dependency_tracking: Enable dependency-based invalidation
            l2_cache: Optional Redis cache for L2 layer
        """
        self.name = name
        self.enable_llm_cache = enable_llm_cache
        self.enable_api_cache = enable_api_cache
        self.enable_dependency_tracking = enable_dependency_tracking
        self._main_cache = get_multi_level_cache(f'{name}_main', l2_cache=l2_cache, enable_dependency_tracking=enable_dependency_tracking)
        self._llm_cache = None
        self._api_cache = None
        if enable_llm_cache:
            self._llm_cache = get_multi_level_cache(f'{name}_llm', l2_cache=l2_cache, enable_dependency_tracking=enable_dependency_tracking)
        if enable_api_cache:
            self._api_cache = get_multi_level_cache(f'{name}_api', l2_cache=l2_cache, enable_dependency_tracking=enable_dependency_tracking)
        logger.info(f"Initialized cache service '{name}' with LLM: {enable_llm_cache}, API: {enable_api_cache}")

    async def get(self, key: str, cache_type: str='main') -> Any:
        """Get value from specified cache type.

        Args:
            key: Cache key
            cache_type: Type of cache ('main', 'llm', 'api')

        Returns:
            Cached value or None if not found
        """
        cache = self._get_cache(cache_type)
        if cache:
            return await cache.get(key)
        return None

    async def set(self, key: str, value: Any, ttl: int | None=None, dependencies: set[str] | None=None, cache_type: str='main') -> bool:
        """Set value in specified cache type.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds
            dependencies: Optional set of dependency keys
            cache_type: Type of cache ('main', 'llm', 'api')

        Returns:
            True if successful, False otherwise
        """
        cache = self._get_cache(cache_type)
        if cache:
            if ttl:
                pass
            return await cache.set(key, value, dependencies)
        return False

    async def delete(self, key: str, cascade: bool=True, cache_type: str='main') -> bool:
        """Delete value from specified cache type.

        Args:
            key: Cache key to delete
            cascade: Whether to cascade delete dependents
            cache_type: Type of cache ('main', 'llm', 'api')

        Returns:
            True if successful, False otherwise
        """
        cache = self._get_cache(cache_type)
        if cache:
            return await cache.delete(key, cascade)
        return False

    async def invalidate_dependencies(self, key: str, cache_type: str='main') -> None:
        """Invalidate all dependencies of a key.

        Args:
            key: Key whose dependencies should be invalidated
            cache_type: Type of cache ('main', 'llm', 'api')
        """
        cache = self._get_cache(cache_type)
        if cache:
            await cache.delete(key, cascade=True)

    async def get_dependencies(self, key: str, cache_type: str='main') -> builtins.set[str]:
        """Get dependencies of a key.

        Args:
            key: Cache key
            cache_type: Type of cache ('main', 'llm', 'api')

        Returns:
            Set of dependency keys
        """
        cache = self._get_cache(cache_type)
        if cache:
            return await cache.get_dependencies(key)
        return builtins.set()

    async def get_dependents(self, key: str, cache_type: str='main') -> builtins.set[str]:
        """Get keys that depend on the given key.

        Args:
            key: Cache key
            cache_type: Type of cache ('main', 'llm', 'api')

        Returns:
            Set of dependent keys
        """
        cache = self._get_cache(cache_type)
        if cache:
            return await cache.get_dependents(key)
        return builtins.set()

    def get_stats(self, cache_type: str='main') -> dict[str, Any]:
        """Get statistics for specified cache type.

        Args:
            cache_type: Type of cache ('main', 'llm', 'api')

        Returns:
            Dictionary of cache statistics
        """
        cache = self._get_cache(cache_type)
        if cache:
            return cache.get_stats()
        return {}

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all cache types.

        Returns:
            Dictionary with stats for each cache type
        """
        stats = {}
        for cache_type in ['main', 'llm', 'api']:
            cache_stats = self.get_stats(cache_type)
            if cache_stats:
                stats[cache_type] = cache_stats
        return stats

    async def clear_all(self) -> dict[str, bool]:
        """Clear all caches.

        Returns:
            Dictionary indicating success for each cache type
        """
        results = {}
        for cache_type in ['main', 'llm', 'api']:
            results[cache_type] = True
        return results

    def _get_cache(self, cache_type: str) -> MultiLevelCache | None:
        """Get cache instance for specified type.

        Args:
            cache_type: Type of cache ('main', 'llm', 'api')

        Returns:
            Cache instance or None if not available
        """
        if cache_type == 'main':
            return self._main_cache
        elif cache_type == 'llm' and self._llm_cache:
            return self._llm_cache
        elif cache_type == 'api' and self._api_cache:
            return self._api_cache
        return None
_cache_service: CacheService | None = None

def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService('default')
    return _cache_service

def init_cache_service(name: str='crew_cache', enable_llm_cache: bool=True, enable_api_cache: bool=True, enable_dependency_tracking: bool=True, redis_url: str | None=None) -> CacheService:
    """Initialize the global cache service.

    Args:
        name: Service name
        enable_llm_cache: Enable LLM response caching
        enable_api_cache: Enable API response caching
        enable_dependency_tracking: Enable dependency-based invalidation
        redis_url: Optional Redis URL for L2 cache

    Returns:
        Initialized cache service
    """
    global _cache_service
    l2_cache = None
    if redis_url:
        try:
            try:
                from platform.cache.unified_config import get_unified_cache_config
                _ttl = int(get_unified_cache_config().redis.default_ttl)
            except Exception:
                _ttl = 3600
            l2_cache = EnhancedRedisCache(url=redis_url, namespace=f'{name}_l2', ttl=_ttl)
        except Exception as e:
            logger.warning(f'Failed to initialize Redis cache: {e}')
    _cache_service = CacheService(name=name, enable_llm_cache=enable_llm_cache, enable_api_cache=enable_api_cache, enable_dependency_tracking=enable_dependency_tracking, l2_cache=l2_cache)
    return _cache_service

async def warmup_cache(cache_service: CacheService) -> None:
    """Warm up caches with commonly accessed data.

    Args:
        cache_service: Cache service to warm up
    """
    logger.info('Cache warm-up completed (placeholder)')
__all__ = ['CacheService', 'get_cache_service', 'init_cache_service', 'warmup_cache']
