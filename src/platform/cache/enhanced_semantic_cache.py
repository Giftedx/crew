"""Enhanced semantic cache implementation for better performance without GPTCache dependency.

This module provides intelligent semantic caching using text similarity algorithms,
prompt preprocessing, and advanced cache management techniques to improve cache
hit rates and reduce LLM API costs.
"""

from __future__ import annotations

import contextlib
import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ultimate_discord_intelligence_bot.obs import metrics


try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Enhanced cache entry with metadata and similarity tracking."""

    key: str
    prompt: str
    response: dict[str, Any]
    model: str
    namespace: str | None
    stored_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    similarity_score: float = 0.0


@dataclass
class SimilarityResult:
    """Result of semantic similarity search."""

    entry: CacheEntry | None
    similarity_score: float
    match_type: str


class EnhancedSemanticCache:
    """Enhanced semantic cache with intelligent similarity matching."""

    def __init__(
        self,
        *,
        similarity_threshold: float = 0.8,
        max_cache_size: int = 1000,
        cache_ttl_seconds: int = 3600,
        enable_embeddings: bool = True,
        enable_tfidf: bool = True,
        namespace: str | None = None,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.cache_ttl_seconds = cache_ttl_seconds
        self.namespace = namespace
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []
        self.enable_embeddings = enable_embeddings and SENTENCE_TRANSFORMERS_AVAILABLE
        self.enable_tfidf = enable_tfidf and SKLEARN_AVAILABLE
        self._embedding_model = None
        self._tfidf_vectorizer = None
        self._tfidf_matrix = None
        self._prompt_embeddings = {}
        if self.enable_embeddings:
            self._init_embedding_model()
        if self.enable_tfidf:
            self._init_tfidf_vectorizer()
        self.stats = {
            "total_requests": 0,
            "exact_hits": 0,
            "semantic_hits": 0,
            "fuzzy_hits": 0,
            "misses": 0,
            "cache_stores": 0,
            "evictions": 0,
        }

    def _init_embedding_model(self) -> None:
        """Initialize sentence transformer for semantic similarity."""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Initialized sentence transformer for semantic caching")
        except Exception as e:
            logger.warning(f"Failed to initialize embedding model: {e}")
            self.enable_embeddings = False

    def _init_tfidf_vectorizer(self) -> None:
        """Initialize TF-IDF vectorizer for text similarity."""
        try:
            if SKLEARN_AVAILABLE:
                self._tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words="english", ngram_range=(1, 2))
                logger.info("Initialized TF-IDF vectorizer for semantic caching")
        except Exception as e:
            logger.warning(f"Failed to initialize TF-IDF vectorizer: {e}")
            self.enable_tfidf = False

    def _preprocess_prompt(self, prompt: str) -> str:
        """Preprocess prompt for better similarity matching."""
        prompt = re.sub("\\s+", " ", prompt.strip())
        prompt = re.sub("\\b\\d{4}-\\d{2}-\\d{2}\\b", "[DATE]", prompt)
        prompt = re.sub("\\b\\d{1,2}:\\d{2}(?::\\d{2})?\\b", "[TIME]", prompt)
        prompt = re.sub(
            "\\b[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}\\b", "[UUID]", prompt
        )
        prompt = prompt.replace("user:", "[USER]:")
        prompt = prompt.replace("assistant:", "[ASSISTANT]:")
        return prompt.lower()

    def _generate_cache_key(self, prompt: str, model: str, **kwargs) -> str:
        """Generate a deterministic cache key."""
        namespace = kwargs.get("namespace", self.namespace or "default")
        normalized_prompt = self._preprocess_prompt(prompt)
        key_data = f"{model}:{namespace}:{normalized_prompt}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _compute_similarity(self, prompt1: str, prompt2: str) -> float:
        """Compute semantic similarity between two prompts."""
        if prompt1 == prompt2:
            return 1.0
        processed1 = self._preprocess_prompt(prompt1)
        processed2 = self._preprocess_prompt(prompt2)
        fuzzy_score = self._fuzzy_similarity(processed1, processed2)
        if fuzzy_score >= 0.9:
            return fuzzy_score
        if self.enable_tfidf:
            tfidf_score = self._tfidf_similarity(processed1, processed2)
            if tfidf_score >= self.similarity_threshold:
                return tfidf_score
        if self.enable_embeddings and self._embedding_model:
            embedding_score = self._embedding_similarity(processed1, processed2)
            if embedding_score >= self.similarity_threshold:
                return embedding_score
        return 0.0

    def _fuzzy_similarity(self, text1: str, text2: str) -> float:
        """Compute fuzzy string similarity."""
        import difflib

        return difflib.SequenceMatcher(None, text1, text2).ratio()

    def _tfidf_similarity(self, text1: str, text2: str) -> float:
        """Compute TF-IDF cosine similarity."""
        if not self._tfidf_vectorizer or not SKLEARN_AVAILABLE:
            return 0.0
        try:
            if self._tfidf_matrix is None:
                all_prompts = [*self._prompt_embeddings.keys(), text1, text2]
                self._tfidf_matrix = self._tfidf_vectorizer.fit_transform(all_prompts)
                self._prompt_embeddings[text1] = len(all_prompts) - 2
                self._prompt_embeddings[text2] = len(all_prompts) - 1
            vectors = self._tfidf_vectorizer.transform([text1, text2])
            similarity_matrix = cosine_similarity(vectors)
            return float(similarity_matrix[0, 1])
        except Exception as e:
            logger.debug(f"TF-IDF similarity error: {e}")
            return 0.0

    def _embedding_similarity(self, text1: str, text2: str) -> float:
        """Compute embedding-based semantic similarity."""
        if not self._embedding_model:
            return 0.0
        try:
            embedding1 = self._embedding_model.encode([text1])[0]
            embedding2 = self._embedding_model.encode([text2])[0]
            similarity = float(
                np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
            )
            return max(0.0, similarity)
        except Exception as e:
            logger.debug(f"Embedding similarity error: {e}")
            return 0.0

    def get(self, prompt: str, model: str, **kwargs) -> dict[str, Any] | None:
        """Retrieve cached response if similar prompt exists."""
        self.stats["total_requests"] += 1
        cache_key = self._generate_cache_key(prompt, model, **kwargs)
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if entry.expires_at > time.time():
                entry.access_count += 1
                entry.last_accessed = time.time()
                self._access_order.remove(cache_key)
                self._access_order.append(cache_key)
                self.stats["exact_hits"] += 1
                logger.debug(f"Exact cache hit for model {model}")
                return entry.response
        best_match = None
        best_score = 0.0
        for entry in self._cache.values():
            if entry.expires_at <= time.time():
                continue
            if entry.model == model and entry.namespace == kwargs.get("namespace"):
                similarity = self._compute_similarity(prompt, entry.prompt)
                if similarity >= self.similarity_threshold and similarity > best_score:
                    best_score = similarity
                    best_match = entry
        if best_match:
            best_match.access_count += 1
            best_match.last_accessed = time.time()
            best_match.similarity_score = best_score
            if best_match.key in self._access_order:
                self._access_order.remove(best_match.key)
            self._access_order.append(best_match.key)
            if best_score >= 0.95:
                self.stats["exact_hits"] += 1
                logger.debug(f"High-confidence semantic cache hit for model {model} (score: {best_score:.3f})")
            else:
                self.stats["semantic_hits"] += 1
                logger.debug(f"Semantic cache hit for model {model} (score: {best_score:.3f})")
            with contextlib.suppress(Exception):
                metrics.LLM_CACHE_HITS.labels(**metrics.label_ctx(), model=model, provider="enhanced_semantic").inc()
            return best_match.response
        self.stats["misses"] += 1
        with contextlib.suppress(Exception):
            metrics.LLM_CACHE_MISSES.labels(**metrics.label_ctx(), model=model, provider="enhanced_semantic").inc()
        return None

    def set(self, prompt: str, model: str, response: dict[str, Any], **kwargs) -> None:
        """Store response in enhanced semantic cache."""
        cache_key = self._generate_cache_key(prompt, model, **kwargs)
        if len(self._cache) >= self.max_cache_size:
            self._evict_lru_entries()
        entry = CacheEntry(
            key=cache_key,
            prompt=prompt,
            response=response,
            model=model,
            namespace=kwargs.get("namespace"),
            stored_at=time.time(),
            expires_at=time.time() + self.cache_ttl_seconds,
        )
        self._cache[cache_key] = entry
        self._access_order.append(cache_key)
        self.stats["cache_stores"] += 1
        if self.enable_tfidf and self._tfidf_vectorizer:
            self._update_tfidf_matrix(prompt)
        logger.debug(f"Stored response in enhanced semantic cache for model {model}")

    def _evict_lru_entries(self) -> None:
        """Evict least recently used entries to maintain cache size."""
        if not self._access_order:
            return
        entries_to_remove = max(1, len(self._access_order) // 10)
        for _ in range(entries_to_remove):
            if not self._access_order:
                break
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                self.stats["evictions"] += 1

    def _update_tfidf_matrix(self, prompt: str) -> None:
        """Update TF-IDF matrix with new prompt."""
        if not self._tfidf_vectorizer or not SKLEARN_AVAILABLE:
            return
        try:
            current_prompts = [entry.prompt for entry in self._cache.values()]
            if current_prompts:
                self._tfidf_matrix = self._tfidf_vectorizer.fit_transform(current_prompts)
        except Exception as e:
            logger.debug(f"Error updating TF-IDF matrix: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = sum(self.stats.values())
        hit_rate = (
            (self.stats["exact_hits"] + self.stats["semantic_hits"]) / total_requests if total_requests > 0 else 0.0
        )
        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "cache_size": len(self._cache),
            "embedding_model_available": self.enable_embeddings,
            "tfidf_model_available": self.enable_tfidf,
        }

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._access_order.clear()
        self.stats = dict.fromkeys(self.stats, 0)
        logger.info("Enhanced semantic cache cleared")


def create_enhanced_semantic_cache(
    similarity_threshold: float = 0.8,
    max_cache_size: int = 1000,
    cache_ttl_seconds: int = 3600,
    enable_embeddings: bool = True,
    enable_tfidf: bool = True,
    namespace: str | None = None,
) -> EnhancedSemanticCache:
    """Factory function for creating enhanced semantic cache instances."""
    return EnhancedSemanticCache(
        similarity_threshold=similarity_threshold,
        max_cache_size=max_cache_size,
        cache_ttl_seconds=cache_ttl_seconds,
        enable_embeddings=enable_embeddings,
        enable_tfidf=enable_tfidf,
        namespace=namespace,
    )


__all__ = ["CacheEntry", "EnhancedSemanticCache", "SimilarityResult", "create_enhanced_semantic_cache"]
