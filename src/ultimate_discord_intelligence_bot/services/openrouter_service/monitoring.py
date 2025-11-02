"""Advanced monitoring and alerting for OpenRouter service.

This module provides comprehensive monitoring, metrics collection,
and alerting capabilities for the OpenRouter service.
"""

from __future__ import annotations
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags

if TYPE_CHECKING:
    from .service import OpenRouterService
log = logging.getLogger(__name__)


@dataclass
class AlertThreshold:
    """Alert threshold configuration."""

    metric_name: str
    threshold_value: float
    comparison: str
    severity: str
    enabled: bool = True


@dataclass
class PerformanceMetrics:
    """Performance metrics container."""

    timestamp: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    throughput_rps: float
    error_rate: float
    cache_hit_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float


class MetricsCollector:
    """Collects and aggregates metrics for the OpenRouter service."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._feature_flags = FeatureFlags()
        self._metrics_history: list[PerformanceMetrics] = []
        self._max_history_size = 1000
        self._current_metrics = {
            "request_count": 0,
            "success_count": 0,
            "error_count": 0,
            "total_latency": 0.0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "start_time": time.time(),
        }
        self._latency_samples: list[float] = []
        self._max_samples = 1000

    def record_request(self, latency_ms: float, tokens: int, cost: float, success: bool, cached: bool = False) -> None:
        """Record metrics for a completed request.

        Args:
            latency_ms: Request latency in milliseconds
            tokens: Number of tokens processed
            cost: Request cost
            success: Whether the request was successful
            cached: Whether the response was cached
        """
        self._current_metrics["request_count"] += 1
        self._current_metrics["total_latency"] += latency_ms
        self._current_metrics["total_tokens"] += tokens
        self._current_metrics["total_cost"] += cost
        if success:
            self._current_metrics["success_count"] += 1
        else:
            self._current_metrics["error_count"] += 1
        if cached:
            self._current_metrics["cache_hits"] += 1
        else:
            self._current_metrics["cache_misses"] += 1
        self._latency_samples.append(latency_ms)
        if len(self._latency_samples) > self._max_samples:
            self._latency_samples.pop(0)

    def _calculate_percentile(self, values: list[float], percentile: float) -> float:
        """Calculate percentile from a list of values.

        Args:
            values: List of values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(percentile / 100 * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics.

        Returns:
            Current performance metrics
        """
        current_time = time.time()
        uptime = current_time - self._current_metrics["start_time"]
        throughput_rps = self._current_metrics["request_count"] / max(uptime, 1)
        error_rate = self._current_metrics["error_count"] / max(self._current_metrics["request_count"], 1) * 100
        total_cache_requests = self._current_metrics["cache_hits"] + self._current_metrics["cache_misses"]
        cache_hit_rate = self._current_metrics["cache_hits"] / max(total_cache_requests, 1) * 100
        latency_p50 = self._calculate_percentile(self._latency_samples, 50)
        latency_p95 = self._calculate_percentile(self._latency_samples, 95)
        latency_p99 = self._calculate_percentile(self._latency_samples, 99)
        memory_usage_mb = len(self._latency_samples) * 0.001
        cpu_usage_percent = min(100, throughput_rps * 0.1)
        return PerformanceMetrics(
            timestamp=current_time,
            latency_p50=latency_p50,
            latency_p95=latency_p95,
            latency_p99=latency_p99,
            throughput_rps=throughput_rps,
            error_rate=error_rate,
            cache_hit_rate=cache_hit_rate,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
        )

    def snapshot_metrics(self) -> None:
        """Take a snapshot of current metrics."""
        metrics = self.get_current_metrics()
        self._metrics_history.append(metrics)
        if len(self._metrics_history) > self._max_history_size:
            self._metrics_history.pop(0)

    def get_metrics_history(self, limit: int | None = None) -> list[PerformanceMetrics]:
        """Get metrics history.

        Args:
            limit: Maximum number of metrics to return

        Returns:
            List of performance metrics
        """
        if limit:
            return self._metrics_history[-limit:]
        return self._metrics_history.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._current_metrics = {
            "request_count": 0,
            "success_count": 0,
            "error_count": 0,
            "total_latency": 0.0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "start_time": time.time(),
        }
        self._latency_samples.clear()
        self._metrics_history.clear()


class AlertManager:
    """Manages alerts and notifications for the OpenRouter service."""

    def __init__(self) -> None:
        """Initialize alert manager."""
        self._feature_flags = FeatureFlags()
        self._thresholds: list[AlertThreshold] = []
        self._alert_history: list[dict[str, Any]] = []
        self._max_alert_history = 100
        self._setup_default_thresholds()

    def _setup_default_thresholds(self) -> None:
        """Setup default alert thresholds."""
        self._thresholds = [
            AlertThreshold("error_rate", 5.0, "gt", "medium"),
            AlertThreshold("error_rate", 10.0, "gt", "high"),
            AlertThreshold("error_rate", 20.0, "gt", "critical"),
            AlertThreshold("latency_p95", 5000.0, "gt", "medium"),
            AlertThreshold("latency_p95", 10000.0, "gt", "high"),
            AlertThreshold("latency_p99", 10000.0, "gt", "high"),
            AlertThreshold("latency_p99", 20000.0, "gt", "critical"),
            AlertThreshold("cache_hit_rate", 50.0, "lt", "low"),
            AlertThreshold("cache_hit_rate", 30.0, "lt", "medium"),
            AlertThreshold("throughput_rps", 0.1, "lt", "low"),
        ]

    def add_threshold(self, threshold: AlertThreshold) -> None:
        """Add a new alert threshold.

        Args:
            threshold: Alert threshold to add
        """
        self._thresholds.append(threshold)
        log.debug("Added alert threshold: %s", threshold.metric_name)

    def check_alerts(self, metrics: PerformanceMetrics) -> list[dict[str, Any]]:
        """Check metrics against alert thresholds.

        Args:
            metrics: Current performance metrics

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        for threshold in self._thresholds:
            if not threshold.enabled:
                continue
            metric_value = getattr(metrics, threshold.metric_name, None)
            if metric_value is None:
                continue
            triggered = False
            if (
                threshold.comparison == "gt"
                and metric_value > threshold.threshold_value
                or (threshold.comparison == "lt" and metric_value < threshold.threshold_value)
                or (threshold.comparison == "eq" and metric_value == threshold.threshold_value)
                or (threshold.comparison == "gte" and metric_value >= threshold.threshold_value)
                or (threshold.comparison == "lte" and metric_value <= threshold.threshold_value)
            ):
                triggered = True
            if triggered:
                alert = {
                    "timestamp": metrics.timestamp,
                    "metric_name": threshold.metric_name,
                    "metric_value": metric_value,
                    "threshold_value": threshold.threshold_value,
                    "comparison": threshold.comparison,
                    "severity": threshold.severity,
                    "message": self._generate_alert_message(threshold, metric_value),
                }
                triggered_alerts.append(alert)
                self._record_alert(alert)
                log.warning(
                    "Alert triggered: %s %s %.2f (threshold: %.2f) - %s",
                    threshold.metric_name,
                    threshold.comparison,
                    metric_value,
                    threshold.threshold_value,
                    threshold.severity,
                )
        return triggered_alerts

    def _generate_alert_message(self, threshold: AlertThreshold, value: float) -> str:
        """Generate alert message.

        Args:
            threshold: Alert threshold
            value: Current metric value

        Returns:
            Alert message
        """
        return f"{threshold.metric_name} is {threshold.comparison} {threshold.threshold_value} (current: {value:.2f}) - {threshold.severity} severity"

    def _record_alert(self, alert: dict[str, Any]) -> None:
        """Record alert in history.

        Args:
            alert: Alert to record
        """
        self._alert_history.append(alert)
        if len(self._alert_history) > self._max_alert_history:
            self._alert_history.pop(0)

    def get_alert_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get alert history.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of alerts
        """
        if limit:
            return self._alert_history[-limit:]
        return self._alert_history.copy()

    def get_thresholds(self) -> list[AlertThreshold]:
        """Get all alert thresholds.

        Returns:
            List of alert thresholds
        """
        return self._thresholds.copy()

    def clear_alert_history(self) -> None:
        """Clear alert history."""
        self._alert_history.clear()


class PerformanceMonitor:
    """Comprehensive performance monitoring for OpenRouter service."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize performance monitor.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._feature_flags = FeatureFlags()
        self._metrics_collector = MetricsCollector()
        self._alert_manager = AlertManager()
        self._monitoring_enabled = True

    def record_request_metrics(
        self, latency_ms: float, tokens: int, cost: float, success: bool, cached: bool = False
    ) -> None:
        """Record metrics for a completed request.

        Args:
            latency_ms: Request latency in milliseconds
            tokens: Number of tokens processed
            cost: Request cost
            success: Whether the request was successful
            cached: Whether the response was cached
        """
        if not self._monitoring_enabled:
            return
        self._metrics_collector.record_request(latency_ms, tokens, cost, success, cached)
        if self._metrics_collector._current_metrics["request_count"] % 10 == 0:
            self._check_alerts()

    def _check_alerts(self) -> None:
        """Check for alerts based on current metrics."""
        try:
            metrics = self._metrics_collector.get_current_metrics()
            alerts = self._alert_manager.check_alerts(metrics)
            for alert in alerts:
                if alert["severity"] == "critical":
                    log.critical("CRITICAL ALERT: %s", alert["message"])
                elif alert["severity"] == "high":
                    log.error("HIGH ALERT: %s", alert["message"])
        except Exception as e:
            log.error("Error checking alerts: %s", e)

    def get_performance_dashboard(self) -> dict[str, Any]:
        """Get comprehensive performance dashboard data.

        Returns:
            Dictionary with dashboard data
        """
        current_metrics = self._metrics_collector.get_current_metrics()
        recent_alerts = self._alert_manager.get_alert_history(limit=10)
        return {
            "current_metrics": {
                "latency_p50": current_metrics.latency_p50,
                "latency_p95": current_metrics.latency_p95,
                "latency_p99": current_metrics.latency_p99,
                "throughput_rps": current_metrics.throughput_rps,
                "error_rate": current_metrics.error_rate,
                "cache_hit_rate": current_metrics.cache_hit_rate,
                "memory_usage_mb": current_metrics.memory_usage_mb,
                "cpu_usage_percent": current_metrics.cpu_usage_percent,
            },
            "recent_alerts": recent_alerts,
            "alert_thresholds": [
                {
                    "metric_name": t.metric_name,
                    "threshold_value": t.threshold_value,
                    "comparison": t.comparison,
                    "severity": t.severity,
                    "enabled": t.enabled,
                }
                for t in self._alert_manager.get_thresholds()
            ],
            "monitoring_enabled": self._monitoring_enabled,
            "feature_flags": {
                "enable_metrics": self._feature_flags.ENABLE_METRICS,
                "enable_alerts": self._feature_flags.ENABLE_ALERTS,
            },
        }

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get metrics summary.

        Returns:
            Dictionary with metrics summary
        """
        current_metrics = self._metrics_collector.get_current_metrics()
        raw_metrics = self._metrics_collector._current_metrics
        return {
            "performance": {
                "latency_p50_ms": round(current_metrics.latency_p50, 2),
                "latency_p95_ms": round(current_metrics.latency_p95, 2),
                "latency_p99_ms": round(current_metrics.latency_p99, 2),
                "throughput_rps": round(current_metrics.throughput_rps, 2),
                "error_rate_percent": round(current_metrics.error_rate, 2),
                "cache_hit_rate_percent": round(current_metrics.cache_hit_rate, 2),
            },
            "counts": {
                "total_requests": raw_metrics["request_count"],
                "successful_requests": raw_metrics["success_count"],
                "failed_requests": raw_metrics["error_count"],
                "cache_hits": raw_metrics["cache_hits"],
                "cache_misses": raw_metrics["cache_misses"],
            },
            "totals": {
                "total_latency_ms": round(raw_metrics["total_latency"], 2),
                "total_tokens": raw_metrics["total_tokens"],
                "total_cost": round(raw_metrics["total_cost"], 4),
            },
        }

    def enable_monitoring(self) -> None:
        """Enable performance monitoring."""
        self._monitoring_enabled = True
        log.info("Performance monitoring enabled")

    def disable_monitoring(self) -> None:
        """Disable performance monitoring."""
        self._monitoring_enabled = False
        log.info("Performance monitoring disabled")

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics_collector.reset_metrics()
        self._alert_manager.clear_alert_history()
        log.info("Performance metrics reset")

    def add_alert_threshold(self, threshold: AlertThreshold) -> None:
        """Add a new alert threshold.

        Args:
            threshold: Alert threshold to add
        """
        self._alert_manager.add_threshold(threshold)

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive monitoring statistics.

        Returns:
            Dictionary with monitoring statistics
        """
        return {
            "monitoring_enabled": self._monitoring_enabled,
            "metrics_summary": self.get_metrics_summary(),
            "dashboard": self.get_performance_dashboard(),
        }


_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor(service: OpenRouterService) -> PerformanceMonitor:
    """Get or create performance monitor for the service.

    Args:
        service: The OpenRouter service instance

    Returns:
        PerformanceMonitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(service)
    return _performance_monitor


def close_performance_monitor() -> None:
    """Close the global performance monitor."""
    global _performance_monitor
    if _performance_monitor:
        _performance_monitor.disable_monitoring()
        _performance_monitor = None
