"""
Advanced Performance Analytics Alert Management System

This module provides comprehensive alert management capabilities including scheduling,
escalation, response coordination, and automated performance monitoring workflows.

Key Features:
- Automated performance monitoring scheduling
- Alert escalation and response coordination
- Configurable notification policies and thresholds
- Integration with crew task scheduling
- Performance trend monitoring and alerting
- Executive reporting automation
- System health orchestration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from core.time import default_utc_now

from .advanced_performance_analytics_discord_integration import AdvancedPerformanceAnalyticsDiscordIntegration
from .crew import UltimateDiscordIntelligenceBotCrew

logger = logging.getLogger(__name__)


class MonitoringFrequency(Enum):
    """Monitoring frequency options."""

    CONTINUOUS = "continuous"  # Real-time monitoring
    HIGH = "high"  # Every 15 minutes
    MEDIUM = "medium"  # Every hour
    LOW = "low"  # Every 4 hours
    DAILY = "daily"  # Once per day
    WEEKLY = "weekly"  # Once per week


class EscalationLevel(Enum):
    """Alert escalation levels."""

    NONE = "none"  # No escalation
    NOTIFY = "notify"  # Send notifications
    ALERT = "alert"  # Send alerts to private channels
    ESCALATE = "escalate"  # Escalate to management
    CRITICAL = "critical"  # Critical escalation with immediate response


@dataclass
class MonitoringSchedule:
    """Configuration for automated monitoring schedules."""

    schedule_id: str
    name: str
    description: str
    frequency: MonitoringFrequency
    enabled: bool = True
    lookback_hours: int = 24
    include_optimization: bool = False
    send_notifications: bool = True
    escalation_level: EscalationLevel = EscalationLevel.NOTIFY
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    last_execution: datetime | None = None
    next_execution: datetime | None = None


@dataclass
class AlertPolicy:
    """Alert policy configuration for automated responses."""

    policy_id: str
    name: str
    description: str
    conditions: dict[str, Any] = field(default_factory=dict)
    actions: list[str] = field(default_factory=list)
    escalation_rules: dict[EscalationLevel, dict[str, Any]] = field(default_factory=dict)
    cooldown_minutes: int = 60
    enabled: bool = True
    priority: int = 1  # 1 = highest, 10 = lowest


class AdvancedPerformanceAnalyticsAlertManager:
    """Comprehensive alert management system for performance analytics."""

    def __init__(
        self,
        discord_integration: AdvancedPerformanceAnalyticsDiscordIntegration | None = None,
        crew: UltimateDiscordIntelligenceBotCrew | None = None,
    ):
        """Initialize the alert management system.

        Args:
            discord_integration: Discord integration instance
            crew: Crew instance for task execution
        """
        self.discord_integration = discord_integration or AdvancedPerformanceAnalyticsDiscordIntegration()
        self.crew = crew
        self.monitoring_schedules: dict[str, MonitoringSchedule] = {}
        self.alert_policies: dict[str, AlertPolicy] = {}
        self.execution_history: list[dict[str, Any]] = []
        self.active_tasks: dict[str, Any] = {}

        # Initialize default schedules and policies
        self._initialize_default_configurations()

    def _initialize_default_configurations(self) -> None:
        """Initialize default monitoring schedules and alert policies."""
        # Default monitoring schedules
        default_schedules = [
            MonitoringSchedule(
                schedule_id="continuous_critical_monitoring",
                name="Continuous Critical Monitoring",
                description="Real-time monitoring for critical performance issues",
                frequency=MonitoringFrequency.HIGH,
                lookback_hours=2,
                send_notifications=True,
                escalation_level=EscalationLevel.ALERT,
                tags=["critical", "real-time", "performance"],
            ),
            MonitoringSchedule(
                schedule_id="hourly_performance_check",
                name="Hourly Performance Check",
                description="Regular performance health checks",
                frequency=MonitoringFrequency.MEDIUM,
                lookback_hours=4,
                send_notifications=True,
                escalation_level=EscalationLevel.NOTIFY,
                tags=["regular", "health-check"],
            ),
            MonitoringSchedule(
                schedule_id="daily_optimization_review",
                name="Daily Optimization Review",
                description="Daily performance optimization analysis",
                frequency=MonitoringFrequency.DAILY,
                lookback_hours=24,
                include_optimization=True,
                send_notifications=True,
                escalation_level=EscalationLevel.NOTIFY,
                tags=["daily", "optimization"],
            ),
            MonitoringSchedule(
                schedule_id="executive_weekly_summary",
                name="Executive Weekly Summary",
                description="Weekly executive performance summary",
                frequency=MonitoringFrequency.WEEKLY,
                lookback_hours=168,  # 7 days
                send_notifications=True,
                escalation_level=EscalationLevel.ESCALATE,
                tags=["executive", "weekly", "summary"],
            ),
        ]

        for schedule in default_schedules:
            self.monitoring_schedules[schedule.schedule_id] = schedule

        # Default alert policies
        default_policies = [
            AlertPolicy(
                policy_id="critical_performance_degradation",
                name="Critical Performance Degradation Response",
                description="Immediate response for critical performance issues",
                conditions={
                    "overall_performance_score": {"operator": "less_than", "value": 0.5},
                    "critical_alerts": {"operator": "greater_than", "value": 0},
                },
                actions=["send_critical_alert", "escalate_to_management", "trigger_optimization"],
                escalation_rules={
                    EscalationLevel.CRITICAL: {"immediate_notification": True, "escalate_after_minutes": 0},
                    EscalationLevel.ESCALATE: {"escalate_after_minutes": 15},
                },
                cooldown_minutes=30,
                priority=1,
            ),
            AlertPolicy(
                policy_id="resource_exhaustion_warning",
                name="Resource Exhaustion Warning Response",
                description="Response for resource exhaustion scenarios",
                conditions={
                    "resource_alerts": {"operator": "greater_than", "value": 2},
                    "capacity_warnings": {"operator": "greater_than", "value": 0},
                },
                actions=["send_warning_alert", "recommend_scaling", "schedule_optimization"],
                escalation_rules={
                    EscalationLevel.ALERT: {"escalate_after_minutes": 30},
                    EscalationLevel.ESCALATE: {"escalate_after_minutes": 60},
                },
                cooldown_minutes=60,
                priority=2,
            ),
        ]

        for policy in default_policies:
            self.alert_policies[policy.policy_id] = policy

    def add_monitoring_schedule(self, schedule: MonitoringSchedule) -> None:
        """Add or update a monitoring schedule.

        Args:
            schedule: Monitoring schedule configuration
        """
        self.monitoring_schedules[schedule.schedule_id] = schedule
        self._calculate_next_execution(schedule)
        logger.info(f"Added/updated monitoring schedule: {schedule.name} ({schedule.schedule_id})")

    def add_alert_policy(self, policy: AlertPolicy) -> None:
        """Add or update an alert policy.

        Args:
            policy: Alert policy configuration
        """
        self.alert_policies[policy.policy_id] = policy
        logger.info(f"Added/updated alert policy: {policy.name} ({policy.policy_id})")

    def _calculate_next_execution(self, schedule: MonitoringSchedule) -> None:
        """Calculate the next execution time for a schedule.

        Args:
            schedule: Monitoring schedule to calculate for
        """
        now = default_utc_now()
        if schedule.frequency == MonitoringFrequency.CONTINUOUS:
            schedule.next_execution = now  # Execute immediately for continuous
        elif schedule.frequency == MonitoringFrequency.HIGH:
            schedule.next_execution = now + timedelta(minutes=15)
        elif schedule.frequency == MonitoringFrequency.MEDIUM:
            schedule.next_execution = now + timedelta(hours=1)
        elif schedule.frequency == MonitoringFrequency.LOW:
            schedule.next_execution = now + timedelta(hours=4)
        elif schedule.frequency == MonitoringFrequency.DAILY:
            schedule.next_execution = now + timedelta(days=1)
        elif schedule.frequency == MonitoringFrequency.WEEKLY:
            schedule.next_execution = now + timedelta(weeks=1)

    async def execute_monitoring_schedule(self, schedule_id: str) -> dict[str, Any]:
        """Execute a specific monitoring schedule.

        Args:
            schedule_id: ID of the schedule to execute

        Returns:
            Execution results
        """
        try:
            if schedule_id not in self.monitoring_schedules:
                return {"status": "error", "error": f"Schedule {schedule_id} not found"}

            schedule = self.monitoring_schedules[schedule_id]

            if not schedule.enabled:
                return {"status": "skipped", "reason": "Schedule is disabled"}

            logger.info(f"Executing monitoring schedule: {schedule.name}")

            # Execute analytics based on schedule configuration
            if schedule.frequency == MonitoringFrequency.WEEKLY and "executive" in schedule.tags:
                # Executive summary
                result = await self.discord_integration.send_executive_summary(schedule.lookback_hours)
            else:
                # Regular monitoring
                alerts = await self.discord_integration.alert_engine.evaluate_analytics_for_alerts(
                    schedule.lookback_hours
                )

                if alerts and schedule.send_notifications:
                    notification_result = await self.discord_integration.send_batch_notifications(alerts)
                    result = {
                        "status": "executed",
                        "alerts_generated": len(alerts),
                        "notifications_sent": notification_result.get("status") == "success",
                    }
                else:
                    result = {"status": "executed", "alerts_generated": len(alerts), "notifications_sent": False}

            # Update schedule timing
            schedule.last_execution = default_utc_now()
            self._calculate_next_execution(schedule)

            # Record execution
            execution_record = {
                "schedule_id": schedule_id,
                "schedule_name": schedule.name,
                "execution_time": schedule.last_execution,
                "next_execution": schedule.next_execution,
                "result": result,
                "escalation_level": schedule.escalation_level.value,
            }

            self.execution_history.append(execution_record)

            # Keep only recent history (last 100 executions)
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]

            # Apply alert policies if alerts were generated
            if result.get("alerts_generated", 0) > 0:
                await self._apply_alert_policies(result, schedule)

            logger.info(f"Completed monitoring schedule execution: {schedule.name}")
            return {
                "status": "success",
                "schedule_executed": schedule.name,
                "execution_result": result,
                "next_execution": schedule.next_execution.isoformat() if schedule.next_execution else None,
            }

        except Exception as e:
            logger.error(f"Error executing monitoring schedule {schedule_id}: {e}")
            return {"status": "error", "schedule_id": schedule_id, "error": str(e)}

    async def _apply_alert_policies(self, monitoring_result: dict[str, Any], schedule: MonitoringSchedule) -> None:
        """Apply alert policies based on monitoring results.

        Args:
            monitoring_result: Results from monitoring execution
            schedule: Schedule that was executed
        """
        try:
            # Check each policy against the monitoring results
            for policy_id, policy in self.alert_policies.items():
                if not policy.enabled:
                    continue

                # Evaluate policy conditions
                if await self._evaluate_policy_conditions(policy, monitoring_result, schedule):
                    await self._execute_policy_actions(policy, monitoring_result, schedule)

        except Exception as e:
            logger.error(f"Error applying alert policies: {e}")

    async def _evaluate_policy_conditions(
        self, policy: AlertPolicy, monitoring_result: dict[str, Any], schedule: MonitoringSchedule
    ) -> bool:
        """Evaluate if policy conditions are met.

        Args:
            policy: Alert policy to evaluate
            monitoring_result: Monitoring execution results
            schedule: Schedule that was executed

        Returns:
            True if conditions are met, False otherwise
        """
        try:
            for condition_key, condition_config in policy.conditions.items():
                operator = condition_config.get("operator", "equals")
                expected_value = condition_config.get("value")

                # Get actual value from monitoring result
                actual_value = monitoring_result.get(condition_key, 0)

                # Evaluate condition
                if operator == "greater_than" and actual_value <= expected_value:
                    return False
                elif operator == "less_than" and actual_value >= expected_value:
                    return False
                elif operator == "equals" and actual_value != expected_value:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error evaluating policy conditions for {policy.policy_id}: {e}")
            return False

    async def _execute_policy_actions(
        self, policy: AlertPolicy, monitoring_result: dict[str, Any], schedule: MonitoringSchedule
    ) -> None:
        """Execute policy actions.

        Args:
            policy: Alert policy with actions to execute
            monitoring_result: Monitoring execution results
            schedule: Schedule that was executed
        """
        try:
            for action in policy.actions:
                if action == "send_critical_alert":
                    await self._send_policy_alert(policy, monitoring_result, "critical")
                elif action == "send_warning_alert":
                    await self._send_policy_alert(policy, monitoring_result, "warning")
                elif action == "escalate_to_management":
                    await self._escalate_to_management(policy, monitoring_result)
                elif action == "trigger_optimization":
                    await self._trigger_optimization(policy, monitoring_result)

            logger.info(f"Executed {len(policy.actions)} actions for policy {policy.policy_id}")

        except Exception as e:
            logger.error(f"Error executing policy actions for {policy.policy_id}: {e}")

    async def _send_policy_alert(self, policy: AlertPolicy, monitoring_result: dict[str, Any], severity: str) -> None:
        """Send policy-triggered alert.

        Args:
            policy: Alert policy
            monitoring_result: Monitoring results
            severity: Alert severity level
        """
        # Create policy alert message
        alert_message = f"""🚨 **POLICY ALERT: {policy.name}** 🚨

