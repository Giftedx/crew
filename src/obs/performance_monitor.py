"""Performance monitoring and alerting system.

This module provides comprehensive performance monitoring, baseline validation,
and alerting capabilities for the Ultimate Discord Intelligence Bot.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any

from .performance_baselines import (
    MetricCategory,
    PerformanceBaselineConfig,
    get_current_performance_tier,
    get_performance_baselines,
)
from .resource_monitor import get_current_resource_usage

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor system performance against established baselines."""

    def __init__(self, baseline_config: PerformanceBaselineConfig | None = None):
        self.baseline_config = baseline_config or get_performance_baselines()
        self.performance_tier = get_current_performance_tier()
        self.alert_callbacks: list[callable] = []
        self.metrics_history: dict[str, list[tuple[float, float]]] = defaultdict(
            list
        )  # metric_name -> [(timestamp, value)]

        # Alert thresholds
        self.alert_cooldown_seconds = 300  # 5 minutes between similar alerts
        self.last_alert_times: dict[str, float] = {}

    def add_alert_callback(self, callback: callable) -> None:
        """Add a callback function for performance alerts."""
        self.alert_callbacks.append(callback)

    def record_metric(self, metric_name: str, value: float) -> None:
        """Record a metric value for monitoring."""
        current_time = time.time()
        self.metrics_history[metric_name].append((current_time, value))

        # Keep only last 1000 values per metric
        if len(self.metrics_history[metric_name]) > 1000:
            self.metrics_history[metric_name] = self.metrics_history[metric_name][-1000:]

        # Check against baselines and trigger alerts if needed
        self._check_baseline_and_alert(metric_name, value)

    def _check_baseline_and_alert(self, metric_name: str, value: float) -> None:
        """Check metric against baseline and trigger alerts if needed."""
        validation = self.baseline_config.validate_metric(metric_name, value)

        if not validation["valid"]:
            logger.warning(f"No baseline configured for metric: {metric_name}")
            return

        alert_level = validation["alert_level"]
        if alert_level in ["warning", "critical"]:
            self._trigger_alert(metric_name, value, validation)

    def _trigger_alert(self, metric_name: str, value: float, validation: dict[str, Any]) -> None:
        """Trigger performance alert."""
        baseline = validation["baseline"]
        alert_level = validation["alert_level"]

        # Check cooldown to avoid alert spam
        cooldown_key = f"{metric_name}:{alert_level}"
        current_time = time.time()

        if current_time - self.last_alert_times.get(cooldown_key, 0) < self.alert_cooldown_seconds:
            return

        self.last_alert_times[cooldown_key] = current_time

        # Create alert message
        alert_message = (
            f"Performance Alert ({alert_level.upper()}): "
            f"{metric_name} = {value:.3f} {baseline.unit} "
            f"(target: {baseline.target_value:.3f}, "
            f"range: {baseline.acceptable_range_min:.3f}-{baseline.acceptable_range_max:.3f})"
        )

        logger.warning(alert_message)

        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(
                    {
                        "level": alert_level,
                        "metric_name": metric_name,
                        "value": value,
                        "baseline": baseline,
                        "validation": validation,
                        "message": alert_message,
                        "timestamp": current_time,
                    }
                )
            except Exception as e:
                logger.error(f"Error in performance alert callback: {e}")

    def get_performance_summary(self) -> dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = {
            "tier": self.performance_tier.value,
            "timestamp": time.time(),
            "total_metrics": len(self.metrics_history),
            "metrics_by_category": {},
            "alert_counts": {"warning": 0, "critical": 0},
            "performance_scores": {},
        }

        # Group metrics by category
        for category in MetricCategory:
            category_metrics = self.baseline_config.get_metrics_by_category(category)
            summary["metrics_by_category"][category.value] = []

            for metric_name, baseline in category_metrics.items():
                if metric_name in self.metrics_history:
                    # Get latest value
                    latest_value = (
                        self.metrics_history[metric_name][-1][1] if self.metrics_history[metric_name] else None
                    )

                    if latest_value is not None:
                        validation = self.baseline_config.validate_metric(metric_name, latest_value)
                        summary["metrics_by_category"][category.value].append(
                            {
                                "name": metric_name,
                                "value": latest_value,
                                "alert_level": validation["alert_level"],
                                "performance_score": validation["performance_score"],
                            }
                        )

                        # Update alert counts
                        if validation["alert_level"] == "warning":
                            summary["alert_counts"]["warning"] += 1
                        elif validation["alert_level"] == "critical":
                            summary["alert_counts"]["critical"] += 1

                        # Store performance scores
                        summary["performance_scores"][metric_name] = validation["performance_score"]

        return summary

    def get_resource_usage_summary(self) -> dict[str, Any]:
        """Get current resource usage summary with baseline validation."""
        resource_usage = get_current_resource_usage()
        summary = {
            "timestamp": resource_usage["timestamp"],
            "hostname": resource_usage["hostname"],
            "resource_metrics": {},
        }

        # Validate resource metrics against baselines
        if "memory" in resource_usage:
            memory_percent = resource_usage["memory"]["usage_percent"]
            validation = self.baseline_config.validate_metric("memory_usage_percent", memory_percent)
            summary["resource_metrics"]["memory"] = {
                "usage_percent": memory_percent,
                "available_bytes": resource_usage["memory"]["available_bytes"],
                "validation": validation,
            }

        if "cpu" in resource_usage:
            cpu_percent = resource_usage["cpu"]["usage_percent"]
            validation = self.baseline_config.validate_metric("cpu_usage_percent", cpu_percent)
            summary["resource_metrics"]["cpu"] = {
                "usage_percent": cpu_percent,
                "load_average": resource_usage["cpu"]["load_average"],
                "validation": validation,
            }

        return summary

    def export_performance_report(self) -> str:
        """Export a comprehensive performance report."""
        summary = self.get_performance_summary()
        resource_summary = self.get_resource_usage_summary()

        report = f"""
# Performance Report - {self.performance_tier.value.title()} Environment

**Generated:** {time.strftime("%Y-%m-%d %H:%M:%S UTC")}
**Total Metrics Tracked:** {summary["total_metrics"]}

## Alert Summary
- **Warnings:** {summary["alert_counts"]["warning"]}
- **Critical:** {summary["alert_counts"]["critical"]}

## Resource Usage
"""

        if "memory" in resource_summary["resource_metrics"]:
            mem = resource_summary["resource_metrics"]["memory"]
            report += f"""
### Memory
- Usage: {mem["usage_percent"]:.1f}% ({mem["validation"]["alert_level"]})
- Available: {mem["available_bytes"] / (1024**3):.1f} GB
"""

        if "cpu" in resource_summary["resource_metrics"]:
            cpu = resource_summary["resource_metrics"]["cpu"]
            report += f"""
### CPU
- Usage: {cpu["usage_percent"]:.1f}% ({cpu["validation"]["alert_level"]})
- Load Average: {cpu["load_average"]:.2f}
"""

        # Add metrics by category
        for category_name, metrics in summary["metrics_by_category"].items():
            if metrics:
                report += f"\n## {category_name.title()} Metrics\n"
                for metric in metrics:
                    report += f"- **{metric['name']}**: {metric['value']:.3f} ({metric['alert_level']})\n"

        return report


