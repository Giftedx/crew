from __future__ import annotations

import time
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult

from .safety import (
    AlertConfig,
    AlertSeverity,
    AlertType,
    ContentFilterConfig,
    RateLimitConfig,
    SafetyManager,
    create_safety_manager,
)


class DiscordSafetyIntegration:
    """Integration layer for Discord AI chatbot safety and moderation."""

    def __init__(self, safety_manager: SafetyManager | None = None):
        self.safety_manager = safety_manager or self._create_default_safety_manager()
        self._initialized = False
        self._stats = {
            "total_messages_processed": 0,
            "messages_blocked": 0,
            "alerts_generated": 0,
            "auto_actions_taken": 0,
            "avg_processing_time_ms": 0.0,
        }

    def _create_default_safety_manager(self) -> SafetyManager:
        """Create a safety manager with default configuration."""
        content_filter_config = ContentFilterConfig(
            low_risk_threshold=0.3,
            medium_risk_threshold=0.6,
            high_risk_threshold=0.8,
            critical_threshold=0.9,
            enable_regex_filtering=True,
            enable_ai_classification=True,
            enable_similarity_filtering=True,
            enable_rate_limiting=True,
            max_messages_per_minute=10,
            max_messages_per_hour=100,
            enable_caching=True,
            cache_size=1000,
            cache_ttl_seconds=3600,
            auto_delete_high_risk=False,
            auto_warn_users=True,
            log_moderation_actions=True,
        )

        rate_limit_config = RateLimitConfig(
            enable_default_rules=True,
            user_messages_per_minute=10,
            user_messages_per_hour=100,
            user_messages_per_day=500,
            guild_messages_per_minute=1000,
            guild_messages_per_hour=10000,
            channel_messages_per_minute=100,
            channel_messages_per_hour=1000,
            global_messages_per_minute=10000,
            global_messages_per_hour=100000,
            warn_threshold=0.8,
            action_threshold=1.0,
            cooldown_seconds=60,
            escalation_cooldown_seconds=300,
            cleanup_interval_seconds=300,
            max_storage_time_seconds=86400,
        )

        alert_config = AlertConfig(
            enable_alerts=True,
            auto_escalate_threshold=3,
            escalation_time_window=3600,
            notify_moderators=True,
            notify_admins=True,
            notify_webhook=True,
            max_alerts_per_user=100,
            max_alerts_per_guild=1000,
            alert_retention_days=30,
            max_alerts_per_minute=10,
            max_alerts_per_hour=100,
            auto_mute_on_escalation=True,
            auto_kick_on_critical=False,
            auto_ban_on_repeat_offenses=False,
            webhook_url=None,
            webhook_timeout=10,
        )

        return create_safety_manager(content_filter_config, rate_limit_config, alert_config)

    async def initialize(self) -> StepResult:
        """Initialize the safety integration."""
        try:
            self._initialized = True
            return StepResult.ok(data={"action": "safety_integration_initialized"})
        except Exception as e:
            return StepResult.fail(f"Failed to initialize safety integration: {e!s}")

    async def process_discord_message(
        self,
        content: str,
        user_id: str,
        guild_id: str | None = None,
        channel_id: str | None = None,
        message_id: str | None = None,
        message_author: dict[str, Any] | None = None,
        message_mentions: list[dict[str, Any]] | None = None,
    ) -> StepResult:
        """Process a Discord message through the safety pipeline."""
        try:
            if not self._initialized:
                return StepResult.fail("Safety integration not initialized")

            start_time = time.time()

            # Process through safety manager
            safety_result = await self.safety_manager.process_message(
                content=content,
                user_id=user_id,
                guild_id=guild_id,
                channel_id=channel_id,
                message_id=message_id,
            )

            # Update statistics
            self._stats["total_messages_processed"] += 1

            if not safety_result.success:
                self._stats["messages_blocked"] += 1

                # Extract alert information if available
                if "filter_result" in safety_result.data:
                    filter_result = safety_result.data["filter_result"]
                    if hasattr(filter_result, "severity"):
                        self._stats["alerts_generated"] += 1

                # Update processing time
                processing_time = (time.time() - start_time) * 1000
                self._update_avg_processing_time(processing_time)

                return StepResult.fail(
                    safety_result.error,
                    data={
                        "safety_check": "failed",
                        "reason": safety_result.data.get("reason", "unknown"),
                        "processing_time_ms": processing_time,
                        "safety_data": safety_result.data,
                    },
                )

            # Message passed safety checks
            processing_time = (time.time() - start_time) * 1000
            self._update_avg_processing_time(processing_time)

            return StepResult.ok(
                data={
                    "safety_check": "passed",
                    "processing_time_ms": processing_time,
                    "safety_data": safety_result.data,
                }
            )

        except Exception as e:
            return StepResult.fail(f"Discord message safety processing failed: {e!s}")

    async def get_user_safety_profile(self, user_id: str) -> StepResult:
        """Get comprehensive safety profile for a user."""
        try:
            if not self._initialized:
                return StepResult.fail("Safety integration not initialized")

            # Get safety status from safety manager
            safety_status_result = await self.safety_manager.get_user_safety_status(user_id)

            if not safety_status_result.success:
                return StepResult.fail(f"Failed to get user safety status: {safety_status_result.error}")

            safety_status = safety_status_result.data

            # Enhance with additional Discord-specific information
            profile = {
                "user_id": user_id,
                "safety_score": safety_status["safety_score"],
                "rate_limit_status": safety_status["rate_limit_status"],
                "recent_alerts": safety_status["recent_alerts"],
                "content_filter_stats": safety_status["content_filter_stats"],
                "recommendations": self._generate_user_recommendations(safety_status),
                "risk_level": self._determine_risk_level(safety_status["safety_score"]),
            }

            return StepResult.ok(data={"user_safety_profile": profile})

        except Exception as e:
            return StepResult.fail(f"Failed to get user safety profile: {e!s}")

    async def get_guild_moderation_dashboard(self, guild_id: str) -> StepResult:
        """Get moderation dashboard data for a guild."""
        try:
            if not self._initialized:
                return StepResult.fail("Safety integration not initialized")

            # Get safety overview from safety manager
            safety_overview_result = await self.safety_manager.get_guild_safety_overview(guild_id)

            if not safety_overview_result.success:
                return StepResult.fail(f"Failed to get guild safety overview: {safety_overview_result.error}")

            safety_overview = safety_overview_result.data

            # Enhance with dashboard-specific information
            dashboard = {
                "guild_id": guild_id,
                "safety_metrics": safety_overview["safety_metrics"],
                "total_alerts": safety_overview["total_alerts"],
                "pending_alerts": safety_overview["pending_alerts"],
                "recent_alerts": safety_overview["recent_alerts"],
                "pending_alerts_list": safety_overview["pending_alerts_list"],
                "moderation_actions": await self._get_recent_moderation_actions(guild_id),
                "top_offenders": await self._get_top_offenders(guild_id),
                "alert_trends": await self._get_alert_trends(guild_id),
                "recommendations": self._generate_guild_recommendations(safety_overview),
            }

            return StepResult.ok(data={"moderation_dashboard": dashboard})

        except Exception as e:
            return StepResult.fail(f"Failed to get guild moderation dashboard: {e!s}")

    async def handle_moderation_action(
        self,
        action_type: str,
        user_id: str,
        moderator_id: str,
        guild_id: str | None = None,
        reason: str | None = None,
        duration: int | None = None,
    ) -> StepResult:
        """Handle a moderation action taken by a human moderator."""
        try:
            if not self._initialized:
                return StepResult.fail("Safety integration not initialized")

            # Create alert for the moderation action
            alert_type = self._map_action_to_alert_type(action_type)
            severity = AlertSeverity.HIGH if action_type in ["ban", "kick"] else AlertSeverity.MEDIUM

            alert_result = await self.safety_manager.alert_manager.create_alert(
                alert_type=alert_type,
                severity=severity,
                user_id=user_id,
                content=f"Moderation action: {action_type}",
                guild_id=guild_id,
                metadata={
                    "action_type": action_type,
                    "moderator_id": moderator_id,
                    "reason": reason,
                    "duration": duration,
                    "manual_action": True,
                },
            )

            if alert_result.success:
                self._stats["auto_actions_taken"] += 1
                return StepResult.ok(
                    data={
                        "moderation_action_recorded": True,
                        "alert_id": alert_result.data.get("alert_id"),
                    }
                )
            else:
                return StepResult.fail(f"Failed to record moderation action: {alert_result.error}")

        except Exception as e:
            return StepResult.fail(f"Failed to handle moderation action: {e!s}")

    def _generate_user_recommendations(self, safety_status: dict[str, Any]) -> list[str]:
        """Generate safety recommendations for a user."""
        recommendations = []
        safety_score = safety_status.get("safety_score", 100)

        if safety_score < 30:
            recommendations.append("User has significant safety violations. Consider temporary restrictions.")
        elif safety_score < 60:
            recommendations.append("User has moderate safety violations. Monitor closely.")
        elif safety_score < 80:
            recommendations.append("User has minor safety violations. Provide gentle guidance.")
        else:
            recommendations.append("User maintains good safety standards.")

        # Check for specific issues
        recent_alerts = safety_status.get("recent_alerts", [])
        if len(recent_alerts) > 5:
            recommendations.append("High number of recent alerts. Consider intervention.")

        rate_limit_status = safety_status.get("rate_limit_status", {})
        if rate_limit_status.get("in_cooldown", False):
            recommendations.append("User currently in rate limit cooldown.")

        return recommendations

    def _determine_risk_level(self, safety_score: float) -> str:
        """Determine risk level based on safety score."""
        if safety_score >= 80:
            return "low"
        elif safety_score >= 60:
            return "medium"
        elif safety_score >= 40:
            return "high"
        else:
            return "critical"

    def _generate_guild_recommendations(self, safety_overview: dict[str, Any]) -> list[str]:
        """Generate recommendations for guild moderation."""
        recommendations = []
        safety_metrics = safety_overview.get("safety_metrics", {})
        safety_score = safety_metrics.get("safety_score", 100)

        if safety_score < 50:
            recommendations.append("Guild has significant moderation issues. Consider stricter policies.")
        elif safety_score < 75:
            recommendations.append("Guild has moderate moderation issues. Monitor activity closely.")
        else:
            recommendations.append("Guild maintains good moderation standards.")

        pending_alerts = safety_overview.get("pending_alerts", 0)
        if pending_alerts > 10:
            recommendations.append("High number of pending alerts. Increase moderation capacity.")

        most_common = safety_metrics.get("most_common_issues", [])
        if most_common:
            top_issue = most_common[0]["type"]
            recommendations.append(f"Most common issue: {top_issue}. Consider targeted policies.")

        return recommendations

    async def _get_recent_moderation_actions(self, guild_id: str) -> list[dict[str, Any]]:
        """Get recent moderation actions for a guild."""
        # This would integrate with Discord API to get actual moderation actions
        # For now, return placeholder data
        return []

    async def _get_top_offenders(self, guild_id: str) -> list[dict[str, Any]]:
        """Get top safety offenders in a guild."""
        # This would analyze alert data to find users with most violations
        # For now, return placeholder data
        return []

    async def _get_alert_trends(self, guild_id: str) -> dict[str, Any]:
        """Get alert trends for a guild."""
        # This would analyze alert patterns over time
        # For now, return placeholder data
        return {
            "trend": "stable",
            "period": "last_7_days",
            "change_percentage": 0.0,
        }

    def _map_action_to_alert_type(self, action_type: str) -> AlertType:
        """Map moderation action type to alert type."""
        action_mapping = {
            "warn": AlertType.CONTENT_VIOLATION,
            "mute": AlertType.RATE_LIMIT_EXCEEDED,
            "kick": AlertType.HARASSMENT,
            "ban": AlertType.HATE_SPEECH,
            "timeout": AlertType.SPAM_DETECTED,
        }
        return action_mapping.get(action_type, AlertType.CONTENT_VIOLATION)

    def _update_avg_processing_time(self, processing_time: float):
        """Update average processing time statistics."""
        total_messages = self._stats["total_messages_processed"]
        current_avg = self._stats["avg_processing_time_ms"]

        if total_messages > 0:
            self._stats["avg_processing_time_ms"] = (
                current_avg * (total_messages - 1) + processing_time
            ) / total_messages
        else:
            self._stats["avg_processing_time_ms"] = processing_time

    def get_integration_statistics(self) -> dict[str, Any]:
        """Get safety integration statistics."""
        return {
            "safety_integration": self._stats.copy(),
            "safety_manager": self.safety_manager.get_safety_statistics(),
        }

    async def close(self):
        """Clean up resources."""
        await self.safety_manager.close()


def create_discord_safety_integration(safety_manager: SafetyManager | None = None) -> DiscordSafetyIntegration:
    """Create a Discord safety integration with the specified safety manager."""
    return DiscordSafetyIntegration(safety_manager)
