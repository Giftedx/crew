"""
Metrics collection for SLO monitoring.

This module provides metrics collection capabilities for monitoring
Service Level Objectives (SLOs) with both simple and Prometheus-style metrics.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


try:
    from prometheus_client import Counter, Gauge, generate_latest
    from prometheus_client import Histogram as PrometheusHistogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Create dummy classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def inc(self, amount=1):
            pass

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def set(self, value):
            pass

    class PrometheusHistogram:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def observe(self, value):
            pass

    def generate_latest():
        return b""


from .slo import SLO, SLOEvaluator


@dataclass
class MetricPoint:
    """A single metric measurement point."""

    name: str
    value: float
    timestamp: float
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class HistogramBucket:
    """Histogram bucket for latency measurements."""

    le: float  # less than or equal
    count: int


@dataclass
class Histogram:
    """Histogram for latency and duration metrics."""

    name: str
    buckets: list[HistogramBucket]
    count: int
    sum: float
    labels: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Simple in-memory metrics collector for SLO monitoring."""

    def __init__(self):
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = defaultdict(float)
        self.histograms: dict[str, list[float]] = defaultdict(list)
        self.start_times: dict[str, float] = {}

    def increment_counter(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        self.counters[key] += value

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge metric value."""
        key = self._make_key(name, labels)
        self.gauges[key] = value

    def observe_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record a histogram observation."""
        key = self._make_key(name, labels)
        self.histograms[key].append(value)

    def start_timer(self, name: str, labels: dict[str, str] | None = None) -> str:
        """Start a timer and return a timer ID."""
        timer_id = f"{name}_{int(time.time() * 1000000)}"
        self.start_times[timer_id] = time.time()
        return timer_id

    def stop_timer(self, timer_id: str, name: str, labels: dict[str, str] | None = None) -> float:
        """Stop a timer and record the duration."""
        if timer_id not in self.start_times:
            return 0.0

        duration = time.time() - self.start_times[timer_id]
        del self.start_times[timer_id]
        self.observe_histogram(name, duration, labels)
        return duration

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> float:
        """Get counter value."""
        key = self._make_key(name, labels)
        return self.counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: dict[str, str] | None = None) -> float:
        """Get gauge value."""
        key = self._make_key(name, labels)
        return self.gauges.get(key, 0.0)

    def get_histogram_quantile(self, name: str, quantile: float, labels: dict[str, str] | None = None) -> float:
        """Get histogram quantile value."""
        key = self._make_key(name, labels)
        values = self.histograms.get(key, [])
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(quantile * (len(sorted_values) - 1))
        return sorted_values[index]

    def get_histogram_sum(self, name: str, labels: dict[str, str] | None = None) -> float:
        """Get histogram sum."""
        key = self._make_key(name, labels)
        return sum(self.histograms.get(key, []))

    def get_histogram_count(self, name: str, labels: dict[str, str] | None = None) -> int:
        """Get histogram count."""
        key = self._make_key(name, labels)
        return len(self.histograms.get(key, []))

    def _make_key(self, name: str, labels: dict[str, str] | None) -> str:
        """Create a key for metric storage."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def reset(self) -> None:
        """Reset all metrics."""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.start_times.clear()


class SLOMonitor:
    """SLO monitoring and evaluation."""

    def __init__(self, slos: list[SLO]):
        self.slos = slos
        self.evaluator = SLOEvaluator(slos)
        self.metrics = MetricsCollector()

    def record_request(self, endpoint: str, duration: float, status_code: int) -> None:
        """Record a request metric."""
        labels = {"endpoint": endpoint, "status": str(status_code)}

        # Record request count
        self.metrics.increment_counter("requests_total", labels=labels)

        # Record duration
        self.metrics.observe_histogram("request_duration_seconds", duration, labels=labels)

        # Record error if applicable
        if status_code >= 400:
            self.metrics.increment_counter("request_errors_total", labels=labels)

    def record_cache_operation(self, operation: str, hit: bool) -> None:
        """Record cache operation metrics."""
        labels = {"operation": operation}

        if hit:
            self.metrics.increment_counter("cache_hits_total", labels=labels)
        else:
            self.metrics.increment_counter("cache_misses_total", labels=labels)

    def record_vector_search(self, duration: float, results_count: int) -> None:
        """Record vector search metrics."""
        labels = {"operation": "vector_search"}
        self.metrics.observe_histogram("vector_search_duration_seconds", duration, labels=labels)
        self.metrics.set_gauge("vector_search_results_count", float(results_count), labels=labels)

    def evaluate_slos(self) -> dict[str, Any]:
        """Evaluate current metrics against SLOs."""
        # Calculate current metric values
        current_metrics = {}

        # Calculate error rate
        total_requests = self.metrics.get_counter("requests_total")
        error_requests = self.metrics.get_counter("request_errors_total")
        error_rate = error_requests / total_requests if total_requests > 0 else 0.0
        current_metrics["error_rate"] = error_rate

        # Calculate P95 latency
        p95_latency = self.metrics.get_histogram_quantile("request_duration_seconds", 0.95)
        current_metrics["p95_latency"] = p95_latency

        # Calculate cache hit rate
        cache_hits = self.metrics.get_counter("cache_hits_total")
        cache_misses = self.metrics.get_counter("cache_misses_total")
        cache_hit_rate = cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0.0
        current_metrics["cache_hit_rate"] = cache_hit_rate

        # Calculate vector search latency
        vector_search_latency = self.metrics.get_histogram_quantile("vector_search_duration_seconds", 0.95)
        current_metrics["vector_search_latency"] = vector_search_latency

        # Evaluate SLOs
        slo_results = self.evaluator.evaluate(current_metrics)

        return {
            "metrics": current_metrics,
            "slo_results": slo_results,
            "timestamp": time.time(),
        }

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get a summary of current metrics."""
        return {
            "counters": dict(self.metrics.counters),
            "gauges": dict(self.metrics.gauges),
            "histogram_counts": {k: len(v) for k, v in self.metrics.histograms.items()},
            "slo_evaluation": self.evaluate_slos(),
        }


