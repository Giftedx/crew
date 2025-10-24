"""Cost alert management system for budget monitoring and notifications.

This module provides comprehensive cost alerting capabilities that integrate
with the existing BudgetManager, CostOptimizer, and alert infrastructure.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels for cost monitoring."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    """Types of cost alerts."""

    BUDGET_THRESHOLD = "budget_threshold"
    BUDGET_EXCEEDED = "budget_exceeded"
    HIGH_COST_REQUEST = "high_cost_request"
    COST_SPIKE = "cost_spike"
    DAILY_LIMIT_APPROACHING = "daily_limit_approaching"
    DAILY_LIMIT_EXCEEDED = "daily_limit_exceeded"
    PER_REQUEST_LIMIT_EXCEEDED = "per_request_limit_exceeded"
    COST_OPTIMIZATION_OPPORTUNITY = "cost_optimization_opportunity"
    MODEL_COST_ANOMALY = "model_cost_anomaly"


@dataclass
class CostAlert:
    """Represents a cost-related alert."""

    alert_type: AlertType
    severity: AlertSeverity
    message: str
    cost_usd: float
    budget_limit: float
    utilization_percent: float
    tenant_id: str
    workspace_id: str
    model_used: str = ""
    component: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert alert to dictionary for serialization."""
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "cost_usd": self.cost_usd,
            "budget_limit": self.budget_limit,
            "utilization_percent": self.utilization_percent,
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "model_used": self.model_used,
            "component": self.component,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class AlertThresholds:
    """Configuration for alert thresholds."""

    # Budget utilization thresholds
    budget_warning_percent: float = 70.0
    budget_critical_percent: float = 90.0
    budget_emergency_percent: float = 95.0

    # Cost spike detection
    cost_spike_multiplier: float = 3.0  # 3x average cost
    cost_spike_window_minutes: int = 15  # 15-minute window

    # High cost request threshold
    high_cost_request_usd: float = 0.10  # $0.10 per request

    # Daily budget thresholds
    daily_warning_percent: float = 75.0
    daily_critical_percent: float = 90.0

    # Model cost anomaly detection
    model_cost_anomaly_multiplier: float = 2.5  # 2.5x average model cost


