"""
Advanced Performance Analytics Discord Integration

This module provides Discord integration for the Advanced Performance Analytics Alert Engine,
bridging analytics insights with the existing Discord notification infrastructure.

Key Features:
- Integration with existing DiscordPrivateAlertTool
- Formatted notifications with metrics and executive summaries
- Alert escalation and routing based on severity
- Real-time analytics dashboard notifications
- Executive reporting through Discord channels
- Automated notification scheduling and management
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from platform.time import default_utc_now
from typing import Any

from .advanced_performance_analytics_alert_engine import (
    AdvancedPerformanceAnalyticsAlertEngine,
    AlertSeverity,
    PerformanceAlert,
)
from .tools.discord_private_alert_tool import DiscordPrivateAlertTool


logger = logging.getLogger(__name__)


@dataclass
class DiscordNotificationConfig:
    """Configuration for Discord notifications."""

    enabled: bool = True
    primary_webhook_url: str | None = None
    private_webhook_url: str | None = None
    executive_webhook_url: str | None = None
    severity_routing: dict[AlertSeverity, str] | None = None
    notification_cooldown_minutes: int = 15
    batch_notifications: bool = True
    include_metrics: bool = True
    include_recommendations: bool = True
    max_message_length: int = 1900


class AdvancedPerformanceAnalyticsDiscordIntegration:
    """Discord integration for Advanced Performance Analytics."""

    def __init__(
        self,
        alert_engine: AdvancedPerformanceAnalyticsAlertEngine | None = None,
        config: DiscordNotificationConfig | None = None,
    ):
        """Initialize Discord integration.

        Args:
            alert_engine: Alert engine instance
            config: Discord notification configuration
        """
        self.alert_engine = alert_engine or AdvancedPerformanceAnalyticsAlertEngine()
        self.config = config or DiscordNotificationConfig()
        self.notification_history: list[dict[str, Any]] = []
        self.last_notification_times: dict[str, datetime] = {}
        self.primary_alert_tool: DiscordPrivateAlertTool | None = None
        self.private_alert_tool: DiscordPrivateAlertTool | None = None
        self.executive_alert_tool: DiscordPrivateAlertTool | None = None
        self._initialize_discord_tools()

    def _initialize_discord_tools(self) -> None:
        """Initialize Discord notification tools."""
        try:
            if self.config.primary_webhook_url:
                self.primary_alert_tool = DiscordPrivateAlertTool(self.config.primary_webhook_url)
            else:
                self.primary_alert_tool = None
            if self.config.private_webhook_url:
                self.private_alert_tool = DiscordPrivateAlertTool(self.config.private_webhook_url)
            else:
                self.private_alert_tool = None
            if self.config.executive_webhook_url:
                self.executive_alert_tool = DiscordPrivateAlertTool(self.config.executive_webhook_url)
            else:
                self.executive_alert_tool = None
            logger.info("Initialized Discord notification tools")
        except Exception as e:
            logger.error(f"Error initializing Discord tools: {e}")

    def _get_alert_tool_for_severity(self, severity: AlertSeverity) -> DiscordPrivateAlertTool | None:
        """Get appropriate Discord tool based on alert severity.

        Args:
            severity: Alert severity level

        Returns:
            Discord alert tool or None if not configured
        """
        if self.config.severity_routing and severity in self.config.severity_routing:
            webhook_url = self.config.severity_routing[severity]
            return DiscordPrivateAlertTool(webhook_url)
        if severity == AlertSeverity.CRITICAL:
            return self.private_alert_tool or self.primary_alert_tool
        elif severity == AlertSeverity.WARNING:
            return self.primary_alert_tool
        else:
            return self.primary_alert_tool

    def _format_alert_for_discord(self, alert: PerformanceAlert) -> dict[str, Any]:
        """Format alert for Discord with enhanced formatting.

        Args:
            alert: Performance alert to format

        Returns:
            Formatted Discord message
        """
        discord_data = alert.to_discord_format()
        if not self.config.include_metrics:
            content_lines = discord_data["content"].split("\n")
            filtered_lines = []
            skip_metrics = False
            for line in content_lines:
                if line.startswith("**Metrics:**"):
                    skip_metrics = True
                    continue
                elif line.startswith("**") and skip_metrics:
                    skip_metrics = False
                if not skip_metrics:
                    filtered_lines.append(line)
            discord_data["content"] = "\n".join(filtered_lines)
        if not self.config.include_recommendations:
            content = discord_data["content"]
            if "**Recommendations:**" in content:
                content = content.split("**Recommendations:**")[0].rstrip()
                discord_data["content"] = content
        if len(discord_data["content"]) > self.config.max_message_length:
            truncated_content = discord_data["content"][: self.config.max_message_length - 50]
            discord_data["content"] = truncated_content + "\n...\n*[Message truncated]*"
        discord_data["analytics_integration"] = {
            "alert_id": alert.alert_id,
            "severity": alert.severity.value,
            "category": alert.category.value,
            "timestamp": alert.timestamp.isoformat(),
        }
        return discord_data

    async def send_alert_notification(self, alert: PerformanceAlert) -> dict[str, Any]:
        """Send alert notification through Discord.

        Args:
            alert: Performance alert to send

        Returns:
            Notification result with status and metadata
        """
        try:
            if not self.config.enabled:
                return {"status": "disabled", "message": "Discord notifications are disabled"}
            cooldown_key = f"{alert.severity.value}_{alert.category.value}"
            if self._is_notification_in_cooldown(cooldown_key):
                return {
                    "status": "cooldown",
                    "message": f"Notification type {cooldown_key} is in cooldown period",
                    "alert_id": alert.alert_id,
                }
            alert_tool = self._get_alert_tool_for_severity(alert.severity)
            if not alert_tool:
                return {
                    "status": "no_tool",
                    "message": f"No Discord tool configured for severity {alert.severity.value}",
                    "alert_id": alert.alert_id,
                }
            discord_data = self._format_alert_for_discord(alert)
            result = alert_tool._run(
                message=discord_data["content"], metrics=alert.metrics, thresholds=alert.thresholds
            )
            notification_record = {
                "alert_id": alert.alert_id,
                "severity": alert.severity.value,
                "category": alert.category.value,
                "timestamp": default_utc_now(),
                "status": "success" if result.success else "failed",
                "webhook_used": alert_tool.webhook_url if hasattr(alert_tool, "webhook_url") else "unknown",
                "message_length": len(discord_data["content"]),
                "result": result.to_dict() if hasattr(result, "to_dict") else str(result),
            }
            self.notification_history.append(notification_record)
            self.last_notification_times[cooldown_key] = default_utc_now()
            if len(self.notification_history) > 500:
                self.notification_history = self.notification_history[-500:]
            if result.success:
                logger.info(f"Successfully sent Discord notification for alert {alert.alert_id}")
                return {
                    "status": "success",
                    "alert_id": alert.alert_id,
                    "notification_id": notification_record["timestamp"].isoformat(),
                    "webhook_used": notification_record["webhook_used"],
                }
            else:
                logger.error(f"Failed to send Discord notification for alert {alert.alert_id}: {result}")
                return {"status": "failed", "alert_id": alert.alert_id, "error": str(result)}
        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")
            return {"status": "error", "alert_id": alert.alert_id, "error": str(e)}

    def _is_notification_in_cooldown(self, cooldown_key: str) -> bool:
        """Check if notification type is in cooldown period.

        Args:
            cooldown_key: Key identifying the notification type

        Returns:
            True if in cooldown, False otherwise
        """
        if cooldown_key not in self.last_notification_times:
            return False
        cooldown_period = timedelta(minutes=self.config.notification_cooldown_minutes)
        time_since_last = default_utc_now() - self.last_notification_times[cooldown_key]
        return time_since_last < cooldown_period

    async def send_batch_notifications(self, alerts: list[PerformanceAlert]) -> dict[str, Any]:
        """Send multiple alerts as batched notifications.

        Args:
            alerts: List of alerts to send

        Returns:
            Batch notification results
        """
        try:
            if not alerts:
                return {"status": "no_alerts", "count": 0}
            if not self.config.batch_notifications:
                results = []
                for alert in alerts:
                    result = await self.send_alert_notification(alert)
                    results.append(result)
                success_count = len([r for r in results if r["status"] == "success"])
                return {
                    "status": "individual_sent",
                    "total_alerts": len(alerts),
                    "successful": success_count,
                    "failed": len(alerts) - success_count,
                    "results": results,
                }
            severity_groups: dict[AlertSeverity, list[PerformanceAlert]] = {}
            for alert in alerts:
                severity = alert.severity
                if severity not in severity_groups:
                    severity_groups[severity] = []
                severity_groups[severity].append(alert)
            batch_results = []
            for severity, severity_alerts in severity_groups.items():
                if len(severity_alerts) == 1:
                    result = await self.send_alert_notification(severity_alerts[0])
                    batch_results.append(result)
                else:
                    batch_result = await self._send_batched_alerts(severity, severity_alerts)
                    batch_results.append(batch_result)
            success_count = len([r for r in batch_results if r["status"] == "success"])
            return {
                "status": "batch_sent",
                "total_alerts": len(alerts),
                "batch_groups": len(batch_results),
                "successful_batches": success_count,
                "failed_batches": len(batch_results) - success_count,
                "results": batch_results,
            }
        except Exception as e:
            logger.error(f"Error sending batch notifications: {e}")
            return {"status": "error", "error": str(e)}

    async def _send_batched_alerts(self, severity: AlertSeverity, alerts: list[PerformanceAlert]) -> dict[str, Any]:
        """Send multiple alerts of the same severity as a single batched notification.

        Args:
            severity: Alert severity level
            alerts: List of alerts with the same severity

        Returns:
            Batch notification result
        """
        try:
            alert_tool = self._get_alert_tool_for_severity(severity)
            if not alert_tool:
                return {
                    "status": "no_tool",
                    "message": f"No Discord tool configured for severity {severity.value}",
                    "alert_count": len(alerts),
                }
            severity_emojis = {AlertSeverity.CRITICAL: "🚨", AlertSeverity.WARNING: "⚠️", AlertSeverity.INFO: "i"}
            severity_emoji = severity_emojis.get(severity, "🔔")
            timestamp = default_utc_now().strftime("%Y-%m-%d %H:%M:%S UTC")
            batch_content = f"{severity_emoji} **BATCH ALERT - {severity.value.upper()}** ({len(alerts)} alerts)\n\n**Generated:** {timestamp}\n\n**Alert Summary:**"
            for i, alert in enumerate(alerts[:10], 1):
                batch_content += f"\n{i}. **{alert.title}**"
                if alert.metrics:
                    top_metric = next(iter(alert.metrics.items()))
                    batch_content += f" | {top_metric[0]}: {top_metric[1]:.2f}"
            if len(alerts) > 10:
                batch_content += f"\n... and {len(alerts) - 10} more alerts"
            all_metrics: dict[str, Any] = {}
            for alert in alerts:
                for metric, value in alert.metrics.items():
                    if metric not in all_metrics:
                        all_metrics[metric] = []
                    all_metrics[metric].append(value)
            if all_metrics:
                batch_content += "\n\n**Aggregated Metrics:**"
                for metric, values in list(all_metrics.items())[:5]:
                    avg_value = sum(values) / len(values)
                    max_value = max(values)
                    batch_content += f"\n• {metric}: avg={avg_value:.2f}, max={max_value:.2f}"
            all_recommendations = set()
            for alert in alerts:
                all_recommendations.update(alert.recommendations)
            if all_recommendations:
                batch_content += "\n\n**Recommendations:**"
                for rec in list(all_recommendations)[:3]:
                    batch_content += f"\n• {rec}"
            batch_content += f"\n\n**Batch ID:** `batch_{timestamp.replace(' ', '_').replace(':', '_')}`"
            result = alert_tool._run(message=batch_content)
            batch_record = {
                "batch_id": f"batch_{timestamp.replace(' ', '_').replace(':', '_')}"
                "severity": severity.value,
                "alert_count": len(alerts),
                "timestamp": default_utc_now(),
                "status": "success" if result.success else "failed",
                "webhook_used": alert_tool.webhook_url if hasattr(alert_tool, "webhook_url") else "unknown",
                "message_length": len(batch_content),
                "alert_ids": [alert.alert_id for alert in alerts],
            }
            self.notification_history.append(batch_record)
            if result.success:
                logger.info(f"Successfully sent batch notification for {len(alerts)} {severity.value} alerts")
                return {
                    "status": "success",
                    "batch_id": batch_record["batch_id"],
                    "alert_count": len(alerts),
                    "severity": severity.value,
                }
            else:
                logger.error(f"Failed to send batch notification: {result}")
                return {"status": "failed", "batch_id": batch_record["batch_id"], "error": str(result)}
        except Exception as e:
            logger.error(f"Error sending batched alerts: {e}")
            return {"status": "error", "alert_count": len(alerts), "error": str(e)}

    async def send_executive_summary(self, hours: int = 24) -> dict[str, Any]:
        """Send executive summary of performance analytics to Discord.

        Args:
            hours: Hours of data to summarize

        Returns:
            Executive summary notification result
        """
        try:
            alert_summary = await self.alert_engine.get_alert_summary(hours=hours)
            if "error" in alert_summary:
                return {"status": "error", "error": alert_summary["error"]}
            analytics_results = await self.alert_engine.analytics_system.run_comprehensive_performance_analysis(
                lookback_hours=hours, include_optimization=False
            )
            if "error" in analytics_results:
                return {"status": "error", "error": analytics_results["error"]}
            timestamp = default_utc_now().strftime("%Y-%m-%d %H:%M:%S UTC")
            executive_summary = analytics_results.get("executive_summary", {})
            summary_content = f"📊 **EXECUTIVE PERFORMANCE SUMMARY** ({hours}h)\n\n**Generated:** {timestamp}\n\n**Overall Performance:**\n• System Health Score: {executive_summary.get('overall_performance_score', 0):.2f}/1.0\n• System Status: {executive_summary.get('system_status', 'unknown').title()}\n• Key Insights: {executive_summary.get('key_insights_count', 0)}\n\n**Alert Activity:**\n• Total Alerts: {alert_summary.get('total_alerts', 0)}\n• Critical: {alert_summary.get('severity_breakdown', {}).get('critical', 0)}\n• Warning: {alert_summary.get('severity_breakdown', {}).get('warning', 0)}\n• Info: {alert_summary.get('severity_breakdown', {}).get('info', 0)}\n\n**Top Issues:**"
            top_metrics = alert_summary.get("most_violated_metrics", {})
            if top_metrics:
                for metric, count in list(top_metrics.items())[:3]:
                    summary_content += f"\n• {metric}: {count} violations"
            else:
                summary_content += "\n• No significant metric violations"
            priority_recommendations = analytics_results.get("priority_recommendations", [])
            if priority_recommendations:
                summary_content += "\n\n**Priority Actions:**"
                for rec in priority_recommendations[:3]:
                    if isinstance(rec, dict) and "title" in rec:
                        summary_content += f"\n• {rec['title']}"
                    elif isinstance(rec, str):
                        summary_content += f"\n• {rec}"
            summary_content += (
                "\n\n📈 **Performance Analytics Dashboard**\n*Detailed analytics available via system interface*"
            )
            alert_tool = self.executive_alert_tool or self.primary_alert_tool
            if not alert_tool:
                return {"status": "no_tool", "message": "No Discord tool configured for executive summaries"}
            result = alert_tool._run(message=summary_content)
            if result.success:
                logger.info(f"Successfully sent executive summary for {hours}h period")
                return {
                    "status": "success",
                    "summary_period_hours": hours,
                    "total_alerts_summarized": alert_summary.get("total_alerts", 0),
                    "message_length": len(summary_content),
                }
            else:
                logger.error(f"Failed to send executive summary: {result}")
                return {"status": "failed", "error": str(result)}
        except Exception as e:
            logger.error(f"Error sending executive summary: {e}")
            return {"status": "error", "error": str(e)}

    async def get_notification_statistics(self, hours: int = 24) -> dict[str, Any]:
        """Get statistics about Discord notifications sent.

        Args:
            hours: Hours to look back

        Returns:
            Notification statistics
        """
        try:
            cutoff_time = default_utc_now() - timedelta(hours=hours)
            recent_notifications = [notif for notif in self.notification_history if notif["timestamp"] >= cutoff_time]
            status_counts: dict[str, int] = {}
            for notif in recent_notifications:
                status = notif["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
            severity_counts: dict[str, int] = {}
            for notif in recent_notifications:
                severity = notif["severity"]
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            message_lengths = [notif.get("message_length", 0) for notif in recent_notifications]
            avg_message_length = sum(message_lengths) / len(message_lengths) if message_lengths else 0
            return {
                "total_notifications": len(recent_notifications),
                "time_period_hours": hours,
                "status_breakdown": status_counts,
                "severity_breakdown": severity_counts,
                "average_message_length": round(avg_message_length, 1),
                "success_rate": round(
                    status_counts.get("success", 0) / len(recent_notifications) * 100 if recent_notifications else 0, 1
                ),
                "configuration": {
                    "enabled": self.config.enabled,
                    "batch_notifications": self.config.batch_notifications,
                    "cooldown_minutes": self.config.notification_cooldown_minutes,
                    "tools_configured": {
                        "primary": self.primary_alert_tool is not None,
                        "private": self.private_alert_tool is not None,
                        "executive": self.executive_alert_tool is not None,
                    },
                },
            }
        except Exception as e:
            logger.error(f"Error generating notification statistics: {e}")
            return {"error": str(e)}


async def send_performance_alert_to_discord(alert: PerformanceAlert, webhook_url: str | None = None) -> dict[str, Any]:
    """Convenience function to send a single performance alert to Discord.

    Args:
        alert: Performance alert to send
        webhook_url: Discord webhook URL (optional)

    Returns:
        Notification result
    """
    config = DiscordNotificationConfig()
    if webhook_url:
        config.primary_webhook_url = webhook_url
    integration = AdvancedPerformanceAnalyticsDiscordIntegration(config=config)
    return await integration.send_alert_notification(alert)


async def send_analytics_monitoring_batch(lookback_hours: int = 2, webhook_url: str | None = None) -> dict[str, Any]:
    """Convenience function to run analytics monitoring and send alerts to Discord.

    Args:
        lookback_hours: Hours of data to analyze
        webhook_url: Discord webhook URL (optional)

    Returns:
        Monitoring and notification results
    """
    config = DiscordNotificationConfig()
    if webhook_url:
        config.primary_webhook_url = webhook_url
    integration = AdvancedPerformanceAnalyticsDiscordIntegration(config=config)
    alerts = await integration.alert_engine.evaluate_analytics_for_alerts(lookback_hours=lookback_hours)
    if not alerts:
        return {"status": "no_alerts", "lookback_hours": lookback_hours}
    notification_result = await integration.send_batch_notifications(alerts)
    return {
        "status": "monitoring_complete",
        "lookback_hours": lookback_hours,
        "alerts_generated": len(alerts),
        "notification_result": notification_result,
    }