# Global metrics collector instance
_global_metrics = MetricsCollector()
_global_slo_monitor: SLOMonitor | None = None


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector."""
    return _global_metrics


def get_slo_monitor() -> SLOMonitor | None:
    """Get the global SLO monitor."""
    return _global_slo_monitor


def initialize_slo_monitoring(slos: list[SLO]) -> SLOMonitor:
    """Initialize global SLO monitoring."""
    global _global_slo_monitor
    _global_slo_monitor = SLOMonitor(slos)
    return _global_slo_monitor


def record_request(endpoint: str, duration: float, status_code: int) -> None:
    """Record a request metric using global monitor."""
    if _global_slo_monitor:
        _global_slo_monitor.record_request(endpoint, duration, status_code)


def record_cache_operation(operation: str, hit: bool) -> None:
    """Record cache operation using global monitor."""
    if _global_slo_monitor:
        _global_slo_monitor.record_cache_operation(operation, hit)


def record_vector_search(duration: float, results_count: int) -> None:
    """Record vector search using global monitor."""
    if _global_slo_monitor:
        _global_slo_monitor.record_vector_search(duration, results_count)


# Prometheus-style metrics (if available)
if PROMETHEUS_AVAILABLE:
    # Request metrics
    REQUEST_COUNT = Counter("app_request_count_total", "Application Request Count", ["method", "endpoint"])
    REQUEST_LATENCY = PrometheusHistogram(
        "app_request_latency_seconds",
        "Request latency in seconds",
        ["method", "endpoint"],
    )
    IN_PROGRESS_REQUESTS = Gauge("app_in_progress_requests", "In-progress requests", ["method", "endpoint"])
    ERROR_COUNT = Counter(
        "app_error_count_total",
        "Application Error Count",
        ["method", "endpoint", "error_type"],
    )

    # Cache metrics
    CACHE_HIT_COUNT = Counter("app_cache_hit_count_total", "Cache Hit Count", ["cache_name"])
    CACHE_MISS_COUNT = Counter("app_cache_miss_count_total", "Cache Miss Count", ["cache_name"])

    # Vector search metrics
    VECTOR_SEARCH_LATENCY = PrometheusHistogram(
        "app_vector_search_latency_seconds",
        "Vector search latency in seconds",
        ["operation"],
    )
    VECTOR_SEARCH_COUNT = Counter("app_vector_search_count_total", "Vector search count", ["operation"])
    VECTOR_SEARCH_ERROR_COUNT = Counter(
        "app_vector_search_error_count_total",
        "Vector search error count",
        ["operation"],
    )

    # Model routing metrics
    MODEL_ROUTING_COUNT = Counter("app_model_routing_count_total", "Model routing count", ["model", "provider"])
    MODEL_ROUTING_LATENCY = PrometheusHistogram(
        "app_model_routing_latency_seconds",
        "Model routing latency in seconds",
        ["model", "provider"],
    )
    MODEL_ROUTING_ERROR_COUNT = Counter(
        "app_model_routing_error_count_total",
        "Model routing error count",
        ["model", "provider"],
    )

    # OAuth metrics
    OAUTH_TOKEN_REFRESH_COUNT = Counter(
        "app_oauth_token_refresh_count_total", "OAuth token refresh count", ["platform"]
    )
    OAUTH_TOKEN_REFRESH_ERROR_COUNT = Counter(
        "app_oauth_token_refresh_error_count_total",
        "OAuth token refresh error count",
        ["platform"],
    )
    OAUTH_TOKEN_REFRESH_LATENCY = PrometheusHistogram(
        "app_oauth_token_refresh_latency_seconds",
        "OAuth token refresh latency in seconds",
        ["platform"],
    )

    # Content ingestion metrics
    CONTENT_INGESTION_COUNT = Counter(
        "app_content_ingestion_count_total",
        "Content ingestion count",
        ["platform", "content_type"],
    )
    CONTENT_INGESTION_ERROR_COUNT = Counter(
        "app_content_ingestion_error_count_total",
        "Content ingestion error count",
        ["platform", "content_type"],
    )
    CONTENT_INGESTION_LATENCY = PrometheusHistogram(
        "app_content_ingestion_latency_seconds",
        "Content ingestion latency in seconds",
        ["platform", "content_type"],
    )

    # Content analysis metrics
    CONTENT_ANALYSIS_COUNT = Counter("app_content_analysis_count_total", "Content analysis count", ["analysis_type"])
    CONTENT_ANALYSIS_ERROR_COUNT = Counter(
        "app_content_analysis_error_count_total",
        "Content analysis error count",
        ["analysis_type"],
    )
    CONTENT_ANALYSIS_LATENCY = PrometheusHistogram(
        "app_content_analysis_latency_seconds",
        "Content analysis latency in seconds",
        ["analysis_type"],
    )

    # Discord metrics
    DISCORD_MESSAGE_COUNT = Counter("app_discord_message_count_total", "Discord message count", ["message_type"])
    DISCORD_MESSAGE_ERROR_COUNT = Counter(
        "app_discord_message_error_count_total",
        "Discord message error count",
        ["message_type"],
    )
    DISCORD_MESSAGE_LATENCY = PrometheusHistogram(
        "app_discord_message_latency_seconds",
        "Discord message latency in seconds",
        ["message_type"],
    )

    # Memory metrics
    MEMORY_STORE_COUNT = Counter("app_memory_store_count_total", "Memory store count", ["store_type"])
    MEMORY_STORE_ERROR_COUNT = Counter("app_memory_store_error_count_total", "Memory store error count", ["store_type"])
    MEMORY_STORE_LATENCY = PrometheusHistogram(
        "app_memory_store_latency_seconds",
        "Memory store latency in seconds",
        ["store_type"],
    )
    MEMORY_RETRIEVAL_COUNT = Counter("app_memory_retrieval_count_total", "Memory retrieval count", ["store_type"])
    MEMORY_RETRIEVAL_ERROR_COUNT = Counter(
        "app_memory_retrieval_error_count_total",
        "Memory retrieval error count",
        ["store_type"],
    )
    MEMORY_RETRIEVAL_LATENCY = PrometheusHistogram(
        "app_memory_retrieval_latency_seconds",
        "Memory retrieval latency in seconds",
        ["store_type"],
    )

    # MCP tool metrics
    MCP_TOOL_CALL_COUNT = Counter("app_mcp_tool_call_count_total", "MCP tool call count", ["tool_name"])
    MCP_TOOL_CALL_ERROR_COUNT = Counter(
        "app_mcp_tool_call_error_count_total",
        "MCP tool call error count",
        ["tool_name"],
    )
    MCP_TOOL_CALL_LATENCY = PrometheusHistogram(
        "app_mcp_tool_call_latency_seconds",
        "MCP tool call latency in seconds",
        ["tool_name"],
    )

    def get_metrics_data() -> bytes:
        """Returns the latest metrics data in Prometheus text format."""
        return generate_latest()
else:
    # Dummy metrics when Prometheus is not available
    REQUEST_COUNT = Counter()
    REQUEST_LATENCY = PrometheusHistogram()
    IN_PROGRESS_REQUESTS = Gauge()
    ERROR_COUNT = Counter()
    CACHE_HIT_COUNT = Counter()
    CACHE_MISS_COUNT = Counter()
    VECTOR_SEARCH_LATENCY = PrometheusHistogram()
    VECTOR_SEARCH_COUNT = Counter()
    VECTOR_SEARCH_ERROR_COUNT = Counter()
    MODEL_ROUTING_COUNT = Counter()
    MODEL_ROUTING_LATENCY = PrometheusHistogram()
    MODEL_ROUTING_ERROR_COUNT = Counter()
    OAUTH_TOKEN_REFRESH_COUNT = Counter()
    OAUTH_TOKEN_REFRESH_ERROR_COUNT = Counter()
    OAUTH_TOKEN_REFRESH_LATENCY = PrometheusHistogram()
    CONTENT_INGESTION_COUNT = Counter()
    CONTENT_INGESTION_ERROR_COUNT = Counter()
    CONTENT_INGESTION_LATENCY = PrometheusHistogram()
    CONTENT_ANALYSIS_COUNT = Counter()
    CONTENT_ANALYSIS_ERROR_COUNT = Counter()
    CONTENT_ANALYSIS_LATENCY = PrometheusHistogram()
    DISCORD_MESSAGE_COUNT = Counter()
    DISCORD_MESSAGE_ERROR_COUNT = Counter()
    DISCORD_MESSAGE_LATENCY = PrometheusHistogram()
    MEMORY_STORE_COUNT = Counter()
    MEMORY_STORE_ERROR_COUNT = Counter()
    MEMORY_STORE_LATENCY = PrometheusHistogram()
    MEMORY_RETRIEVAL_COUNT = Counter()
    MEMORY_RETRIEVAL_ERROR_COUNT = Counter()
    MEMORY_RETRIEVAL_LATENCY = PrometheusHistogram()
    MCP_TOOL_CALL_COUNT = Counter()
    MCP_TOOL_CALL_ERROR_COUNT = Counter()
    MCP_TOOL_CALL_LATENCY = PrometheusHistogram()

    def get_metrics_data() -> bytes:
        """Returns empty metrics data when Prometheus is not available."""
        return b""


__all__ = [
    "CACHE_HIT_COUNT",
    "CACHE_MISS_COUNT",
    "CONTENT_ANALYSIS_COUNT",
    "CONTENT_ANALYSIS_ERROR_COUNT",
    "CONTENT_ANALYSIS_LATENCY",
    "CONTENT_INGESTION_COUNT",
    "CONTENT_INGESTION_ERROR_COUNT",
    "CONTENT_INGESTION_LATENCY",
    "DISCORD_MESSAGE_COUNT",
    "DISCORD_MESSAGE_ERROR_COUNT",
    "DISCORD_MESSAGE_LATENCY",
    "ERROR_COUNT",
    "IN_PROGRESS_REQUESTS",
    "MCP_TOOL_CALL_COUNT",
    "MCP_TOOL_CALL_ERROR_COUNT",
    "MCP_TOOL_CALL_LATENCY",
    "MEMORY_RETRIEVAL_COUNT",
    "MEMORY_RETRIEVAL_ERROR_COUNT",
    "MEMORY_RETRIEVAL_LATENCY",
    "MEMORY_STORE_COUNT",
    "MEMORY_STORE_ERROR_COUNT",
    "MEMORY_STORE_LATENCY",
    "MODEL_ROUTING_COUNT",
    "MODEL_ROUTING_ERROR_COUNT",
    "MODEL_ROUTING_LATENCY",
    "OAUTH_TOKEN_REFRESH_COUNT",
    "OAUTH_TOKEN_REFRESH_ERROR_COUNT",
    "OAUTH_TOKEN_REFRESH_LATENCY",
    # Prometheus metrics
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "VECTOR_SEARCH_COUNT",
    "VECTOR_SEARCH_ERROR_COUNT",
    "VECTOR_SEARCH_LATENCY",
    "Histogram",
    "MetricPoint",
    "MetricsCollector",
    "SLOMonitor",
    "get_metrics",
    "get_metrics_data",
    "get_slo_monitor",
    "initialize_slo_monitoring",
    "record_cache_operation",
    "record_request",
    "record_vector_search",
]

# Content Moderation Metrics
MODERATION_CHECKS_COUNT = Counter("moderation_checks_total", "Content Moderation Checks", ["category", "action"])
MODERATION_BLOCKS_COUNT = Counter("moderation_blocks_total", "Content Blocked by Moderation", ["category"])
MODERATION_LATENCY = (
    PrometheusHistogram("moderation_latency_seconds", "Moderation check latency in seconds", ["provider"])
    if PROMETHEUS_AVAILABLE
    else None
)
