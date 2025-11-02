"""
Cache monitoring and metrics integration layer.

This module provides comprehensive monitoring for cache systems, integrating with
the existing Prometheus metrics infrastructure to track cache performance,
health, and usage patterns.
"""
from __future__ import annotations
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any
from platform.observability.metrics import CACHE_COMPRESSION_RATIO, CACHE_COMPRESSIONS, CACHE_DECOMPRESSIONS, CACHE_DEMOTIONS, CACHE_ENTRIES_COUNT, CACHE_ERRORS, CACHE_EVICTIONS, CACHE_HIT_RATE_RATIO, CACHE_HITS, CACHE_MISSES, CACHE_OPERATION_LATENCY, CACHE_PROMOTIONS, CACHE_SIZE_BYTES, label_ctx
logger = logging.getLogger(__name__)

class CacheMonitor:
    """Monitoring facade for cache performance and health tracking."""

    def __init__(self, cache_name: str, enable_monitoring: bool=True, enable_latency_tracking: bool=True, enable_health_checks: bool=True):
        self.cache_name = cache_name
        self.enable_monitoring = enable_monitoring
        self.enable_latency_tracking = enable_latency_tracking
        self.enable_health_checks = enable_health_checks
        self._labels = label_ctx()

    @asynccontextmanager
    async def track_operation(self, operation: str, cache_level: str='unknown'):
        """Context manager to track cache operation latency and errors."""
        if not self.enable_monitoring:
            async with _null_context():
                yield
            return
        start_time = time.time()
        error_type = None
        try:
            async with _null_context():
                yield
        except Exception as e:
            error_type = type(e).__name__
            raise
        finally:
            if self.enable_latency_tracking:
                duration_ms = (time.time() - start_time) * 1000
                labels = {**self._labels, 'cache_name': self.cache_name, 'operation': operation}
                CACHE_OPERATION_LATENCY.labels(**labels).observe(duration_ms)
            if error_type:
                error_labels = {**self._labels, 'cache_name': self.cache_name, 'operation': operation, 'error_type': error_type}
                CACHE_ERRORS.labels(**error_labels).inc()

    def record_hit(self, cache_level: str='l1') -> None:
        """Record a cache hit."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name, 'cache_level': cache_level}
        CACHE_HITS.labels(**labels).inc()

    def record_miss(self, cache_level: str='l1') -> None:
        """Record a cache miss."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name, 'cache_level': cache_level}
        CACHE_MISSES.labels(**labels).inc()

    def record_promotion(self) -> None:
        """Record an entry promotion to higher cache level."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name}
        CACHE_PROMOTIONS.labels(**labels).inc()

    def record_demotion(self) -> None:
        """Record an entry demotion to lower cache level."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name}
        CACHE_DEMOTIONS.labels(**labels).inc()

    def record_eviction(self, cache_level: str='l1') -> None:
        """Record an entry eviction due to capacity limits."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name, 'cache_level': cache_level}
        CACHE_EVICTIONS.labels(**labels).inc()

    def record_compression(self, original_size: int, compressed_size: int) -> None:
        """Record compression operation and effectiveness."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name}
        CACHE_COMPRESSIONS.labels(**labels).inc()
        if original_size > 0:
            ratio = compressed_size / original_size
            CACHE_COMPRESSION_RATIO.labels(**labels).observe(ratio)

    def record_decompression(self) -> None:
        """Record decompression operation."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name}
        CACHE_DECOMPRESSIONS.labels(**labels).inc()

    def update_size_metrics(self, size_bytes: int, cache_level: str='l1') -> None:
        """Update cache size gauge."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name, 'cache_level': cache_level}
        CACHE_SIZE_BYTES.labels(**labels).set(size_bytes)

    def update_entries_count(self, count: int, cache_level: str='l1') -> None:
        """Update cache entries count gauge."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name, 'cache_level': cache_level}
        CACHE_ENTRIES_COUNT.labels(**labels).set(count)

    def update_hit_rate(self, hit_rate: float, cache_level: str='l1') -> None:
        """Update cache hit rate gauge (0.0-1.0)."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name, 'cache_level': cache_level}
        CACHE_HIT_RATE_RATIO.labels(**labels).set(hit_rate)

    def record_invalidation(self, keys_invalidated: int, reason: str='unknown') -> None:
        """Record a cache invalidation operation."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name, 'operation': f'invalidate_{reason}'}
        CACHE_OPERATION_LATENCY.labels(**labels).observe(0)
        logger.debug(f'Recorded invalidation: {keys_invalidated} keys, reason: {reason}')

    def record_dependency_graph_size(self, size: int) -> None:
        """Record the current size of the dependency graph."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name, 'cache_level': 'dependency_graph'}
        CACHE_ENTRIES_COUNT.labels(**labels).set(size)

    def record_circular_ref_detected(self) -> None:
        """Record detection of a circular dependency reference."""
        if not self.enable_monitoring:
            return
        labels = {**self._labels, 'cache_name': self.cache_name, 'operation': 'dependency_tracking', 'error_type': 'circular_reference'}
        CACHE_ERRORS.labels(**labels).inc()

    def record_invalidation_latency(self, latency_ms: float, cascade: bool=False) -> None:
        """Record the latency of an invalidation operation."""
        if not self.enable_monitoring or not self.enable_latency_tracking:
            return
        operation = 'invalidate_cascade' if cascade else 'invalidate_single'
        labels = {**self._labels, 'cache_name': self.cache_name, 'operation': operation}
        CACHE_OPERATION_LATENCY.labels(**labels).observe(latency_ms)

    def get_health_status(self) -> dict[str, Any]:
        """Get cache health status information."""
        if not self.enable_health_checks:
            return {'status': 'monitoring_disabled'}
        return {'cache_name': self.cache_name, 'monitoring_enabled': self.enable_monitoring, 'latency_tracking_enabled': self.enable_latency_tracking, 'health_checks_enabled': self.enable_health_checks, 'status': 'healthy'}

