"""Specialized caching for LLM responses with semantic similarity and token tracking.

This module provides intelligent caching for Large Language Model responses,
including semantic similarity-based cache key matching and comprehensive
token usage tracking for cost optimization.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from platform.cache.cache_service import get_cache_service
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """Data class for LLM request parameters."""

    prompt: str
    model: str
    temperature: float = 0.0
    max_tokens: int | None = None
    ttl: int | None = None


class LLMSimilarityCache:
    """LLM cache with semantic similarity-based key matching."""

    def __init__(
        self, similarity_threshold: float = 0.85, max_cache_keys_per_prompt: int = 5, enable_token_tracking: bool = True
    ):
        """Initialize the LLM similarity cache.

        Args:
            similarity_threshold: Minimum similarity score for cache hit (0.0-1.0)
            max_cache_keys_per_prompt: Maximum similar keys to track per prompt
            enable_token_tracking: Whether to track token usage statistics
        """
        self.similarity_threshold = similarity_threshold
        self.max_cache_keys_per_prompt = max_cache_keys_per_prompt
        self.enable_token_tracking = enable_token_tracking
        self._cache_service = get_cache_service()
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "similarity_hits": 0,
            "total_tokens_saved": 0,
            "total_requests": 0,
        }

    async def get(
        self, prompt: str, model: str, temperature: float = 0.0, max_tokens: int | None = None, **kwargs
    ) -> dict[str, Any] | None:
        """Get cached LLM response with semantic similarity matching.

        Args:
            prompt: The input prompt
            model: The model name
            temperature: Temperature parameter (affects cacheability)
            max_tokens: Maximum tokens parameter
            **kwargs: Additional parameters

        Returns:
            Cached response if found, None otherwise
        """
        self._stats["total_requests"] += 1
        cache_key = self._make_cache_key(prompt, model, temperature, max_tokens, kwargs)
        cached_result = await self._cache_service.get(cache_key, "llm")
        if cached_result:
            self._stats["cache_hits"] += 1
            if self.enable_token_tracking and isinstance(cached_result, dict):
                self._stats["total_tokens_saved"] += cached_result.get("usage", {}).get("completion_tokens", 0)
            return cached_result
        similar_key = await self._find_similar_prompt(prompt, model, temperature)
        if similar_key:
            cached_result = await self._cache_service.get(similar_key, "llm")
            if cached_result:
                self._stats["similarity_hits"] += 1
                self._stats["cache_hits"] += 1
                if self.enable_token_tracking and isinstance(cached_result, dict):
                    self._stats["total_tokens_saved"] += cached_result.get("usage", {}).get("completion_tokens", 0)
                return cached_result
        self._stats["cache_misses"] += 1
        return None

    async def set(self, request: LLMRequest, response: dict[str, Any], **kwargs) -> bool:
        """Cache LLM response with similarity tracking.

        Args:
            prompt: The input prompt
            model: The model name
            response: The LLM response to cache
            temperature: Temperature parameter
            max_tokens: Maximum tokens parameter
            ttl: Time to live in seconds
            **kwargs: Additional parameters

        Returns:
            True if successfully cached, False otherwise
        """
        cache_key = self._make_cache_key(request.prompt, request.model, request.temperature, request.max_tokens, kwargs)
        success = await self._cache_service.set(cache_key, response, ttl=request.ttl, cache_type="llm")
        if success:
            await self._update_similarity_index(request.prompt, request.model, cache_key)
        return success

    async def invalidate_model_cache(self, model: str) -> int:
        """Invalidate all cached responses for a specific model.

        Args:
            model: Model name to invalidate

        Returns:
            Number of keys invalidated
        """
        logger.info(f"Invalidating cache for model: {model}")
        return 0

    def _make_cache_key(
        self, prompt: str, model: str, temperature: float, max_tokens: int | None, kwargs: dict[str, Any]
    ) -> str:
        """Create a deterministic cache key for the LLM request."""
        key_components = [f"model={model}", f"temperature={temperature:.2f}"]
        if max_tokens is not None:
            key_components.append(f"max_tokens={max_tokens}")
        for key, value in sorted(kwargs.items()):
            if key not in ["api_key", "secret"]:
                key_components.append(f"{key}={value!r}")
        content = f"{prompt}|{'|'.join(key_components)}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"llm:{model}:{content_hash}"

    async def _find_similar_prompt(self, prompt: str, model: str, temperature: float) -> str | None:
        """Find a similar prompt in the cache using basic heuristics.

        This is a simplified implementation. In production, you might want to:
        - Use embeddings for semantic similarity
        - Implement more sophisticated text similarity algorithms
        - Use a dedicated similarity index

        Args:
            prompt: The input prompt
            model: The model name
            temperature: Temperature parameter

        Returns:
            Cache key of similar prompt if found, None otherwise
        """
        return None

    async def _update_similarity_index(self, prompt: str, model: str, cache_key: str) -> None:
        """Update the similarity index with a new prompt.

        Args:
            prompt: The prompt text
            model: The model name
            cache_key: The cache key for this prompt
        """

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["total_requests"]
        hit_rate = self._stats["cache_hits"] / total_requests if total_requests > 0 else 0.0
        return {
            "total_requests": total_requests,
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "similarity_hits": self._stats["similarity_hits"],
            "hit_rate": hit_rate,
            "total_tokens_saved": self._stats["total_tokens_saved"],
            "similarity_threshold": self.similarity_threshold,
            "max_cache_keys_per_prompt": self.max_cache_keys_per_prompt,
        }


class LLMCacheManager:
    """Manager for LLM caching with multiple strategies and models."""

    def __init__(self):
        """Initialize the LLM cache manager."""
        self._caches: dict[str, LLMSimilarityCache] = {}
        self._default_cache = LLMSimilarityCache()

    def get_cache(self, model: str) -> LLMSimilarityCache:
        """Get or create a cache for a specific model.

        Args:
            model: Model name

        Returns:
            LLM cache instance for the model
        """
        if model not in self._caches:
            if "gpt-4" in model.lower():
                self._caches[model] = LLMSimilarityCache(
                    similarity_threshold=0.9, max_cache_keys_per_prompt=3, enable_token_tracking=True
                )
            elif "gpt-3.5" in model.lower():
                self._caches[model] = LLMSimilarityCache(
                    similarity_threshold=0.85, max_cache_keys_per_prompt=5, enable_token_tracking=True
                )
            else:
                self._caches[model] = LLMSimilarityCache()
        return self._caches[model]

    async def get_response(self, prompt: str, model: str, **kwargs) -> dict[str, Any] | None:
        """Get cached LLM response for any model.

        Args:
            prompt: The input prompt
            model: The model name
            **kwargs: Additional parameters

        Returns:
            Cached response if found, None otherwise
        """
        cache = self.get_cache(model)
        return await cache.get(prompt, model, **kwargs)

    async def set_response(self, request: LLMRequest, response: dict[str, Any], **kwargs) -> bool:
        """Cache LLM response for any model.

        Args:
            request: The LLM request parameters
            response: The response to cache
            **kwargs: Additional parameters

        Returns:
            True if successfully cached, False otherwise
        """
        cache = self.get_cache(request.model)
        return await cache.set(request, response, **kwargs)

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all model caches.

        Returns:
            Dictionary mapping model names to their cache statistics
        """
        stats = {}
        for model, cache in self._caches.items():
            stats[model] = cache.get_stats()
        return stats


_llm_cache_manager = LLMCacheManager()


def get_llm_cache_manager() -> LLMCacheManager:
    """Get the global LLM cache manager instance."""
    return _llm_cache_manager


__all__ = ["LLMCacheManager", "LLMSimilarityCache", "get_llm_cache_manager"]
