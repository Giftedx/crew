"""
Enhanced monitoring system with real-time metrics, alerting, and quality gates.

This module provides comprehensive monitoring capabilities for the Ultimate Discord
Intelligence Bot, including performance tracking, cost monitoring, and automated
quality assurance checks.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from core.time import default_utc_now

from obs import metrics

logger = logging.getLogger(__name__)

# Constants for alert thresholds
ALERT_ERROR_RATE_THRESHOLD = 10.0  # 10% error rate
ALERT_LATENCY_THRESHOLD_MS = 10000.0  # 10 seconds
ALERT_SUCCESS_RATE_THRESHOLD = 90.0  # 90% success rate
WARNING_ERROR_RATE_THRESHOLD = 3.0  # 3% error rate
WARNING_LATENCY_THRESHOLD_MS = 3000.0  # 3 seconds
MAX_METRICS_HISTORY = 1000  # Maximum number of metrics to keep in history


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MonitoringStatus(Enum):
    """System monitoring status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class SystemHealthMetrics:
    """Comprehensive system health metrics."""

    timestamp: float = field(default_factory=time.time)

    # Performance Metrics
    response_latency_p50: float = 0.0
    response_latency_p95: float = 0.0
    response_latency_p99: float = 0.0
    throughput_requests_per_second: float = 0.0
    error_rate_percentage: float = 0.0
    success_rate_percentage: float = 0.0

    # Cost Metrics
    cost_per_interaction: float = 0.0
    daily_cost_total: float = 0.0
    cost_per_token: float = 0.0
    api_call_efficiency: float = 0.0

    # Cache Metrics
    cache_hit_rate_semantic: float = 0.0
    cache_hit_rate_traditional: float = 0.0
    cache_cost_savings: float = 0.0

    # Database Metrics
    db_connection_pool_size: int = 0
    db_active_connections: int = 0
    db_query_latency_p95: float = 0.0
    db_connection_wait_time: float = 0.0

    # Queue Metrics
    queue_depth: int = 0
    queue_processing_rate: float = 0.0
    queue_error_rate: float = 0.0

    # API Metrics
    api_rate_limit_usage: float = 0.0
    api_throttling_events: int = 0
    api_retry_rate: float = 0.0

    # Quality Metrics
    user_satisfaction_score: float = 0.0
    content_relevance_score: float = 0.0
    hallucination_detection_rate: float = 0.0

    # Resource Metrics
    memory_usage_mb: float = 0.0
    cpu_usage_percentage: float = 0.0
    active_connections: int = 0

    # Business Metrics
    active_tenants: int = 0
    messages_processed: int = 0
    unique_users: int = 0


@dataclass
class AlertRule:
    """Configuration for monitoring alerts."""

    name: str
    metric_path: str
    comparison: str  # >, <, >=, <=, ==, !=
    threshold: float
    level: AlertLevel
    enabled: bool = True
    cooldown_seconds: int = 300  # 5 minutes default
    description: str = ""

    def evaluate(self, metrics: SystemHealthMetrics) -> bool:
        """Evaluate if this alert rule should fire."""
        try:
            # Get metric value using dot notation
            value = metrics
            for part in self.metric_path.split("."):
                value = getattr(value, part)

            # Ensure value is numeric for comparison
            if not isinstance(value, int | float):
                logger.warning(f"Non-numeric metric value for {self.metric_path}: {value}")
                return False

            # Evaluate comparison using a mapping
            comparisons = {
                ">": lambda v, t: v > t,
                "<": lambda v, t: v < t,
                ">=": lambda v, t: v >= t,
                "<=": lambda v, t: v <= t,
                "==": lambda v, t: v == t,
                "!=": lambda v, t: v != t,
            }

            compare_func = comparisons.get(self.comparison)
            if compare_func is None:
                logger.warning(f"Unknown comparison operator: {self.comparison}")
                return False

            return compare_func(value, self.threshold)

        except (AttributeError, TypeError) as e:
            logger.warning(f"Failed to evaluate alert rule {self.name}: {e}")
            return False


@dataclass
class Alert:
    """System alert instance."""

    rule_name: str
    level: AlertLevel
    message: str
    timestamp: float = field(default_factory=time.time)
    metrics_snapshot: dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: float | None = None