# Global performance monitor instance
_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor instance."""
    global _performance_monitor

    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def record_metric(metric_name: str, value: float) -> None:
    """Record a metric value for monitoring."""
    monitor = get_performance_monitor()
    monitor.record_metric(metric_name, value)


def get_performance_summary() -> dict[str, Any]:
    """Get current performance summary."""
    monitor = get_performance_monitor()
    return monitor.get_performance_summary()


def export_performance_report() -> str:
    """Export a comprehensive performance report."""
    monitor = get_performance_monitor()
    return monitor.export_performance_report()


# Discord alert callback example
def discord_performance_alert(alert_data: dict[str, Any]) -> None:
    """Example Discord alert callback for performance issues."""
    from ultimate_discord_intelligence_bot.tools.discord_private_alert_tool import DiscordPrivateAlertTool

    level = alert_data["level"]
    metric_name = alert_data["metric_name"]
    value = alert_data["value"]
    baseline = alert_data["baseline"]

    message = (
        f"🚨 **Performance Alert ({level.upper()})**\n"
        f"**Metric:** {metric_name}\n"
        f"**Current Value:** {value:.3f} {baseline.unit}\n"
        f"**Target:** {baseline.target_value:.3f} {baseline.unit}\n"
        f"**Acceptable Range:** {baseline.acceptable_range_min:.3f} - {baseline.acceptable_range_max:.3f}\n"
        f"**Performance Score:** {alert_data['validation']['performance_score']:.1f}/100"
    )

    try:
        alert_tool = DiscordPrivateAlertTool()
        alert_tool._run(message)
    except Exception as e:
        logger.error(f"Failed to send Discord performance alert: {e}")


def initialize_performance_monitoring() -> None:
    """Initialize performance monitoring with Discord alerts."""
    monitor = get_performance_monitor()
    monitor.add_alert_callback(discord_performance_alert)
    logger.info("Performance monitoring initialized with Discord alerts")


__all__ = [
    "PerformanceMonitor",
    "get_performance_monitor",
    "record_metric",
    "get_performance_summary",
    "export_performance_report",
    "discord_performance_alert",
    "initialize_performance_monitoring",
]
