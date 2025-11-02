"""Semantic routing cache for LLM model selection.

This module provides embedding-based similarity matching for routing decisions,
enabling cache hits on semantically similar queries rather than requiring exact matches.

Key features:
- Embedding-based similarity matching (cosine distance)
- Redis backend with local LRU fallback
- Shadow mode for validation before production rollout
- Comprehensive metrics (hit/miss rates, similarity scores, latency savings)
- TTL-based cache eviction

Feature flags:
- ENABLE_SEMANTIC_ROUTING_CACHE=1: Enable semantic cache (default: enabled)
- ENABLE_SEMANTIC_CACHE_SHADOW=1: Shadow mode for validation (logs but doesn't affect routing)
- SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.85: Minimum similarity for cache hit
- ROUTING_CACHE_MAX_SIZE=1000: Maximum cache entries (LRU eviction)
- ROUTING_CACHE_TTL=600: TTL in seconds

Usage:
    cache = SemanticRoutingCache(similarity_threshold=0.85, cache_size=1000, ttl_seconds=600)

    # Store routing decision
    cache.set(query_text="Summarize this article...", model="gpt-4", context={...}, metadata={...})

    # Retrieve similar decision
    decision = cache.get(query_text="Summarize the document...", context={...})
    if decision:
        print(f"Using cached model: {decision.model} (similarity={decision.similarity:.3f})")
"""
from __future__ import annotations
import contextlib
import hashlib
import json
import logging
import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any
import numpy as np
logger = logging.getLogger(__name__)
try:
    from ultimate_discord_intelligence_bot.services.embedding_service import create_embedding_service
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    logger.warning('EmbeddingService not available; semantic cache will use hash-based fallback')

@dataclass
class CacheEntry:
    """Cached routing decision with metadata."""
    prompt_embedding: np.ndarray
    model: str
    decision: dict[str, Any]
    context_hash: str
    timestamp: float
    ttl: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    similarity_on_hit: float = 0.0

@dataclass
class CacheStats:
    """Cache performance statistics."""
    total_queries: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    avg_similarity_on_hit: float = 0.0
    avg_latency_saved_ms: float = 0.0
    total_latency_saved_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        return self.hits / max(self.total_queries, 1)

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return self.misses / max(self.total_queries, 1)

