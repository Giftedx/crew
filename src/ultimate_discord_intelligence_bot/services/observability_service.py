"""
Observability Service for comprehensive monitoring and metrics.

This module provides centralized observability capabilities including
metrics collection, logging, tracing, and performance monitoring.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from ..step_result import StepResult
from ..tenancy.helpers import require_tenant


logger = logging.getLogger(__name__)


@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""

    enable_metrics: bool = True
    metrics_endpoint: str | None = None
    batch_size: int = 100
    flush_interval: float = 30.0
    enable_histograms: bool = True
    enable_counters: bool = True
    enable_gauges: bool = True


class MetricsCollector:
    """Metrics collector for system observability."""

    def __init__(self, config: MetricsConfig | None = None):
        """Initialize metrics collector.

        Args:
            config: Metrics configuration
        """
        self.config = config or MetricsConfig()
        self.counters: dict[str, float] = {}
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list[float]] = {}
        self.timestamps: dict[str, float] = {}

        logger.info("Initialized MetricsCollector with config: %s", self.config)

    def increment_counter(self, name: str, value: float = 1.0, tags: dict[str, str] | None = None):
        """Increment a counter metric.

        Args:
            name: Metric name
            value: Increment value
            tags: Optional tags
        """
        if not self.config.enable_counters:
            return

        key = self._get_metric_key(name, tags)
        self.counters[key] = self.counters.get(key, 0.0) + value
        logger.debug("Incremented counter %s by %s", name, value)

    def set_gauge(self, name: str, value: float, tags: dict[str, str] | None = None):
        """Set a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            tags: Optional tags
        """
        if not self.config.enable_gauges:
            return

        key = self._get_metric_key(name, tags)
        self.gauges[key] = value
        logger.debug("Set gauge %s to %s", name, value)

    def record_histogram(self, name: str, value: float, tags: dict[str, str] | None = None):
        """Record a histogram value.

        Args:
            name: Metric name
            value: Histogram value
            tags: Optional tags
        """
        if not self.config.enable_histograms:
            return

        key = self._get_metric_key(name, tags)
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
        logger.debug("Recorded histogram %s value %s", name, value)

    def start_timer(self, name: str, tags: dict[str, str] | None = None) -> str:
        """Start a timer.

        Args:
            name: Timer name
            tags: Optional tags

        Returns:
            Timer ID
        """
        timer_id = f"{name}_{int(time.time() * 1000)}"
        self.timestamps[timer_id] = time.time()
        logger.debug("Started timer %s", name)
        return timer_id

    def stop_timer(self, timer_id: str) -> float:
        """Stop a timer and record duration.

        Args:
            timer_id: Timer ID

        Returns:
            Duration in seconds
        """
        if timer_id not in self.timestamps:
            logger.warning("Timer %s not found", timer_id)
            return 0.0

        start_time = self.timestamps.pop(timer_id)
        duration = time.time() - start_time
        logger.debug("Stopped timer %s, duration: %.3fs", timer_id, duration)
        return duration

    def _get_metric_key(self, name: str, tags: dict[str, str] | None = None) -> str:
        """Get metric key with tags.

        Args:
            name: Metric name
            tags: Optional tags

        Returns:
            Metric key
        """
        if not tags:
            return name

        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get metrics summary.

        Returns:
            Metrics summary
        """
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                name: {
                    "count": len(values),
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "avg": sum(values) / len(values) if values else 0,
                }
                for name, values in self.histograms.items()
            },
            "active_timers": len(self.timestamps),
        }

    def reset_metrics(self):
        """Reset all metrics."""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.timestamps.clear()
        logger.info("Reset all metrics")


class ObservabilityService:
    """Comprehensive observability service."""

    def __init__(self, config: MetricsConfig | None = None):
        """Initialize observability service.

        Args:
            config: Metrics configuration
        """
        self.config = config or MetricsConfig()
        self.metrics = MetricsCollector(config)
        self.logger = logging.getLogger("observability")

        logger.info("Initialized ObservabilityService")

    @require_tenant(strict_flag_enabled=False)
    async def record_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool,
        tenant: str = "",
        workspace: str = "",
        **kwargs: Any,
    ) -> StepResult:
        """Record an operation for observability.

        Args:
            operation: Operation name
            duration_ms: Operation duration in milliseconds
            success: Whether operation succeeded
            tenant: Tenant identifier
            workspace: Workspace identifier
            **kwargs: Additional operation data

        Returns:
            StepResult indicating recording success/failure
        """
        try:
            # Record metrics
            self.metrics.increment_counter(
                f"operation_{operation}",
                tags={"success": str(success), "tenant": tenant},
            )
            self.metrics.record_histogram(
                f"operation_{operation}_duration_ms",
                duration_ms,
                tags={"tenant": tenant},
            )

            # Log operation
            level = logging.INFO if success else logging.ERROR
            self.logger.log(
                level,
                "Operation %s completed in %.2fms (success: %s, tenant: %s)",
                operation,
                duration_ms,
                success,
                tenant,
                extra={
                    "operation": operation,
                    "duration_ms": duration_ms,
                    "success": success,
                    "tenant": tenant,
                    "workspace": workspace,
                    **kwargs,
                },
            )

            return StepResult.ok(data={"recorded": True})

        except Exception as e:
            logger.error("Failed to record operation: %s", str(e))
            return StepResult.fail(f"Failed to record operation: {e!s}")

    async def get_system_health(self) -> StepResult:
        """Get system health status.

        Returns:
            StepResult with health status
        """
        try:
            health = {
                "status": "healthy",
                "timestamp": time.time(),
                "metrics": self.metrics.get_metrics_summary(),
                "config": {
                    "metrics_enabled": self.config.enable_metrics,
                    "batch_size": self.config.batch_size,
                    "flush_interval": self.config.flush_interval,
                },
            }

            return StepResult.ok(data=health)

        except Exception as e:
            logger.error("Failed to get system health: %s", str(e))
            return StepResult.fail(f"Failed to get system health: {e!s}")

    async def health_check(self) -> StepResult:
        """Perform health check.

        Returns:
            StepResult with health status
        """
        try:
            return StepResult.ok(data={"status": "healthy", "service": "observability"})

        except Exception as e:
            logger.error("Health check failed: %s", str(e))
            return StepResult.fail(f"Health check failed: {e!s}")

    def get_metrics(self) -> StepResult:
        """Get current metrics.

        Returns:
            StepResult with metrics data
        """
        try:
            metrics_data = self.metrics.get_metrics_summary()
            return StepResult.ok(data=metrics_data)

        except Exception as e:
            logger.error("Failed to get metrics: %s", str(e))
            return StepResult.fail(f"Failed to get metrics: {e!s}")

    def reset_metrics(self) -> StepResult:
        """Reset all metrics.

        Returns:
            StepResult indicating success/failure
        """
        try:
            self.metrics.reset_metrics()
            return StepResult.ok(data={"reset": True})

        except Exception as e:
            logger.error("Failed to reset metrics: %s", str(e))
            return StepResult.fail(f"Failed to reset metrics: {e!s}")
