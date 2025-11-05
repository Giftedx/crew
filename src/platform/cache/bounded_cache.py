"""Bounded cache implementation with LRU eviction policy.

Provides a simple thread-safe in‑memory LRU cache with TTL and lightweight
statistics. Includes defensive handling for ``ttl=None`` (falls back to
``DEFAULT_TTL``) to avoid TypeErrors when settings hydration is incomplete.
"""

from __future__ import annotations

import logging
import sys
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock
from typing import Any

from ..secure_config import get_config


logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_MAX_SIZE = 1000
DEFAULT_TTL = 3600  # 1 hour
MAX_REASONABLE_CACHE_SIZE = 10000


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired_removals: int = 0

    @property
    def hit_ratio(self) -> float:  # pragma: no cover - trivial
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def reset(self) -> None:  # pragma: no cover - not used in tests presently
        self.hits = self.misses = self.evictions = self.expired_removals = 0


class BoundedLRUCache:
    """Thread‑safe LRU cache with TTL and bounded size."""

    def __init__(self, max_size: int | None = None, ttl: int | None = DEFAULT_TTL, name: str = "cache") -> None:
        config = get_config()
        if max_size is None:
            configured_size = getattr(config, f"{name}_max_size", DEFAULT_MAX_SIZE)
            max_size = min(configured_size, MAX_REASONABLE_CACHE_SIZE)

        self.max_size = max_size
        self.ttl = DEFAULT_TTL if ttl is None else ttl
        self.name = name
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = RLock()
        self.stats = CacheStats()
        logger.info("Initialized %s cache (max_size=%s, ttl=%ss)", name, self.max_size, self.ttl)

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                self.stats.misses += 1
                return None
            value, exp = item
            if exp < time.time():
                del self._cache[key]
                self.stats.expired_removals += 1
                self.stats.misses += 1
                return None
            self._cache.move_to_end(key)
            self.stats.hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            expiration = time.time() + self.ttl
            self._cache[key] = (value, expiration)
            self._cache.move_to_end(key)
            while self.max_size is not None and len(self._cache) > self.max_size:
                oldest, _ = self._cache.popitem(last=False)
                self.stats.evictions += 1
                logger.debug("%s cache evicted key: %s", self.name, oldest)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            removed = len(self._cache)
            self._cache.clear()
            logger.info("Cleared %s cache (%d entries removed)", self.name, removed)

    def cleanup_expired(self) -> int:
        with self._lock:
            now = time.time()
            expired = [k for k, (_, exp) in self._cache.items() if exp < now]
            for k in expired:
                del self._cache[k]
            self.stats.expired_removals += len(expired)
            if expired:
                logger.debug("%s cache cleaned %d expired entries", self.name, len(expired))
            return len(expired)

    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    def is_full(self) -> bool:
        with self._lock:
            return self.max_size is not None and len(self._cache) >= self.max_size

    def get_stats(self) -> dict[str, Any]:  # pragma: no cover - simple aggregation
        with self._lock:
            return {
                "name": self.name,
                "current_size": len(self._cache),
                "max_size": self.max_size,
                "hit_ratio": self.stats.hit_ratio,
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "evictions": self.stats.evictions,
                "expired_removals": self.stats.expired_removals,
                "ttl_seconds": self.ttl,
                "is_full": self.is_full(),
            }

    def get_memory_info(self) -> dict[str, Any]:  # pragma: no cover - diagnostics only
        with self._lock:
            key_bytes = sum(sys.getsizeof(k) for k in self._cache)
            val_bytes = sum(sys.getsizeof(v) for v, _ in self._cache.values())
            overhead = sys.getsizeof(self._cache)
            total = key_bytes + val_bytes + overhead
            return {
                "total_bytes": total,
                "key_bytes": key_bytes,
                "value_bytes": val_bytes,
                "overhead_bytes": overhead,
                "avg_bytes_per_entry": total / len(self._cache) if self._cache else 0,
            }


_cache_instances: dict[str, BoundedLRUCache] = {}


def get_bounded_cache(name: str, max_size: int | None = None, ttl: int | None = DEFAULT_TTL) -> BoundedLRUCache:
    if name not in _cache_instances:
        _cache_instances[name] = BoundedLRUCache(max_size=max_size, ttl=ttl, name=name)
    return _cache_instances[name]


def get_cache_stats() -> dict[str, Any]:  # pragma: no cover
    return {n: c.get_stats() for n, c in _cache_instances.items()}


def cleanup_all_caches() -> dict[str, int]:  # pragma: no cover
    removed: dict[str, int] = {}
    for n, c in _cache_instances.items():
        count = c.cleanup_expired()
        if count:
            removed[n] = count
    return removed


def create_llm_cache(ttl: int = DEFAULT_TTL, max_size: int = DEFAULT_MAX_SIZE) -> BoundedLRUCache:  # pragma: no cover
    return get_bounded_cache("llm", max_size=max_size, ttl=ttl)


def create_retrieval_cache(
    ttl: int = DEFAULT_TTL, max_size: int = DEFAULT_MAX_SIZE
) -> BoundedLRUCache:  # pragma: no cover
    return get_bounded_cache("retrieval", max_size=max_size, ttl=ttl)
