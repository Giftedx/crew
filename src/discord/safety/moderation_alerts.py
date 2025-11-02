from __future__ import annotations

import asyncio
import contextlib
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from platform.core.step_result import StepResult
from typing import Any


class AlertSeverity(Enum):
    """Severity levels for moderation alerts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of moderation alerts."""

    CONTENT_VIOLATION = "content_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SPAM_DETECTED = "spam_detected"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    NSFW_CONTENT = "nsfw_content"
    VIOLENCE = "violence"
    SELF_HARM = "self_harm"
    MISINFORMATION = "misinformation"
    PERSONAL_INFO_LEAK = "personal_info_leak"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    USER_BEHAVIOR_ANOMALY = "user_behavior_anomaly"


class AlertStatus(Enum):
    """Status of moderation alerts."""

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


@dataclass
class ModerationAlert:
    """Moderation alert data structure."""

    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    user_id: str
    guild_id: str | None
    channel_id: str | None
    message_id: str | None
    content: str
    timestamp: float
    metadata: dict[str, Any]
    status: AlertStatus = AlertStatus.PENDING
    assigned_moderator: str | None = None
    resolution_notes: str | None = None
    resolution_timestamp: float | None = None


@dataclass
class AlertConfig:
    """Configuration for moderation alert system."""

    enable_alerts: bool = True
    auto_escalate_threshold: int = 3
    escalation_time_window: int = 3600
    notify_moderators: bool = True
    notify_admins: bool = True
    notify_webhook: bool = True
    max_alerts_per_user: int = 100
    max_alerts_per_guild: int = 1000
    alert_retention_days: int = 30
    max_alerts_per_minute: int = 10
    max_alerts_per_hour: int = 100
    auto_mute_on_escalation: bool = True
    auto_kick_on_critical: bool = False
    auto_ban_on_repeat_offenses: bool = False
    webhook_url: str | None = None
    webhook_timeout: int = 10


