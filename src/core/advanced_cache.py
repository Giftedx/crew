"""Advanced semantic caching with multi-level optimization.

This module provides sophisticated caching strategies including semantic similarity,
prompt compression, and predictive cache warming for optimal performance.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata for optimization."""

    key: str
    value: Any
    compressed_prompt: str
    embedding: list[float]
    created_at: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    cost_saved: float = 0.0
    latency_saved: float = 0.0


class AdvancedSemanticCache:
    """Multi-level semantic cache with compression and warming."""

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        compression_ratio: float = 0.3,
        max_entries: int = 10000,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """Initialize advanced semantic cache.

        Args:
            similarity_threshold: Minimum similarity for cache hits
            compression_ratio: Target compression ratio (0.3 = 30% of original)
            max_entries: Maximum number of cache entries
            embedding_model: Sentence transformer model for embeddings
        """
        self.similarity_threshold = similarity_threshold
        self.compression_ratio = compression_ratio
        self.max_entries = max_entries

        # Cache storage
        self.l1_cache: dict[str, CacheEntry] = {}  # Exact matches
        self.l2_cache: dict[str, CacheEntry] = {}  # Compressed prompt matches
        self.l3_cache: dict[str, CacheEntry] = {}  # Semantic similarity matches

        # Embedding model
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            logger.info(f"Loaded embedding model: {embedding_model}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None

        # Compression patterns for common prompt templates
        self.compression_patterns = [
            (r"Please analyze the following", "Analyze:"),
            (r"Can you help me with", "Help:"),
            (r"I would like you to", "Do:"),
            (r"Could you please", "Please:"),
            (r"Thank you in advance", ""),
            (r"Let me know if you need", ""),
        ]

        # Metrics
        self.metrics = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0,
            "compressions_applied": 0,
            "total_savings_usd": 0.0,
            "total_latency_saved": 0.0,
        }

    def get(self, prompt: str, expected_tokens: int = 1000) -> tuple[Any | None, dict[str, Any]]:
        """Get cached response with multi-level lookup.

        Args:
            prompt: Input prompt
            expected_tokens: Expected response tokens for cost calculation

        Returns:
            Tuple of (cached_response, metadata)
        """
        metadata = {
            "cache_level": None,
            "similarity_score": None,
            "compression_applied": False,
            "cost_saved": 0.0,
            "latency_saved": 0.0,
        }

        # L1: Exact match
        if prompt in self.l1_cache:
            entry = self.l1_cache[prompt]
            entry.access_count += 1
            entry.last_accessed = time.time()

            self.metrics["l1_hits"] += 1
            metadata.update(
                {
                    "cache_level": "L1",
                    "cost_saved": self._calculate_cost_savings(expected_tokens),
                    "latency_saved": 0.5,  # Estimated latency savings
                }
            )

            return entry.value, metadata

        # L2: Compressed prompt match
        compressed = self._compress_prompt(prompt)
        if compressed in self.l2_cache:
            entry = self.l2_cache[compressed]
            entry.access_count += 1
            entry.last_accessed = time.time()

            self.metrics["l2_hits"] += 1
            metadata.update(
                {
                    "cache_level": "L2",
                    "compression_applied": True,
                    "cost_saved": self._calculate_cost_savings(expected_tokens),
                    "latency_saved": 0.3,
                }
            )

            return entry.value, metadata

        # L3: Semantic similarity match
        if self.embedding_model:
            semantic_result = self._semantic_search(prompt)
            if semantic_result:
                entry, similarity = semantic_result
                entry.access_count += 1
                entry.last_accessed = time.time()

                self.metrics["l3_hits"] += 1
                metadata.update(
                    {
                        "cache_level": "L3",
                        "similarity_score": similarity,
                        "cost_saved": self._calculate_cost_savings(expected_tokens),
                        "latency_saved": 0.2,
                    }
                )

                return entry.value, metadata

        # Cache miss
        self.metrics["misses"] += 1
        metadata["cache_level"] = "MISS"

        return None, metadata

    def put(
        self,
        prompt: str,
        response: Any,
        expected_tokens: int = 1000,
        cost_estimate: float = 0.0,
    ) -> StepResult:
        """Store response in cache with multi-level optimization.

        Args:
            prompt: Input prompt
            response: Cached response
            expected_tokens: Expected response tokens
            cost_estimate: Estimated cost of the request
        """
        try:
            # Generate embeddings if model available
            embedding = None
            if self.embedding_model:
                try:
                    embedding = self.embedding_model.encode(prompt).tolist()
                except Exception as e:
                    logger.warning(f"Failed to generate embedding: {e}")

            # Create cache entry
            entry = CacheEntry(
                key=prompt,
                value=response,
                compressed_prompt=self._compress_prompt(prompt),
                embedding=embedding or [],
                created_at=time.time(),
                cost_saved=cost_estimate,
            )

            # Store in L1 (exact match)
            self.l1_cache[prompt] = entry

            # Store in L2 (compressed match)
            compressed = entry.compressed_prompt
            if compressed != prompt:  # Only if compression changed the prompt
                self.l2_cache[compressed] = entry
                self.metrics["compressions_applied"] += 1

            # Store in L3 (semantic match) - only if we have embeddings
            if embedding:
                # Use hash of embedding as key for L3
                embedding_key = hashlib.md5(json.dumps(embedding).encode(), usedforsecurity=False).hexdigest()[:16]  # nosec B324 - non-cryptographic cache key
                self.l3_cache[embedding_key] = entry

            # Cleanup if cache is full
            self._cleanup_if_needed()

            return StepResult.ok(
                data={
                    "cached": True,
                    "levels_stored": ["L1", "L2", "L3"] if embedding else ["L1", "L2"],
                    "compression_applied": compressed != prompt,
                }
            )

        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
            return StepResult.fail(f"Cache storage failed: {e!s}")

    def _compress_prompt(self, prompt: str) -> str:
        """Compress prompt using pattern matching and heuristics."""
        import re

        compressed = prompt

        # Apply compression patterns
        for pattern, replacement in self.compression_patterns:
            compressed = re.sub(pattern, replacement, compressed, flags=re.IGNORECASE)

        # Remove extra whitespace
        compressed = re.sub(r"\s+", " ", compressed).strip()

        # If compression didn't achieve target ratio, apply more aggressive compression
        if len(compressed) / len(prompt) > self.compression_ratio:
            # Remove common filler words and phrases
            filler_patterns = [
                r"\b(please|kindly|would you|could you|can you)\b",
                r"\b(thank you|thanks|appreciate|grateful)\b",
                r"\b(let me know|please let me know)\b",
                r"\b(in advance|ahead of time)\b",
            ]

            for pattern in filler_patterns:
                compressed = re.sub(pattern, "", compressed, flags=re.IGNORECASE)

            compressed = re.sub(r"\s+", " ", compressed).strip()

        return compressed

    def _semantic_search(self, prompt: str) -> tuple[CacheEntry, float] | None:
        """Find semantically similar cached responses."""
        if not self.embedding_model:
            return None

        try:
            # Generate embedding for input prompt
            query_embedding = self.embedding_model.encode(prompt)

            best_match = None
            best_similarity = 0.0

            # Search through L3 cache entries
            for entry in self.l3_cache.values():
                if not entry.embedding:
                    continue

                # Calculate cosine similarity
                stored_embedding = np.array(entry.embedding)
                similarity = np.dot(query_embedding, stored_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                )

                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = entry

            if best_match:
                return best_match, best_similarity

            return None

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return None

    def _calculate_cost_savings(self, tokens: int) -> float:
        """Calculate cost savings for cached response."""
        # Rough estimate: $0.002 per 1K tokens
        return (tokens / 1000) * 0.002

    def _cleanup_if_needed(self) -> None:
        """Clean up cache if it exceeds max entries."""
        total_entries = len(self.l1_cache) + len(self.l2_cache) + len(self.l3_cache)

        if total_entries > self.max_entries:
            # Remove least recently used entries
            all_entries = list(self.l1_cache.values())
            all_entries.sort(key=lambda x: x.last_accessed)

            # Remove oldest 10% of entries
            remove_count = max(1, total_entries // 10)

            for entry in all_entries[:remove_count]:
                # Remove from all levels
                if entry.key in self.l1_cache:
                    del self.l1_cache[entry.key]
                if entry.compressed_prompt in self.l2_cache:
                    del self.l2_cache[entry.compressed_prompt]

                # Remove from L3 (find by embedding)
                for key, l3_entry in list(self.l3_cache.items()):
                    if l3_entry.key == entry.key:
                        del self.l3_cache[key]
                        break

    def warm_cache(self, common_prompts: list[str], responses: list[Any]) -> StepResult:
        """Pre-populate cache with common queries."""
        try:
            if len(common_prompts) != len(responses):
                return StepResult.fail("Prompts and responses lists must have same length")

            warmed_count = 0
            for prompt, response in zip(common_prompts, responses, strict=False):
                result = self.put(prompt, response)
                if result.success:
                    warmed_count += 1

            return StepResult.ok(
                data={
                    "warmed_count": warmed_count,
                    "total_attempted": len(common_prompts),
                }
            )

        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            return StepResult.fail(f"Cache warming failed: {e!s}")

    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics."""
        total_hits = self.metrics["l1_hits"] + self.metrics["l2_hits"] + self.metrics["l3_hits"]
        total_requests = total_hits + self.metrics["misses"]
        hit_rate = total_hits / total_requests if total_requests > 0 else 0.0

        return {
            **self.metrics,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "cache_size": {
                "l1_entries": len(self.l1_cache),
                "l2_entries": len(self.l2_cache),
                "l3_entries": len(self.l3_cache),
                "total_entries": len(self.l1_cache) + len(self.l2_cache) + len(self.l3_cache),
            },
            "configuration": {
                "similarity_threshold": self.similarity_threshold,
                "compression_ratio": self.compression_ratio,
                "max_entries": self.max_entries,
                "embedding_model_loaded": self.embedding_model is not None,
            },
        }

    def health_check(self) -> StepResult:
        """Perform health check on cache."""
        try:
            metrics = self.get_metrics()

            # Check if hit rate is below target
            target_hit_rate = 0.6  # 60%
            health_status = "healthy"
            issues = []

            if metrics["hit_rate"] < target_hit_rate:
                health_status = "degraded"
                issues.append(f"Hit rate {metrics['hit_rate']:.2%} below target {target_hit_rate:.2%}")

            # Check if cache is too full
            cache_utilization = metrics["cache_size"]["total_entries"] / self.max_entries
            if cache_utilization > 0.9:
                health_status = "degraded"
                issues.append(f"Cache utilization {cache_utilization:.2%} above 90%")

            return StepResult.ok(
                data={
                    "advanced_cache_healthy": health_status == "healthy",
                    "health_status": health_status,
                    "issues": issues,
                    "metrics": metrics,
                }
            )

        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return StepResult.fail(f"Health check failed: {e!s}")


# Global cache instance
_advanced_cache: AdvancedSemanticCache | None = None


def get_advanced_cache() -> AdvancedSemanticCache:
    """Get the global advanced cache instance."""
    global _advanced_cache
    if _advanced_cache is None:
        _advanced_cache = AdvancedSemanticCache()
    return _advanced_cache
