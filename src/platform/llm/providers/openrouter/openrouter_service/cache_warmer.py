"""Cache warming and optimization for OpenRouter service.

This module provides cache warming capabilities to preload frequently
used prompts and optimize cache performance.
"""

from __future__ import annotations

import asyncio
import gzip
import json
import logging
import time
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags


if TYPE_CHECKING:
    from .service import OpenRouterService
log = logging.getLogger(__name__)


class CacheCompressor:
    """Handles compression and decompression of cache entries."""

    @staticmethod
    def compress(data: dict[str, Any]) -> bytes:
        """Compress cache data using gzip.

        Args:
            data: Dictionary to compress

        Returns:
            Compressed bytes
        """
        try:
            json_str = json.dumps(data, separators=(",", ":"))
            return gzip.compress(json_str.encode("utf-8"))
        except Exception as e:
            log.debug("Compression failed: %s", e)
            return json.dumps(data).encode("utf-8")

    @staticmethod
    def decompress(compressed_data: bytes) -> dict[str, Any] | None:
        """Decompress cache data.

        Args:
            compressed_data: Compressed bytes

        Returns:
            Decompressed dictionary or None if failed
        """
        try:
            try:
                decompressed = gzip.decompress(compressed_data)
                return json.loads(decompressed.decode("utf-8"))
            except (gzip.BadGzipFile, json.JSONDecodeError):
                return json.loads(compressed_data.decode("utf-8"))
        except Exception as e:
            log.debug("Decompression failed: %s", e)
            return None

    @staticmethod
    def get_compression_ratio(original: dict[str, Any], compressed: bytes) -> float:
        """Calculate compression ratio.

        Args:
            original: Original data
            compressed: Compressed data

        Returns:
            Compression ratio (0.0 to 1.0)
        """
        try:
            original_size = len(json.dumps(original, separators=(",", ":")).encode("utf-8"))
            compressed_size = len(compressed)
            return 1.0 - compressed_size / original_size
        except Exception:
            return 0.0


