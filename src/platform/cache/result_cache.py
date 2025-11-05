"""Result Caching System for Expensive Operations.

This module provides a comprehensive caching system for tool results,
enabling performance optimization through intelligent result caching.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import wraps
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable

@dataclass
class CacheEntry:
    """A cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime | None = None
    access_count: int = 0
    last_accessed: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def touch(self):
        """Update access information."""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {'key': self.key, 'value': self.value, 'created_at': self.created_at.isoformat(), 'expires_at': self.expires_at.isoformat() if self.expires_at else None, 'access_count': self.access_count, 'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None, 'metadata': self.metadata}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheEntry:
        """Create from dictionary."""
        return cls(key=data['key'], value=data['value'], created_at=datetime.fromisoformat(data['created_at']), expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None, access_count=data.get('access_count', 0), last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None, metadata=data.get('metadata', {}))

class ResultCache:
    """Intelligent result cache with TTL, LRU eviction, and metadata tracking."""

    def __init__(self, max_size: int=1000, default_ttl: int=3600, cleanup_interval: int=300, enable_metrics: bool=True):
        """Initialize the result cache."""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self.enable_metrics = enable_metrics
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []
        self._last_cleanup = time.time()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expired_cleanups = 0

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a cache key from function name and arguments."""
        key_data = {'func': func_name, 'args': args, 'kwargs': sorted(kwargs.items()) if kwargs else {}}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    def get(self, key: str) -> Any | None:
        """Get a value from the cache."""
        if key not in self._cache:
            self._misses += 1
            return None
        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self._expired_cleanups += 1
            self._misses += 1
            return None
        entry.touch()
        self._hits += 1
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        return entry.value

    def set(self, key: str, value: Any, ttl: int | None=None, metadata: dict[str, Any] | None=None) -> None:
        """Set a value in the cache."""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        entry = CacheEntry(key=key, value=value, created_at=datetime.now(timezone.utc), expires_at=expires_at, metadata=metadata or {})
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()
        self._cache[key] = entry
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        self._cleanup_if_needed()

    def _evict_lru(self):
        """Evict the least recently used entry."""
        if not self._access_order:
            return
        lru_key = self._access_order[0]
        if lru_key in self._cache:
            del self._cache[lru_key]
            self._access_order.remove(lru_key)
            self._evictions += 1

    def _cleanup_if_needed(self):
        """Clean up expired entries if needed."""
        current_time = time.time()
        if current_time - self._last_cleanup < self.cleanup_interval:
            return
        self._last_cleanup = current_time
        self._cleanup_expired()

    def _cleanup_expired(self):
        """Remove expired entries."""
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
        for key in expired_keys:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self._expired_cleanups += 1

    def invalidate(self, key: str) -> bool:
        """Invalidate a cache entry."""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate entries matching a pattern."""
        invalidated = 0
        keys_to_remove = [key for key in self._cache if pattern in key]
        for key in keys_to_remove:
            if self.invalidate(key):
                invalidated += 1
        return invalidated

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expired_cleanups = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests * 100 if total_requests > 0 else 0
        return {'size': len(self._cache), 'max_size': self.max_size, 'hits': self._hits, 'misses': self._misses, 'hit_rate': hit_rate, 'evictions': self._evictions, 'expired_cleanups': self._expired_cleanups, 'utilization': len(self._cache) / self.max_size * 100}

    def get_entries(self) -> list[dict[str, Any]]:
        """Get all cache entries as dictionaries."""
        return [entry.to_dict() for entry in self._cache.values()]

    def export_cache(self) -> dict[str, Any]:
        """Export cache data for persistence."""
        return {'entries': self.get_entries(), 'stats': self.get_stats(), 'exported_at': datetime.now(timezone.utc).isoformat()}
_global_cache = ResultCache()

def get_result_cache() -> ResultCache:
    """Get the global result cache instance."""
    return _global_cache

def cache_result(ttl: int | None=None, key_prefix: str='', metadata: dict[str, Any] | None=None):
    """Decorator for caching function results."""

    def decorator(func: Callable) -> Callable:

        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_result_cache()
            func_name = f'{key_prefix}{func.__name__}' if key_prefix else func.__name__
            cache_key = cache._generate_key(func_name, args, kwargs)
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            result = func(*args, **kwargs)
            if (isinstance(result, StepResult) and result.success) or not isinstance(result, StepResult):
                cache.set(cache_key, result, ttl=ttl, metadata=metadata)
            return result
        return wrapper
    return decorator

def cache_tool_result(ttl: int | None=None, key_prefix: str='', metadata: dict[str, Any] | None=None):
    """Decorator specifically for caching tool results."""

    def decorator(func: Callable) -> Callable:

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            cache = get_result_cache()
            tool_name = getattr(self, 'name', self.__class__.__name__)
            func_name = f'{key_prefix}{tool_name}_{func.__name__}' if key_prefix else f'{tool_name}_{func.__name__}'
            cache_key = cache._generate_key(func_name, args, kwargs)
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            result = func(self, *args, **kwargs)
            if isinstance(result, StepResult) and result.success:
                cache.set(cache_key, result, ttl=ttl, metadata=metadata)
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate cache entries matching a pattern."""
    cache = get_result_cache()
    return cache.invalidate_pattern(pattern)

def clear_result_cache():
    """Clear all cached results."""
    cache = get_result_cache()
    cache.clear()

def get_cache_stats() -> dict[str, Any]:
    """Get cache statistics."""
    cache = get_result_cache()
    return cache.get_stats()
