"""Tool Usage Metrics Collection and Observability Infrastructure.

This module provides comprehensive metrics collection for tool usage,
performance monitoring, and observability across the system.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from platform.core.step_result import StepResult


@dataclass
class ToolMetrics:
    """Metrics for a specific tool."""

    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    min_execution_time: float = float("inf")
    max_execution_time: float = 0.0
    last_called: datetime | None = None
    first_called: datetime | None = None
    error_count: int = 0
    success_rate: float = 0.0

    def update(self, execution_time: float, success: bool, error: str | None = None):
        """Update metrics with a new tool call."""
        self.total_calls += 1
        self.total_execution_time += execution_time
        self.average_execution_time = self.total_execution_time / self.total_calls
        self.min_execution_time = min(self.min_execution_time, execution_time)
        self.max_execution_time = max(self.max_execution_time, execution_time)
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if error:
                self.error_count += 1
        self.success_rate = self.successful_calls / self.total_calls if self.total_calls > 0 else 0.0
        now = datetime.now(timezone.utc)
        if not self.first_called:
            self.first_called = now
        self.last_called = now


@dataclass
class SystemMetrics:
    """System-wide metrics."""

    total_tool_calls: int = 0
    total_execution_time: float = 0.0
    active_tools: int = 0
    system_uptime: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    last_updated: datetime | None = None

    def update(self, tool_calls: int, execution_time: float, active_tools: int):
        """Update system metrics."""
        self.total_tool_calls += tool_calls
        self.total_execution_time += execution_time
        self.active_tools = active_tools
        self.last_updated = datetime.now(timezone.utc)


class MetricsCollector:
    """Comprehensive metrics collection for tool usage and system observability."""

    def __init__(self, metrics_file: str = "tool_metrics.json"):
        """Initialize the metrics collector."""
        self.metrics_file = Path(metrics_file)
        self.tool_metrics: dict[str, ToolMetrics] = {}
        self.system_metrics = SystemMetrics()
        self.start_time = time.time()
        self._load_metrics()

    def _load_metrics(self):
        """Load existing metrics from file."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file) as f:
                    data = json.load(f)
                for tool_name, metrics_data in data.get("tool_metrics", {}).items():
                    self.tool_metrics[tool_name] = ToolMetrics(**metrics_data)
                system_data = data.get("system_metrics", {})
                self.system_metrics = SystemMetrics(**system_data)
            except Exception as e:
                print(f"⚠️  Failed to load metrics: {e}")

    def _save_metrics(self):
        """Save metrics to file."""
        try:
            data = {
                "tool_metrics": {name: asdict(metrics) for name, metrics in self.tool_metrics.items()},
                "system_metrics": asdict(self.system_metrics),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            with open(self.metrics_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Failed to save metrics: {e}")

    def record_tool_call(self, tool_name: str, execution_time: float, result: StepResult):
        """Record a tool call with metrics."""
        if tool_name not in self.tool_metrics:
            self.tool_metrics[tool_name] = ToolMetrics(tool_name=tool_name)
        success = result.success if hasattr(result, "success") else True
        error = result.error if hasattr(result, "error") and (not success) else None
        self.tool_metrics[tool_name].update(execution_time, success, error)
        self._update_system_metrics()
        self._save_metrics()

    def _update_system_metrics(self):
        """Update system-wide metrics."""
        total_calls = sum(metrics.total_calls for metrics in self.tool_metrics.values())
        total_time = sum(metrics.total_execution_time for metrics in self.tool_metrics.values())
        active_tools = len([m for m in self.tool_metrics.values() if m.total_calls > 0])
        self.system_metrics.update(total_calls, total_time, active_tools)
        self.system_metrics.system_uptime = time.time() - self.start_time
        try:
            import psutil

            process = psutil.Process()
            self.system_metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            self.system_metrics.cpu_usage_percent = process.cpu_percent()
        except ImportError:
            pass

    def get_tool_metrics(self, tool_name: str) -> ToolMetrics | None:
        """Get metrics for a specific tool."""
        return self.tool_metrics.get(tool_name)

    def get_all_tool_metrics(self) -> dict[str, ToolMetrics]:
        """Get metrics for all tools."""
        return self.tool_metrics.copy()

    def get_system_metrics(self) -> SystemMetrics:
        """Get system-wide metrics."""
        self._update_system_metrics()
        return self.system_metrics

    def get_top_tools(self, limit: int = 10) -> list[ToolMetrics]:
        """Get top tools by usage."""
        return sorted(self.tool_metrics.values(), key=lambda x: x.total_calls, reverse=True)[:limit]

    def get_slowest_tools(self, limit: int = 10) -> list[ToolMetrics]:
        """Get slowest tools by average execution time."""
        return sorted(
            [m for m in self.tool_metrics.values() if m.total_calls > 0],
            key=lambda x: x.average_execution_time,
            reverse=True,
        )[:limit]

    def get_most_error_prone_tools(self, limit: int = 10) -> list[ToolMetrics]:
        """Get tools with highest error rates."""
        return sorted(
            [m for m in self.tool_metrics.values() if m.total_calls > 0],
            key=lambda x: x.failed_calls / x.total_calls,
            reverse=True,
        )[:limit]

    def generate_metrics_report(self) -> dict[str, Any]:
        """Generate comprehensive metrics report."""
        self._update_system_metrics()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_metrics": asdict(self.system_metrics),
            "tool_count": len(self.tool_metrics),
            "active_tools": len([m for m in self.tool_metrics.values() if m.total_calls > 0]),
            "total_tool_calls": sum(m.total_calls for m in self.tool_metrics.values()),
            "average_execution_time": sum(m.average_execution_time for m in self.tool_metrics.values())
            / len(self.tool_metrics)
            if self.tool_metrics
            else 0,
            "top_tools": [asdict(tool) for tool in self.get_top_tools(5)],
            "slowest_tools": [asdict(tool) for tool in self.get_slowest_tools(5)],
            "error_prone_tools": [asdict(tool) for tool in self.get_most_error_prone_tools(5)],
            "tool_metrics": {name: asdict(metrics) for name, metrics in self.tool_metrics.items()},
        }

    def reset_metrics(self):
        """Reset all metrics."""
        self.tool_metrics.clear()
        self.system_metrics = SystemMetrics()
        self.start_time = time.time()
        self._save_metrics()

    def export_metrics(self, export_file: str) -> bool:
        """Export metrics to a file."""
        try:
            report = self.generate_metrics_report()
            with open(export_file, "w") as f:
                json.dump(report, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"❌ Failed to export metrics: {e}")
            return False


_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_tool_usage(tool_name: str, execution_time: float, result: StepResult):
    """Record tool usage metrics."""
    collector = get_metrics_collector()
    collector.record_tool_call(tool_name, execution_time, result)


def get_tool_metrics(tool_name: str) -> ToolMetrics | None:
    """Get metrics for a specific tool."""
    collector = get_metrics_collector()
    return collector.get_tool_metrics(tool_name)


def get_system_metrics() -> SystemMetrics:
    """Get system-wide metrics."""
    collector = get_metrics_collector()
    return collector.get_system_metrics()


def generate_metrics_report() -> dict[str, Any]:
    """Generate comprehensive metrics report."""
    collector = get_metrics_collector()
    return collector.generate_metrics_report()
