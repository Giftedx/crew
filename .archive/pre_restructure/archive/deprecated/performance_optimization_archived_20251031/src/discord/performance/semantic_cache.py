"""
Enhanced semantic caching system for Discord message processing.

This module implements intelligent semantic caching to reduce redundant
processing and improve response times through similarity-based caching.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import time
import typing
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from performance_optimization.src.ultimate_discord_intelligence_bot.step_result import StepResult


@dataclass
class CacheEntry:
    """Represents a cached entry with semantic information."""

    key: str
    content: str
    embedding: np.ndarray
    result: Any
    timestamp: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def age_seconds(self) -> float:
        """Get the age of this cache entry in seconds."""
        return time.time() - self.timestamp

    @property
    def access_frequency(self) -> float:
        """Calculate access frequency (accesses per hour)."""
        age_hours = self.age_seconds / 3600.0
        return self.access_count / max(age_hours, 0.1)


@dataclass
class SemanticCacheConfig:
    """Configuration for semantic caching."""

    max_entries: int = 1000
    max_age_seconds: float = 3600.0  # 1 hour
    similarity_threshold: float = 0.85
    embedding_dimension: int = 384
    enable_lru: bool = True
    enable_frequency_tracking: bool = True
    cache_ttl_seconds: float = 1800.0  # 30 minutes
    cleanup_interval_seconds: float = 300.0  # 5 minutes


class SemanticCache:
    """
    Enhanced semantic cache for Discord message processing.

    This cache stores processing results based on semantic similarity
    of message content, enabling efficient retrieval of similar responses.
    """

    def __init__(self, config: SemanticCacheConfig, embedding_function: typing.Callable[[str], np.ndarray]):
        self.config = config
        self.embedding_function = embedding_function

        # Cache storage
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._embedding_index: dict[str, np.ndarray] = {}

        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "total_queries": 0,
            "cache_size": 0,
            "avg_similarity_score": 0.0,
            "evictions": 0,
        }

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Start background cleanup
        self._cleanup_task = asyncio.create_task(self._background_cleanup())

    async def get(self, content: str, similarity_threshold: float | None = None) -> StepResult:
        """
        Retrieve a cached result based on semantic similarity.

        Args:
            content: Message content to search for
            similarity_threshold: Override default similarity threshold

        Returns:
            StepResult with cached data if found, None if miss
        """
        try:
            threshold = similarity_threshold or self.config.similarity_threshold

            async with self._lock:
                self._stats["total_queries"] += 1

                # Generate embedding for query
                query_embedding = await self._get_embedding(content)

                # Find best match
                best_match = await self._find_best_match(query_embedding, threshold)

                if best_match:
                    # Update access statistics
                    best_match.access_count += 1
                    best_match.last_accessed = time.time()

                    # Move to end (most recently used)
                    if self.config.enable_lru:
                        self._cache.move_to_end(best_match.key)

                    self._stats["hits"] += 1

                    return StepResult.ok(
                        data={
                            "result": best_match.result,
                            "similarity_score": best_match.metadata.get("similarity_score", 0.0),
                            "cache_key": best_match.key,
                            "age_seconds": best_match.age_seconds,
                            "access_count": best_match.access_count,
                        }
                    )
                else:
                    self._stats["misses"] += 1
                    return StepResult.fail("Cache miss", status="cache_miss")

        except Exception as e:
            return StepResult.fail(f"Cache retrieval failed: {e!s}")

    async def put(self, content: str, result: Any, metadata: dict[str, Any] | None = None) -> StepResult:
        """
        Store a result in the semantic cache.

        Args:
            content: Message content
            result: Processing result to cache
            metadata: Additional metadata

        Returns:
            StepResult indicating success/failure
        """
        try:
            async with self._lock:
                # Generate cache key
                cache_key = self._generate_cache_key(content)

                # Generate embedding
                embedding = await self._get_embedding(content)

                # Create cache entry
                entry = CacheEntry(
                    key=cache_key,
                    content=content,
                    embedding=embedding,
                    result=result,
                    timestamp=time.time(),
                    metadata=metadata or {},
                )

                # Store in cache
                self._cache[cache_key] = entry
                self._embedding_index[cache_key] = embedding

                # Move to end (most recently used)
                if self.config.enable_lru:
                    self._cache.move_to_end(cache_key)

                # Evict if necessary
                await self._evict_if_necessary()

                self._stats["cache_size"] = len(self._cache)

                return StepResult.ok(data={"cache_key": cache_key, "action": "cached", "cache_size": len(self._cache)})

        except Exception as e:
            return StepResult.fail(f"Cache storage failed: {e!s}")

    async def _get_embedding(self, content: str) -> np.ndarray:
        """Get embedding for content, with caching."""
        # Simple content-based cache key for embeddings
        embedding_key = hashlib.md5(content.encode()).hexdigest()

        if embedding_key in self._embedding_index:
            return self._embedding_index[embedding_key]

        # Generate new embedding
        if asyncio.iscoroutinefunction(self.embedding_function):
            embedding = await self.embedding_function(content)
        else:
            embedding = self.embedding_function(content)

        # Ensure embedding is numpy array
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding)

        # Normalize embedding
        embedding = embedding / np.linalg.norm(embedding)

        return embedding

    async def _find_best_match(self, query_embedding: np.ndarray, threshold: float) -> CacheEntry | None:
        """Find the best matching cache entry."""
        best_entry = None
        best_similarity = 0.0

        for entry in self._cache.values():
            # Skip expired entries
            if entry.age_seconds > self.config.max_age_seconds:
                continue

            # Calculate cosine similarity
            similarity = np.dot(query_embedding, entry.embedding)

            if similarity >= threshold and similarity > best_similarity:
                best_similarity = similarity
                best_entry = entry

        if best_entry:
            # Update similarity score in metadata
            best_entry.metadata["similarity_score"] = best_similarity
            self._stats["avg_similarity_score"] = (
                self._stats["avg_similarity_score"] * (self._stats["hits"] - 1) + best_similarity
            ) / self._stats["hits"]

        return best_entry

    def _generate_cache_key(self, content: str) -> str:
        """Generate a cache key for content."""
        # Use content hash for deterministic keys
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        timestamp = int(time.time())
        return f"semantic_{content_hash}_{timestamp}"

    async def _evict_if_necessary(self):
        """Evict entries if cache is full."""
        while len(self._cache) > self.config.max_entries:
            # Remove least recently used entry
            if self.config.enable_lru:
                key, _ = self._cache.popitem(last=False)
            else:
                # Remove oldest entry
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
                self._cache.pop(oldest_key)
                key = oldest_key

            # Remove from embedding index
            self._embedding_index.pop(key, None)

            self._stats["evictions"] += 1

    async def _background_cleanup(self):
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_seconds)

                async with self._lock:
                    expired_keys = []
                    time.time()

                    for key, entry in self._cache.items():
                        if entry.age_seconds > self.config.max_age_seconds:
                            expired_keys.append(key)

                    # Remove expired entries
                    for key in expired_keys:
                        self._cache.pop(key, None)
                        self._embedding_index.pop(key, None)

                    if expired_keys:
                        self._stats["cache_size"] = len(self._cache)

            except Exception as e:
                # Log error but continue
                print(f"Cache cleanup error: {e!s}")

    async def get_stats(self) -> StepResult:
        """Get cache statistics."""
        async with self._lock:
            hit_rate = self._stats["hits"] / max(self._stats["total_queries"], 1) * 100

            stats = self._stats.copy()
            stats.update(
                {
                    "hit_rate_percent": hit_rate,
                    "cache_size": len(self._cache),
                    "embedding_index_size": len(self._embedding_index),
                }
            )

            return StepResult.ok(data=stats)

    async def clear(self) -> StepResult:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._embedding_index.clear()
            self._stats["cache_size"] = 0

            return StepResult.ok(data={"action": "cache_cleared"})

    async def get_cache_info(self) -> StepResult:
        """Get detailed cache information."""
        async with self._lock:
            entries_info = []

            for entry in self._cache.values():
                entries_info.append(
                    {
                        "key": entry.key,
                        "content_preview": entry.content[:50] + "..." if len(entry.content) > 50 else entry.content,
                        "age_seconds": entry.age_seconds,
                        "access_count": entry.access_count,
                        "access_frequency": entry.access_frequency,
                        "metadata": entry.metadata,
                    }
                )

            return StepResult.ok(
                data={
                    "total_entries": len(self._cache),
                    "entries": entries_info,
                    "config": {
                        "max_entries": self.config.max_entries,
                        "max_age_seconds": self.config.max_age_seconds,
                        "similarity_threshold": self.config.similarity_threshold,
                        "embedding_dimension": self.config.embedding_dimension,
                    },
                }
            )

    async def shutdown(self) -> StepResult:
        """Gracefully shutdown the cache."""
        # Cancel background task
        self._cleanup_task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await self._cleanup_task

        # Clear cache
        await self.clear()

        return StepResult.ok(data={"action": "cache_shutdown_complete"})


class AdaptiveSemanticCache(SemanticCache):
    """
    Adaptive semantic cache that learns optimal parameters.

    This cache automatically adjusts similarity thresholds and other
    parameters based on hit rates and performance metrics.
    """

    def __init__(self, config: SemanticCacheConfig, embedding_function: typing.Callable[[str], np.ndarray]):
        super().__init__(config, embedding_function)

        # Adaptive parameters
        self._adaptive_threshold = config.similarity_threshold
        self._threshold_adjustment_rate = 0.01
        self._min_threshold = 0.7
        self._max_threshold = 0.95

        # Performance tracking
        self._recent_hit_rates: list[float] = []
        self._recent_similarities: list[float] = []
        self._adaptation_window = 100  # Number of queries to consider for adaptation

    async def get(self, content: str, similarity_threshold: float | None = None) -> StepResult:
        """Enhanced get with adaptive threshold."""
        # Use adaptive threshold if not specified
        threshold = similarity_threshold or self._adaptive_threshold

        result = await super().get(content, threshold)

        # Track performance for adaptation
        if result.success:
            similarity = result.data.get("similarity_score", 0.0)
            self._recent_similarities.append(similarity)

            # Adapt threshold based on recent performance
            await self._adapt_threshold()

        return result

    async def _adapt_threshold(self):
        """Adapt similarity threshold based on recent performance."""
        if len(self._recent_similarities) < 10:
            return

        # Calculate recent hit rate
        recent_queries = min(len(self._recent_similarities), self._adaptation_window)
        recent_hits = sum(1 for s in self._recent_similarities[-recent_queries:] if s >= self._adaptive_threshold)
        recent_hit_rate = recent_hits / recent_queries

        # Adjust threshold based on hit rate
        if recent_hit_rate > 0.8:  # High hit rate, can be more selective
            self._adaptive_threshold = min(
                self._adaptive_threshold + self._threshold_adjustment_rate, self._max_threshold
            )
        elif recent_hit_rate < 0.3:  # Low hit rate, be more permissive
            self._adaptive_threshold = max(
                self._adaptive_threshold - self._threshold_adjustment_rate, self._min_threshold
            )

        # Keep only recent data
        if len(self._recent_similarities) > self._adaptation_window:
            self._recent_similarities = self._recent_similarities[-self._adaptation_window :]

    async def get_stats(self) -> StepResult:
        """Get enhanced stats including adaptive parameters."""
        base_stats = await super().get_stats()

        if base_stats.success:
            stats = base_stats.data
            stats.update(
                {
                    "adaptive_threshold": self._adaptive_threshold,
                    "threshold_range": [self._min_threshold, self._max_threshold],
                    "recent_similarities_count": len(self._recent_similarities),
                }
            )

            return StepResult.ok(data=stats)

        return base_stats


# Factory function for creating semantic caches
def create_semantic_cache(
    config: SemanticCacheConfig,
    embedding_function: typing.Callable[[str], np.ndarray],
    adaptive: bool = True,
) -> SemanticCache:
    """Create a semantic cache with the specified configuration."""
    if adaptive:
        return AdaptiveSemanticCache(config, embedding_function)
    else:
        return SemanticCache(config, embedding_function)
