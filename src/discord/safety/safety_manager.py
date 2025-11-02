from __future__ import annotations
import asyncio
from typing import Any
from platform.core.step_result import StepResult
from .content_filter import ContentFilterConfig, ContentFilterResult, create_content_filter
from .moderation_alerts import AlertConfig, AlertSeverity, AlertType, create_moderation_alert_manager
from .rate_limiter import RateLimitConfig, create_rate_limiter

class SafetyManager:
    """Unified safety and moderation management system."""

    def __init__(self, content_filter_config: ContentFilterConfig | None=None, rate_limit_config: RateLimitConfig | None=None, alert_config: AlertConfig | None=None):
        self.content_filter = create_content_filter(content_filter_config)
        self.rate_limiter = create_rate_limiter(rate_limit_config)
        self.alert_manager = create_moderation_alert_manager(alert_config)
        self._auto_create_alerts = True
        self._auto_enforce_rate_limits = True
        self._auto_filter_content = True
        self._stats = {'total_messages_processed': 0, 'messages_filtered': 0, 'rate_limits_hit': 0, 'alerts_generated': 0, 'auto_actions_taken': 0, 'avg_processing_time_ms': 0.0}

    async def process_message(self, content: str, user_id: str, guild_id: str | None=None, channel_id: str | None=None, message_id: str | None=None) -> StepResult:
        """Process a message through the complete safety pipeline."""
        try:
            start_time = asyncio.get_event_loop().time()
            if self._auto_enforce_rate_limits:
                rate_limit_result = await self.rate_limiter.check_rate_limit(user_id=user_id, guild_id=guild_id, channel_id=channel_id, request_type='message')
                if not rate_limit_result.success:
                    if self._auto_create_alerts:
                        await self.alert_manager.create_alert(alert_type=AlertType.RATE_LIMIT_EXCEEDED, severity=AlertSeverity.MEDIUM, user_id=user_id, content=content, guild_id=guild_id, channel_id=channel_id, message_id=message_id, metadata={'rate_limit_error': rate_limit_result.error, 'action': 'rate_limit_check_failed'})
                    self._stats['rate_limits_hit'] += 1
                    return StepResult.fail(f'Rate limit exceeded: {rate_limit_result.error}', data={'safety_check': 'failed', 'reason': 'rate_limit'})
            if self._auto_filter_content:
                content_filter_result = await self.content_filter.filter_content(content=content, user_id=user_id, guild_id=guild_id)
                if not content_filter_result.success:
                    return StepResult.fail(f'Content filtering failed: {content_filter_result.error}', data={'safety_check': 'failed', 'reason': 'content_filter_error'})
                filter_result: ContentFilterResult = content_filter_result.data['filter_result']
                if not filter_result.is_safe:
                    alert_type = self._map_content_category_to_alert_type(filter_result.categories)
                    severity = self._map_content_severity_to_alert_severity(filter_result.severity)
                    if self._auto_create_alerts:
                        await self.alert_manager.create_alert(alert_type=alert_type, severity=severity, user_id=user_id, content=content, guild_id=guild_id, channel_id=channel_id, message_id=message_id, metadata={'filter_result': {'severity': filter_result.severity.value, 'categories': [cat.value for cat in filter_result.categories], 'confidence': filter_result.confidence, 'flagged_patterns': filter_result.flagged_patterns, 'suggestions': filter_result.suggestions}})
                    self._stats['messages_filtered'] += 1
                    self._stats['alerts_generated'] += 1
                    return StepResult.fail(f'Content flagged as {filter_result.severity.value}: {(filter_result.suggestions[0] if filter_result.suggestions else 'Inappropriate content detected')}', data={'safety_check': 'failed', 'reason': 'content_filtered', 'filter_result': filter_result})
            self._stats['total_messages_processed'] += 1
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            self._update_avg_processing_time(processing_time)
            return StepResult.ok(data={'safety_check': 'passed', 'processing_time_ms': processing_time, 'checks_performed': ['rate_limit', 'content_filter']})
        except Exception as e:
            return StepResult.fail(f'Safety processing failed: {e!s}')

    def _map_content_category_to_alert_type(self, categories: list) -> AlertType:
        """Map content filter categories to alert types."""
        if not categories:
            return AlertType.CONTENT_VIOLATION
        category = categories[0]
        category_mapping = {'harassment': AlertType.HARASSMENT, 'spam': AlertType.SPAM_DETECTED, 'nsfw': AlertType.NSFW_CONTENT, 'hate_speech': AlertType.HATE_SPEECH, 'violence': AlertType.VIOLENCE, 'self_harm': AlertType.SELF_HARM, 'misinformation': AlertType.MISINFORMATION, 'personal_info': AlertType.PERSONAL_INFO_LEAK}
        return category_mapping.get(category.value, AlertType.CONTENT_VIOLATION)

    def _map_content_severity_to_alert_severity(self, severity) -> AlertSeverity:
        """Map content filter severity to alert severity."""
        severity_mapping = {'safe': AlertSeverity.LOW, 'low_risk': AlertSeverity.LOW, 'medium_risk': AlertSeverity.MEDIUM, 'high_risk': AlertSeverity.HIGH, 'critical': AlertSeverity.CRITICAL}
        return severity_mapping.get(severity.value, AlertSeverity.MEDIUM)

    def _update_avg_processing_time(self, processing_time: float):
        """Update average processing time statistics."""
        total_messages = self._stats['total_messages_processed']
        current_avg = self._stats['avg_processing_time_ms']
        if total_messages > 0:
            self._stats['avg_processing_time_ms'] = (current_avg * (total_messages - 1) + processing_time) / total_messages
        else:
            self._stats['avg_processing_time_ms'] = processing_time

    async def get_user_safety_status(self, user_id: str) -> StepResult:
        """Get comprehensive safety status for a user."""
        try:
            rate_limit_status = self.rate_limiter.get_user_status(user_id)
            alerts_result = await self.alert_manager.get_user_alerts(user_id)
            user_alerts = alerts_result.data.get('alerts', []) if alerts_result.success else []
            content_filter_stats = self.content_filter.get_statistics()
            return StepResult.ok(data={'user_id': user_id, 'rate_limit_status': rate_limit_status, 'recent_alerts': user_alerts[:10], 'content_filter_stats': content_filter_stats, 'safety_score': self._calculate_user_safety_score(user_alerts, rate_limit_status)})
        except Exception as e:
            return StepResult.fail(f'Failed to get user safety status: {e!s}')

    def _calculate_user_safety_score(self, alerts: list[dict], rate_limit_status: dict) -> float:
        """Calculate a safety score for a user (0-100, higher is better)."""
        base_score = 100.0
        for alert in alerts:
            severity = alert.get('severity', 'medium')
            severity_penalties = {'low': 5, 'medium': 10, 'high': 20, 'critical': 40}
            base_score -= severity_penalties.get(severity, 10)
        if rate_limit_status.get('in_cooldown', False):
            base_score -= 30
        recent_actions = rate_limit_status.get('recent_actions', [])
        base_score -= len(recent_actions) * 5
        return max(0.0, min(100.0, base_score))

    async def get_guild_safety_overview(self, guild_id: str) -> StepResult:
        """Get safety overview for a guild."""
        try:
            alerts_result = await self.alert_manager.get_guild_alerts(guild_id)
            guild_alerts = alerts_result.data.get('alerts', []) if alerts_result.success else []
            pending_result = await self.alert_manager.get_pending_alerts()
            pending_alerts = pending_result.data.get('pending_alerts', []) if pending_result.success else []
            guild_pending_alerts = [alert for alert in pending_alerts if alert.get('guild_id') == guild_id]
            return StepResult.ok(data={'guild_id': guild_id, 'total_alerts': len(guild_alerts), 'pending_alerts': len(guild_pending_alerts), 'recent_alerts': guild_alerts[:20], 'pending_alerts_list': guild_pending_alerts, 'safety_metrics': self._calculate_guild_safety_metrics(guild_alerts)})
        except Exception as e:
            return StepResult.fail(f'Failed to get guild safety overview: {e!s}')

    def _calculate_guild_safety_metrics(self, alerts: list[dict]) -> dict[str, Any]:
        """Calculate safety metrics for a guild."""
        if not alerts:
            return {'safety_score': 100.0, 'alert_trend': 'stable', 'most_common_issues': [], 'severity_distribution': {}}
        alert_counts = {}
        severity_counts = {}
        for alert in alerts:
            alert_type = alert.get('alert_type', 'unknown')
            severity = alert.get('severity', 'medium')
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        total_alerts = len(alerts)
        critical_alerts = severity_counts.get('critical', 0)
        high_alerts = severity_counts.get('high', 0)
        medium_alerts = severity_counts.get('medium', 0)
        low_alerts = severity_counts.get('low', 0)
        safety_score = 100.0 - (critical_alerts * 10 + high_alerts * 5 + medium_alerts * 2 + low_alerts * 1)
        safety_score = max(0.0, min(100.0, safety_score))
        most_common = sorted(alert_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return {'safety_score': safety_score, 'alert_trend': 'increasing' if total_alerts > 10 else 'stable', 'most_common_issues': [{'type': issue_type, 'count': count} for issue_type, count in most_common], 'severity_distribution': severity_counts, 'total_alerts': total_alerts}

    def get_safety_statistics(self) -> dict[str, Any]:
        """Get comprehensive safety system statistics."""
        return {'safety_manager': self._stats.copy(), 'content_filter': self.content_filter.get_statistics(), 'rate_limiter': self.rate_limiter.get_statistics(), 'alert_manager': self.alert_manager.get_statistics()}

    def configure_auto_actions(self, auto_create_alerts: bool | None=None, auto_enforce_rate_limits: bool | None=None, auto_filter_content: bool | None=None):
        """Configure automatic safety actions."""
        if auto_create_alerts is not None:
            self._auto_create_alerts = auto_create_alerts
        if auto_enforce_rate_limits is not None:
            self._auto_enforce_rate_limits = auto_enforce_rate_limits
        if auto_filter_content is not None:
            self._auto_filter_content = auto_filter_content

    async def close(self):
        """Clean up resources."""
        await self.rate_limiter.close()
        await self.alert_manager.close()

def create_safety_manager(content_filter_config: ContentFilterConfig | None=None, rate_limit_config: RateLimitConfig | None=None, alert_config: AlertConfig | None=None) -> SafetyManager:
    """Create a safety manager with the specified configurations."""
    return SafetyManager(content_filter_config, rate_limit_config, alert_config)