class CostAlertManager:
    """Manages cost alerts and integrates with existing systems."""

    def __init__(self, thresholds: AlertThresholds | None = None):
        self.thresholds = thresholds or AlertThresholds()
        self.alert_history: list[CostAlert] = []
        self.cost_history: list[dict[str, Any]] = []
        self._last_alert_times: dict[str, float] = {}
        self._alert_cooldown_seconds = 300  # 5 minutes cooldown between same alerts

    def check_cost_alerts(
        self,
        cost_usd: float,
        model: str,
        component: str,
        tenant_id: str,
        workspace_id: str,
        budget_manager: Any,  # BudgetManager from token_meter
        cost_optimizer: Any,  # CostOptimizer
    ) -> StepResult:
        """Check for cost alerts and generate notifications."""
        try:
            alerts_generated = []

            # Record cost for analysis
            self.cost_history.append(
                {
                    "cost_usd": cost_usd,
                    "model": model,
                    "component": component,
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "timestamp": time.time(),
                }
            )

            # Check per-request cost alert
            if cost_usd > self.thresholds.high_cost_request_usd:
                alert = self._create_alert(
                    AlertType.HIGH_COST_REQUEST,
                    AlertSeverity.WARNING,
                    f"High cost request: ${cost_usd:.4f} (limit: ${self.thresholds.high_cost_request_usd:.4f})",
                    cost_usd,
                    self.thresholds.high_cost_request_usd,
                    (cost_usd / self.thresholds.high_cost_request_usd) * 100,
                    tenant_id,
                    workspace_id,
                    model,
                    component,
                )
                alerts_generated.append(alert)

            # Check per-request budget limit
            if cost_usd > budget_manager.max_per_request:
                alert = self._create_alert(
                    AlertType.PER_REQUEST_LIMIT_EXCEEDED,
                    AlertSeverity.CRITICAL,
                    f"Per-request budget exceeded: ${cost_usd:.4f} > ${budget_manager.max_per_request:.4f}",
                    cost_usd,
                    budget_manager.max_per_request,
                    (cost_usd / budget_manager.max_per_request) * 100,
                    tenant_id,
                    workspace_id,
                    model,
                    component,
                )
                alerts_generated.append(alert)

            # Check daily budget utilization
            daily_spend = budget_manager.spent_today
            daily_utilization = (daily_spend / budget_manager.daily_budget) * 100

            if daily_utilization >= self.thresholds.budget_emergency_percent:
                alert = self._create_alert(
                    AlertType.DAILY_LIMIT_EXCEEDED,
                    AlertSeverity.EMERGENCY,
                    f"Daily budget exceeded: ${daily_spend:.2f} > ${budget_manager.daily_budget:.2f}",
                    daily_spend,
                    budget_manager.daily_budget,
                    daily_utilization,
                    tenant_id,
                    workspace_id,
                    model,
                    component,
                )
                alerts_generated.append(alert)
            elif daily_utilization >= self.thresholds.budget_critical_percent:
                alert = self._create_alert(
                    AlertType.DAILY_LIMIT_APPROACHING,
                    AlertSeverity.CRITICAL,
                    f"Daily budget critical: ${daily_spend:.2f} ({daily_utilization:.1f}% of ${budget_manager.daily_budget:.2f})",
                    daily_spend,
                    budget_manager.daily_budget,
                    daily_utilization,
                    tenant_id,
                    workspace_id,
                    model,
                    component,
                )
                alerts_generated.append(alert)
            elif daily_utilization >= self.thresholds.budget_warning_percent:
                alert = self._create_alert(
                    AlertType.DAILY_LIMIT_APPROACHING,
                    AlertSeverity.WARNING,
                    f"Daily budget warning: ${daily_spend:.2f} ({daily_utilization:.1f}% of ${budget_manager.daily_budget:.2f})",
                    daily_spend,
                    budget_manager.daily_budget,
                    daily_utilization,
                    tenant_id,
                    workspace_id,
                    model,
                    component,
                )
                alerts_generated.append(alert)

            # Check for cost spikes
            spike_alert = self._check_cost_spike(cost_usd, tenant_id, workspace_id, model, component)
            if spike_alert:
                alerts_generated.append(spike_alert)

            # Check for model cost anomalies
            anomaly_alert = self._check_model_cost_anomaly(cost_usd, model, tenant_id, workspace_id, component)
            if anomaly_alert:
                alerts_generated.append(anomaly_alert)

            # Process and record alerts
            for alert in alerts_generated:
                self._process_alert(alert)

            return StepResult.ok(
                data={
                    "alerts_generated": len(alerts_generated),
                    "alerts": [alert.to_dict() for alert in alerts_generated],
                    "daily_spend": daily_spend,
                    "daily_utilization_percent": daily_utilization,
                }
            )

        except Exception as e:
            logger.error(f"Cost alert checking failed: {e}")
            return StepResult.fail(f"Cost alert checking failed: {e!s}")

    def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        cost_usd: float,
        budget_limit: float,
        utilization_percent: float,
        tenant_id: str,
        workspace_id: str,
        model: str,
        component: str,
        metadata: dict[str, Any] | None = None,
    ) -> CostAlert:
        """Create a cost alert."""
        return CostAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            cost_usd=cost_usd,
            budget_limit=budget_limit,
            utilization_percent=utilization_percent,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            model_used=model,
            component=component,
            metadata=metadata or {},
        )

    def _check_cost_spike(
        self,
        cost_usd: float,
        tenant_id: str,
        workspace_id: str,
        model: str,
        component: str,
    ) -> CostAlert | None:
        """Check for cost spikes in recent history."""
        try:
            # Get recent costs within the spike window
            window_start = time.time() - (self.thresholds.cost_spike_window_minutes * 60)
            recent_costs = [
                entry["cost_usd"]
                for entry in self.cost_history
                if entry["timestamp"] >= window_start
                and entry["tenant_id"] == tenant_id
                and entry["workspace_id"] == workspace_id
            ]

            if len(recent_costs) < 3:  # Need at least 3 data points
                return None

            # Calculate average cost (excluding current)
            avg_cost = sum(recent_costs[:-1]) / len(recent_costs[:-1])

            # Check if current cost is a spike
            if cost_usd > avg_cost * self.thresholds.cost_spike_multiplier:
                return self._create_alert(
                    AlertType.COST_SPIKE,
                    AlertSeverity.WARNING,
                    f"Cost spike detected: ${cost_usd:.4f} (avg: ${avg_cost:.4f}, {cost_usd / avg_cost:.1f}x)",
                    cost_usd,
                    avg_cost,
                    (cost_usd / avg_cost) * 100,
                    tenant_id,
                    workspace_id,
                    model,
                    component,
                    metadata={
                        "average_cost": avg_cost,
                        "spike_multiplier": cost_usd / avg_cost,
                    },
                )

            return None

        except Exception as e:
            logger.error(f"Cost spike detection failed: {e}")
            return None

    def _check_model_cost_anomaly(
        self,
        cost_usd: float,
        model: str,
        tenant_id: str,
        workspace_id: str,
        component: str,
    ) -> CostAlert | None:
        """Check for model cost anomalies."""
        try:
            # Get historical costs for this model
            model_costs = [
                entry["cost_usd"]
                for entry in self.cost_history
                if entry["model"] == model and entry["tenant_id"] == tenant_id and entry["workspace_id"] == workspace_id
            ]

            if len(model_costs) < 5:  # Need at least 5 data points
                return None

            # Calculate average cost (excluding current)
            avg_model_cost = sum(model_costs[:-1]) / len(model_costs[:-1])

            # Check if current cost is anomalous
            if cost_usd > avg_model_cost * self.thresholds.model_cost_anomaly_multiplier:
                return self._create_alert(
                    AlertType.MODEL_COST_ANOMALY,
                    AlertSeverity.WARNING,
                    f"Model cost anomaly: {model} cost ${cost_usd:.4f} (avg: ${avg_model_cost:.4f}, {cost_usd / avg_model_cost:.1f}x)",
                    cost_usd,
                    avg_model_cost,
                    (cost_usd / avg_model_cost) * 100,
                    tenant_id,
                    workspace_id,
                    model,
                    component,
                    metadata={
                        "average_model_cost": avg_model_cost,
                        "anomaly_multiplier": cost_usd / avg_model_cost,
                    },
                )

            return None

        except Exception as e:
            logger.error(f"Model cost anomaly detection failed: {e}")
            return None

    def _process_alert(self, alert: CostAlert) -> None:
        """Process and record an alert."""
        try:
            # Check cooldown to avoid spam
            alert_key = f"{alert.alert_type.value}:{alert.tenant_id}:{alert.workspace_id}"
            now = time.time()

            if alert_key in self._last_alert_times:
                time_since_last = now - self._last_alert_times[alert_key]
                if time_since_last < self._alert_cooldown_seconds:
                    logger.debug(f"Alert {alert_key} suppressed due to cooldown")
                    return

            # Record alert
            self.alert_history.append(alert)
            self._last_alert_times[alert_key] = now

            # Send to alert system
            self._send_alert(alert)

            logger.info(f"Cost alert generated: {alert.severity.value} - {alert.message}")

        except Exception as e:
            logger.error(f"Alert processing failed: {e}")

    def _send_alert(self, alert: CostAlert) -> None:
        """Send alert to external systems."""
        try:
            # Integrate with existing alert system
            from core.alerts import alerts

            alert_message = (
                f"[{alert.severity.value.upper()}] {alert.alert_type.value}: {alert.message}\n"
                f"Tenant: {alert.tenant_id}, Workspace: {alert.workspace_id}\n"
                f"Model: {alert.model_used}, Component: {alert.component}\n"
                f"Cost: ${alert.cost_usd:.4f}, Utilization: {alert.utilization_percent:.1f}%"
            )

            alerts.record(alert_message)

            # Send to Discord if configured
            self._send_discord_alert(alert)

        except Exception as e:
            logger.error(f"Alert sending failed: {e}")

    def _send_discord_alert(self, alert: CostAlert) -> None:
        """Send cost alert to Discord."""
        try:
            # Only send critical and emergency alerts to Discord
            if alert.severity not in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
                return

            # Format Discord message
            emoji_map = {
                AlertSeverity.CRITICAL: "⚠️",
                AlertSeverity.EMERGENCY: "🚨",
            }

            emoji = emoji_map.get(alert.severity, "ℹ️")

            discord_message = (
                f"{emoji} **Cost Alert: {alert.severity.value.upper()}**\n"
                f"**Type:** {alert.alert_type.value}\n"
                f"**Message:** {alert.message}\n"
                f"**Tenant:** {alert.tenant_id}\n"
                f"**Workspace:** {alert.workspace_id}\n"
                f"**Cost:** ${alert.cost_usd:.4f}\n"
                f"**Model:** {alert.model_used}\n"
                f"**Component:** {alert.component}"
            )

            # Send to Discord webhook (if configured)
            from core.http_utils import resilient_post
            from core.secure_config import get_config

            try:
                config = get_config()
                webhook = config.get_webhook("discord_alert")

                resilient_post(
                    webhook,
                    json_payload={"content": discord_message[:1900]},  # Discord limit
                    headers={"Content-Type": "application/json"},
                    timeout_seconds=10,
                )

                logger.info(f"Discord cost alert sent: {alert.alert_type.value}")

            except ValueError:
                logger.debug("Discord alert webhook not configured")
            except Exception as e:
                logger.error(f"Discord alert sending failed: {e}")

        except Exception as e:
            logger.error(f"Discord alert processing failed: {e}")

    def get_alert_summary(self, tenant_id: str | None = None, workspace_id: str | None = None) -> StepResult:
        """Get summary of recent alerts."""
        try:
            # Filter alerts by tenant/workspace if specified
            filtered_alerts = self.alert_history
            if tenant_id:
                filtered_alerts = [a for a in filtered_alerts if a.tenant_id == tenant_id]
            if workspace_id:
                filtered_alerts = [a for a in filtered_alerts if a.workspace_id == workspace_id]

            # Get recent alerts (last 24 hours)
            recent_time = time.time() - (24 * 60 * 60)
            recent_alerts = [a for a in filtered_alerts if a.timestamp >= recent_time]

            # Group by severity
            severity_counts: dict[str, int] = {}
            alert_type_counts: dict[str, int] = {}

            for alert in recent_alerts:
                severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
                alert_type_counts[alert.alert_type.value] = alert_type_counts.get(alert.alert_type.value, 0) + 1

            return StepResult.ok(
                data={
                    "total_alerts": len(filtered_alerts),
                    "recent_alerts_24h": len(recent_alerts),
                    "severity_breakdown": severity_counts,
                    "alert_type_breakdown": alert_type_counts,
                    "latest_alerts": [alert.to_dict() for alert in recent_alerts[-5:]],  # Last 5 alerts
                }
            )

        except Exception as e:
            logger.error(f"Alert summary generation failed: {e}")
            return StepResult.fail(f"Alert summary failed: {e!s}")

    def clear_alert_history(self, tenant_id: str | None = None) -> StepResult:
        """Clear alert history for a tenant or all tenants."""
        try:
            if tenant_id:
                self.alert_history = [a for a in self.alert_history if a.tenant_id != tenant_id]
            else:
                self.alert_history.clear()

            return StepResult.ok(data={"cleared": True})

        except Exception as e:
            logger.error(f"Alert history clearing failed: {e}")
            return StepResult.fail(f"Alert history clearing failed: {e!s}")

    def health_check(self) -> StepResult:
        """Health check for the cost alert manager."""
        try:
            return StepResult.ok(
                data={
                    "cost_alert_manager_healthy": True,
                    "total_alerts": len(self.alert_history),
                    "cost_history_entries": len(self.cost_history),
                    "thresholds": {
                        "budget_warning_percent": self.thresholds.budget_warning_percent,
                        "budget_critical_percent": self.thresholds.budget_critical_percent,
                        "budget_emergency_percent": self.thresholds.budget_emergency_percent,
                        "cost_spike_multiplier": self.thresholds.cost_spike_multiplier,
                        "high_cost_request_usd": self.thresholds.high_cost_request_usd,
                    },
                    "alert_cooldown_seconds": self._alert_cooldown_seconds,
                    "timestamp": time.time(),
                }
            )

        except Exception as e:
            logger.error(f"Cost alert manager health check failed: {e}")
            return StepResult.fail(f"Health check failed: {e!s}")


# Global cost alert manager instance
_cost_alert_manager: CostAlertManager | None = None


def get_cost_alert_manager() -> CostAlertManager:
    """Get the global cost alert manager instance."""
    global _cost_alert_manager
    if _cost_alert_manager is None:
        _cost_alert_manager = CostAlertManager()
    return _cost_alert_manager


__all__ = [
    "AlertSeverity",
    "AlertThresholds",
    "AlertType",
    "CostAlert",
    "CostAlertManager",
    "get_cost_alert_manager",
]