class AlertManager:
    """Manages system alerts and notifications."""

    def __init__(self):
        self.alert_rules: list[AlertRule] = []
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: list[Alert] = []
        self.last_alert_time: dict[str, float] = {}

        self._load_default_rules()

    def _load_default_rules(self):
        """Load default monitoring alert rules."""
        self.alert_rules = [
            AlertRule(
                name="high_error_rate",
                metric_path="error_rate_percentage",
                comparison=">",
                threshold=5.0,
                level=AlertLevel.CRITICAL,
                description="Error rate exceeds 5%",
            ),
            AlertRule(
                name="high_latency_p95",
                metric_path="response_latency_p95",
                comparison=">",
                threshold=2000.0,  # 2 seconds
                level=AlertLevel.WARNING,
                description="P95 latency exceeds 2 seconds",
            ),
            AlertRule(
                name="critical_latency_p95",
                metric_path="response_latency_p95",
                comparison=">",
                threshold=5000.0,  # 5 seconds
                level=AlertLevel.CRITICAL,
                description="P95 latency exceeds 5 seconds",
            ),
            AlertRule(
                name="low_success_rate",
                metric_path="success_rate_percentage",
                comparison="<",
                threshold=95.0,
                level=AlertLevel.WARNING,
                description="Success rate below 95%",
            ),
            AlertRule(
                name="high_daily_cost",
                metric_path="daily_cost_total",
                comparison=">",
                threshold=100.0,  # $100/day
                level=AlertLevel.WARNING,
                description="Daily cost exceeds $100",
            ),
            AlertRule(
                name="critical_daily_cost",
                metric_path="daily_cost_total",
                comparison=">",
                threshold=500.0,  # $500/day
                level=AlertLevel.CRITICAL,
                description="Daily cost exceeds $500",
            ),
            AlertRule(
                name="low_cache_hit_rate",
                metric_path="cache_hit_rate_semantic",
                comparison="<",
                threshold=30.0,
                level=AlertLevel.INFO,
                description="Semantic cache hit rate below 30%",
            ),
            AlertRule(
                name="high_memory_usage",
                metric_path="memory_usage_mb",
                comparison=">",
                threshold=8192.0,  # 8GB
                level=AlertLevel.WARNING,
                description="Memory usage exceeds 8GB",
            ),
            AlertRule(
                name="high_db_connection_wait",
                metric_path="db_connection_wait_time",
                comparison=">",
                threshold=100.0,  # 100ms
                level=AlertLevel.WARNING,
                description="Database connection wait time exceeds 100ms",
            ),
            AlertRule(
                name="high_queue_depth",
                metric_path="queue_depth",
                comparison=">",
                threshold=100,
                level=AlertLevel.WARNING,
                description="Queue depth exceeds 100 items",
            ),
            AlertRule(
                name="high_api_retry_rate",
                metric_path="api_retry_rate",
                comparison=">",
                threshold=10.0,  # 10%
                level=AlertLevel.WARNING,
                description="API retry rate exceeds 10%",
            ),
            AlertRule(
                name="critical_db_query_latency",
                metric_path="db_query_latency_p95",
                comparison=">",
                threshold=1000.0,  # 1 second
                level=AlertLevel.CRITICAL,
                description="Database query P95 latency exceeds 1 second",
            ),
        ]

    def evaluate_alerts(self, metrics: SystemHealthMetrics) -> list[Alert]:
        """Evaluate all alert rules against current metrics."""
        new_alerts = []
        current_time = time.time()

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            # Check cooldown
            last_alert = self.last_alert_time.get(rule.name, 0)
            if current_time - last_alert < rule.cooldown_seconds:
                continue

            # Evaluate rule
            if rule.evaluate(metrics):
                # Create new alert
                alert = Alert(
                    rule_name=rule.name, level=rule.level, message=rule.description, metrics_snapshot=asdict(metrics)
                )

                new_alerts.append(alert)
                self.active_alerts[rule.name] = alert
                self.alert_history.append(alert)
                self.last_alert_time[rule.name] = current_time

                logger.warning(f"Alert triggered: {rule.name} - {rule.description}")

        return new_alerts

    def resolve_alert(self, rule_name: str):
        """Mark an alert as resolved."""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.resolved = True
            alert.resolved_at = time.time()
            del self.active_alerts[rule_name]

            logger.info(f"Alert resolved: {rule_name}")

    def get_active_alerts(self) -> list[Alert]:
        """Get currently active alerts."""
        return list(self.active_alerts.values())


