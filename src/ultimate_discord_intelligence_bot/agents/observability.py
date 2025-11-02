"""Observability agents for monitoring and system health.

This module contains agents responsible for monitoring system health,
performance analytics, and alerting.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from crewai import Agent
from app.config.feature_flags import FeatureFlags
from ultimate_discord_intelligence_bot.tools import AdvancedPerformanceAnalyticsTool, CheckpointManagementTool, EarlyExitConditionsTool, EscalationManagementTool, ResourceAllocationTool, SystemStatusTool, WorkflowOptimizationTool
from ultimate_discord_intelligence_bot.tools.observability import CacheOptimizationTool, CostTrackingTool, OrchestrationStatusTool, RouterStatusTool, UnifiedMetricsTool
from domains.intelligence.verification import ConsistencyCheckTool, OutputValidationTool
_flags = FeatureFlags.from_env()

class ObservabilityAgents:
    """Observability agents for monitoring and system health."""

    def __init__(self):
        """Initialize observability agents."""
        self.flags = _flags

    def system_monitoring_specialist(self) -> Agent:
        """System monitoring specialist."""
        from crewai import Agent
        return Agent(role='System Monitoring Specialist', goal='Monitor system health and performance with comprehensive metrics and alerting.', backstory='Expert in system monitoring with focus on health metrics and performance tracking.', tools=[SystemStatusTool(), AdvancedPerformanceAnalyticsTool(), UnifiedMetricsTool(), OrchestrationStatusTool(), RouterStatusTool(), CostTrackingTool()], verbose=True, allow_delegation=False)

    def performance_analytics_specialist(self) -> Agent:
        """Performance analytics specialist."""
        from crewai import Agent
        return Agent(role='Performance Analytics Specialist', goal='Analyze system performance and identify optimization opportunities.', backstory='Specialist in performance analytics with expertise in system optimization and efficiency.', tools=[AdvancedPerformanceAnalyticsTool(), CacheOptimizationTool(), WorkflowOptimizationTool(), ResourceAllocationTool(), UnifiedMetricsTool()], verbose=True, allow_delegation=False)

    def alert_management_specialist(self) -> Agent:
        """Alert management specialist."""
        from crewai import Agent
        return Agent(role='Alert Management Specialist', goal='Manage alerts and notifications with intelligent routing and escalation.', backstory='Expert in alert management with focus on intelligent notification and escalation systems.', tools=[EscalationManagementTool(), SystemStatusTool(), AdvancedPerformanceAnalyticsTool(), UnifiedMetricsTool()], verbose=True, allow_delegation=False)

    def quality_assurance_specialist(self) -> Agent:
        """Quality assurance specialist."""
        from crewai import Agent
        return Agent(role='Quality Assurance Specialist', goal='Ensure output quality and system reliability with comprehensive testing and validation.', backstory='Specialist in quality assurance with expertise in testing, validation, and reliability engineering.', tools=[OutputValidationTool(), ConsistencyCheckTool(), SystemStatusTool(), AdvancedPerformanceAnalyticsTool()], verbose=True, allow_delegation=False)

    def resource_optimization_specialist(self) -> Agent:
        """Resource optimization specialist."""
        from crewai import Agent
        return Agent(role='Resource Optimization Specialist', goal='Optimize resource usage and allocation for maximum efficiency and cost-effectiveness.', backstory='Expert in resource optimization with focus on efficiency and cost management.', tools=[ResourceAllocationTool(), CacheOptimizationTool(), WorkflowOptimizationTool(), CostTrackingTool(), AdvancedPerformanceAnalyticsTool()], verbose=True, allow_delegation=False)

    def orchestration_monitoring_specialist(self) -> Agent:
        """Orchestration monitoring specialist."""
        from crewai import Agent
        return Agent(role='Orchestration Monitoring Specialist', goal='Monitor orchestration systems and ensure smooth workflow execution.', backstory='Specialist in orchestration monitoring with expertise in workflow management and execution tracking.', tools=[OrchestrationStatusTool(), RouterStatusTool(), SystemStatusTool(), AdvancedPerformanceAnalyticsTool(), CheckpointManagementTool(), EarlyExitConditionsTool()], verbose=True, allow_delegation=False)

    def cost_optimization_specialist(self) -> Agent:
        """Cost optimization specialist."""
        from crewai import Agent
        return Agent(role='Cost Optimization Specialist', goal='Optimize costs and resource usage for maximum value and efficiency.', backstory='Expert in cost optimization with focus on value engineering and resource efficiency.', tools=[CostTrackingTool(), ResourceAllocationTool(), CacheOptimizationTool(), WorkflowOptimizationTool(), AdvancedPerformanceAnalyticsTool()], verbose=True, allow_delegation=False)