"""
Advanced Performance Analytics Alert Engine

This module provides intelligent alerting capabilities for the Advanced Performance Analytics System.
It transforms analytics insights into actionable alerts with severity classification, trend analysis,
and integration with Discord notification infrastructure.

Key Features:
- Intelligent alert generation from analytics insights
- Multi-level severity classification (Critical, Warning, Info)
- Trend-based alerting with threshold monitoring
- Integration with Discord notification systems
- Executive summary generation for alerts
- Automated alert scheduling and management
- Escalation workflows and response coordination
"""
from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from platform.time import default_utc_now
from .advanced_performance_analytics_integration import AdvancedPerformanceAnalyticsSystem
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels for performance analytics."""
    CRITICAL = 'critical'
    WARNING = 'warning'
    INFO = 'info'

class AlertCategory(Enum):
    """Categories of performance alerts."""
    PERFORMANCE_DEGRADATION = 'performance_degradation'
    RESOURCE_EXHAUSTION = 'resource_exhaustion'
    ANOMALY_DETECTION = 'anomaly_detection'
    PREDICTIVE_WARNING = 'predictive_warning'
    OPTIMIZATION_OPPORTUNITY = 'optimization_opportunity'
    SYSTEM_HEALTH = 'system_health'

@dataclass
class PerformanceAlert:
    """Structured performance alert with metadata and context."""
    alert_id: str
    severity: AlertSeverity
    category: AlertCategory
    title: str
    description: str
    metrics: dict[str, float] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=default_utc_now)
    source: str = 'analytics_engine'
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_discord_format(self) -> dict[str, Any]:
        """Convert alert to Discord-friendly format."""
        severity_emojis = {AlertSeverity.CRITICAL: '🚨', AlertSeverity.WARNING: '⚠️', AlertSeverity.INFO: 'i'}
        category_emojis = {AlertCategory.PERFORMANCE_DEGRADATION: '📉', AlertCategory.RESOURCE_EXHAUSTION: '💾', AlertCategory.ANOMALY_DETECTION: '🔍', AlertCategory.PREDICTIVE_WARNING: '🔮', AlertCategory.OPTIMIZATION_OPPORTUNITY: '⚡', AlertCategory.SYSTEM_HEALTH: '🏥'}
        severity_emoji = severity_emojis.get(self.severity, '🔔')
        category_emoji = category_emojis.get(self.category, '📊')
        metrics_text = ''
        if self.metrics:
            metrics_lines = []
            for metric, value in self.metrics.items():
                threshold = self.thresholds.get(metric)
                if threshold is not None:
                    status = '🔴' if value > threshold else '🟢'
                    metrics_lines.append(f'{status} {metric}: {value:.2f} (threshold: {threshold:.2f})')
                else:
                    metrics_lines.append(f'📊 {metric}: {value:.2f}')
            metrics_text = '\n'.join(metrics_lines)
        recommendations_text = ''
        if self.recommendations:
            recommendations_text = '\n**Recommendations:**\n' + '\n'.join((f'• {rec}' for rec in self.recommendations))
        tags_text = ''
        if self.tags:
            tags_text = f'\n**Tags:** {', '.join(self.tags)}'
        content = f'{severity_emoji} **{self.severity.value.upper()} ALERT** {category_emoji}\n\n**{self.title}**\n\n{self.description}\n\n**Metrics:**\n{metrics_text}\n{recommendations_text}\n{tags_text}\n\n**Source:** {self.source} | **Time:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n**Alert ID:** `{self.alert_id}`'
        return {'content': content, 'username': 'Performance Analytics', 'allowed_mentions': {'users': []}}

@dataclass
class AlertRule:
    """Configuration for automated alert generation."""
    rule_id: str
    name: str
    description: str
    category: AlertCategory
    severity: AlertSeverity
    metric_thresholds: dict[str, float] = field(default_factory=dict)
    trend_conditions: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    cooldown_minutes: int = 30
    tags: list[str] = field(default_factory=list)
    escalation_rules: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

class AdvancedPerformanceAnalyticsAlertEngine:
    """Advanced alert engine for performance analytics insights."""

    def __init__(self, analytics_system: AdvancedPerformanceAnalyticsSystem | None=None):
        """Initialize the alert engine.

        Args:
            analytics_system: Advanced performance analytics system instance
        """
        self.analytics_system = analytics_system or AdvancedPerformanceAnalyticsSystem()
        self.alert_rules: dict[str, AlertRule] = {}
        self.alert_history: list[PerformanceAlert] = []
        self.last_alert_times: dict[str, datetime] = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize default alert rules for common scenarios."""
        default_rules = [AlertRule(rule_id='performance_degradation_critical', name='Critical Performance Degradation', description='Detect critical performance degradation across system components', category=AlertCategory.PERFORMANCE_DEGRADATION, severity=AlertSeverity.CRITICAL, metric_thresholds={'overall_performance_score': 0.5, 'response_time': 5.0, 'error_rate': 0.1}, cooldown_minutes=15, tags=['critical', 'performance', 'degradation']), AlertRule(rule_id='resource_exhaustion_warning', name='Resource Exhaustion Warning', description='Monitor for resource exhaustion indicators', category=AlertCategory.RESOURCE_EXHAUSTION, severity=AlertSeverity.WARNING, metric_thresholds={'memory_usage': 0.85, 'cpu_usage': 0.8, 'disk_usage': 0.9}, cooldown_minutes=30, tags=['resources', 'capacity', 'warning']), AlertRule(rule_id='anomaly_detection_info', name='Performance Anomaly Detected', description='Statistical anomalies in performance metrics', category=AlertCategory.ANOMALY_DETECTION, severity=AlertSeverity.INFO, metric_thresholds={'anomaly_score': 0.7, 'deviation_threshold': 2.0}, cooldown_minutes=60, tags=['anomaly', 'statistics', 'detection']), AlertRule(rule_id='predictive_warning_critical', name='Predictive Performance Warning', description='Early warning based on predictive analytics', category=AlertCategory.PREDICTIVE_WARNING, severity=AlertSeverity.WARNING, metric_thresholds={'forecast_degradation': 0.3, 'prediction_confidence': 0.8}, cooldown_minutes=120, tags=['predictive', 'forecast', 'early-warning']), AlertRule(rule_id='optimization_opportunity', name='Optimization Opportunity', description='Identify opportunities for performance optimization', category=AlertCategory.OPTIMIZATION_OPPORTUNITY, severity=AlertSeverity.INFO, metric_thresholds={'optimization_potential': 0.2, 'efficiency_score': 0.7}, cooldown_minutes=240, tags=['optimization', 'efficiency', 'opportunity'])]
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add or update an alert rule.

        Args:
            rule: Alert rule configuration
        """
        self.alert_rules[rule.rule_id] = rule
        logger.info(f'Added/updated alert rule: {rule.name} ({rule.rule_id})')

    def remove_alert_rule(self, rule_id: str) -> bool:
        """Remove an alert rule.

        Args:
            rule_id: ID of the rule to remove

        Returns:
            True if rule was removed, False if not found
        """
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f'Removed alert rule: {rule_id}')
            return True
        return False

    def _is_rule_in_cooldown(self, rule_id: str) -> bool:
        """Check if a rule is in cooldown period.

        Args:
            rule_id: ID of the rule to check

        Returns:
            True if in cooldown, False otherwise
        """
        if rule_id not in self.last_alert_times:
            return False
        rule = self.alert_rules.get(rule_id)
        if not rule:
            return False
        cooldown_period = timedelta(minutes=rule.cooldown_minutes)
        time_since_last = default_utc_now() - self.last_alert_times[rule_id]
        return time_since_last < cooldown_period

    async def evaluate_analytics_for_alerts(self, lookback_hours: int=24) -> list[PerformanceAlert]:
        """Evaluate analytics data and generate alerts based on rules.

        Args:
            lookback_hours: Hours of historical data to analyze

        Returns:
            List of generated alerts
        """
        try:
            logger.info(f'Evaluating analytics data for alerts (lookback: {lookback_hours}h)')
            analytics_results = await self.analytics_system.run_comprehensive_performance_analysis(lookback_hours=lookback_hours, include_optimization=False)
            if 'error' in analytics_results:
                logger.error(f'Failed to get analytics results: {analytics_results['error']}')
                return []
            alerts: list[PerformanceAlert] = []
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                if self._is_rule_in_cooldown(rule_id):
                    logger.debug(f'Rule {rule_id} is in cooldown, skipping')
                    continue
                alert = await self._evaluate_rule_against_analytics(rule, analytics_results)
                if alert:
                    alerts.append(alert)
                    self.last_alert_times[rule_id] = default_utc_now()
            self.alert_history.extend(alerts)
            if len(self.alert_history) > 1000:
                self.alert_history = self.alert_history[-1000:]
            logger.info(f'Generated {len(alerts)} alerts from analytics evaluation')
            return alerts
        except Exception as e:
            logger.error(f'Error evaluating analytics for alerts: {e}')
            return []

    async def _evaluate_rule_against_analytics(self, rule: AlertRule, analytics_results: dict[str, Any]) -> PerformanceAlert | None:
        """Evaluate a specific rule against analytics results.

        Args:
            rule: Alert rule to evaluate
            analytics_results: Analytics results to evaluate against

        Returns:
            Alert if rule conditions are met, None otherwise
        """
        try:
            executive_summary = analytics_results.get('executive_summary', {})
            component_results = analytics_results.get('component_results', {})
            priority_recommendations = analytics_results.get('priority_recommendations', [])
            metrics = {'overall_performance_score': executive_summary.get('overall_performance_score', 1.0), 'system_health_score': component_results.get('analytics', {}).get('health_score', 1.0), 'reliability_score': component_results.get('predictive', {}).get('reliability_score', 1.0), 'anomalies_detected': component_results.get('analytics', {}).get('anomalies_detected', 0), 'early_warnings': component_results.get('predictive', {}).get('early_warnings', 0), 'optimization_potential': component_results.get('optimization', {}).get('success_rate', 0)}
            violated_thresholds = []
            violated_metrics = {}
            for metric_name, threshold in rule.metric_thresholds.items():
                metric_value = metrics.get(metric_name, 0)
                if metric_value > threshold:
                    violated_thresholds.append(metric_name)
                    violated_metrics[metric_name] = metric_value
            if not violated_thresholds:
                return None
            alert_id = f'{rule.rule_id}_{default_utc_now().strftime('%Y%m%d_%H%M%S')}'
            relevant_recommendations = []
            for rec in priority_recommendations[:3]:
                if isinstance(rec, dict) and 'title' in rec:
                    relevant_recommendations.append(rec['title'])
                elif isinstance(rec, str):
                    relevant_recommendations.append(rec)
            if rule.category == AlertCategory.PERFORMANCE_DEGRADATION:
                relevant_recommendations.append('Review system performance metrics and identify bottlenecks')
            elif rule.category == AlertCategory.RESOURCE_EXHAUSTION:
                relevant_recommendations.append('Scale resources or optimize resource usage')
            elif rule.category == AlertCategory.ANOMALY_DETECTION:
                relevant_recommendations.append('Investigate anomalous behavior patterns')
            violated_details = []
            for metric in violated_thresholds:
                value = violated_metrics[metric]
                threshold = rule.metric_thresholds[metric]
                violated_details.append(f'{metric}: {value:.3f} > {threshold:.3f}')
            description = f'{rule.description}\n\nViolated thresholds:\n' + '\n'.join((f'• {detail}' for detail in violated_details))
            alert = PerformanceAlert(alert_id=alert_id, severity=rule.severity, category=rule.category, title=rule.name, description=description, metrics=violated_metrics, thresholds=rule.metric_thresholds, recommendations=relevant_recommendations, tags=rule.tags.copy(), metadata={'rule_id': rule.rule_id, 'violated_thresholds': violated_thresholds, 'analytics_timestamp': analytics_results.get('analysis_metadata', {}).get('timestamp')})
            logger.info(f'Generated alert: {alert.title} (ID: {alert_id})')
            return alert
        except Exception as e:
            logger.error(f'Error evaluating rule {rule.rule_id}: {e}')
            return None

    async def get_alert_summary(self, hours: int=24) -> dict[str, Any]:
        """Get summary of alerts generated in the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            Alert summary statistics
        """
        try:
            cutoff_time = default_utc_now() - timedelta(hours=hours)
            recent_alerts = [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]
            severity_counts = {}
            for severity in AlertSeverity:
                severity_counts[severity.value] = len([a for a in recent_alerts if a.severity == severity])
            category_counts = {}
            for category in AlertCategory:
                category_counts[category.value] = len([a for a in recent_alerts if a.category == category])
            metric_violations: dict[str, Any] = {}
            for alert in recent_alerts:
                for metric in alert.metrics:
                    metric_violations[metric] = metric_violations.get(metric, 0) + 1
            return {'total_alerts': len(recent_alerts), 'time_period_hours': hours, 'severity_breakdown': severity_counts, 'category_breakdown': category_counts, 'most_violated_metrics': dict(sorted(metric_violations.items(), key=lambda x: x[1], reverse=True)[:5]), 'active_rules': len([r for r in self.alert_rules.values() if r.enabled]), 'rules_in_cooldown': len([r for r in self.alert_rules if self._is_rule_in_cooldown(r)])}
        except Exception as e:
            logger.error(f'Error generating alert summary: {e}')
            return {'error': str(e)}

    async def process_continuous_monitoring(self, interval_minutes: int=30) -> None:
        """Run continuous monitoring with periodic alert evaluation.

        Args:
            interval_minutes: Minutes between evaluation cycles
        """
        logger.info(f'Starting continuous monitoring (interval: {interval_minutes} minutes)')
        while True:
            try:
                alerts = await self.evaluate_analytics_for_alerts(lookback_hours=2)
                if alerts:
                    logger.info(f'Continuous monitoring generated {len(alerts)} alerts')
                await asyncio.sleep(interval_minutes * 60)
            except asyncio.CancelledError:
                logger.info('Continuous monitoring cancelled')
                break
            except Exception as e:
                logger.error(f'Error in continuous monitoring cycle: {e}')
                await asyncio.sleep(60)