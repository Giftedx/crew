"""Intelligent Alerting Service - Advanced alerting with ML-based thresholds

This service provides intelligent alerting capabilities with adaptive thresholds,
anomaly detection, and context-aware notifications.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""

    THRESHOLD = "threshold"
    ANOMALY = "anomaly"
    TREND = "trend"
    PATTERN = "pattern"
    SYSTEM = "system"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    BUSINESS = "business"


@dataclass
class AlertCondition:
    """Condition for triggering an alert"""

    metric_name: str
    operator: str  # >, <, >=, <=, ==, !=
    threshold_value: Union[int, float]
    time_window: int  # seconds
    evaluation_periods: int = 1
    comparison_metric: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """Rule defining when and how to trigger alerts"""

    rule_id: str
    name: str
    description: str
    alert_type: AlertType
    alert_level: AlertLevel
    conditions: List[AlertCondition]
    enabled: bool = True
    cooldown_period: int = 300  # seconds
    max_alerts_per_hour: int = 10
    notification_channels: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertAction:
    """Action to take when an alert is triggered"""

    action_type: str  # notify, scale, restart, rollback, etc.
    target: str  # service, agent, component
    parameters: Dict[str, Any]
    delay_seconds: int = 0
    retry_count: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert instance"""

    alert_id: str
    rule_id: str
    alert_level: AlertLevel
    alert_type: AlertType
    title: str
    description: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    status: str = "active"  # active, resolved, suppressed
    affected_components: List[str] = field(default_factory=list)
    metrics_data: Dict[str, Any] = field(default_factory=dict)
    actions_taken: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertingConfig:
    """Configuration for intelligent alerting"""

    enable_alerting: bool = True
    enable_anomaly_detection: bool = True
    enable_adaptive_thresholds: bool = True
    enable_correlation: bool = True

    # Alerting settings
    default_cooldown_period: int = 300  # 5 minutes
    max_alerts_per_rule_per_hour: int = 10
    alert_retention_days: int = 30

    # Anomaly detection settings
    anomaly_threshold: float = 3.0  # standard deviations
    min_data_points: int = 10
    learning_period_days: int = 7

    # Notification settings
    notification_timeout: int = 30  # seconds
    retry_attempts: int = 3
    enable_escalation: bool = True
    escalation_delay: int = 900  # 15 minutes

    # Performance settings
    max_concurrent_evaluations: int = 20
    evaluation_interval: int = 60  # seconds
    batch_size: int = 100


