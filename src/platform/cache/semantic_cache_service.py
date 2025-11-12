"""Semantic caching service for tool results using embeddings-based similarity matching.

This module provides semantic caching capabilities that can reuse cached results
for similar tool inputs, significantly improving cache hit rates beyond exact matches.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from platform.cache.multi_level_cache import MultiLevelCache
from typing import Any

import numpy as np

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics


logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available, semantic caching disabled")


class SemanticCacheService:
    """Service for semantic caching using embeddings-based similarity matching."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.85,
        cache_ttl: int = 3600,
        max_cache_size: int = 10000,
        enable_cache: bool = True,
    ):
        """Initialize semantic cache service.

        Args:
            model_name: Sentence transformer model name
            similarity_threshold: Cosine similarity threshold for cache hits
            cache_ttl: Time-to-live for semantic cache entries
            max_cache_size: Maximum number of entries in semantic cache
            enable_cache: Whether semantic caching is enabled
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size
        self.enable_cache = enable_cache and SENTENCE_TRANSFORMERS_AVAILABLE

        self.model: SentenceTransformer | None = None
        self.cache = MultiLevelCache(
            redis_url=None,  # Use memory-only for semantic cache
            max_memory_size=max_cache_size,
            default_ttl=cache_ttl,
        )

        # Cache for embeddings to avoid recomputation
        self.embedding_cache: dict[str, np.ndarray] = {}
        self.embedding_cache_keys: list[str] = []

        # Metrics
        self.metrics = get_metrics()
        self.semantic_hit_counter = self.metrics.counter(
            "semantic_cache_hits_total", labels={"service": "semantic_cache"}
        )
        self.semantic_miss_counter = self.metrics.counter(
            "semantic_cache_misses_total", labels={"service": "semantic_cache"}
        )
        self.embedding_generation_counter = self.metrics.counter(
            "embedding_generations_total", labels={"service": "semantic_cache"}
        )

        if self.enable_cache:
            self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the sentence transformer model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("Sentence transformers not available, disabling semantic caching")
            self.enable_cache = False
            return

        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Initialized semantic cache with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize semantic cache model: {e}")
            self.enable_cache = False

    def _get_embedding(self, text: str) -> np.ndarray | None:
        """Get embedding for text, using cache if available."""
        if not self.enable_cache or not self.model:
            return None

        # Create cache key from text
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        cache_key = f"embed:{text_hash}"

        # Check embedding cache
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]

        try:
            # Generate new embedding
            embedding = self.model.encode([text], convert_to_tensor=False)[0]
            self.embedding_generation_counter.inc()

            # Cache the embedding
            self.embedding_cache[cache_key] = embedding
            self.embedding_cache_keys.append(cache_key)

            # Evict old embeddings if cache is full
            if len(self.embedding_cache) > 1000:  # Keep last 1000 embeddings
                oldest_key = self.embedding_cache_keys.pop(0)
                if oldest_key in self.embedding_cache:
                    del self.embedding_cache[oldest_key]

            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            return None

    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0

    def _serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """Serialize embedding for storage."""
        return embedding.tobytes()

    def _deserialize_embedding(self, data: bytes, shape: tuple[int, ...] = (384,)) -> np.ndarray:
        """Deserialize embedding from storage."""
        return np.frombuffer(data, dtype=np.float32).reshape(shape)

    async def get_semantic_match(
        self,
        query_text: str,
        namespace: str,
        tenant: str = "",
        workspace: str = "",
    ) -> dict[str, Any] | None:
        """Find semantically similar cached result.

        Args:
            query_text: Text to find similar results for
            namespace: Cache namespace
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            Cached result if similar enough, None otherwise
        """
        if not self.enable_cache or not self.model:
            return None

        query_embedding = self._get_embedding(query_text)
        if query_embedding is None:
            return None

        # Search through cached entries in this namespace
        search_key = f"semantic_search:{namespace}:{tenant}:{workspace}"
        cached_entries = self.cache.get(search_key, {"operation": "semantic_search"})

        if not cached_entries:
            return None

        best_match = None
        best_similarity = 0.0

        # Check similarity against all cached entries
        for entry_key, entry_data in cached_entries.items():
            if "embedding" not in entry_data:
                continue

            try:
                cached_embedding = self._deserialize_embedding(entry_data["embedding"])
                similarity = self._calculate_similarity(query_embedding, cached_embedding)

                if similarity >= self.similarity_threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = {
                        "result": entry_data["result"],
                        "similarity": similarity,
                        "original_key": entry_key,
                    }
            except Exception as e:
                logger.debug(f"Failed to check similarity for {entry_key}: {e}")
                continue

        if best_match:
            self.semantic_hit_counter.inc()
            logger.debug(f"Semantic cache hit: similarity={best_similarity:.3f}, threshold={self.similarity_threshold}")
            return best_match
        else:
            self.semantic_miss_counter.inc()
            return None

    async def store_semantic_entry(
        self,
        text: str,
        result: Any,
        namespace: str,
        tenant: str = "",
        workspace: str = "",
        original_key: str | None = None,
    ) -> bool:
        """Store a result in semantic cache.

        Args:
            text: Text that was processed
            result: Result to cache
            namespace: Cache namespace
            tenant: Tenant identifier
            workspace: Workspace identifier
            original_key: Original cache key for this result

        Returns:
            True if stored successfully
        """
        if not self.enable_cache or not self.model:
            return False

        embedding = self._get_embedding(text)
        if embedding is None:
            return False

        try:
            # Generate unique key for this entry
            text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
            entry_key = f"{text_hash}_{tenant}_{workspace}"

            # Prepare entry data
            entry_data = {
                "result": result,
                "embedding": self._serialize_embedding(embedding),
                "text_hash": text_hash,
                "original_key": original_key,
                "created_at": asyncio.get_event_loop().time(),
            }

            # Get or create the namespace cache
            search_key = f"semantic_search:{namespace}:{tenant}:{workspace}"
            cached_entries = self.cache.get(search_key, {"operation": "semantic_search"}) or {}

            # Add new entry
            cached_entries[entry_key] = entry_data

            # Store back in cache
            success = self.cache.set(
                search_key,
                {"operation": "semantic_search"},
                cached_entries,
                ttl=self.cache_ttl,
                tenant=tenant,
                workspace=workspace,
            )

            if success:
                logger.debug(f"Stored semantic cache entry: {entry_key}")
            return success

        except Exception as e:
            logger.error(f"Failed to store semantic cache entry: {e}")
            return False

    async def warm_cache(
        self,
        texts_and_results: list[tuple[str, Any]],
        namespace: str,
        tenant: str = "",
        workspace: str = "",
    ) -> dict[str, Any]:
        """Warm the semantic cache with pre-computed results.

        Args:
            texts_and_results: List of (text, result) tuples to cache
            namespace: Cache namespace
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            Statistics about cache warming
        """
        if not self.enable_cache:
            return {"status": "disabled", "cached_count": 0}

        cached_count = 0
        failed_count = 0

        for text, result in texts_and_results:
            try:
                success = await self.store_semantic_entry(text, result, namespace, tenant, workspace)
                if success:
                    cached_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to warm cache for text: {e}")
                failed_count += 1

        logger.info(f"Cache warming complete: {cached_count} cached, {failed_count} failed")
        return {
            "status": "complete",
            "cached_count": cached_count,
            "failed_count": failed_count,
            "total_processed": len(texts_and_results),
        }

    def get_stats(self) -> dict[str, Any]:
        """Get semantic cache statistics."""
        return {
            "enabled": self.enable_cache,
            "model_name": self.model_name if self.model else None,
            "similarity_threshold": self.similarity_threshold,
            "cache_ttl": self.cache_ttl,
            "embedding_cache_size": len(self.embedding_cache),
            "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
        }

    def clear_cache(self, namespace: str | None = None, tenant: str = "", workspace: str = "") -> bool:
        """Clear semantic cache entries.

        Args:
            namespace: Specific namespace to clear (None for all)
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            True if cleared successfully
        """
        try:
            if namespace:
                search_key = f"semantic_search:{namespace}:{tenant}:{workspace}"
                return self.cache.delete(search_key, {"operation": "semantic_search"}, tenant, workspace)
            else:
                # Clear all semantic cache entries
                return self.cache.clear(tenant, workspace)
        except Exception as e:
            logger.error(f"Failed to clear semantic cache: {e}")
            return False


# Global instance
_semantic_cache_instance: SemanticCacheService | None = None


def get_semantic_cache_service(
    model_name: str = "all-MiniLM-L6-v2",
    similarity_threshold: float = 0.85,
    **kwargs: Any,
) -> SemanticCacheService:
    """Get or create global semantic cache service instance."""
    global _semantic_cache_instance
    if _semantic_cache_instance is None:
        _semantic_cache_instance = SemanticCacheService(
            model_name=model_name,
            similarity_threshold=similarity_threshold,
            **kwargs,
        )
    return _semantic_cache_instance


__all__ = ["SemanticCacheService", "get_semantic_cache_service"]