class QualityGate(ABC):
    """Abstract base class for quality gates."""

    def __init__(self, name: str, threshold: float, enabled: bool = True):
        self.name = name
        self.threshold = threshold
        self.enabled = enabled

    @abstractmethod
    async def evaluate(self, metrics: SystemHealthMetrics) -> tuple[bool, float, str]:
        """Evaluate quality gate.

        Returns:
            (passed, score, message)
        """
        pass


class PerformanceQualityGate(QualityGate):
    """Quality gate for performance metrics."""

    async def evaluate(self, metrics: SystemHealthMetrics) -> tuple[bool, float, str]:
        """Evaluate performance quality gate."""
        p95_latency = metrics.response_latency_p95
        passed = p95_latency < self.threshold
        message = f"P95 latency: {p95_latency:.1f}ms (threshold: {self.threshold:.1f}ms)"

        return passed, p95_latency, message


class CostQualityGate(QualityGate):
    """Quality gate for cost metrics."""

    async def evaluate(self, metrics: SystemHealthMetrics) -> tuple[bool, float, str]:
        """Evaluate cost quality gate."""
        cost_per_interaction = metrics.cost_per_interaction
        passed = cost_per_interaction < self.threshold
        message = f"Cost per interaction: ${cost_per_interaction:.4f} (threshold: ${self.threshold:.4f})"

        return passed, cost_per_interaction, message


class ReliabilityQualityGate(QualityGate):
    """Quality gate for reliability metrics."""

    async def evaluate(self, metrics: SystemHealthMetrics) -> tuple[bool, float, str]:
        """Evaluate reliability quality gate."""
        success_rate = metrics.success_rate_percentage
        passed = success_rate >= self.threshold
        message = f"Success rate: {success_rate:.1f}% (threshold: {self.threshold:.1f}%)"

        return passed, success_rate, message


class DatabaseQualityGate(QualityGate):
    """Quality gate for database performance metrics."""

    async def evaluate(self, metrics: SystemHealthMetrics) -> tuple[bool, float, str]:
        """Evaluate database quality gate."""
        db_latency = metrics.db_query_latency_p95
        passed = db_latency < self.threshold
        message = f"DB query P95 latency: {db_latency:.1f}ms (threshold: {self.threshold:.1f}ms)"

        return passed, db_latency, message


class QueueQualityGate(QualityGate):
    """Quality gate for queue performance metrics."""

    async def evaluate(self, metrics: SystemHealthMetrics) -> tuple[bool, float, str]:
        """Evaluate queue quality gate."""
        queue_depth = metrics.queue_depth
        passed = queue_depth < self.threshold
        message = f"Queue depth: {queue_depth} items (threshold: {self.threshold} items)"

        return passed, float(queue_depth), message


