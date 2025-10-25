"""
Performance monitoring and optimization manager for Discord AI processing.

This module provides comprehensive performance monitoring, optimization,
and adaptive tuning for the Discord AI system.
"""

from __future__ import annotations

import asyncio
import contextlib
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import psutil
from performance_optimization.src.ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""

    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    active_threads: int
    active_connections: int


@dataclass
class ProcessingMetrics:
    """Processing-specific metrics."""

    operation_name: str
    timestamp: float
    duration_ms: float
    success: bool
    input_size: int
    output_size: int
    memory_used_mb: float
    cpu_time_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationConfig:
    """Configuration for performance optimization."""

    monitoring_interval_seconds: float = 1.0
    metrics_history_size: int = 1000
    alert_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "processing_time_ms": 5000.0,
            "error_rate_percent": 10.0,
        }
    )
    enable_adaptive_optimization: bool = True
    optimization_interval_seconds: float = 60.0
    enable_alerts: bool = True


class PerformanceManager:
    """
    Comprehensive performance monitoring and optimization manager.

    This manager tracks system and application performance metrics,
    provides alerts, and implements adaptive optimizations.
    """

    def __init__(self, config: OptimizationConfig):
        self.config = config

        # Metrics storage
        self._system_metrics: deque = deque(maxlen=config.metrics_history_size)
        self._processing_metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=config.metrics_history_size))

        # Performance tracking
        self._operation_timers: dict[str, float] = {}
        self._operation_counts: dict[str, int] = defaultdict(int)
        self._operation_errors: dict[str, int] = defaultdict(int)

        # Optimization state
        self._optimization_state: dict[str, Any] = {
            "batch_sizes": {},
            "cache_sizes": {},
            "timeout_settings": {},
            "concurrency_limits": {},
        }

        # Alert system
        self._alerts: list[dict[str, Any]] = []
        self._alert_callbacks: list[Callable[[dict[str, Any]], None]] = []

        # Background tasks
        self._monitoring_task: asyncio.Task | None = None
        self._optimization_task: asyncio.Task | None = None

        # Thread safety
        self._lock = threading.Lock()

        # Start monitoring
        self._start_monitoring()

    def _start_monitoring(self):
        """Start background monitoring tasks."""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._monitor_performance())

        if self.config.enable_adaptive_optimization:
            if self._optimization_task is None or self._optimization_task.done():
                self._optimization_task = asyncio.create_task(self._adaptive_optimization())

    async def _monitor_performance(self):
        """Background task to monitor system performance."""
        while True:
            try:
                await asyncio.sleep(self.config.monitoring_interval_seconds)

                # Collect system metrics
                metrics = self._collect_system_metrics()

                with self._lock:
                    self._system_metrics.append(metrics)

                # Check for alerts
                if self.config.enable_alerts:
                    await self._check_alerts(metrics)

            except Exception as e:
                print(f"Performance monitoring error: {e!s}")

    def _collect_system_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics."""
        # CPU and memory
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_mb = memory.used / (1024 * 1024)
        memory_percent = memory.percent

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_io_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
        disk_io_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0

        # Network I/O
        network_io = psutil.net_io_counters()
        network_io_sent_mb = network_io.bytes_sent / (1024 * 1024) if network_io else 0
        network_io_recv_mb = network_io.bytes_recv / (1024 * 1024) if network_io else 0

        # Thread and connection counts
        active_threads = threading.active_count()
        active_connections = len(psutil.Process().connections()) if hasattr(psutil.Process(), "connections") else 0

        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb,
            network_io_sent_mb=network_io_sent_mb,
            network_io_recv_mb=network_io_recv_mb,
            active_threads=active_threads,
            active_connections=active_connections,
        )

    async def _check_alerts(self, metrics: PerformanceMetrics):
        """Check for performance alerts."""
        alerts = []

        # CPU alert
        if metrics.cpu_percent > self.config.alert_thresholds["cpu_percent"]:
            alerts.append(
                {
                    "type": "high_cpu",
                    "severity": "warning",
                    "message": f"High CPU usage: {metrics.cpu_percent:.1f}%",
                    "value": metrics.cpu_percent,
                    "threshold": self.config.alert_thresholds["cpu_percent"],
                    "timestamp": metrics.timestamp,
                }
            )

        # Memory alert
        if metrics.memory_percent > self.config.alert_thresholds["memory_percent"]:
            alerts.append(
                {
                    "type": "high_memory",
                    "severity": "critical",
                    "message": f"High memory usage: {metrics.memory_percent:.1f}%",
                    "value": metrics.memory_percent,
                    "threshold": self.config.alert_thresholds["memory_percent"],
                    "timestamp": metrics.timestamp,
                }
            )

        # Process alerts
        for alert in alerts:
            self._alerts.append(alert)

            # Call alert callbacks
            for callback in self._alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert)
                    else:
                        callback(alert)
                except Exception as e:
                    print(f"Alert callback error: {e!s}")

    async def _adaptive_optimization(self):
        """Background task for adaptive optimization."""
        while True:
            try:
                await asyncio.sleep(self.config.optimization_interval_seconds)

                # Analyze recent performance
                optimization_suggestions: list[dict[str, Any]] = await self._analyze_performance()

                # Apply optimizations
                for suggestion in optimization_suggestions:
                    await self._apply_optimization(suggestion)

            except Exception as e:
                print(f"Adaptive optimization error: {e!s}")

    async def _analyze_performance(self) -> list[dict[str, Any]]:
        """Analyze performance and suggest optimizations."""
        suggestions = []

        with self._lock:
            if len(self._system_metrics) < 10:
                return suggestions

            recent_metrics = list(self._system_metrics)[-10:]

            # Analyze CPU usage
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            if avg_cpu > 70:
                suggestions.append(
                    {
                        "type": "reduce_batch_size",
                        "reason": f"High CPU usage: {avg_cpu:.1f}%",
                        "action": "decrease_batch_sizes",
                    }
                )

            # Analyze memory usage
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            if avg_memory > 75:
                suggestions.append(
                    {
                        "type": "reduce_cache_size",
                        "reason": f"High memory usage: {avg_memory:.1f}%",
                        "action": "decrease_cache_sizes",
                    }
                )

            # Analyze processing times
            for operation, metrics_queue in self._processing_metrics.items():
                if len(metrics_queue) >= 5:
                    recent_processing = list(metrics_queue)[-5:]
                    avg_time = sum(m.duration_ms for m in recent_processing) / len(recent_processing)

                    if avg_time > self.config.alert_thresholds["processing_time_ms"]:
                        suggestions.append(
                            {
                                "type": "optimize_operation",
                                "operation": operation,
                                "reason": f"Slow processing: {avg_time:.1f}ms",
                                "action": "optimize_processing",
                            }
                        )

        return suggestions

    async def _apply_optimization(self, suggestion: dict[str, Any]):
        """Apply an optimization suggestion."""
        optimization_type = suggestion["type"]

        if optimization_type == "reduce_batch_size":
            # Reduce batch sizes across operations
            for operation in self._optimization_state["batch_sizes"]:
                current_size = self._optimization_state["batch_sizes"][operation]
                new_size = max(1, int(current_size * 0.8))
                self._optimization_state["batch_sizes"][operation] = new_size

        elif optimization_type == "reduce_cache_size":
            # Reduce cache sizes
            for cache_name in self._optimization_state["cache_sizes"]:
                current_size = self._optimization_state["cache_sizes"][cache_name]
                new_size = max(100, int(current_size * 0.7))
                self._optimization_state["cache_sizes"][cache_name] = new_size

        elif optimization_type == "optimize_operation":
            operation = suggestion["operation"]
            # Apply operation-specific optimizations
            if operation not in self._optimization_state["timeout_settings"]:
                self._optimization_state["timeout_settings"][operation] = 30.0

            # Reduce timeout for slow operations
            current_timeout = self._optimization_state["timeout_settings"][operation]
            new_timeout = max(5.0, current_timeout * 0.8)
            self._optimization_state["timeout_settings"][operation] = new_timeout

    def start_operation_timer(self, operation_name: str):
        """Start timing an operation."""
        self._operation_timers[operation_name] = time.time()

    def end_operation_timer(self, operation_name: str) -> float:
        """End timing an operation and return duration."""
        if operation_name in self._operation_timers:
            start_time = self._operation_timers.pop(operation_name)
            duration_ms = (time.time() - start_time) * 1000

            # Record operation
            self._operation_counts[operation_name] += 1

            return duration_ms
        return 0.0

    def record_processing_metrics(self, metrics: ProcessingMetrics):
        """Record processing metrics."""
        with self._lock:
            self._processing_metrics[metrics.operation_name].append(metrics)

            if not metrics.success:
                self._operation_errors[metrics.operation_name] += 1

    def add_alert_callback(self, callback: Callable[[dict[str, Any]], None]):
        """Add an alert callback function."""
        self._alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable[[dict[str, Any]], None]):
        """Remove an alert callback function."""
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)

    async def get_performance_summary(self) -> StepResult:
        """Get comprehensive performance summary."""
        with self._lock:
            summary = {
                "system_metrics": {
                    "current": self._system_metrics[-1].__dict__ if self._system_metrics else None,
                    "avg_cpu_percent": self._calculate_avg_metric("cpu_percent"),
                    "avg_memory_percent": self._calculate_avg_metric("memory_percent"),
                    "avg_active_threads": self._calculate_avg_metric("active_threads"),
                },
                "processing_metrics": {},
                "operation_stats": {},
                "optimization_state": self._optimization_state.copy(),
                "recent_alerts": self._alerts[-10:] if self._alerts else [],
                "alert_count": len(self._alerts),
            }

            # Add processing metrics for each operation
            for operation, metrics_queue in self._processing_metrics.items():
                if metrics_queue:
                    recent_metrics = list(metrics_queue)[-10:]

                    avg_duration = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)
                    success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics) * 100

                    summary["processing_metrics"][operation] = {
                        "avg_duration_ms": avg_duration,
                        "success_rate_percent": success_rate,
                        "total_operations": self._operation_counts[operation],
                        "error_count": self._operation_errors[operation],
                    }

            # Add operation statistics
            for operation, count in self._operation_counts.items():
                error_count = self._operation_errors[operation]
                error_rate = (error_count / max(count, 1)) * 100

                summary["operation_stats"][operation] = {
                    "total_count": count,
                    "error_count": error_count,
                    "error_rate_percent": error_rate,
                }

        return StepResult.ok(data=summary)

    def _calculate_avg_metric(self, metric_name: str) -> float:
        """Calculate average of a system metric."""
        if not self._system_metrics:
            return 0.0

        values = [getattr(m, metric_name) for m in self._system_metrics]
        return sum(values) / len(values)

    async def get_optimization_recommendations(self) -> StepResult:
        """Get optimization recommendations based on current performance."""
        recommendations: list[dict[str, Any]] = []

        with self._lock:
            if not self._system_metrics:
                return StepResult.ok(data={"recommendations": recommendations})

            recent_metrics = list(self._system_metrics)[-20:]

            # CPU recommendations
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            if avg_cpu > 60:
                recommendations.append(
                    {
                        "type": "cpu_optimization",
                        "priority": "high" if avg_cpu > 80 else "medium",
                        "description": f"High CPU usage ({avg_cpu:.1f}%)",
                        "suggestions": [
                            "Reduce batch sizes",
                            "Implement request throttling",
                            "Optimize processing algorithms",
                        ],
                    }
                )

            # Memory recommendations
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            if avg_memory > 70:
                recommendations.append(
                    {
                        "type": "memory_optimization",
                        "priority": "high" if avg_memory > 85 else "medium",
                        "description": f"High memory usage ({avg_memory:.1f}%)",
                        "suggestions": ["Reduce cache sizes", "Implement memory cleanup", "Optimize data structures"],
                    }
                )

            # Processing time recommendations
            for operation, metrics_queue in self._processing_metrics.items():
                if len(metrics_queue) >= 10:
                    recent_metrics = list(metrics_queue)[-10:]
                    avg_time = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)

                    if avg_time > 1000:  # 1 second
                        recommendations.append(
                            {
                                "type": "processing_optimization",
                                "priority": "high" if avg_time > 5000 else "medium",
                                "operation": operation,
                                "description": f"Slow processing ({avg_time:.1f}ms)",
                                "suggestions": [
                                    "Optimize algorithm complexity",
                                    "Implement caching",
                                    "Use batch processing",
                                ],
                            }
                        )

        return StepResult.ok(data={"recommendations": recommendations})

    async def shutdown(self) -> StepResult:
        """Gracefully shutdown the performance manager."""
        # Cancel background tasks
        if self._monitoring_task:
            self._monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitoring_task

        if self._optimization_task:
            self._optimization_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._optimization_task

        return StepResult.ok(data={"action": "performance_manager_shutdown_complete"})


# Factory function for creating performance managers
def create_performance_manager(config: OptimizationConfig) -> PerformanceManager:
    """Create a performance manager with the specified configuration."""
    return PerformanceManager(config)