**Policy ID:** {policy.policy_id}
**Severity:** {severity.upper()}
**Triggered:** {default_utc_now().strftime("%Y-%m-%d %H:%M:%S UTC")}

**Description:** {policy.description}

**Monitoring Results:**
• Alerts Generated: {monitoring_result.get("alerts_generated", 0)}
• Notifications Sent: {monitoring_result.get("notifications_sent", False)}

**Actions:** {", ".join(policy.actions)}

**Policy Priority:** {policy.priority}
**Cooldown:** {policy.cooldown_minutes} minutes"""

        # Send via Discord integration
        if hasattr(self.discord_integration, "private_alert_tool") and self.discord_integration.private_alert_tool:
            self.discord_integration.private_alert_tool._run(message=alert_message)

    async def _escalate_to_management(self, policy: AlertPolicy, monitoring_result: dict[str, Any]) -> None:
        """Escalate alert to management channels.

        Args:
            policy: Alert policy
            monitoring_result: Monitoring results
        """
        # Send executive summary with escalation context
        await self.discord_integration.send_executive_summary(hours=24)

    async def _trigger_optimization(self, policy: AlertPolicy, monitoring_result: dict[str, Any]) -> None:
        """Trigger automated optimization.

        Args:
            policy: Alert policy
            monitoring_result: Monitoring results
        """
        # Execute optimization through analytics system
        optimization_results = (
            await self.discord_integration.alert_engine.analytics_system.run_comprehensive_performance_analysis(
                lookback_hours=24, include_optimization=True
            )
        )
        logger.info(f"Policy-triggered optimization completed: {optimization_results.get('status', 'unknown')}")

    async def get_management_dashboard(self) -> dict[str, Any]:
        """Get comprehensive management dashboard data.

        Returns:
            Management dashboard with schedules, policies, and execution status
        """
        try:
            now = default_utc_now()

            # Schedule status
            schedule_status = {}
            for schedule_id, schedule in self.monitoring_schedules.items():
                next_exec = schedule.next_execution
                schedule_status[schedule_id] = {
                    "name": schedule.name,
                    "enabled": schedule.enabled,
                    "frequency": schedule.frequency.value,
                    "last_execution": schedule.last_execution.isoformat() if schedule.last_execution else None,
                    "next_execution": next_exec.isoformat() if next_exec else None,
                    "overdue": next_exec < now if next_exec else False,
                    "escalation_level": schedule.escalation_level.value,
                }

            # Policy status
            policy_status = {}
            for policy_id, policy in self.alert_policies.items():
                policy_status[policy_id] = {
                    "name": policy.name,
                    "enabled": policy.enabled,
                    "priority": policy.priority,
                    "cooldown_minutes": policy.cooldown_minutes,
                    "conditions_count": len(policy.conditions),
                    "actions_count": len(policy.actions),
                }

            # Recent execution summary
            recent_executions = self.execution_history[-10:]  # Last 10 executions
            execution_summary = {
                "total_executions": len(self.execution_history),
                "recent_executions": len(recent_executions),
                "successful_executions": len([e for e in recent_executions if e["result"].get("status") == "executed"]),
                "last_execution": recent_executions[-1]["execution_time"].isoformat() if recent_executions else None,
            }

            return {
                "dashboard_timestamp": now.isoformat(),
                "schedules": {
                    "total": len(self.monitoring_schedules),
                    "enabled": len([s for s in self.monitoring_schedules.values() if s.enabled]),
                    "status": schedule_status,
                },
                "policies": {
                    "total": len(self.alert_policies),
                    "enabled": len([p for p in self.alert_policies.values() if p.enabled]),
                    "status": policy_status,
                },
                "execution_summary": execution_summary,
                "system_status": "operational",
            }

        except Exception as e:
            logger.error(f"Error generating management dashboard: {e}")
            return {"error": str(e)}

    async def run_scheduled_monitoring_cycle(self) -> dict[str, Any]:
        """Run a complete monitoring cycle for all due schedules.

        Returns:
            Results of the monitoring cycle
        """
        try:
            now = default_utc_now()
            executed_schedules = []
            skipped_schedules = []

            for schedule_id, schedule in self.monitoring_schedules.items():
                if not schedule.enabled:
                    skipped_schedules.append({"schedule_id": schedule_id, "reason": "disabled"})
                    continue

                # Check if schedule is due
                if schedule.next_execution and schedule.next_execution <= now:
                    result = await self.execute_monitoring_schedule(schedule_id)
                    executed_schedules.append(result)
                else:
                    skipped_schedules.append({"schedule_id": schedule_id, "reason": "not_due"})

            return {
                "status": "cycle_complete",
                "cycle_timestamp": now.isoformat(),
                "executed_schedules": len(executed_schedules),
                "skipped_schedules": len(skipped_schedules),
                "execution_details": executed_schedules,
                "skip_details": skipped_schedules,
            }

        except Exception as e:
            logger.error(f"Error running scheduled monitoring cycle: {e}")
            return {"status": "error", "error": str(e)}


# Convenience functions for easy integration
async def start_automated_monitoring(
    discord_integration: AdvancedPerformanceAnalyticsDiscordIntegration | None = None,
) -> AdvancedPerformanceAnalyticsAlertManager:
    """Start automated performance monitoring with default configurations.

    Args:
        discord_integration: Discord integration instance

    Returns:
        Configured alert manager
    """
    alert_manager = AdvancedPerformanceAnalyticsAlertManager(discord_integration=discord_integration)
    logger.info("Started automated performance monitoring with default configurations")
    return alert_manager


async def execute_immediate_performance_check(lookback_hours: int = 2) -> dict[str, Any]:
    """Execute immediate performance check with alerting.

    Args:
        lookback_hours: Hours of data to analyze

    Returns:
        Performance check results
    """
    alert_manager = AdvancedPerformanceAnalyticsAlertManager()

    # Create immediate monitoring schedule
    immediate_schedule = MonitoringSchedule(
        schedule_id="immediate_check",
        name="Immediate Performance Check",
        description="On-demand performance analysis",
        frequency=MonitoringFrequency.CONTINUOUS,
        lookback_hours=lookback_hours,
        send_notifications=True,
        escalation_level=EscalationLevel.NOTIFY,
    )

    alert_manager.add_monitoring_schedule(immediate_schedule)
    return await alert_manager.execute_monitoring_schedule("immediate_check")