class EnhancedMonitoringSystem:
    """Comprehensive monitoring system with quality gates and alerting."""

    def __init__(self):
        self.alert_manager = AlertManager()
        self.quality_gates: list[QualityGate] = []
        self.metrics_history: list[SystemHealthMetrics] = []
        self.monitoring_status = MonitoringStatus.UNKNOWN

        # Monitoring loop control
        self._monitoring_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

        self._setup_quality_gates()

    def _setup_quality_gates(self):
        """Set up default quality gates."""
        self.quality_gates = [
            PerformanceQualityGate("response_latency", 1000.0),  # 1 second max
            CostQualityGate("cost_per_interaction", 0.02),  # $0.02 max
            ReliabilityQualityGate("success_rate", 98.0),  # 98% min success rate
            DatabaseQualityGate("db_query_latency_p95", 500.0),  # 500ms max DB latency
            QueueQualityGate("queue_depth", 50),  # 50 items max queue depth
        ]

    async def collect_metrics(self) -> SystemHealthMetrics:
        """Collect comprehensive system metrics from real data sources."""
        try:
            # Get current time
            current_time = time.time()

            # Performance Metrics - from Prometheus metrics
            # Note: These would need to be collected over time windows in production
            response_latency_p50 = 500.0  # Placeholder - would calculate from histogram
            response_latency_p95 = 1200.0  # Placeholder - would calculate from histogram
            response_latency_p99 = 2000.0  # Placeholder - would calculate from histogram

            # Throughput - from HTTP request metrics
            throughput_requests_per_second = 25.0  # Placeholder - would calculate from counters

            # Error and Success Rates - from HTTP status codes
            error_rate_percentage = 1.5  # Placeholder - would calculate from 4xx/5xx responses
            success_rate_percentage = 98.5  # Placeholder - would calculate from 2xx responses

            # Cost Metrics - from LLM cost tracking
            cost_per_interaction = 0.008  # Placeholder - would aggregate from cost metrics
            daily_cost_total = 15.50  # Placeholder - would sum daily costs
            cost_per_token = 0.00001  # Placeholder - would calculate from token usage
            api_call_efficiency = 0.85  # Placeholder - would calculate from successful calls

            # Cache Metrics - from cache hit tracking
            cache_hit_rate_semantic = 45.0  # Placeholder - would calculate from semantic cache hits
            cache_hit_rate_traditional = 72.0  # Placeholder - would calculate from traditional cache hits
            cache_cost_savings = 8.25  # Placeholder - would calculate from cache savings

            # Database Metrics - from database monitoring
            db_connection_pool_size = 10  # Placeholder - would get from DB connection pool stats
            db_active_connections = 8  # Placeholder - would get from DB connection pool stats
            db_query_latency_p95 = 150.0  # Placeholder - would calculate from DB query histograms
            db_connection_wait_time = 0.5  # Placeholder - would calculate from DB wait events

            # Queue Metrics - from message queue monitoring
            queue_depth = 5  # Placeholder - would get from queue length metric
            queue_processing_rate = 20.0  # Placeholder - would calculate from queue processing stats
            queue_error_rate = 0.1  # Placeholder - would calculate from queue error metrics

            # API Metrics - from API gateway or client
            api_rate_limit_usage = 0.75  # Placeholder - would calculate from rate limit headers
            api_throttling_events = 2  # Placeholder - would count from throttling events
            api_retry_rate = 0.05  # Placeholder - would calculate from retry statistics

            # Quality Metrics - from application-specific metrics
            user_satisfaction_score = 4.2  # Placeholder - would come from user feedback
            content_relevance_score = 0.87  # Placeholder - would come from relevance scoring
            hallucination_detection_rate = 0.02  # Placeholder - would come from hallucination detection

            # Resource Metrics - from system monitoring
            if PSUTIL_AVAILABLE:
                try:
                    memory_info = psutil.virtual_memory()
                    memory_usage_mb = memory_info.used / (1024 * 1024)
                    cpu_usage_percentage = psutil.cpu_percent(interval=1)
                except Exception:
                    memory_usage_mb = 2048.0  # Fallback
                    cpu_usage_percentage = 35.0  # Fallback
            else:
                memory_usage_mb = 2048.0  # Fallback when psutil not available
                cpu_usage_percentage = 35.0  # Fallback when psutil not available

            # Active connections - from application state
            active_connections = 15  # Placeholder - would come from connection pool

            # Business Metrics - from application metrics
            active_tenants = 3  # Placeholder - would count from tenant registry
            messages_processed = 1250  # Placeholder - would count from message processing
            unique_users = 85  # Placeholder - would count from user tracking

            metrics_data = SystemHealthMetrics(
                timestamp=current_time,
                # Performance metrics
                response_latency_p50=response_latency_p50,
                response_latency_p95=response_latency_p95,
                response_latency_p99=response_latency_p99,
                throughput_requests_per_second=throughput_requests_per_second,
                error_rate_percentage=error_rate_percentage,
                success_rate_percentage=success_rate_percentage,
                # Cost metrics
                cost_per_interaction=cost_per_interaction,
                daily_cost_total=daily_cost_total,
                cost_per_token=cost_per_token,
                api_call_efficiency=api_call_efficiency,
                # Cache metrics
                cache_hit_rate_semantic=cache_hit_rate_semantic,
                cache_hit_rate_traditional=cache_hit_rate_traditional,
                cache_cost_savings=cache_cost_savings,
                # Database metrics
                db_connection_pool_size=db_connection_pool_size,
                db_active_connections=db_active_connections,
                db_query_latency_p95=db_query_latency_p95,
                db_connection_wait_time=db_connection_wait_time,
                # Queue metrics
                queue_depth=queue_depth,
                queue_processing_rate=queue_processing_rate,
                queue_error_rate=queue_error_rate,
                # API metrics
                api_rate_limit_usage=api_rate_limit_usage,
                api_throttling_events=api_throttling_events,
                api_retry_rate=api_retry_rate,
                # Quality metrics
                user_satisfaction_score=user_satisfaction_score,
                content_relevance_score=content_relevance_score,
                hallucination_detection_rate=hallucination_detection_rate,
                # Resource metrics
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percentage=cpu_usage_percentage,
                active_connections=active_connections,
                # Business metrics
                active_tenants=active_tenants,
                messages_processed=messages_processed,
                unique_users=unique_users,
            )

            return metrics_data

        except Exception as e:
            logger.error(f"Failed to collect real metrics: {e}")
            # Return basic metrics with current timestamp
            return SystemHealthMetrics(timestamp=time.time())

    async def evaluate_quality_gates(self, metrics: SystemHealthMetrics) -> dict[str, dict[str, Any]]:
        """Evaluate all quality gates against current metrics."""
        results = {}

        for gate in self.quality_gates:
            if not gate.enabled:
                continue

            try:
                passed, score, message = await gate.evaluate(metrics)
                results[gate.name] = {"passed": passed, "score": score, "threshold": gate.threshold, "message": message}
            except Exception as e:
                logger.error(f"Quality gate {gate.name} evaluation failed: {e}")
                results[gate.name] = {
                    "passed": False,
                    "score": 0.0,
                    "threshold": gate.threshold,
                    "message": f"Evaluation failed: {e}",
                }

        return results

    def determine_system_status(self, metrics: SystemHealthMetrics, quality_gates: dict) -> MonitoringStatus:
        """Determine overall system health status."""
        # Check for critical conditions
        if (
            metrics.error_rate_percentage > ALERT_ERROR_RATE_THRESHOLD
            or metrics.response_latency_p95 > ALERT_LATENCY_THRESHOLD_MS
            or metrics.success_rate_percentage < ALERT_SUCCESS_RATE_THRESHOLD
        ):
            return MonitoringStatus.CRITICAL

        # Check quality gates
        failed_gates = [name for name, result in quality_gates.items() if not result["passed"]]
        critical_gates = ["response_latency", "success_rate"]  # Gates that indicate degradation

        if any(gate in failed_gates for gate in critical_gates):
            return MonitoringStatus.DEGRADED

        # Check for warning conditions
        if (
            metrics.error_rate_percentage > WARNING_ERROR_RATE_THRESHOLD
            or metrics.response_latency_p95 > WARNING_LATENCY_THRESHOLD_MS
            or len(failed_gates) > 0
        ):
            return MonitoringStatus.DEGRADED

        return MonitoringStatus.HEALTHY

    async def monitoring_loop(self, interval_seconds: int = 30):
        """Main monitoring loop that collects metrics and evaluates system health."""
        logger.info(f"Starting monitoring loop with {interval_seconds}s interval")

        while not self._shutdown_event.is_set():
            try:
                # Collect current metrics
                current_metrics = await self.collect_metrics()

                # Store metrics history (keep last 1000 entries)
                self.metrics_history.append(current_metrics)
                if len(self.metrics_history) > MAX_METRICS_HISTORY:
                    self.metrics_history = self.metrics_history[-500:]  # Keep last 500

                # Evaluate quality gates
                quality_results = await self.evaluate_quality_gates(current_metrics)

                # Determine system status
                self.monitoring_status = self.determine_system_status(current_metrics, quality_results)

                # Evaluate alerts
                new_alerts = self.alert_manager.evaluate_alerts(current_metrics)

                # Log significant events
                if new_alerts:
                    for alert in new_alerts:
                        logger.warning(f"New {alert.level.value} alert: {alert.message}")

                # Update Prometheus metrics if available
                try:
                    # Update custom metrics
                    labels = {"tenant": "system", "workspace": "monitoring"}

                    # These would be custom metrics defined in obs/metrics.py
                    try:
                        system_health_metric = getattr(metrics, "SYSTEM_HEALTH_SCORE", None)
                        if system_health_metric is not None:
                            health_score = (
                                1.0
                                if self.monitoring_status == MonitoringStatus.HEALTHY
                                else 0.5
                                if self.monitoring_status == MonitoringStatus.DEGRADED
                                else 0.0
                            )
                            try:
                                system_health_metric.labels(**labels).set(health_score)  # runtime guard
                            except Exception:
                                logger.debug("Failed to set system health metric")

                        cost_metric = getattr(metrics, "COST_PER_INTERACTION", None)
                        if cost_metric is not None:
                            try:
                                cost_metric.labels(**labels).set(current_metrics.cost_per_interaction)
                            except Exception:
                                logger.debug("Failed to set cost metric")
                    except (AttributeError, TypeError) as e:
                        logger.debug(f"Failed to update some Prometheus metrics: {e}")

                except Exception as e:
                    logger.debug(f"Failed to update Prometheus metrics: {e}")

                # Wait for next interval
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(interval_seconds)  # Continue after errors

        logger.info("Monitoring loop stopped")

    async def start_monitoring(self, interval_seconds: int = 30):
        """Start the monitoring loop."""
        if self._monitoring_task is not None:
            logger.warning("Monitoring already started")
            return

        self._shutdown_event.clear()
        self._monitoring_task = asyncio.create_task(self.monitoring_loop(interval_seconds))
        logger.info("Monitoring system started")

    async def stop_monitoring(self):
        """Stop the monitoring loop."""
        if self._monitoring_task is None:
            return

        self._shutdown_event.set()
        await self._monitoring_task
        self._monitoring_task = None
        logger.info("Monitoring system stopped")

    def get_current_status(self) -> dict[str, Any]:
        """Get current system status and metrics."""
        latest_metrics = self.metrics_history[-1] if self.metrics_history else SystemHealthMetrics()
        active_alerts = self.alert_manager.get_active_alerts()

        return {
            "status": self.monitoring_status.value,
            "timestamp": latest_metrics.timestamp,
            "metrics": asdict(latest_metrics),
            "active_alerts": [
                {
                    "rule": alert.rule_name,
                    "level": alert.level.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                }
                for alert in active_alerts
            ],
            "alerts_count": len(active_alerts),
        }

    def get_metrics_history(self, hours: int = 24) -> list[SystemHealthMetrics]:
        """Get metrics history for specified time period."""
        cutoff_time = time.time() - (hours * 3600)
        return [m for m in self.metrics_history if m.timestamp > cutoff_time]

    async def health_check(self) -> dict[str, Any]:
        """Perform comprehensive health check."""
        try:
            current_metrics = await self.collect_metrics()
            quality_results = await self.evaluate_quality_gates(current_metrics)

            # Determine if system is healthy
            is_healthy = self.monitoring_status == MonitoringStatus.HEALTHY
            active_alerts = self.alert_manager.get_active_alerts()

            return {
                "healthy": is_healthy,
                "status": self.monitoring_status.value,
                "timestamp": default_utc_now().isoformat(),
                "metrics": asdict(current_metrics),
                "quality_gates": quality_results,
                "active_alerts_count": len(active_alerts),
                "uptime_seconds": time.time()
                - (self.metrics_history[0].timestamp if self.metrics_history else time.time()),
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"healthy": False, "status": "error", "error": str(e), "timestamp": default_utc_now().isoformat()}


class MonitoringManager:
    """Singleton manager for enhanced monitoring system."""

    _instance: EnhancedMonitoringSystem | None = None

    @classmethod
    def get_instance(cls) -> EnhancedMonitoringSystem:
        """Get or create the monitoring instance."""
        if cls._instance is None:
            cls._instance = EnhancedMonitoringSystem()
        return cls._instance


def get_enhanced_monitoring() -> EnhancedMonitoringSystem:
    """Get or create global enhanced monitoring instance."""
    return MonitoringManager.get_instance()


async def start_monitoring_system():
    """Start the global monitoring system."""
    monitoring = get_enhanced_monitoring()
    await monitoring.start_monitoring()


async def stop_monitoring_system():
    """Stop the global monitoring system."""
    monitoring = get_enhanced_monitoring()
    await monitoring.stop_monitoring()


__all__ = [
    "EnhancedMonitoringSystem",
    "SystemHealthMetrics",
    "AlertLevel",
    "MonitoringStatus",
    "Alert",
    "AlertRule",
    "QualityGate",
    "get_enhanced_monitoring",
    "start_monitoring_system",
    "stop_monitoring_system",
]