class CacheMonitorManager:
    """Global manager for cache monitors."""

    def __init__(self):
        self._monitors: dict[str, CacheMonitor] = {}
        self._lock = asyncio.Lock()

    async def get_monitor(self, cache_name: str, enable_monitoring: bool=True, **kwargs) -> CacheMonitor:
        """Get or create a cache monitor for the given cache name."""
        async with self._lock:
            if cache_name not in self._monitors:
                self._monitors[cache_name] = CacheMonitor(cache_name=cache_name, enable_monitoring=enable_monitoring, **kwargs)
            return self._monitors[cache_name]

    def get_all_monitors(self) -> dict[str, CacheMonitor]:
        """Get all registered cache monitors."""
        return self._monitors.copy()

    async def cleanup_monitor(self, cache_name: str) -> None:
        """Remove a cache monitor."""
        async with self._lock:
            if cache_name in self._monitors:
                del self._monitors[cache_name]

    def get_health_overview(self) -> dict[str, Any]:
        """Get health overview for all monitored caches."""
        overview = {}
        for name, monitor in self._monitors.items():
            overview[name] = monitor.get_health_status()
        return overview
_monitor_manager = CacheMonitorManager()

async def get_cache_monitor(cache_name: str, enable_monitoring: bool=True, **kwargs) -> CacheMonitor:
    """Get a cache monitor instance for the given cache name."""
    return await _monitor_manager.get_monitor(cache_name=cache_name, enable_monitoring=enable_monitoring, **kwargs)

def get_cache_health_overview() -> dict[str, Any]:
    """Get health overview for all monitored caches."""
    return _monitor_manager.get_health_overview()

@asynccontextmanager
async def _null_context():
    """Null context manager for when monitoring is disabled."""
    yield
__all__ = ['CacheMonitor', 'CacheMonitorManager', 'get_cache_health_overview', 'get_cache_monitor']