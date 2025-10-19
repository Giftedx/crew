"""
Advanced metrics collection system for the Ultimate Discord Intelligence Bot.

Provides comprehensive metrics collection with multiple backends, aggregation,
and real-time monitoring capabilities for production observability.
"""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics supported."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"


class MetricBackend(Enum):
    """Available metric backends."""

    MEMORY = "memory"
    PROMETHEUS = "prometheus"
    INFLUXDB = "influxdb"
    CUSTOM = "custom"


class AggregationType(Enum):
    """Types of aggregations for metrics."""

    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"


@dataclass
class MetricConfig:
    """Configuration for a specific metric."""

    name: str
    metric_type: MetricType
    description: str = ""
    labels: dict[str, str] = field(default_factory=dict)
    unit: str = ""
    aggregation_type: AggregationType = AggregationType.SUM
    retention_period: float = 3600.0  # seconds
    max_samples: int = 10000


@dataclass
class MetricValue:
    """A single metric value with metadata."""

    value: float
    timestamp: float
    labels: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class MetricData:
    """Collection of metric values for a specific metric."""

    config: MetricConfig
    values: deque[MetricValue] = field(default_factory=lambda: deque(maxlen=10000))
    aggregated_value: float = 0.0
    last_update: float = 0.0

    def add_value(
        self, value: float, labels: dict[str, str] | None = None, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add a new value to the metric."""
        metric_value = MetricValue(
            value=value,
            timestamp=time.time(),
            labels=labels or {},
            metadata=metadata or {},
        )
        self.values.append(metric_value)
        self.last_update = metric_value.timestamp
        self._update_aggregated_value()

    def _update_aggregated_value(self) -> None:
        """Update the aggregated value based on the aggregation type."""
        if not self.values:
            self.aggregated_value = 0.0
            return

        values_list = [v.value for v in self.values]

        if self.config.aggregation_type == AggregationType.SUM:
            self.aggregated_value = sum(values_list)
        elif self.config.aggregation_type == AggregationType.AVERAGE:
            self.aggregated_value = sum(values_list) / len(values_list)
        elif self.config.aggregation_type == AggregationType.MIN:
            self.aggregated_value = min(values_list)
        elif self.config.aggregation_type == AggregationType.MAX:
            self.aggregated_value = max(values_list)
        elif self.config.aggregation_type == AggregationType.COUNT:
            self.aggregated_value = len(values_list)
        else:
            self.aggregated_value = sum(values_list) / len(values_list)  # Default to average

    def get_recent_values(self, duration: float) -> list[MetricValue]:
        """Get values from the last specified duration."""
        cutoff_time = time.time() - duration
        return [v for v in self.values if v.timestamp >= cutoff_time]

    def cleanup_old_values(self, retention_period: float) -> int:
        """Remove old values beyond retention period."""
        cutoff_time = time.time() - retention_period
        initial_count = len(self.values)

        # Remove old values
        while self.values and self.values[0].timestamp < cutoff_time:
            self.values.popleft()

        removed_count = initial_count - len(self.values)
        if removed_count > 0:
            self._update_aggregated_value()

        return removed_count


@dataclass
class MetricsCollectorConfig:
    """Configuration for the metrics collector."""

    # Backend configuration
    primary_backend: MetricBackend = MetricBackend.MEMORY
    enable_prometheus: bool = False
    enable_influxdb: bool = False

    # Collection configuration
    collection_interval: float = 1.0  # seconds
    max_metrics: int = 10000
    default_retention_period: float = 3600.0  # 1 hour

    # System metrics
    enable_system_metrics: bool = True
    system_metrics_interval: float = 5.0  # seconds

    # Export configuration
    export_interval: float = 30.0  # seconds
    enable_auto_export: bool = True

    # Performance tracking
    enable_metrics: bool = True


class MetricsCollector:
    """
    Advanced metrics collection system with multiple backends and real-time monitoring.

    Provides comprehensive metrics collection for the Ultimate Discord Intelligence Bot
    with support for counters, gauges, histograms, summaries, and timers.
    """

    def __init__(self, config: MetricsCollectorConfig | None = None):
        """Initialize metrics collector."""
        self.config = config or MetricsCollectorConfig()
        self.metrics: dict[str, MetricData] = {}
        self.system_metrics: dict[str, float] = {}

        # Backend configurations
        self.backends: dict[MetricBackend, Any] = {}
        self._initialize_backends()

        # Collection tasks
        self._collection_task: asyncio.Task[None] | None = None
        self._system_metrics_task: asyncio.Task[None] | None = None
        self._export_task: asyncio.Task[None] | None = None

        # Performance tracking
        self.total_metrics_collected: int = 0
        self.collection_start_time: float = time.time()

        logger.info(f"Metrics collector initialized with config: {self.config}")

    def _initialize_backends(self) -> None:
        """Initialize metric backends."""
        if self.config.enable_prometheus:
            try:
                from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Summary

                self.backends[MetricBackend.PROMETHEUS] = {
                    "registry": CollectorRegistry(),
                    "counters": {},
                    "gauges": {},
                    "histograms": {},
                    "summaries": {},
                }
                logger.info("Prometheus backend initialized")
            except ImportError:
                logger.warning("Prometheus client not available, skipping Prometheus backend")

        # Memory backend is always available
        self.backends[MetricBackend.MEMORY] = {"metrics": {}}

    def start_collection(self) -> None:
        """Start metrics collection."""
        if self._collection_task and not self._collection_task.done():
            logger.warning("Metrics collection already started")
            return

        # Start system metrics collection if enabled
        if self.config.enable_system_metrics:
            self._system_metrics_task = asyncio.create_task(self._collect_system_metrics())

        # Start auto-export if enabled
        if self.config.enable_auto_export:
            self._export_task = asyncio.create_task(self._auto_export_metrics())

        logger.info("Metrics collection started")

    def stop_collection(self) -> None:
        """Stop metrics collection."""
        if self._system_metrics_task:
            self._system_metrics_task.cancel()

        if self._export_task:
            self._export_task.cancel()

        logger.info("Metrics collection stopped")

    async def _collect_system_metrics(self) -> None:
        """Collect system metrics periodically."""
        while True:
            try:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                self.system_metrics["cpu_percent"] = cpu_percent

                # Memory metrics
                memory = psutil.virtual_memory()
                self.system_metrics["memory_percent"] = memory.percent
                self.system_metrics["memory_available_gb"] = memory.available / (1024**3)
                self.system_metrics["memory_used_gb"] = memory.used / (1024**3)

                # Disk metrics
                disk = psutil.disk_usage("/")
                self.system_metrics["disk_percent"] = disk.percent
                self.system_metrics["disk_free_gb"] = disk.free / (1024**3)

                # Network metrics
                network = psutil.net_io_counters()
                self.system_metrics["network_bytes_sent"] = network.bytes_sent
                self.system_metrics["network_bytes_recv"] = network.bytes_recv

                # Process metrics
                process = psutil.Process()
                self.system_metrics["process_cpu_percent"] = process.cpu_percent()
                self.system_metrics["process_memory_mb"] = process.memory_info().rss / (1024**2)
                self.system_metrics["process_num_threads"] = process.num_threads()

                # Record system metrics
                for metric_name, value in self.system_metrics.items():
                    self.record_gauge(f"system_{metric_name}", value, {"source": "system"})

                await asyncio.sleep(self.config.system_metrics_interval)

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(self.config.system_metrics_interval)

    async def _auto_export_metrics(self) -> None:
        """Automatically export metrics at configured intervals."""
        while True:
            try:
                await asyncio.sleep(self.config.export_interval)
                await self.export_metrics()
            except Exception as e:
                logger.error(f"Error in auto-export: {e}")

    def create_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str = "",
        labels: dict[str, str] | None = None,
        unit: str = "",
        aggregation_type: AggregationType | None = None,
        retention_period: float | None = None,
    ) -> MetricConfig:
        """Create a new metric configuration."""
        config = MetricConfig(
            name=name,
            metric_type=metric_type,
            description=description,
            labels=labels or {},
            unit=unit,
            aggregation_type=aggregation_type or AggregationType.SUM,
            retention_period=retention_period or self.config.default_retention_period,
        )

        # Initialize metric data
        self.metrics[name] = MetricData(config=config)

        # Initialize in backends
        self._initialize_metric_in_backends(config)

        logger.info(f"Created metric: {name} ({metric_type.value})")
        return config

    def _initialize_metric_in_backends(self, config: MetricConfig) -> None:
        """Initialize metric in all configured backends."""
        # Prometheus backend
        if MetricBackend.PROMETHEUS in self.backends:
            prometheus_backend = self.backends[MetricBackend.PROMETHEUS]
            registry = prometheus_backend["registry"]

            try:
                from prometheus_client import Counter, Gauge, Histogram, Summary

                if config.metric_type == MetricType.COUNTER:
                    prometheus_backend["counters"][config.name] = Counter(
                        config.name, config.description, list(config.labels.keys()), registry=registry
                    )
                elif config.metric_type == MetricType.GAUGE:
                    prometheus_backend["gauges"][config.name] = Gauge(
                        config.name, config.description, list(config.labels.keys()), registry=registry
                    )
                elif config.metric_type == MetricType.HISTOGRAM:
                    prometheus_backend["histograms"][config.name] = Histogram(
                        config.name, config.description, list(config.labels.keys()), registry=registry
                    )
                elif config.metric_type == MetricType.SUMMARY:
                    prometheus_backend["summaries"][config.name] = Summary(
                        config.name, config.description, list(config.labels.keys()), registry=registry
                    )
            except ImportError:
                pass

    def record_counter(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Record a counter metric."""
        if name not in self.metrics:
            self.create_metric(name, MetricType.COUNTER, aggregation_type=AggregationType.SUM)

        self.metrics[name].add_value(value, labels)
        self.total_metrics_collected += 1

        # Update Prometheus backend
        if MetricBackend.PROMETHEUS in self.backends and name in self.backends[MetricBackend.PROMETHEUS]["counters"]:
            counter = self.backends[MetricBackend.PROMETHEUS]["counters"][name]
            counter.labels(**(labels or {})).inc(value)

    def record_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record a gauge metric."""
        if name not in self.metrics:
            self.create_metric(name, MetricType.GAUGE, aggregation_type=AggregationType.AVERAGE)

        self.metrics[name].add_value(value, labels)
        self.total_metrics_collected += 1

        # Update Prometheus backend
        if MetricBackend.PROMETHEUS in self.backends and name in self.backends[MetricBackend.PROMETHEUS]["gauges"]:
            gauge = self.backends[MetricBackend.PROMETHEUS]["gauges"][name]
            gauge.labels(**(labels or {})).set(value)

    def record_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record a histogram metric."""
        if name not in self.metrics:
            self.create_metric(name, MetricType.HISTOGRAM, aggregation_type=AggregationType.AVERAGE)

        self.metrics[name].add_value(value, labels)
        self.total_metrics_collected += 1

        # Update Prometheus backend
        if MetricBackend.PROMETHEUS in self.backends and name in self.backends[MetricBackend.PROMETHEUS]["histograms"]:
            histogram = self.backends[MetricBackend.PROMETHEUS]["histograms"][name]
            histogram.labels(**(labels or {})).observe(value)

    def record_summary(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record a summary metric."""
        if name not in self.metrics:
            self.create_metric(name, MetricType.SUMMARY, aggregation_type=AggregationType.AVERAGE)

        self.metrics[name].add_value(value, labels)
        self.total_metrics_collected += 1

        # Update Prometheus backend
        if MetricBackend.PROMETHEUS in self.backends and name in self.backends[MetricBackend.PROMETHEUS]["summaries"]:
            summary = self.backends[MetricBackend.PROMETHEUS]["summaries"][name]
            summary.labels(**(labels or {})).observe(value)

    def record_timer(self, name: str, duration: float, labels: dict[str, str] | None = None) -> None:
        """Record a timer metric."""
        # Timer is typically implemented as a histogram
        self.record_histogram(f"{name}_duration", duration, labels)
        self.record_counter(f"{name}_count", 1.0, labels)

    def time_function(
        self, name: str, labels: dict[str, str] | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to time a function execution."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.record_timer(name, duration, labels)

            return wrapper

        return decorator

    def get_metric_value(self, name: str) -> float:
        """Get the current aggregated value for a metric."""
        if name not in self.metrics:
            return 0.0
        return self.metrics[name].aggregated_value

    def get_metric_history(self, name: str, duration: float = 300.0) -> list[MetricValue]:
        """Get metric history for the specified duration."""
        if name not in self.metrics:
            return []
        return self.metrics[name].get_recent_values(duration)

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Get all metrics with their current values."""
        return {
            name: {
                "config": {
                    "name": data.config.name,
                    "type": data.config.metric_type.value,
                    "description": data.config.description,
                    "aggregation_type": data.config.aggregation_type.value,
                },
                "current_value": data.aggregated_value,
                "last_update": data.last_update,
                "value_count": len(data.values),
            }
            for name, data in self.metrics.items()
        }

    def get_system_metrics(self) -> dict[str, float]:
        """Get current system metrics."""
        return dict(self.system_metrics)

    def cleanup_old_metrics(self) -> int:
        """Clean up old metric values based on retention periods."""
        total_removed = 0
        for metric_data in self.metrics.values():
            removed = metric_data.cleanup_old_values(metric_data.config.retention_period)
            total_removed += removed

        if total_removed > 0:
            logger.info(f"Cleaned up {total_removed} old metric values")

        return total_removed

    async def export_metrics(self) -> dict[str, Any]:
        """Export metrics to configured backends."""
        export_results = {}

        # Export to Prometheus
        if MetricBackend.PROMETHEUS in self.backends:
            try:
                prometheus_data = await self._export_to_prometheus()
                export_results["prometheus"] = prometheus_data
            except Exception as e:
                logger.error(f"Error exporting to Prometheus: {e}")
                export_results["prometheus"] = {"error": str(e)}

        # Export to InfluxDB
        if MetricBackend.INFLUXDB in self.backends:
            try:
                influxdb_data = await self._export_to_influxdb()
                export_results["influxdb"] = influxdb_data
            except Exception as e:
                logger.error(f"Error exporting to InfluxDB: {e}")
                export_results["influxdb"] = {"error": str(e)}

        return export_results

    async def _export_to_prometheus(self) -> dict[str, Any]:
        """Export metrics to Prometheus."""
        if MetricBackend.PROMETHEUS not in self.backends:
            return {"error": "Prometheus backend not configured"}

        # Prometheus metrics are already updated in real-time
        # This method could be used to generate metrics summary
        return {
            "status": "success",
            "metrics_count": len(self.metrics),
            "export_time": time.time(),
        }

    async def _export_to_influxdb(self) -> dict[str, Any]:
        """Export metrics to InfluxDB."""
        # This would implement InfluxDB export in production
        return {
            "status": "not_implemented",
            "message": "InfluxDB export not implemented",
        }

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get a summary of the metrics collection system."""
        current_time = time.time()
        uptime = current_time - self.collection_start_time

        return {
            "uptime_seconds": uptime,
            "total_metrics_collected": self.total_metrics_collected,
            "active_metrics": len(self.metrics),
            "system_metrics_enabled": self.config.enable_system_metrics,
            "collection_interval": self.config.collection_interval,
            "export_interval": self.config.export_interval,
            "backends_configured": [backend.value for backend in self.backends.keys()],
            "system_metrics": self.get_system_metrics(),
        }


# Global metrics collector instance
_global_metrics_collector: MetricsCollector | None = None


def get_global_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


def set_global_metrics_collector(collector: MetricsCollector) -> None:
    """Set the global metrics collector instance."""
    global _global_metrics_collector
    _global_metrics_collector = collector


# Convenience functions for global metrics collector
def record_counter(name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
    """Record a counter metric using the global collector."""
    get_global_metrics_collector().record_counter(name, value, labels)


def record_gauge(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    """Record a gauge metric using the global collector."""
    get_global_metrics_collector().record_gauge(name, value, labels)


def record_histogram(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    """Record a histogram metric using the global collector."""
    get_global_metrics_collector().record_histogram(name, value, labels)


def record_timer(name: str, duration: float, labels: dict[str, str] | None = None) -> None:
    """Record a timer metric using the global collector."""
    get_global_metrics_collector().record_timer(name, duration, labels)


def time_function(
    name: str, labels: dict[str, str] | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to time a function using the global collector."""
    return get_global_metrics_collector().time_function(name, labels)
