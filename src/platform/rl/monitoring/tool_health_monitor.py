"""Tool Health Monitoring

Tracks tool execution health and automatically disables unhealthy tools.
Integrates with ToolRoutingBandit to prevent routing to failing tools.
"""
from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from typing import Any
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

@dataclass
class ToolHealthMetrics:
    """Health metrics for a single tool"""
    tool_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_latency_ms: float = 0.0
    error_count_window: list[int] = field(default_factory=list)
    last_error_time: float = 0.0
    last_success_time: float = 0.0
    is_enabled: bool = True
    auto_disabled_at: float | None = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0-1.0)"""
        if self.total_executions == 0:
            return 1.0
        return self.successful_executions / self.total_executions

    @property
    def error_rate(self) -> float:
        """Calculate error rate (0.0-1.0)"""
        return 1.0 - self.success_rate

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency"""
        if self.successful_executions == 0:
            return 0.0
        return self.total_latency_ms / self.successful_executions

    @property
    def health_score(self) -> float:
        """
        Calculate composite health score (0.0-1.0)

        Factors:
        - Success rate (70% weight)
        - Recent error pattern (20% weight)
        - Latency stability (10% weight)
        """
        success_component = self.success_rate * 0.7
        if len(self.error_count_window) > 0:
            recent_error_rate = sum(self.error_count_window) / len(self.error_count_window)
            recent_success_rate = 1.0 - recent_error_rate
            recent_component = recent_success_rate * 0.2
        else:
            recent_component = 0.2
        if self.avg_latency_ms > 0:
            latency_score = max(0.0, 1.0 - self.avg_latency_ms / 30000.0)
            latency_component = latency_score * 0.1
        else:
            latency_component = 0.1
        return success_component + recent_component + latency_component

@dataclass
class HealthStatistics:
    """Aggregate health statistics across all tools"""
    total_tools: int = 0
    healthy_tools: int = 0
    degraded_tools: int = 0
    unhealthy_tools: int = 0
    disabled_tools: int = 0
    avg_health_score: float = 0.0
    total_executions: int = 0
    total_failures: int = 0