class CacheWarmer:
    """Preloads cache with frequently used prompts and patterns."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize cache warmer.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._feature_flags = FeatureFlags()
        self._compressor = CacheCompressor()
        self._warming_tasks: set[asyncio.Task] = set()
        self._stats = {
            "prompts_warmed": 0,
            "cache_hits_generated": 0,
            "compression_ratio_avg": 0.0,
            "warming_time_avg": 0.0,
        }

    def _get_common_prompts(self) -> list[dict[str, Any]]:
        """Get list of common prompts to warm cache with.

        Returns:
            List of prompt configurations
        """
        return [
            {"prompt": "Hello, how are you?", "task_type": "general", "model": "openai/gpt-4o-mini"},
            {
                "prompt": "Analyze this content for bias and accuracy",
                "task_type": "analysis",
                "model": "openai/gpt-4o-mini",
            },
            {"prompt": "Summarize the following text", "task_type": "general", "model": "openai/gpt-4o-mini"},
            {
                "prompt": "What is the main topic of this discussion?",
                "task_type": "analysis",
                "model": "openai/gpt-4o-mini",
            },
            {"prompt": "Generate a response to this question", "task_type": "general", "model": "openai/gpt-4o-mini"},
        ]

    async def _warm_single_prompt(self, prompt_config: dict[str, Any]) -> None:
        """Warm cache for a single prompt.

        Args:
            prompt_config: Prompt configuration dictionary
        """
        try:
            start_time = time.perf_counter()
            result = self._service.route(
                prompt=prompt_config["prompt"], task_type=prompt_config["task_type"], model=prompt_config["model"]
            )
            if result.success:
                self._stats["prompts_warmed"] += 1
                self._stats["cache_hits_generated"] += 1
                if self._feature_flags.ENABLE_OPENROUTER_ADVANCED_CACHING:
                    original_data = result.data
                    compressed = self._compressor.compress(original_data)
                    ratio = self._compressor.get_compression_ratio(original_data, compressed)
                    current_avg = self._stats["compression_ratio_avg"]
                    count = self._stats["prompts_warmed"]
                    self._stats["compression_ratio_avg"] = (current_avg * (count - 1) + ratio) / count
                warming_time = time.perf_counter() - start_time
                current_avg = self._stats["warming_time_avg"]
                count = self._stats["prompts_warmed"]
                self._stats["warming_time_avg"] = (current_avg * (count - 1) + warming_time) / count
                log.debug("Warmed cache for prompt: %s (%.3fs)", prompt_config["prompt"][:50], warming_time)
            else:
                log.warning("Failed to warm cache for prompt: %s", prompt_config["prompt"][:50])
        except Exception as e:
            log.error("Error warming cache for prompt: %s", e)

    async def warm_cache(self, custom_prompts: list[dict[str, Any]] | None = None) -> StepResult:
        """Warm cache with common prompts.

        Args:
            custom_prompts: Optional custom prompts to warm with

        Returns:
            StepResult with warming statistics
        """
        if not self._feature_flags.ENABLE_OPENROUTER_ADVANCED_CACHING:
            return StepResult.fail("Advanced caching is disabled")
        try:
            prompts_to_warm = custom_prompts or self._get_common_prompts()
            log.info("Starting cache warming with %d prompts", len(prompts_to_warm))
            tasks = []
            for prompt_config in prompts_to_warm:
                task = asyncio.create_task(self._warm_single_prompt(prompt_config))
                tasks.append(task)
                self._warming_tasks.add(task)
                task.add_done_callback(self._warming_tasks.discard)
            await asyncio.gather(*tasks, return_exceptions=True)
            log.info(
                "Cache warming completed: %d prompts warmed, avg time: %.3fs",
                self._stats["prompts_warmed"],
                self._stats["warming_time_avg"],
            )
            return StepResult.ok(
                data={
                    "prompts_warmed": self._stats["prompts_warmed"],
                    "cache_hits_generated": self._stats["cache_hits_generated"],
                    "compression_ratio_avg": self._stats["compression_ratio_avg"],
                    "warming_time_avg": self._stats["warming_time_avg"],
                }
            )
        except Exception as e:
            log.error("Cache warming failed: %s", e)
            return StepResult.fail(f"Cache warming failed: {e!s}")

    async def warm_cache_async(self, prompts: list[str], task_type: str = "general") -> None:
        """Asynchronously warm cache with a list of prompts.

        Args:
            prompts: List of prompts to warm
            task_type: Task type for the prompts
        """
        if not self._feature_flags.ENABLE_OPENROUTER_ADVANCED_CACHING:
            return
        prompt_configs = [
            {"prompt": prompt, "task_type": task_type, "model": "openai/gpt-4o-mini"} for prompt in prompts
        ]
        task = asyncio.create_task(self.warm_cache(prompt_configs))
        self._warming_tasks.add(task)
        task.add_done_callback(self._warming_tasks.discard)

    def get_stats(self) -> dict[str, Any]:
        """Get cache warming statistics.

        Returns:
            Dictionary with warming statistics
        """
        return {
            **self._stats,
            "active_warming_tasks": len(self._warming_tasks),
            "advanced_caching_enabled": self._feature_flags.ENABLE_OPENROUTER_ADVANCED_CACHING,
        }

    def reset_stats(self) -> None:
        """Reset cache warming statistics."""
        self._stats = {
            "prompts_warmed": 0,
            "cache_hits_generated": 0,
            "compression_ratio_avg": 0.0,
            "warming_time_avg": 0.0,
        }

    async def stop_warming(self) -> None:
        """Stop all active warming tasks."""
        if self._warming_tasks:
            for task in self._warming_tasks:
                task.cancel()
            await asyncio.gather(*self._warming_tasks, return_exceptions=True)
            self._warming_tasks.clear()
            log.info("Stopped all cache warming tasks")


class EnhancedCacheManager:
    """Enhanced cache manager with compression and warming capabilities."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize enhanced cache manager.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._feature_flags = FeatureFlags()
        self._compressor = CacheCompressor()
        self._warmer = CacheWarmer(service)
        self._stats = {"cache_hits": 0, "cache_misses": 0, "compression_saves": 0, "total_compression_ratio": 0.0}

    def get_cached_response(self, prompt: str, model: str, **kwargs: Any) -> dict[str, Any] | None:
        """Get cached response with compression support.

        Args:
            prompt: The prompt
            model: The model used
            **kwargs: Additional parameters

        Returns:
            Cached response or None
        """
        try:
            if not self._service.cache:
                return None
            cache_key = self._service.cache.make_key(prompt, model)
            cached_data = self._service.cache.get(cache_key)
            if cached_data:
                self._stats["cache_hits"] += 1
                if self._feature_flags.ENABLE_OPENROUTER_ADVANCED_CACHING and isinstance(cached_data, bytes):
                    decompressed = self._compressor.decompress(cached_data)
                    if decompressed:
                        return decompressed
                    return cached_data
                return cached_data
            else:
                self._stats["cache_misses"] += 1
                return None
        except Exception as e:
            log.debug("Cache retrieval failed: %s", e)
            self._stats["cache_misses"] += 1
            return None

    def set_cached_response(self, prompt: str, model: str, response: dict[str, Any], **kwargs: Any) -> None:
        """Set cached response with compression support.

        Args:
            prompt: The prompt
            model: The model used
            response: The response to cache
            **kwargs: Additional parameters
        """
        try:
            if not self._service.cache:
                return
            cache_key = self._service.cache.make_key(prompt, model)
            if self._feature_flags.ENABLE_OPENROUTER_ADVANCED_CACHING:
                compressed = self._compressor.compress(response)
                compression_ratio = self._compressor.get_compression_ratio(response, compressed)
                if compression_ratio > 0.1:
                    self._service.cache.set(cache_key, compressed)
                    self._stats["compression_saves"] += 1
                    current_avg = self._stats["total_compression_ratio"]
                    count = self._stats["compression_saves"]
                    self._stats["total_compression_ratio"] = (current_avg * (count - 1) + compression_ratio) / count
                    log.debug("Cached compressed response (%.1f%% compression)", compression_ratio * 100)
                else:
                    self._service.cache.set(cache_key, response)
            else:
                self._service.cache.set(cache_key, response)
        except Exception as e:
            log.debug("Cache storage failed: %s", e)

    async def warm_cache(self, custom_prompts: list[dict[str, Any]] | None = None) -> StepResult:
        """Warm the cache with common prompts.

        Args:
            custom_prompts: Optional custom prompts to warm with

        Returns:
            StepResult with warming results
        """
        return await self._warmer.warm_cache(custom_prompts)

    def get_stats(self) -> dict[str, Any]:
        """Get enhanced cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._stats["cache_hits"] + self._stats["cache_misses"]
        hit_rate = self._stats["cache_hits"] / total_requests * 100 if total_requests > 0 else 0
        return {
            **self._stats,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "warmer_stats": self._warmer.get_stats(),
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._stats = {"cache_hits": 0, "cache_misses": 0, "compression_saves": 0, "total_compression_ratio": 0.0}
        self._warmer.reset_stats()

    async def close(self) -> None:
        """Close the enhanced cache manager."""
        await self._warmer.stop_warming()
