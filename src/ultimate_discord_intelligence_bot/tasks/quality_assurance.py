"""Quality assurance tasks for the Ultimate Discord Intelligence Bot.

This module contains tasks for quality assessment, validation, and
performance monitoring workflows.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crewai import Task
from domains.orchestration.agents import AnalysisAgents, ObservabilityAgents, VerificationAgents


class QualityAssuranceTasks:
    """Quality assurance tasks for the Ultimate Discord Intelligence Bot."""

    def __init__(self):
        """Initialize quality assurance tasks."""
        self.analysis_agents = AnalysisAgents()
        self.verification_agents = VerificationAgents()
        self.observability_agents = ObservabilityAgents()

    def assess_content_quality(self) -> Task:
        """Assess content quality and accuracy."""
        from crewai import Task

        return Task(
            description="Assess the quality and accuracy of content analysis results, fact-checking outcomes, and intelligence synthesis.",
            expected_output="Quality assessment report with accuracy metrics, reliability scores, and improvement recommendations.",
            agent=self.analysis_agents.analysis_cartographer(),
        )

    def validate_fact_checking_results(self) -> Task:
        """Validate fact-checking results and accuracy."""
        from crewai import Task

        return Task(
            description="Validate fact-checking results for accuracy, completeness, and source reliability.",
            expected_output="Fact-checking validation report with accuracy metrics and source verification status.",
            agent=self.verification_agents.verification_director(),
        )

    def monitor_system_performance(self) -> Task:
        """Monitor system performance and health."""
        from crewai import Task

        return Task(
            description="Monitor system performance, resource usage, and health metrics to ensure optimal operation.",
            expected_output="System performance report with metrics, health status, and optimization recommendations.",
            agent=self.observability_agents.system_monitoring_specialist(),
        )

    def optimize_resource_usage(self) -> Task:
        """Optimize resource usage and allocation."""
        from crewai import Task

        return Task(
            description="Analyze resource usage patterns and optimize allocation for maximum efficiency and cost-effectiveness.",
            expected_output="Resource optimization report with usage analysis, efficiency metrics, and optimization recommendations.",
            agent=self.observability_agents.resource_optimization_specialist(),
        )

    def ensure_output_consistency(self) -> Task:
        """Ensure output consistency and reliability."""
        from crewai import Task

        return Task(
            description="Ensure output consistency across all analysis results and verify reliability of conclusions.",
            expected_output="Consistency validation report with reliability metrics and quality assurance status.",
            agent=self.verification_agents.verification_director(),
        )

    def track_quality_metrics(self) -> Task:
        """Track quality metrics and performance indicators."""
        from crewai import Task

        return Task(
            description="Track quality metrics and performance indicators to monitor system effectiveness and reliability.",
            expected_output="Quality metrics report with performance indicators, trends, and improvement recommendations.",
            agent=self.observability_agents.quality_assurance_specialist(),
        )