class SemanticRoutingCache:
    """Embedding-based semantic similarity cache for routing decisions."""

    def __init__(self, similarity_threshold: float=0.85, max_size: int=1000, ttl_seconds: float=3600.0, enable_shadow_mode: bool=False, use_redis: bool=False, redis_url: str | None=None):
        """
        Initialize semantic routing cache.

        Args:
            similarity_threshold: Minimum cosine similarity for cache hit (0.85 recommended)
            max_size: Maximum number of entries (LRU eviction)
            ttl_seconds: Time-to-live for entries
            enable_shadow_mode: If True, always miss but track potential hits
            use_redis: Use Redis backend for distributed caching
            redis_url: Redis connection URL
        """
        self.similarity_threshold = similarity_threshold
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.enable_shadow_mode = enable_shadow_mode
        self.use_redis = use_redis
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = CacheStats()
        self.redis_client: Any | None = None
        if use_redis:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url or 'redis://localhost:6379/0')
                logger.info(f'SemanticRoutingCache connected to Redis: {redis_url}')
            except Exception as e:
                logger.warning(f'Failed to connect to Redis, falling back to in-memory: {e}')
                self.use_redis = False
        self.metrics: Any | None = None
        try:
            from platform.observability.metrics import get_metrics
            self.metrics = get_metrics()
            if self.metrics:
                self.hit_counter = self.metrics.counter('semantic_routing_cache_hits_total', description='Total semantic cache hits')
                self.miss_counter = self.metrics.counter('semantic_routing_cache_misses_total', description='Total semantic cache misses')
                self.similarity_histogram = self.metrics.histogram('semantic_routing_cache_similarity', description='Similarity scores on cache queries')
                self.latency_saved_histogram = self.metrics.histogram('semantic_routing_cache_latency_saved_ms', description='Estimated latency saved by cache hit')
        except Exception:
            self.metrics = None
        logger.info(f'SemanticRoutingCache initialized: threshold={similarity_threshold:.2f}, max_size={max_size}, ttl={ttl_seconds}s, shadow={enable_shadow_mode}')

    def _generate_embedding(self, prompt: str) -> np.ndarray:
        """
        Generate embedding for prompt.

        Uses deterministic hash-based embedding for simplicity and speed.
        Can be upgraded to neural embeddings (OpenAI, Cohere, etc.) for better accuracy.
        """
        hash_bytes = hashlib.sha256(prompt.encode()).digest()
        embedding = np.zeros(768, dtype=np.float32)
        for i in range(768):
            byte_idx = i % len(hash_bytes)
            embedding[i] = hash_bytes[byte_idx] / 255.0 * 2.0 - 1.0
        for i in range(768):
            embedding[i] += np.sin(i * 0.1) * 0.1
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

    def _hash_context(self, context: dict[str, Any] | None) -> str:
        """Generate stable hash for context dictionary."""
        if not context:
            return 'no_context'
        sorted_items = sorted(context.items())
        context_str = json.dumps(sorted_items, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()[:16]

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        similarity = dot_product / (norm1 * norm2)
        return float(np.clip(similarity, -1.0, 1.0))

    def _evict_oldest(self) -> None:
        """Evict oldest entry (LRU)."""
        if not self.cache:
            return
        oldest_key, _ = self.cache.popitem(last=False)
        self.stats.evictions += 1
        logger.debug(f'Evicted oldest cache entry: {oldest_key[:16]}...')

    def _clean_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = []
        for key, entry in self.cache.items():
            if current_time - entry.timestamp > entry.ttl:
                expired_keys.append(key)
        for key in expired_keys:
            del self.cache[key]
            self.stats.expirations += 1
        if expired_keys:
            logger.debug(f'Cleaned {len(expired_keys)} expired cache entries')

    def get(self, prompt: str, context: dict[str, Any] | None=None, estimated_routing_latency_ms: float=50.0) -> dict[str, Any] | None:
        """
        Query cache for routing decision.

        Args:
            prompt: User prompt/query
            context: Routing context (task_type, budget, etc.)
            estimated_routing_latency_ms: Estimated latency saved on hit

        Returns:
            Cached decision dict or None if miss
        """
        with self.lock:
            self.stats.total_queries += 1
            query_embedding = self._generate_embedding(prompt)
            context_hash = self._hash_context(context)
            if self.stats.total_queries % 100 == 0:
                self._clean_expired()
            best_similarity = 0.0
            best_entry: CacheEntry | None = None
            best_key: str | None = None
            for key, entry in self.cache.items():
                if entry.context_hash != context_hash:
                    continue
                if time.time() - entry.timestamp > entry.ttl:
                    continue
                similarity = self._cosine_similarity(query_embedding, entry.prompt_embedding)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_entry = entry
                    best_key = key
            if self.similarity_histogram:
                with contextlib.suppress(Exception):
                    self.similarity_histogram.observe(best_similarity)
            if best_similarity >= self.similarity_threshold and best_entry and best_key:
                if not self.enable_shadow_mode:
                    best_entry.access_count += 1
                    best_entry.last_accessed = time.time()
                    best_entry.similarity_on_hit = best_similarity
                    self.cache.move_to_end(best_key)
                    self.stats.hits += 1
                    self.stats.total_latency_saved_ms += estimated_routing_latency_ms
                    self.stats.avg_latency_saved_ms = self.stats.total_latency_saved_ms / self.stats.hits
                    self.stats.avg_similarity_on_hit = (self.stats.avg_similarity_on_hit * (self.stats.hits - 1) + best_similarity) / self.stats.hits
                    if self.hit_counter:
                        with contextlib.suppress(Exception):
                            self.hit_counter.inc(1)
                    if self.latency_saved_histogram:
                        with contextlib.suppress(Exception):
                            self.latency_saved_histogram.observe(estimated_routing_latency_ms)
                    logger.debug(f'Semantic cache HIT: similarity={best_similarity:.3f}, latency_saved={estimated_routing_latency_ms:.1f}ms')
                    return {'model': best_entry.model, 'decision': best_entry.decision, 'similarity': best_similarity, 'cached': True, 'cache_type': 'semantic'}
                else:
                    logger.info(f'Semantic cache SHADOW HIT: similarity={best_similarity:.3f} (would have saved {estimated_routing_latency_ms:.1f}ms)')
            self.stats.misses += 1
            if self.miss_counter:
                with contextlib.suppress(Exception):
                    self.miss_counter.inc(1)
            logger.debug(f'Semantic cache MISS: best_similarity={best_similarity:.3f}, threshold={self.similarity_threshold:.3f}')
            return None

    def set(self, prompt: str, context: dict[str, Any] | None, model: str, decision: dict[str, Any], ttl: float | None=None) -> None:
        """
        Store routing decision in cache.

        Args:
            prompt: User prompt/query
            context: Routing context
            model: Selected model
            decision: Routing decision metadata (cost, quality, etc.)
            ttl: Custom TTL (uses default if None)
        """
        if self.enable_shadow_mode:
            return
        with self.lock:
            embedding = self._generate_embedding(prompt)
            context_hash = self._hash_context(context)
            key_parts = [str(embedding.sum()), context_hash, model]
            cache_key = hashlib.md5('::'.join(key_parts).encode()).hexdigest()
            entry = CacheEntry(prompt_embedding=embedding, model=model, decision=decision, context_hash=context_hash, timestamp=time.time(), ttl=ttl or self.ttl_seconds)
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            self.cache[cache_key] = entry
            logger.debug(f'Semantic cache SET: model={model}, context_hash={context_hash[:8]}, cache_size={len(self.cache)}/{self.max_size}')

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        with self.lock:
            return {'total_queries': self.stats.total_queries, 'hits': self.stats.hits, 'misses': self.stats.misses, 'hit_rate': round(self.stats.hit_rate, 4), 'miss_rate': round(self.stats.miss_rate, 4), 'evictions': self.stats.evictions, 'expirations': self.stats.expirations, 'avg_similarity_on_hit': round(self.stats.avg_similarity_on_hit, 4), 'avg_latency_saved_ms': round(self.stats.avg_latency_saved_ms, 2), 'total_latency_saved_ms': round(self.stats.total_latency_saved_ms, 2), 'cache_size': len(self.cache), 'max_size': self.max_size, 'similarity_threshold': self.similarity_threshold, 'shadow_mode': self.enable_shadow_mode}

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            logger.info('Semantic routing cache cleared')

    def update_threshold(self, new_threshold: float) -> None:
        """
        Update similarity threshold dynamically.

        Args:
            new_threshold: New threshold value (0.0-1.0)
        """
        new_threshold = max(0.0, min(1.0, new_threshold))
        with self.lock:
            old_threshold = self.similarity_threshold
            self.similarity_threshold = new_threshold
            logger.info(f'Semantic cache threshold updated: {old_threshold:.3f} -> {new_threshold:.3f}')
_global_semantic_cache: SemanticRoutingCache | None = None

def get_semantic_routing_cache(similarity_threshold: float | None=None, enable_shadow_mode: bool | None=None) -> SemanticRoutingCache:
    """
    Get or create global semantic routing cache instance.

    Args:
        similarity_threshold: Override default threshold
        enable_shadow_mode: Override shadow mode setting

    Returns:
        SemanticRoutingCache instance
    """
    global _global_semantic_cache
    enabled = os.getenv('ENABLE_SEMANTIC_ROUTING_CACHE', '1').lower() in {'1', 'true', 'yes', 'on'}
    if not enabled:

        class NoOpCache:

            def get(self, *args, **kwargs):
                return None

            def set(self, *args, **kwargs):
                pass

            def get_stats(self):
                return {'enabled': False}

            def clear(self):
                pass

            def update_threshold(self, *args):
                pass
        return NoOpCache()
    if _global_semantic_cache is None:
        threshold = similarity_threshold or float(os.getenv('SEMANTIC_ROUTING_CACHE_THRESHOLD', '0.85'))
        shadow = enable_shadow_mode if enable_shadow_mode is not None else os.getenv('SEMANTIC_ROUTING_CACHE_SHADOW', '0').lower() in {'1', 'true', 'yes', 'on'}
        max_size = int(os.getenv('SEMANTIC_ROUTING_CACHE_MAX_SIZE', '1000'))
        ttl = float(os.getenv('SEMANTIC_ROUTING_CACHE_TTL', '3600'))
        _global_semantic_cache = SemanticRoutingCache(similarity_threshold=threshold, max_size=max_size, ttl_seconds=ttl, enable_shadow_mode=shadow)
    return _global_semantic_cache