class IntelligentAlertingService:
    """Intelligent alerting service with adaptive thresholds and anomaly detection"""

    def __init__(self, config: Optional[AlertingConfig] = None):
        self.config = config or AlertingConfig()
        self._initialized = False
        self._alert_rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self._evaluation_tasks: List[asyncio.Task] = []
        self._last_evaluation_time: Dict[str, datetime] = {}

        # Initialize alerting service
        self._initialize_alerting()

    def _initialize_alerting(self) -> None:
        """Initialize the intelligent alerting service"""
        try:
            self._initialized = True
            logger.info("Intelligent Alerting Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Intelligent Alerting Service: {e}")
            self._initialized = False

    async def create_alert_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        alert_type: AlertType,
        alert_level: AlertLevel,
        conditions: List[AlertCondition],
        enabled: bool = True,
        cooldown_period: Optional[int] = None,
        max_alerts_per_hour: Optional[int] = None,
        notification_channels: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Create a new alert rule"""
        try:
            if not self._initialized:
                return StepResult.fail("Intelligent Alerting Service not initialized")

            # Resolve tenant context
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"

            # Create alert rule
            alert_rule = AlertRule(
                rule_id=rule_id,
                name=name,
                description=description,
                alert_type=alert_type,
                alert_level=alert_level,
                conditions=conditions,
                enabled=enabled,
                cooldown_period=cooldown_period or self.config.default_cooldown_period,
                max_alerts_per_hour=max_alerts_per_hour
                or self.config.max_alerts_per_rule_per_hour,
                notification_channels=notification_channels or [],
                tags=tags or [],
                metadata={
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    **(metadata or {}),
                },
            )

            # Store alert rule
            self._alert_rules[rule_id] = alert_rule

            logger.info(f"Alert rule created: {rule_id} - {name}")

            return StepResult.ok(
                data={
                    "created": True,
                    "rule_id": rule_id,
                    "name": name,
                    "alert_type": alert_type.value,
                    "alert_level": alert_level.value,
                    "conditions_count": len(conditions),
                }
            )

        except Exception as e:
            logger.error(f"Error creating alert rule: {e}")
            return StepResult.fail(f"Alert rule creation failed: {str(e)}")

    async def evaluate_metric_for_alerts(
        self,
        metric_name: str,
        value: Union[int, float],
        timestamp: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Evaluate a metric against all applicable alert rules"""
        try:
            if not self._initialized:
                return StepResult.fail("Intelligent Alerting Service not initialized")

            # Resolve tenant context
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"

            timestamp = timestamp or datetime.now(timezone.utc)

            # Store metric in history
            if metric_name not in self._metrics_history:
                self._metrics_history[metric_name] = []

            self._metrics_history[metric_name].append(
                {
                    "value": value,
                    "timestamp": timestamp,
                    "labels": labels or {},
                    "metadata": metadata or {},
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                }
            )

            # Keep only recent metrics (last 24 hours)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            self._metrics_history[metric_name] = [
                m
                for m in self._metrics_history[metric_name]
                if m["timestamp"] > cutoff_time
            ]

            # Evaluate against alert rules
            triggered_alerts = []

            for rule_id, rule in self._alert_rules.items():
                if not rule.enabled:
                    continue

                # Check if rule applies to this metric
                if not self._rule_applies_to_metric(
                    rule, metric_name, tenant_id, workspace_id
                ):
                    continue

                # Check cooldown period
                if self._is_rule_in_cooldown(rule_id, timestamp):
                    continue

                # Check rate limiting
                if self._is_rate_limited(rule_id, timestamp):
                    continue

                # Evaluate conditions
                if await self._evaluate_alert_conditions(
                    rule, metric_name, value, timestamp
                ):
                    # Trigger alert
                    alert = await self._trigger_alert(
                        rule, metric_name, value, timestamp, labels, metadata
                    )
                    if alert:
                        triggered_alerts.append(alert)

            # Also check for anomalies if enabled
            if self.config.enable_anomaly_detection:
                anomaly_alerts = await self._detect_anomalies(
                    metric_name, value, timestamp, tenant_id, workspace_id
                )
                triggered_alerts.extend(anomaly_alerts)

            return StepResult.ok(
                data={
                    "evaluated": True,
                    "metric_name": metric_name,
                    "value": value,
                    "timestamp": timestamp.isoformat(),
                    "triggered_alerts": len(triggered_alerts),
                    "alert_ids": [alert.alert_id for alert in triggered_alerts],
                }
            )

        except Exception as e:
            logger.error(f"Error evaluating metric for alerts: {e}")
            return StepResult.fail(f"Metric evaluation failed: {str(e)}")

    async def resolve_alert(
        self,
        alert_id: str,
        resolution_reason: str,
        resolved_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StepResult:
        """Resolve an active alert"""
        try:
            if not self._initialized:
                return StepResult.fail("Intelligent Alerting Service not initialized")

            if alert_id not in self._active_alerts:
                return StepResult.fail(
                    f"Alert {alert_id} not found or already resolved"
                )

            alert = self._active_alerts[alert_id]
            alert.status = "resolved"
            alert.resolved_at = datetime.now(timezone.utc)
            alert.metadata.update(
                {
                    "resolution_reason": resolution_reason,
                    "resolved_by": resolved_by,
                    "resolved_at": alert.resolved_at.isoformat(),
                    **(metadata or {}),
                }
            )

            # Move to history
            self._alert_history.append(alert)
            del self._active_alerts[alert_id]

            logger.info(f"Alert resolved: {alert_id} - {resolution_reason}")

            return StepResult.ok(
                data={
                    "resolved": True,
                    "alert_id": alert_id,
                    "resolution_reason": resolution_reason,
                    "resolved_by": resolved_by,
                    "resolved_at": alert.resolved_at.isoformat(),
                }
            )

        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return StepResult.fail(f"Alert resolution failed: {str(e)}")

    async def get_active_alerts(
        self,
        alert_level: Optional[AlertLevel] = None,
        alert_type: Optional[AlertType] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Get all active alerts matching criteria"""
        try:
            if not self._initialized:
                return StepResult.fail("Intelligent Alerting Service not initialized")

            filtered_alerts = []

            for alert in self._active_alerts.values():
                # Apply filters
                if alert_level and alert.alert_level != alert_level:
                    continue
                if alert_type and alert.alert_type != alert_type:
                    continue
                if tenant_id and alert.metadata.get("tenant_id") != tenant_id:
                    continue
                if workspace_id and alert.metadata.get("workspace_id") != workspace_id:
                    continue

                filtered_alerts.append(alert)

            return StepResult.ok(
                data={
                    "active_alerts": filtered_alerts,
                    "total_count": len(filtered_alerts),
                    "filtered_by": {
                        "alert_level": alert_level.value if alert_level else None,
                        "alert_type": alert_type.value if alert_type else None,
                        "tenant_id": tenant_id,
                        "workspace_id": workspace_id,
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return StepResult.fail(f"Active alerts retrieval failed: {str(e)}")

    async def get_alert_statistics(
        self,
        hours: int = 24,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Get alert statistics for specified time period"""
        try:
            if not self._initialized:
                return StepResult.fail("Intelligent Alerting Service not initialized")

            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)

            # Filter alerts by time and criteria
            filtered_alerts = []
            all_alerts = list(self._active_alerts.values()) + self._alert_history

            for alert in all_alerts:
                if alert.triggered_at < start_time or alert.triggered_at > end_time:
                    continue
                if tenant_id and alert.metadata.get("tenant_id") != tenant_id:
                    continue
                if workspace_id and alert.metadata.get("workspace_id") != workspace_id:
                    continue

                filtered_alerts.append(alert)

            if not filtered_alerts:
                return StepResult.ok(
                    data={
                        "statistics": {
                            "total_alerts": 0,
                            "time_range": {
                                "start": start_time.isoformat(),
                                "end": end_time.isoformat(),
                                "hours": hours,
                            },
                        }
                    }
                )

            # Calculate statistics
            total_alerts = len(filtered_alerts)
            active_alerts = len([a for a in filtered_alerts if a.status == "active"])
            resolved_alerts = len(
                [a for a in filtered_alerts if a.status == "resolved"]
            )

            # Group by alert level
            level_counts = {}
            for alert in filtered_alerts:
                level = alert.alert_level.value
                level_counts[level] = level_counts.get(level, 0) + 1

            # Group by alert type
            type_counts = {}
            for alert in filtered_alerts:
                alert_type = alert.alert_type.value
                type_counts[alert_type] = type_counts.get(alert_type, 0) + 1

            # Group by rule
            rule_counts = {}
            for alert in filtered_alerts:
                rule_id = alert.rule_id
                rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1

            # Calculate resolution time statistics
            resolved_with_times = [a for a in filtered_alerts if a.resolved_at]
            if resolved_with_times:
                resolution_times = [
                    (a.resolved_at - a.triggered_at).total_seconds()
                    for a in resolved_with_times
                ]
                avg_resolution_time = sum(resolution_times) / len(resolution_times)
                min_resolution_time = min(resolution_times)
                max_resolution_time = max(resolution_times)
            else:
                avg_resolution_time = min_resolution_time = max_resolution_time = 0

            return StepResult.ok(
                data={
                    "statistics": {
                        "total_alerts": total_alerts,
                        "active_alerts": active_alerts,
                        "resolved_alerts": resolved_alerts,
                        "resolution_rate": resolved_alerts / total_alerts
                        if total_alerts > 0
                        else 0,
                        "alert_levels": level_counts,
                        "alert_types": type_counts,
                        "top_rules": sorted(
                            rule_counts.items(), key=lambda x: x[1], reverse=True
                        )[:10],
                        "resolution_times": {
                            "average_seconds": avg_resolution_time,
                            "min_seconds": min_resolution_time,
                            "max_seconds": max_resolution_time,
                        },
                        "time_range": {
                            "start": start_time.isoformat(),
                            "end": end_time.isoformat(),
                            "hours": hours,
                        },
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return StepResult.fail(f"Alert statistics retrieval failed: {str(e)}")

    def _rule_applies_to_metric(
        self, rule: AlertRule, metric_name: str, tenant_id: str, workspace_id: str
    ) -> bool:
        """Check if an alert rule applies to a metric"""
        try:
            # Check if any condition matches the metric
            for condition in rule.conditions:
                if condition.metric_name == metric_name:
                    return True

            # Check tenant/workspace match
            if (
                rule.metadata.get("tenant_id")
                and rule.metadata.get("tenant_id") != tenant_id
            ):
                return False
            if (
                rule.metadata.get("workspace_id")
                and rule.metadata.get("workspace_id") != workspace_id
            ):
                return False

            return False

        except Exception:
            return False

    def _is_rule_in_cooldown(self, rule_id: str, timestamp: datetime) -> bool:
        """Check if a rule is in cooldown period"""
        try:
            if rule_id not in self._last_evaluation_time:
                return False

            rule = self._alert_rules.get(rule_id)
            if not rule:
                return False

            cooldown_end = self._last_evaluation_time[rule_id] + timedelta(
                seconds=rule.cooldown_period
            )
            return timestamp < cooldown_end

        except Exception:
            return False

    def _is_rate_limited(self, rule_id: str, timestamp: datetime) -> bool:
        """Check if a rule is rate limited"""
        try:
            rule = self._alert_rules.get(rule_id)
            if not rule:
                return True

            # Count alerts in the last hour
            hour_ago = timestamp - timedelta(hours=1)
            recent_alerts = [
                alert
                for alert in self._alert_history
                if alert.rule_id == rule_id and alert.triggered_at > hour_ago
            ]

            return len(recent_alerts) >= rule.max_alerts_per_hour

        except Exception:
            return True

    async def _evaluate_alert_conditions(
        self,
        rule: AlertRule,
        metric_name: str,
        value: Union[int, float],
        timestamp: datetime,
    ) -> bool:
        """Evaluate alert conditions for a rule"""
        try:
            for condition in rule.conditions:
                if condition.metric_name != metric_name:
                    continue

                # Evaluate the condition
                if condition.operator == ">":
                    if value <= condition.threshold_value:
                        continue
                elif condition.operator == "<":
                    if value >= condition.threshold_value:
                        continue
                elif condition.operator == ">=":
                    if value < condition.threshold_value:
                        continue
                elif condition.operator == "<=":
                    if value > condition.threshold_value:
                        continue
                elif condition.operator == "==":
                    if value != condition.threshold_value:
                        continue
                elif condition.operator == "!=":
                    if value == condition.threshold_value:
                        continue

                # Condition met
                return True

            return False

        except Exception as e:
            logger.error(f"Error evaluating alert conditions: {e}")
            return False

    async def _trigger_alert(
        self,
        rule: AlertRule,
        metric_name: str,
        value: Union[int, float],
        timestamp: datetime,
        labels: Optional[Dict[str, str]],
        metadata: Optional[Dict[str, Any]],
    ) -> Optional[Alert]:
        """Trigger an alert based on a rule"""
        try:
            # Generate alert ID
            alert_id = f"{rule.rule_id}:{int(timestamp.timestamp())}"

            # Create alert
            alert = Alert(
                alert_id=alert_id,
                rule_id=rule.rule_id,
                alert_level=rule.alert_level,
                alert_type=rule.alert_type,
                title=f"{rule.name} - {metric_name}",
                description=f"{rule.description}\nMetric: {metric_name} = {value}",
                triggered_at=timestamp,
                affected_components=[metric_name],
                metrics_data={
                    "metric_name": metric_name,
                    "value": value,
                    "labels": labels or {},
                    "timestamp": timestamp.isoformat(),
                },
                metadata={
                    "rule_name": rule.name,
                    "rule_description": rule.description,
                    "conditions": [
                        {
                            "metric_name": c.metric_name,
                            "operator": c.operator,
                            "threshold": c.threshold_value,
                        }
                        for c in rule.conditions
                    ],
                    **(metadata or {}),
                },
            )

            # Store alert
            self._active_alerts[alert_id] = alert
            self._last_evaluation_time[rule.rule_id] = timestamp

            # Send notifications
            await self._send_notifications(alert, rule)

            logger.warning(f"Alert triggered: {alert_id} - {alert.title}")

            return alert

        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
            return None

    async def _detect_anomalies(
        self,
        metric_name: str,
        value: Union[int, float],
        timestamp: datetime,
        tenant_id: str,
        workspace_id: str,
    ) -> List[Alert]:
        """Detect anomalies in metric values"""
        try:
            anomalies = []

            if metric_name not in self._metrics_history:
                return anomalies

            # Get recent values for anomaly detection
            recent_values = [
                m["value"]
                for m in self._metrics_history[metric_name]
                if (timestamp - m["timestamp"]).total_seconds() < 3600  # Last hour
            ]

            if len(recent_values) < self.config.min_data_points:
                return anomalies

            # Calculate statistics
            mean_value = sum(recent_values) / len(recent_values)
            variance = sum((x - mean_value) ** 2 for x in recent_values) / len(
                recent_values
            )
            std_dev = variance**0.5

            if std_dev == 0:
                return anomalies

            # Check if current value is an anomaly
            z_score = abs(value - mean_value) / std_dev

            if z_score >= self.config.anomaly_threshold:
                # Create anomaly alert
                alert_id = f"anomaly:{metric_name}:{int(timestamp.timestamp())}"

                alert = Alert(
                    alert_id=alert_id,
                    rule_id="anomaly_detection",
                    alert_level=AlertLevel.WARNING,
                    alert_type=AlertType.ANOMALY,
                    title=f"Anomaly detected in {metric_name}",
                    description=f"Metric {metric_name} shows anomalous behavior. Value: {value}, Z-score: {z_score:.2f}",
                    triggered_at=timestamp,
                    affected_components=[metric_name],
                    metrics_data={
                        "metric_name": metric_name,
                        "value": value,
                        "mean": mean_value,
                        "std_dev": std_dev,
                        "z_score": z_score,
                        "threshold": self.config.anomaly_threshold,
                        "timestamp": timestamp.isoformat(),
                    },
                    metadata={
                        "anomaly_type": "statistical",
                        "detection_method": "z_score",
                        "tenant_id": tenant_id,
                        "workspace_id": workspace_id,
                    },
                )

                self._active_alerts[alert_id] = alert
                anomalies.append(alert)

                logger.warning(
                    f"Anomaly detected: {metric_name} - Z-score: {z_score:.2f}"
                )

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    async def _send_notifications(self, alert: Alert, rule: AlertRule) -> None:
        """Send notifications for an alert"""
        try:
            if not rule.notification_channels:
                return

            # Prepare notification data
            notification_data = {
                "alert_id": alert.alert_id,
                "title": alert.title,
                "description": alert.description,
                "alert_level": alert.alert_level.value,
                "alert_type": alert.alert_type.value,
                "triggered_at": alert.triggered_at.isoformat(),
                "affected_components": alert.affected_components,
                "metrics_data": alert.metrics_data,
                "rule_name": rule.name,
            }

            # Send to each notification channel
            for channel in rule.notification_channels:
                try:
                    await self._send_notification_to_channel(channel, notification_data)
                except Exception as e:
                    logger.error(f"Failed to send notification to {channel}: {e}")

        except Exception as e:
            logger.error(f"Error sending notifications: {e}")

    async def _send_notification_to_channel(
        self, channel: str, data: Dict[str, Any]
    ) -> None:
        """Send notification to a specific channel"""
        try:
            # This would integrate with actual notification systems
            # For now, just log the notification
            logger.info(f"Notification sent to {channel}: {data['title']}")

            # TODO: Implement actual notification channels
            # - Discord webhooks
            # - Email
            # - Slack
            # - PagerDuty
            # - SMS

        except Exception as e:
            logger.error(f"Error sending notification to channel {channel}: {e}")

    def get_alerting_status(self) -> Dict[str, Any]:
        """Get alerting service status"""
        return {
            "initialized": self._initialized,
            "total_rules": len(self._alert_rules),
            "active_alerts": len(self._active_alerts),
            "total_alert_history": len(self._alert_history),
            "metrics_tracked": len(self._metrics_history),
            "config": {
                "enable_alerting": self.config.enable_alerting,
                "enable_anomaly_detection": self.config.enable_anomaly_detection,
                "enable_adaptive_thresholds": self.config.enable_adaptive_thresholds,
                "anomaly_threshold": self.config.anomaly_threshold,
                "evaluation_interval": self.config.evaluation_interval,
            },
        }