class ToolHealthMonitor:
    """
    Monitors tool execution health and auto-disables unhealthy tools

    Features:
    - Tracks per-tool success/error rates
    - Sliding window for recent error patterns
    - Composite health scoring
    - Auto-disable when health < threshold
    - Auto-enable after recovery period
    - Integration with ToolRoutingBandit
    """

    def __init__(self, health_threshold: float=0.4, window_size: int=100, recovery_period_s: float=3600.0, enable_auto_disable: bool=True):
        """
        Initialize health monitor

        Args:
            health_threshold: Minimum health score to remain enabled
            window_size: Size of sliding window for recent errors
            recovery_period_s: Time to wait before re-enabling
            enable_auto_disable: Whether to auto-disable unhealthy tools
        """
        self.health_threshold = health_threshold
        self.window_size = window_size
        self.recovery_period_s = recovery_period_s
        self.enable_auto_disable = enable_auto_disable
        self.tool_metrics: dict[str, ToolHealthMetrics] = {}
        self.start_time = time.time()
        logger.info(f'ToolHealthMonitor initialized (threshold={health_threshold}, window={window_size}, recovery={recovery_period_s}s)')

    def record_execution(self, tool_name: str, success: bool, latency_ms: float=0.0, error_type: str | None=None) -> None:
        """
        Record tool execution outcome

        Args:
            tool_name: Name of the tool
            success: Whether execution succeeded
            latency_ms: Execution latency in milliseconds
            error_type: Type of error (if failed)
        """
        if tool_name not in self.tool_metrics:
            self.tool_metrics[tool_name] = ToolHealthMetrics(tool_name=tool_name)
        metrics = self.tool_metrics[tool_name]
        now = time.time()
        metrics.total_executions += 1
        if success:
            metrics.successful_executions += 1
            metrics.total_latency_ms += latency_ms
            metrics.last_success_time = now
            metrics.error_count_window.append(0)
        else:
            metrics.failed_executions += 1
            metrics.last_error_time = now
            metrics.error_count_window.append(1)
            logger.warning(f'Tool {tool_name} failed (error_type={error_type}, health_score={metrics.health_score:.2f})')
        if len(metrics.error_count_window) > self.window_size:
            metrics.error_count_window.pop(0)
        self._check_and_update_health(metrics)

    def _check_and_update_health(self, metrics: ToolHealthMetrics) -> None:
        """
        Check tool health and auto-disable if unhealthy

        Args:
            metrics: Tool metrics to check
        """
        if not self.enable_auto_disable:
            return
        health_score = metrics.health_score
        if metrics.is_enabled and health_score < self.health_threshold:
            metrics.is_enabled = False
            metrics.auto_disabled_at = time.time()
            logger.warning(f'Tool {metrics.tool_name} AUTO-DISABLED (health_score={health_score:.2f} < threshold={self.health_threshold})')
        elif not metrics.is_enabled and metrics.auto_disabled_at:
            time_disabled = time.time() - metrics.auto_disabled_at
            if time_disabled >= self.recovery_period_s and health_score >= self.health_threshold + 0.1:
                metrics.is_enabled = True
                metrics.auto_disabled_at = None
                logger.info(f'Tool {metrics.tool_name} AUTO-ENABLED (health_score={health_score:.2f}, recovered after {time_disabled:.0f}s)')

    def is_tool_enabled(self, tool_name: str) -> bool:
        """
        Check if tool is enabled for routing

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool is healthy and enabled
        """
        if tool_name not in self.tool_metrics:
            return True
        return self.tool_metrics[tool_name].is_enabled

    def get_tool_health(self, tool_name: str) -> ToolHealthMetrics | None:
        """
        Get health metrics for a specific tool

        Args:
            tool_name: Name of the tool

        Returns:
            Health metrics or None if unknown
        """
        return self.tool_metrics.get(tool_name)

    def get_healthy_tools(self, min_health: float | None=None) -> list[str]:
        """
        Get list of healthy tool names

        Args:
            min_health: Minimum health score (defaults to threshold)

        Returns:
            List of tool names meeting health criteria
        """
        threshold = min_health or self.health_threshold
        return [name for name, metrics in self.tool_metrics.items() if metrics.is_enabled and metrics.health_score >= threshold]

    def get_statistics(self) -> HealthStatistics:
        """
        Get aggregate health statistics

        Returns:
            Statistics across all tools
        """
        stats = HealthStatistics()
        health_scores: list[float] = []
        for metrics in self.tool_metrics.values():
            stats.total_tools += 1
            stats.total_executions += metrics.total_executions
            stats.total_failures += metrics.failed_executions
            health_score = metrics.health_score
            health_scores.append(health_score)
            if not metrics.is_enabled:
                stats.disabled_tools += 1
            elif health_score >= 0.8:
                stats.healthy_tools += 1
            elif health_score >= self.health_threshold:
                stats.degraded_tools += 1
            else:
                stats.unhealthy_tools += 1
        if health_scores:
            stats.avg_health_score = sum(health_scores) / len(health_scores)
        return stats

    def get_health_report(self) -> dict[str, Any]:
        """
        Get comprehensive health report

        Returns:
            Dictionary with health data for all tools
        """
        stats = self.get_statistics()
        return {'statistics': {'total_tools': stats.total_tools, 'healthy_tools': stats.healthy_tools, 'degraded_tools': stats.degraded_tools, 'unhealthy_tools': stats.unhealthy_tools, 'disabled_tools': stats.disabled_tools, 'avg_health_score': stats.avg_health_score, 'total_executions': stats.total_executions, 'total_failures': stats.total_failures}, 'tool_health': {name: {'health_score': metrics.health_score, 'success_rate': metrics.success_rate, 'error_rate': metrics.error_rate, 'avg_latency_ms': metrics.avg_latency_ms, 'total_executions': metrics.total_executions, 'is_enabled': metrics.is_enabled, 'last_success_time': metrics.last_success_time, 'last_error_time': metrics.last_error_time} for name, metrics in self.tool_metrics.items()}, 'config': {'health_threshold': self.health_threshold, 'window_size': self.window_size, 'recovery_period_s': self.recovery_period_s, 'enable_auto_disable': self.enable_auto_disable}}

    def reset_tool(self, tool_name: str) -> StepResult:
        """
        Reset a tool's health metrics and re-enable

        Args:
            tool_name: Name of the tool

        Returns:
            StepResult indicating success/failure
        """
        if tool_name not in self.tool_metrics:
            return StepResult.fail(f'Unknown tool: {tool_name}')
        self.tool_metrics[tool_name] = ToolHealthMetrics(tool_name=tool_name)
        logger.info(f'Tool {tool_name} health metrics reset')
        return StepResult.ok(message=f'Tool {tool_name} reset')
_monitor: ToolHealthMonitor | None = None

def get_health_monitor(auto_create: bool=True) -> ToolHealthMonitor | None:
    """Get global health monitor instance"""
    global _monitor
    if _monitor is None and auto_create:
        _monitor = ToolHealthMonitor()
    return _monitor

def set_health_monitor(monitor: ToolHealthMonitor) -> None:
    """Set global health monitor instance"""
    global _monitor
    _monitor = monitor
__all__ = ['HealthStatistics', 'ToolHealthMetrics', 'ToolHealthMonitor', 'get_health_monitor', 'set_health_monitor']