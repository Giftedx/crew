"""Cache warming service for proactive cache population and optimization.

This module provides intelligent cache warming strategies to improve hit rates
and reduce latency for frequently accessed data in the Ultimate Discord Intelligence Bot.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable
    from platform.cache.enhanced_redis_cache import EnhancedRedisCache


logger = logging.getLogger(__name__)
LOW_EFFICIENCY_THRESHOLD = 0.3
MEDIUM_EFFICIENCY_THRESHOLD = 0.5
HIGH_ACCESS_DIVERSITY_THRESHOLD = 10
MIN_PATTERN_LENGTH = 3
STABLE_PATTERN_LENGTH = 5
MAX_PATTERN_HISTORY = 10
PATTERN_VARIATION_THRESHOLD = 0.5


@dataclass
class AccessPattern:
    """Represents a cache access pattern with frequency and timing data."""

    key: str
    access_count: int = 0
    last_accessed: float = 0.0
    first_accessed: float = 0.0
    access_times: list[float] = field(default_factory=list)
    average_interval: float = 0.0
    peak_hour: int = 0
    weekday_pattern: dict[int, int] = field(default_factory=lambda: defaultdict(int))

    def record_access(self, timestamp: float | None = None) -> None:
        """Record a cache access event."""
        if timestamp is None:
            timestamp = time.time()
        self.access_count += 1
        self.last_accessed = timestamp
        if self.first_accessed == 0.0:
            self.first_accessed = timestamp
        self.access_times.append(timestamp)
        dt = datetime.fromtimestamp(timestamp)
        self.peak_hour = dt.hour
        self.weekday_pattern[dt.weekday()] += 1
        if len(self.access_times) > 1:
            intervals = [self.access_times[i] - self.access_times[i - 1] for i in range(1, len(self.access_times))]
            self.average_interval = sum(intervals) / len(intervals)

    def get_access_frequency(self) -> float:
        """Calculate access frequency (accesses per hour)."""
        if self.first_accessed == 0.0:
            return 0.0
        time_span = self.last_accessed - self.first_accessed
        if time_span <= 0:
            return 0.0
        return self.access_count / time_span * 3600

    def get_recency_score(self) -> float:
        """Calculate recency score (0-1, higher = more recent)."""
        if self.last_accessed == 0.0:
            return 0.0
        hours_since_last_access = (time.time() - self.last_accessed) / 3600
        return 2 ** (-hours_since_last_access / 24)

    def get_popularity_score(self) -> float:
        """Calculate popularity score based on access patterns."""
        frequency = self.get_access_frequency()
        recency = self.get_recency_score()
        return frequency * 0.7 + recency * 0.3


class AccessPatternTracker:
    """Tracks and analyzes cache access patterns for intelligent warming."""

    def __init__(self, max_patterns: int = 10000):
        self.max_patterns = max_patterns
        self.patterns: dict[str, AccessPattern] = {}
        self.key_cache_map: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def record_access(self, cache_name: str, key: str, timestamp: float | None = None) -> None:
        """Record a cache access for pattern analysis."""
        async with self._lock:
            pattern_key = f"{cache_name}:{key}"
            if pattern_key not in self.patterns:
                if len(self.patterns) >= self.max_patterns:
                    oldest_key = min(self.patterns.keys(), key=lambda k: self.patterns[k].last_accessed)
                    del self.patterns[oldest_key]
                self.patterns[pattern_key] = AccessPattern(key=key)
                self.key_cache_map[key] = cache_name
            self.patterns[pattern_key].record_access(timestamp)

    async def get_top_patterns(self, cache_name: str, limit: int = 50) -> list[AccessPattern]:
        """Get top access patterns for a specific cache."""
        async with self._lock:
            cache_patterns = [
                pattern for pattern_key, pattern in self.patterns.items() if pattern_key.startswith(f"{cache_name}:")
            ]
            cache_patterns.sort(key=lambda p: p.get_popularity_score(), reverse=True)
            return cache_patterns[:limit]

    async def get_predictive_candidates(self, cache_name: str, min_access_count: int = 5) -> list[str]:
        """Get keys that should be predictively warmed based on patterns."""
        async with self._lock:
            candidates = []
            for pattern_key, pattern in self.patterns.items():
                if not pattern_key.startswith(f"{cache_name}:"):
                    continue
                if pattern.access_count >= min_access_count:
                    hours_since_last = (time.time() - pattern.last_accessed) / 3600
                    if hours_since_last <= pattern.average_interval / 3600:
                        candidates.append(pattern.key)
            return candidates[:100]

    async def cleanup_old_patterns(self, max_age_days: int = 30) -> int:
        """Remove patterns older than specified age."""
        async with self._lock:
            cutoff_time = time.time() - max_age_days * 24 * 3600
            old_keys = [key for key, pattern in self.patterns.items() if pattern.last_accessed < cutoff_time]
            for key in old_keys:
                del self.patterns[key]
            removed_count = len(old_keys)
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old access patterns")
            return removed_count


class CacheWarmer:
    """Intelligent cache warming service with predictive loading strategies."""

    def __init__(self, cache: EnhancedRedisCache, warm_interval_hours: int = 6) -> None:
        self.cache = cache
        self.warm_interval_hours = warm_interval_hours
        self._warming_task: asyncio.Task[None] | None = None
        self._shutdown_event = asyncio.Event()

    async def start_warming_cycle(self) -> None:
        """Start the periodic cache warming cycle."""
        if self._warming_task is not None:
            logger.warning("Cache warming already running")
            return
        self._shutdown_event.clear()
        self._warming_task = asyncio.create_task(self._warming_loop())
        logger.info(f"Cache warming cycle started with {self.warm_interval_hours}h interval")

    async def stop_warming_cycle(self) -> None:
        """Stop the periodic cache warming cycle."""
        if self._warming_task is None:
            return
        self._shutdown_event.set()
        await self._warming_task
        self._warming_task = None
        logger.info("Cache warming cycle stopped")

    async def _warming_loop(self) -> None:
        """Main warming loop that runs periodically."""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_cache_warming()
                await asyncio.sleep(self.warm_interval_hours * 3600)
            except Exception as e:
                logger.error(f"Cache warming cycle error: {e}")
                await asyncio.sleep(300)

    async def _perform_cache_warming(self) -> None:
        """Perform intelligent cache warming based on access patterns."""
        try:
            frequent_keys = self.cache.get_frequent_keys(limit=50)
            if not frequent_keys:
                logger.debug("No frequent keys found for cache warming")
                return
            logger.info(f"Found {len(frequent_keys)} frequently accessed keys for warming")
            for key, access_count in frequent_keys[:10]:
                logger.debug(f"Would warm cache for key '{key}' (accessed {access_count} times)")
            efficiency = self.cache.get_cache_efficiency_score()
            logger.info(f"Current cache efficiency score: {efficiency:.2f}")
            if efficiency < MEDIUM_EFFICIENCY_THRESHOLD:
                logger.warning(f"Low cache efficiency detected: {efficiency:.2f}")
        except Exception as e:
            logger.error(f"Failed to perform cache warming: {e}")

    async def warm_specific_keys(
        self, keys: list[str], data_fetcher: Callable[[str], dict[str, Any] | None], batch_size: int = 10
    ) -> int:
        """Warm cache with specific keys using provided data fetcher.

        Args:
            keys: List of keys to warm
            data_fetcher: Function to fetch data for each key
            batch_size: Number of keys to warm in each batch

        Returns:
            Total number of keys successfully warmed
        """
        if not keys:
            return 0
        total_warmed = 0
        for i in range(0, len(keys), batch_size):
            batch = keys[i : i + batch_size]
            try:
                batch_warmed = self.cache.warm_cache(batch, data_fetcher)
                total_warmed += batch_warmed
                logger.debug(f"Warmed {batch_warmed}/{len(batch)} keys in batch {i // batch_size + 1}")
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Failed to warm batch {i // batch_size + 1}: {e}")
                continue
        logger.info(f"Cache warming completed: {total_warmed}/{len(keys)} keys warmed")
        return total_warmed

    def get_warming_stats(self) -> dict[str, Any]:
        """Get cache warming statistics and recommendations."""
        try:
            frequent_keys = self.cache.get_frequent_keys(limit=20)
            efficiency = self.cache.get_cache_efficiency_score()
            cache_stats = self.cache.get_stats()
            return {
                "cache_efficiency": efficiency,
                "frequent_keys_count": len(frequent_keys),
                "top_keys": frequent_keys[:5],
                "cache_stats": cache_stats,
                "recommendations": self._generate_recommendations(efficiency, frequent_keys),
            }
        except Exception as e:
            logger.error(f"Failed to get warming stats: {e}")
            return {"error": str(e)}

    def _generate_recommendations(self, efficiency: float, frequent_keys: list[tuple[str, int]]) -> list[str]:
        """Generate cache optimization recommendations."""
        recommendations = []
        if efficiency < LOW_EFFICIENCY_THRESHOLD:
            recommendations.append("Critical: Cache efficiency is very low. Consider increasing cache size or TTL.")
        elif efficiency < MEDIUM_EFFICIENCY_THRESHOLD:
            recommendations.append("Warning: Cache efficiency could be improved. Review frequently missed keys.")
        if len(frequent_keys) > HIGH_ACCESS_DIVERSITY_THRESHOLD:
            recommendations.append(
                f"High access pattern diversity detected ({len(frequent_keys)} keys). Consider cache warming for top keys."
            )
        if len(frequent_keys) == 0:
            recommendations.append("No access patterns detected. Enable access tracking for better cache optimization.")
        return recommendations


class PredictiveCacheWarmer(CacheWarmer):
    """Advanced cache warmer with predictive loading based on usage patterns."""

    def __init__(
        self, cache: EnhancedRedisCache, warm_interval_hours: int = 4, prediction_window_hours: int = 24
    ) -> None:
        super().__init__(cache, warm_interval_hours)
        self.prediction_window_hours = prediction_window_hours
        self._usage_patterns: dict[str, list[int]] = {}

    async def _perform_cache_warming(self) -> None:
        """Perform predictive cache warming based on historical patterns."""
        try:
            await self._analyze_usage_patterns()
            frequent_keys = self.cache.get_frequent_keys(limit=100)
            if not frequent_keys:
                logger.debug("No frequent keys found for predictive warming")
                return
            predicted_keys = self._predict_needed_keys(frequent_keys)
            logger.info(f"Predictive warming: {len(predicted_keys)} keys predicted for future access")
            efficiency = self.cache.get_cache_efficiency_score()
            predictive_score = self._calculate_predictive_score(frequent_keys)
            logger.info(f"Cache efficiency: {efficiency:.2f}, Predictive score: {predictive_score:.2f}")
        except Exception as e:
            logger.error(f"Failed to perform predictive cache warming: {e}")

    async def _analyze_usage_patterns(self) -> None:
        """Analyze historical usage patterns for prediction."""
        try:
            frequent_keys = self.cache.get_frequent_keys(limit=50)
            for key, count in frequent_keys:
                if key not in self._usage_patterns:
                    self._usage_patterns[key] = []
                self._usage_patterns[key].append(count)
                if len(self._usage_patterns[key]) > MAX_PATTERN_HISTORY:
                    self._usage_patterns[key] = self._usage_patterns[key][-MAX_PATTERN_HISTORY:]
        except Exception as e:
            logger.error(f"Failed to analyze usage patterns: {e}")

    def _predict_needed_keys(self, frequent_keys: list[tuple[str, int]]) -> list[str]:
        """Predict which keys will be needed based on patterns."""
        predicted = []
        for key, current_count in frequent_keys:
            if key in self._usage_patterns and len(self._usage_patterns[key]) >= MIN_PATTERN_LENGTH:
                recent_counts = self._usage_patterns[key][-MIN_PATTERN_LENGTH:]
                avg_recent = sum(recent_counts) / len(recent_counts)
                if current_count > avg_recent * 1.2:
                    predicted.append(key)
        return predicted[:20]

    def _calculate_predictive_score(self, frequent_keys: list[tuple[str, int]]) -> float:
        """Calculate predictive cache score based on pattern stability."""
        if not frequent_keys:
            return 0.0
        stable_patterns = 0
        for key, _ in frequent_keys[:20]:
            if key in self._usage_patterns and len(self._usage_patterns[key]) >= STABLE_PATTERN_LENGTH:
                counts = self._usage_patterns[key]
                avg = sum(counts) / len(counts)
                variance = sum((x - avg) ** 2 for x in counts) / len(counts)
                cv = variance**0.5 / avg if avg > 0 else 1.0
                if cv < PATTERN_VARIATION_THRESHOLD:
                    stable_patterns += 1
        return stable_patterns / min(20, len(frequent_keys))


class StartupCacheWarmer:
    """Handles cache warming on application startup to reduce cold start latency."""

    def __init__(self):
        self.warmers: dict[str, Callable[[], int]] = {}
        self._is_warming = False

    def register_warmer(self, cache_name: str, warmer_func: Callable[[], int]) -> None:
        """Register a cache warmer function for a specific cache type."""
        self.warmers[cache_name] = warmer_func
        logger.info(f"Registered startup warmer for {cache_name} cache")

    async def warm_all_caches(self, max_concurrent: int = 3) -> dict[str, int]:
        """Warm all registered caches concurrently with limited concurrency."""
        if self._is_warming:
            logger.warning("Startup warming already in progress")
            return {}
        self._is_warming = True
        try:
            results = {}
            warmer_items = list(self.warmers.items())
            for i in range(0, len(warmer_items), max_concurrent):
                batch = warmer_items[i : i + max_concurrent]
                tasks = []
                for cache_name, warmer_func in batch:
                    task = asyncio.create_task(self._warm_single_cache(cache_name, warmer_func))
                    tasks.append(task)
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                for (cache_name, _), result in zip(batch, batch_results, strict=False):
                    if isinstance(result, Exception):
                        logger.error(f"Failed to warm {cache_name} cache: {result}")
                        results[cache_name] = 0
                    elif isinstance(result, int):
                        results[cache_name] = result
                    else:
                        try:
                            results[cache_name] = int(float(result))
                        except Exception:
                            results[cache_name] = 0
            total_warmed = sum(results.values())
            logger.info(f"Startup cache warming completed: {total_warmed} total entries warmed")
            return results
        finally:
            self._is_warming = False

    async def _warm_single_cache(self, cache_name: str, warmer_func: Callable[[], int]) -> int:
        """Warm a single cache with error handling."""
        try:
            logger.info(f"Starting startup warming for {cache_name} cache")
            warmed_count = warmer_func()
            logger.info(f"Completed startup warming for {cache_name} cache: {warmed_count} entries")
            return warmed_count
        except Exception as e:
            logger.error(f"Error during startup warming of {cache_name} cache: {e}")
            return 0


_startup_warmer = StartupCacheWarmer()
_access_tracker = AccessPatternTracker()


def get_startup_warmer() -> StartupCacheWarmer:
    """Get the global startup cache warmer instance."""
    return _startup_warmer


def get_access_tracker() -> AccessPatternTracker:
    """Get the global access pattern tracker instance."""
    return _access_tracker