class ModerationAlertManager:
    """Manages moderation alerts and notifications."""

    def __init__(self, config: AlertConfig):
        self.config = config
        self._alerts: dict[str, ModerationAlert] = {}
        self._user_alerts: dict[str, list[str]] = defaultdict(list)
        self._guild_alerts: dict[str, list[str]] = defaultdict(list)
        self._channel_alerts: dict[str, list[str]] = defaultdict(list)
        self._user_alert_counts: dict[str, deque] = defaultdict(lambda: deque())
        self._guild_alert_counts: dict[str, deque] = defaultdict(lambda: deque())
        self._alert_rate_limits: dict[str, deque] = defaultdict(lambda: deque())
        self._stats = {
            "total_alerts_generated": 0,
            "alerts_by_type": defaultdict(int),
            "alerts_by_severity": defaultdict(int),
            "alerts_resolved": 0,
            "alerts_escalated": 0,
            "auto_actions_taken": 0,
            "avg_resolution_time_minutes": 0.0,
        }
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        user_id: str,
        content: str,
        guild_id: str | None = None,
        channel_id: str | None = None,
        message_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Create a new moderation alert."""
        try:
            if not self.config.enable_alerts:
                return StepResult.ok(data={"alert_created": False, "reason": "alerts_disabled"})
            rate_limit_check = await self._check_alert_rate_limit(user_id, guild_id)
            if not rate_limit_check.success:
                return rate_limit_check
            alert_id = f"alert_{int(time.time() * 1000)}_{user_id}"
            alert = ModerationAlert(
                alert_id=alert_id,
                alert_type=alert_type,
                severity=severity,
                user_id=user_id,
                guild_id=guild_id,
                channel_id=channel_id,
                message_id=message_id,
                content=content,
                timestamp=time.time(),
                metadata=metadata or {},
                status=AlertStatus.PENDING,
            )
            self._alerts[alert_id] = alert
            self._user_alerts[user_id].append(alert_id)
            if guild_id:
                self._guild_alerts[guild_id].append(alert_id)
            if channel_id:
                self._channel_alerts[channel_id].append(alert_id)
            await self._update_alert_counters(user_id, guild_id)
            escalation_result = await self._check_auto_escalation(user_id, guild_id)
            if escalation_result.success and escalation_result.data.get("escalated"):
                alert.status = AlertStatus.ESCALATED
                await self._handle_escalation(alert)
            await self._send_notifications(alert)
            self._update_statistics(alert)
            return StepResult.ok(data={"alert_created": True, "alert_id": alert_id})
        except Exception as e:
            return StepResult.fail(f"Failed to create alert: {e!s}")

    async def acknowledge_alert(self, alert_id: str, moderator_id: str) -> StepResult:
        """Acknowledge an alert."""
        try:
            if alert_id not in self._alerts:
                return StepResult.fail("Alert not found")
            alert = self._alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.assigned_moderator = moderator_id
            return StepResult.ok(data={"alert_acknowledged": True})
        except Exception as e:
            return StepResult.fail(f"Failed to acknowledge alert: {e!s}")

    async def resolve_alert(self, alert_id: str, moderator_id: str, resolution_notes: str | None = None) -> StepResult:
        """Resolve an alert."""
        try:
            if alert_id not in self._alerts:
                return StepResult.fail("Alert not found")
            alert = self._alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.assigned_moderator = moderator_id
            alert.resolution_notes = resolution_notes
            alert.resolution_timestamp = time.time()
            self._stats["alerts_resolved"] += 1
            resolution_time = alert.resolution_timestamp - alert.timestamp
            self._update_avg_resolution_time(resolution_time)
            return StepResult.ok(data={"alert_resolved": True})
        except Exception as e:
            return StepResult.fail(f"Failed to resolve alert: {e!s}")

    async def dismiss_alert(self, alert_id: str, moderator_id: str, reason: str | None = None) -> StepResult:
        """Dismiss an alert as false positive."""
        try:
            if alert_id not in self._alerts:
                return StepResult.fail("Alert not found")
            alert = self._alerts[alert_id]
            alert.status = AlertStatus.DISMISSED
            alert.assigned_moderator = moderator_id
            alert.resolution_notes = f"Dismissed: {reason or 'False positive'}"
            alert.resolution_timestamp = time.time()
            return StepResult.ok(data={"alert_dismissed": True})
        except Exception as e:
            return StepResult.fail(f"Failed to dismiss alert: {e!s}")

    async def escalate_alert(self, alert_id: str, moderator_id: str, reason: str) -> StepResult:
        """Manually escalate an alert."""
        try:
            if alert_id not in self._alerts:
                return StepResult.fail("Alert not found")
            alert = self._alerts[alert_id]
            alert.status = AlertStatus.ESCALATED
            alert.assigned_moderator = moderator_id
            alert.resolution_notes = f"Escalated: {reason}"
            await self._handle_escalation(alert)
            self._stats["alerts_escalated"] += 1
            return StepResult.ok(data={"alert_escalated": True})
        except Exception as e:
            return StepResult.fail(f"Failed to escalate alert: {e!s}")

    async def get_user_alerts(self, user_id: str, status: AlertStatus | None = None, limit: int = 50) -> StepResult:
        """Get alerts for a specific user."""
        try:
            user_alert_ids = self._user_alerts.get(user_id, [])
            alerts = []
            for alert_id in user_alert_ids[-limit:]:
                if alert_id in self._alerts:
                    alert = self._alerts[alert_id]
                    if status is None or alert.status == status:
                        alerts.append(self._serialize_alert(alert))
            return StepResult.ok(data={"alerts": alerts})
        except Exception as e:
            return StepResult.fail(f"Failed to get user alerts: {e!s}")

    async def get_guild_alerts(self, guild_id: str, status: AlertStatus | None = None, limit: int = 100) -> StepResult:
        """Get alerts for a specific guild."""
        try:
            guild_alert_ids = self._guild_alerts.get(guild_id, [])
            alerts = []
            for alert_id in guild_alert_ids[-limit:]:
                if alert_id in self._alerts:
                    alert = self._alerts[alert_id]
                    if status is None or alert.status == status:
                        alerts.append(self._serialize_alert(alert))
            return StepResult.ok(data={"alerts": alerts})
        except Exception as e:
            return StepResult.fail(f"Failed to get guild alerts: {e!s}")

    async def get_pending_alerts(self, limit: int = 50) -> StepResult:
        """Get all pending alerts."""
        try:
            pending_alerts = []
            for alert in self._alerts.values():
                if alert.status == AlertStatus.PENDING:
                    pending_alerts.append(self._serialize_alert(alert))
                    if len(pending_alerts) >= limit:
                        break
            pending_alerts.sort(key=lambda a: (self._severity_priority(a["severity"]), -a["timestamp"]))
            return StepResult.ok(data={"pending_alerts": pending_alerts})
        except Exception as e:
            return StepResult.fail(f"Failed to get pending alerts: {e!s}")

    async def _check_alert_rate_limit(self, user_id: str, guild_id: str | None) -> StepResult:
        """Check rate limits for alert generation."""
        current_time = time.time()
        user_alerts = self._alert_rate_limits[user_id]
        while user_alerts and user_alerts[0] < current_time - 60:
            user_alerts.popleft()
        if len(user_alerts) >= self.config.max_alerts_per_minute:
            return StepResult.fail("Alert generation rate limit exceeded for user")
        if guild_id:
            guild_alerts = self._alert_rate_limits[guild_id]
            while guild_alerts and guild_alerts[0] < current_time - 3600:
                guild_alerts.popleft()
            if len(guild_alerts) >= self.config.max_alerts_per_hour:
                return StepResult.fail("Alert generation rate limit exceeded for guild")
        user_alerts.append(current_time)
        if guild_id:
            self._alert_rate_limits[guild_id].append(current_time)
        return StepResult.ok(data={"rate_limit_check": "passed"})

    async def _update_alert_counters(self, user_id: str, guild_id: str | None):
        """Update alert counters for escalation detection."""
        current_time = time.time()
        window_start = current_time - self.config.escalation_time_window
        user_count = self._user_alert_counts[user_id]
        while user_count and user_count[0] < window_start:
            user_count.popleft()
        user_count.append(current_time)
        if guild_id:
            guild_count = self._guild_alert_counts[guild_id]
            while guild_count and guild_count[0] < window_start:
                guild_count.popleft()
            guild_count.append(current_time)

    async def _check_auto_escalation(self, user_id: str, guild_id: str | None) -> StepResult:
        """Check if user should be auto-escalated."""
        user_count = len(self._user_alert_counts[user_id])
        if user_count >= self.config.auto_escalate_threshold:
            return StepResult.ok(data={"escalated": True, "reason": "user_threshold_exceeded"})
        if guild_id:
            guild_count = len(self._guild_alert_counts[guild_id])
            if guild_count >= self.config.auto_escalate_threshold * 2:
                return StepResult.ok(data={"escalated": True, "reason": "guild_threshold_exceeded"})
        return StepResult.ok(data={"escalated": False})

    async def _handle_escalation(self, alert: ModerationAlert):
        """Handle escalated alert with auto-actions.

        Note: Auto-actions require Discord bot instance with appropriate permissions.
        Current implementation logs actions for external executor to process.
        """
        actions_taken = []
        if self.config.auto_mute_on_escalation:
            action_result = await self._execute_auto_mute(alert)
            if action_result.success:
                actions_taken.append("mute")
                alert.metadata["auto_mute_executed"] = True
        if self.config.auto_kick_on_critical and alert.severity == AlertSeverity.CRITICAL:
            action_result = await self._execute_auto_kick(alert)
            if action_result.success:
                actions_taken.append("kick")
                alert.metadata["auto_kick_executed"] = True
        if self.config.auto_ban_on_repeat_offenses:
            user_alerts = len(self._user_alerts.get(alert.user_id, []))
            if user_alerts >= 5:
                action_result = await self._execute_auto_ban(alert)
                if action_result.success:
                    actions_taken.append("ban")
                    alert.metadata["auto_ban_executed"] = True
        if actions_taken:
            self._stats["auto_actions_taken"] += 1
            alert.metadata["auto_actions"] = actions_taken

    async def _execute_auto_mute(self, alert: ModerationAlert) -> StepResult:
        """Execute auto-mute action.

        Integration point: Requires Discord bot with MODERATE_MEMBERS permission.
        Implementation should call discord.Member.timeout() with appropriate duration.

        Returns:
            StepResult with mute action details
        """
        action = {
            "type": "mute",
            "user_id": alert.user_id,
            "guild_id": alert.guild_id,
            "reason": f"Auto-mute: {alert.alert_type.value} (Alert {alert.alert_id})",
            "duration_seconds": 3600,
            "timestamp": time.time(),
        }
        if "pending_actions" not in alert.metadata:
            alert.metadata["pending_actions"] = []
        alert.metadata["pending_actions"].append(action)
        return StepResult.ok(data={"action": action, "status": "queued"})

    async def _execute_auto_kick(self, alert: ModerationAlert) -> StepResult:
        """Execute auto-kick action.

        Integration point: Requires Discord bot with KICK_MEMBERS permission.
        Implementation should call discord.Member.kick() with reason.

        Returns:
            StepResult with kick action details
        """
        action = {
            "type": "kick",
            "user_id": alert.user_id,
            "guild_id": alert.guild_id,
            "reason": f"Auto-kick: {alert.alert_type.value} (Alert {alert.alert_id})",
            "timestamp": time.time(),
        }
        if "pending_actions" not in alert.metadata:
            alert.metadata["pending_actions"] = []
        alert.metadata["pending_actions"].append(action)
        return StepResult.ok(data={"action": action, "status": "queued"})

    async def _execute_auto_ban(self, alert: ModerationAlert) -> StepResult:
        """Execute auto-ban action.

        Integration point: Requires Discord bot with BAN_MEMBERS permission.
        Implementation should call discord.Guild.ban() with reason and delete_message_days.

        Returns:
            StepResult with ban action details
        """
        action = {
            "type": "ban",
            "user_id": alert.user_id,
            "guild_id": alert.guild_id,
            "reason": f"Auto-ban: Repeat offenses ({len(self._user_alerts.get(alert.user_id, []))} alerts)",
            "delete_message_days": 1,
            "timestamp": time.time(),
        }
        if "pending_actions" not in alert.metadata:
            alert.metadata["pending_actions"] = []
        alert.metadata["pending_actions"].append(action)
        return StepResult.ok(data={"action": action, "status": "queued"})

    async def _send_notifications(self, alert: ModerationAlert):
        """Send notifications for new alerts.

        Integration points:
        - Discord channels: Requires bot with SEND_MESSAGES permission in mod channels
        - Webhooks: Requires webhook URL configuration
        - Email: Requires SMTP configuration

        Current implementation logs notifications for external delivery.
        """
        notifications = []
        if self.config.notify_moderators and alert.guild_id:
            notifications.append(
                {"type": "moderator_channel", "guild_id": alert.guild_id, "embed": self._create_alert_embed(alert)}
            )
        if self.config.notify_admins and alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            notifications.append(
                {
                    "type": "admin_channel",
                    "guild_id": alert.guild_id,
                    "embed": self._create_alert_embed(alert),
                    "mention_admins": True,
                }
            )
        if self.config.notify_webhook and self.config.webhook_url:
            notifications.append(
                {"type": "webhook", "url": self.config.webhook_url, "payload": self._serialize_alert(alert)}
            )
        alert.metadata["notifications"] = notifications

    def _create_alert_embed(self, alert: ModerationAlert) -> dict[str, Any]:
        """Create Discord embed for alert notification.

        Returns:
            Dictionary representing Discord embed structure
        """
        severity_colors = {
            AlertSeverity.LOW: 9807270,
            AlertSeverity.MEDIUM: 15965202,
            AlertSeverity.HIGH: 15158332,
            AlertSeverity.CRITICAL: 10038562,
        }
        return {
            "title": f"🚨 Moderation Alert: {alert.alert_type.value.replace('_', ' ').title()}"
            "description": alert.content[:1000],
            "color": severity_colors.get(alert.severity, 9807270),
            "fields": [
                {"name": "Severity", "value": alert.severity.value.upper(), "inline": True},
                {"name": "User", "value": f"<@{alert.user_id}>", "inline": True},
                {"name": "Alert ID", "value": alert.alert_id, "inline": True},
                {"name": "Status", "value": alert.status.value, "inline": True},
            ],
            "timestamp": alert.timestamp,
            "footer": {"text": "Moderation Alert System"},
        }

    def _serialize_alert(self, alert: ModerationAlert) -> dict[str, Any]:
        """Serialize alert for API responses."""
        return {
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "user_id": alert.user_id,
            "guild_id": alert.guild_id,
            "channel_id": alert.channel_id,
            "message_id": alert.message_id,
            "content": alert.content[:500],
            "timestamp": alert.timestamp,
            "status": alert.status.value,
            "assigned_moderator": alert.assigned_moderator,
            "resolution_notes": alert.resolution_notes,
            "resolution_timestamp": alert.resolution_timestamp,
            "metadata": alert.metadata,
        }

    def _severity_priority(self, severity: str) -> int:
        """Get priority number for severity (lower = higher priority)."""
        priorities = {
            AlertSeverity.CRITICAL.value: 0,
            AlertSeverity.HIGH.value: 1,
            AlertSeverity.MEDIUM.value: 2,
            AlertSeverity.LOW.value: 3,
        }
        return priorities.get(severity, 4)

    def _update_statistics(self, alert: ModerationAlert):
        """Update alert statistics."""
        self._stats["total_alerts_generated"] += 1
        self._stats["alerts_by_type"][alert.alert_type.value] += 1
        self._stats["alerts_by_severity"][alert.severity.value] += 1

    def _update_avg_resolution_time(self, resolution_time: float):
        """Update average resolution time."""
        resolved_count = self._stats["alerts_resolved"]
        current_avg = self._stats["avg_resolution_time_minutes"]
        resolution_minutes = resolution_time / 60
        if resolved_count > 0:
            self._stats["avg_resolution_time_minutes"] = (
                current_avg * (resolved_count - 1) + resolution_minutes
            ) / resolved_count
        else:
            self._stats["avg_resolution_time_minutes"] = resolution_minutes

    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(3600)
                await self._cleanup_old_alerts()
            except Exception as e:
                print(f"Alert cleanup error: {e}")

    async def _cleanup_old_alerts(self):
        """Clean up old alerts beyond retention period."""
        current_time = time.time()
        cutoff_time = current_time - self.config.alert_retention_days * 86400
        alerts_to_remove = []
        for alert_id, alert in self._alerts.items():
            if alert.timestamp < cutoff_time and alert.status in [AlertStatus.RESOLVED, AlertStatus.DISMISSED]:
                alerts_to_remove.append(alert_id)
        for alert_id in alerts_to_remove:
            await self._remove_alert(alert_id)

    async def _remove_alert(self, alert_id: str):
        """Remove an alert from all tracking structures."""
        if alert_id not in self._alerts:
            return
        alert = self._alerts[alert_id]
        del self._alerts[alert_id]
        if alert_id in self._user_alerts[alert.user_id]:
            self._user_alerts[alert.user_id].remove(alert_id)
        if alert.guild_id and alert_id in self._guild_alerts[alert.guild_id]:
            self._guild_alerts[alert.guild_id].remove(alert_id)
        if alert.channel_id and alert_id in self._channel_alerts[alert.channel_id]:
            self._channel_alerts[alert.channel_id].remove(alert_id)

    def get_statistics(self) -> dict[str, Any]:
        """Get alert system statistics."""
        stats = self._stats.copy()
        stats["alerts_by_type"] = dict(stats["alerts_by_type"])
        stats["alerts_by_severity"] = dict(stats["alerts_by_severity"])
        stats["total_active_alerts"] = len(
            [alert for alert in self._alerts.values() if alert.status == AlertStatus.PENDING]
        )
        stats["total_resolved_alerts"] = len(
            [alert for alert in self._alerts.values() if alert.status == AlertStatus.RESOLVED]
        )
        return stats

    async def close(self):
        """Clean up resources."""
        if hasattr(self, "_cleanup_task"):
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task


def create_moderation_alert_manager(config: AlertConfig | None = None) -> ModerationAlertManager:
    """Create a moderation alert manager with the specified configuration."""
    if config is None:
        config = AlertConfig()
    return ModerationAlertManager(config)
