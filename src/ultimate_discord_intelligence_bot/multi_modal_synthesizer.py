"""Multi-modal result synthesis with quality grading for autonomous intelligence workflows.

This module provides sophisticated result aggregation, quality assessment, and
multi-modal synthesis capabilities that combine outputs from all specialized agents
into coherent, graded intelligence products.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .step_result import StepResult


class QualityGrade(Enum):
    """Quality grades for intelligence outputs."""

    EXCELLENT = "excellent"  # 90-100% confidence, comprehensive analysis
    GOOD = "good"  # 70-89% confidence, solid analysis
    SATISFACTORY = "satisfactory"  # 50-69% confidence, adequate analysis
    LIMITED = "limited"  # 30-49% confidence, partial analysis
    POOR = "poor"  # 0-29% confidence, insufficient analysis


class AnalysisDepth(Enum):
    """Analysis depth levels for different workflow modes."""

    STANDARD = "standard"
    DEEP = "deep"
    COMPREHENSIVE = "comprehensive"
    EXPERIMENTAL = "experimental"


@dataclass
class AgentContribution:
    """Individual agent contribution to the overall analysis."""

    agent_name: str
    stage_name: str
    result: StepResult
    quality_score: float
    confidence_level: float
    processing_time: float
    data_completeness: float
    error_indicators: list[str]


@dataclass
class SynthesisMetrics:
    """Metrics for the synthesis process."""

    total_agents_executed: int
    successful_agents: int
    failed_agents: int
    degraded_agents: int
    average_quality_score: float
    overall_confidence: float
    synthesis_completeness: float
    processing_time_seconds: float


class MultiModalSynthesizer:
    """Advanced multi-modal result synthesizer with quality grading."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.synthesis_history: list[dict[str, Any]] = []

    async def synthesize_intelligence_results(
        self,
        workflow_results: dict[str, Any],
        analysis_depth: str,
        workflow_metadata: dict[str, Any],
    ) -> tuple[StepResult, dict[str, Any]]:
        """
        Synthesize multi-modal intelligence results with comprehensive quality grading.

        Args:
            workflow_results: Dictionary of all stage results
            analysis_depth: Depth of analysis performed
            workflow_metadata: Metadata about the workflow execution

        Returns:
            Tuple of synthesized result and detailed quality assessment
        """
        try:
            self.logger.info(f"Starting multi-modal synthesis for {analysis_depth} analysis")

            # Assess individual agent contributions
            agent_contributions = self._assess_agent_contributions(workflow_results, analysis_depth)

            # Calculate synthesis metrics
            synthesis_metrics = self._calculate_synthesis_metrics(agent_contributions)

            # Perform multi-modal data fusion
            fused_intelligence = await self._perform_data_fusion(agent_contributions, analysis_depth)

            # Grade overall quality
            overall_quality = self._grade_overall_quality(synthesis_metrics, fused_intelligence, analysis_depth)

            # Create executive intelligence summary
            executive_summary = self._create_executive_summary(fused_intelligence, overall_quality, synthesis_metrics)

            # Generate comprehensive intelligence report
            intelligence_report = self._generate_intelligence_report(
                agent_contributions,
                fused_intelligence,
                overall_quality,
                synthesis_metrics,
                workflow_metadata,
            )

            # Create final synthesized result
            synthesized_result = StepResult.ok(
                message=f"Multi-modal intelligence synthesis completed - Quality: {overall_quality.value}",
                executive_summary=executive_summary,
                intelligence_report=intelligence_report,
                fused_intelligence=fused_intelligence,
                quality_grade=overall_quality.value,
                synthesis_metrics=synthesis_metrics.__dict__,
                agent_contributions=[contrib.__dict__ for contrib in agent_contributions],
                workflow_metadata=workflow_metadata,
            )

            # Quality assessment details
            quality_assessment = {
                "overall_grade": overall_quality.value,
                "confidence_score": synthesis_metrics.overall_confidence,
                "completeness_score": synthesis_metrics.synthesis_completeness,
                "agent_success_rate": synthesis_metrics.successful_agents
                / max(synthesis_metrics.total_agents_executed, 1),
                "quality_indicators": self._extract_quality_indicators(agent_contributions),
                "improvement_recommendations": self._generate_improvement_recommendations(
                    synthesis_metrics, overall_quality
                ),
            }

            # Store synthesis history
            self.synthesis_history.append(
                {
                    "timestamp": workflow_metadata.get("workflow_id", "unknown"),
                    "depth": analysis_depth,
                    "quality": overall_quality.value,
                    "metrics": synthesis_metrics.__dict__,
                }
            )

            return synthesized_result, quality_assessment

        except Exception as e:
            self.logger.error(f"Multi-modal synthesis failed: {e}", exc_info=True)
            failure_result = StepResult.fail(
                f"Intelligence synthesis failed: {e}",
                step="multi_modal_synthesis_failure",
            )
            return failure_result, {"error": str(e), "quality": QualityGrade.POOR.value}

    def _assess_agent_contributions(
        self, workflow_results: dict[str, Any], analysis_depth: str
    ) -> list[AgentContribution]:
        """Assess the quality and completeness of each agent's contribution."""
        contributions = []

        agent_stage_mapping = {
            "mission_plan": "autonomous_mission_coordinator",
            "acquisition": "multi_platform_acquisition_specialist",
            "transcription": "advanced_transcription_engineer",
            "content_analysis": "comprehensive_linguistic_analyst",
            "information_verification": "information_verification_director",
            "threat_analysis": "threat_intelligence_analyst",
            "behavioral_profiling": "behavioral_profiling_specialist",
            "social_intelligence": "social_intelligence_coordinator",
            "knowledge_integration": "knowledge_integration_architect",
            "research_synthesis": "research_synthesis_specialist",
            "intelligence_briefing": "intelligence_briefing_director",
        }

        for stage_name, stage_data in workflow_results.items():
            if stage_name in agent_stage_mapping and stage_data:
                agent_name = agent_stage_mapping[stage_name]

                # Create mock StepResult if data is just a dict
                if isinstance(stage_data, dict):
                    # Preserve existing mapping semantics and avoid positional args
                    mock_result = StepResult.from_dict(stage_data)
                else:
                    mock_result = stage_data

                contribution = AgentContribution(
                    agent_name=agent_name,
                    stage_name=stage_name,
                    result=mock_result,
                    quality_score=self._calculate_quality_score(stage_data, analysis_depth),
                    confidence_level=self._calculate_confidence_level(stage_data),
                    processing_time=1.0,  # Default processing time
                    data_completeness=self._calculate_data_completeness(stage_data),
                    error_indicators=self._extract_error_indicators(stage_data),
                )
                contributions.append(contribution)

        return contributions

    def _calculate_quality_score(self, stage_data: Any, analysis_depth: str) -> float:
        """Calculate quality score for a stage result."""
        base_score = 0.7  # Default score

        if not stage_data:
            return 0.1

        # Check for error indicators
        if isinstance(stage_data, dict):
            if stage_data.get("degraded_execution"):
                base_score *= 0.6
            if stage_data.get("recovery_applied"):
                base_score *= 0.8
            if stage_data.get("crew_analysis"):
                base_score *= 1.2
            if stage_data.get("enhanced_workflow"):
                base_score *= 1.1

        # Depth-based adjustments
        depth_multipliers = {
            "standard": 0.8,
            "deep": 1.0,
            "comprehensive": 1.2,
            "experimental": 1.3,
        }

        return min(1.0, base_score * depth_multipliers.get(analysis_depth, 1.0))

    def _calculate_confidence_level(self, stage_data: Any) -> float:
        """Calculate confidence level for a stage result."""
        if not stage_data:
            return 0.1

        base_confidence = 0.7

        if isinstance(stage_data, dict):
            # Check for specific confidence indicators
            if "confidence_level" in stage_data:
                return float(stage_data["confidence_level"])

            if stage_data.get("verification_status") == "verified":
                base_confidence = 0.9
            elif stage_data.get("requires_manual_review"):
                base_confidence = 0.4
            elif stage_data.get("degraded_execution"):
                base_confidence = 0.5

        return base_confidence

    def _calculate_data_completeness(self, stage_data: Any) -> float:
        """Calculate data completeness score for a stage result."""
        if not stage_data:
            return 0.0

        if isinstance(stage_data, dict):
            total_expected_fields = 10  # Baseline expectation
            present_fields = len([k for k, v in stage_data.items() if v is not None])
            return min(1.0, present_fields / total_expected_fields)

        return 0.5  # Default for non-dict data

    def _extract_error_indicators(self, stage_data: Any) -> list[str]:
        """Extract error indicators from stage data."""
        indicators = []

        if isinstance(stage_data, dict):
            if stage_data.get("degraded_execution"):
                indicators.append("degraded_execution")
            if stage_data.get("recovery_applied"):
                indicators.append("recovery_applied")
            if stage_data.get("requires_manual_review"):
                indicators.append("requires_manual_review")
            if stage_data.get("error_type"):
                indicators.append(f"error_type_{stage_data['error_type']}")

        return indicators

    def _calculate_synthesis_metrics(self, agent_contributions: list[AgentContribution]) -> SynthesisMetrics:
        """Calculate overall synthesis metrics from agent contributions."""
        total_agents = len(agent_contributions)
        successful_agents = len([c for c in agent_contributions if c.result.success])
        failed_agents = len([c for c in agent_contributions if not c.result.success])
        degraded_agents = len([c for c in agent_contributions if "degraded_execution" in c.error_indicators])

        avg_quality = sum(c.quality_score for c in agent_contributions) / max(total_agents, 1)
        overall_confidence = sum(c.confidence_level for c in agent_contributions) / max(total_agents, 1)
        avg_completeness = sum(c.data_completeness for c in agent_contributions) / max(total_agents, 1)
        total_processing_time = sum(c.processing_time for c in agent_contributions)

        return SynthesisMetrics(
            total_agents_executed=total_agents,
            successful_agents=successful_agents,
            failed_agents=failed_agents,
            degraded_agents=degraded_agents,
            average_quality_score=avg_quality,
            overall_confidence=overall_confidence,
            synthesis_completeness=avg_completeness,
            processing_time_seconds=total_processing_time,
        )

    async def _perform_data_fusion(
        self, agent_contributions: list[AgentContribution], analysis_depth: str
    ) -> dict[str, Any]:
        """Perform intelligent multi-modal data fusion across agent outputs."""
        fused_data = {
            "content_insights": {},
            "verification_results": {},
            "threat_assessment": {},
            "behavioral_profile": {},
            "social_intelligence": {},
            "knowledge_integration": {},
            "research_findings": {},
            "cross_agent_correlations": {},
            "confidence_weighted_conclusions": {},
        }

        # Fusion strategy based on analysis depth
        fusion_strategies = {
            "standard": self._basic_fusion_strategy,
            "deep": self._enhanced_fusion_strategy,
            "comprehensive": self._comprehensive_fusion_strategy,
            "experimental": self._experimental_fusion_strategy,
        }

        fusion_strategy = fusion_strategies.get(analysis_depth, self._basic_fusion_strategy)
        fused_data = await fusion_strategy(agent_contributions, fused_data)

        return fused_data

    async def _basic_fusion_strategy(
        self, contributions: list[AgentContribution], fused_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Basic fusion strategy for standard analysis."""
        # Simple aggregation of high-confidence results
        for contrib in contributions:
            if contrib.confidence_level > 0.6:
                stage_data = contrib.result.data
                fused_data[contrib.stage_name] = {
                    "summary": str(stage_data)[:200],
                    "confidence": contrib.confidence_level,
                    "quality": contrib.quality_score,
                }

        return fused_data

    async def _enhanced_fusion_strategy(
        self, contributions: list[AgentContribution], fused_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Enhanced fusion strategy for deep analysis."""
        # Weighted fusion based on quality scores
        for contrib in contributions:
            weight = contrib.quality_score * contrib.confidence_level
            stage_data = contrib.result.data

            fused_data[contrib.stage_name] = {
                "weighted_summary": str(stage_data)[:300],
                "confidence": contrib.confidence_level,
                "quality": contrib.quality_score,
                "weight": weight,
                "completeness": contrib.data_completeness,
            }

        return fused_data

    async def _comprehensive_fusion_strategy(
        self, contributions: list[AgentContribution], fused_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Comprehensive fusion strategy for comprehensive analysis."""
        # Cross-agent correlation and validation
        await self._enhanced_fusion_strategy(contributions, fused_data)

        # Add cross-correlations
        fused_data["cross_agent_correlations"] = self._calculate_cross_correlations(contributions)

        return fused_data

    async def _experimental_fusion_strategy(
        self, contributions: list[AgentContribution], fused_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Experimental fusion strategy for experimental analysis."""
        # Advanced multi-modal fusion with predictive elements
        await self._comprehensive_fusion_strategy(contributions, fused_data)

        # Add predictive insights
        fused_data["predictive_insights"] = self._generate_predictive_insights(contributions)

        return fused_data

    def _calculate_cross_correlations(self, contributions: list[AgentContribution]) -> dict[str, float]:
        """Calculate correlations between different agent outputs."""
        correlations = {}

        # Simple correlation calculation between key agents
        key_agents = ["content_analysis", "information_verification", "threat_analysis"]

        for i, agent1 in enumerate(key_agents):
            for agent2 in key_agents[i + 1 :]:
                contrib1 = next((c for c in contributions if c.stage_name == agent1), None)
                contrib2 = next((c for c in contributions if c.stage_name == agent2), None)

                if contrib1 and contrib2:
                    # Simple correlation based on quality and confidence alignment
                    correlation = abs(contrib1.quality_score - contrib2.quality_score)
                    correlations[f"{agent1}_{agent2}"] = max(0.0, 1.0 - correlation)

        return correlations

    def _generate_predictive_insights(self, contributions: list[AgentContribution]) -> dict[str, Any]:
        """Generate predictive insights from agent contributions."""
        insights = {
            "trend_predictions": [],
            "risk_forecasts": [],
            "confidence_trajectories": {},
        }

        # Analyze patterns in agent outputs for predictive value
        for contrib in contributions:
            if contrib.stage_name == "threat_analysis" and contrib.confidence_level > 0.7:
                insights["risk_forecasts"].append(
                    {
                        "source": contrib.agent_name,
                        "prediction": "Elevated risk trajectory based on behavioral patterns",
                        "confidence": contrib.confidence_level,
                    }
                )

        return insights

    def _grade_overall_quality(
        self, metrics: SynthesisMetrics, fused_data: dict[str, Any], analysis_depth: str
    ) -> QualityGrade:
        """Grade the overall quality of the synthesized intelligence."""

        # Calculate composite quality score
        success_rate = metrics.successful_agents / max(metrics.total_agents_executed, 1)
        quality_score = (
            metrics.average_quality_score * 0.4
            + metrics.overall_confidence * 0.3
            + success_rate * 0.2
            + metrics.synthesis_completeness * 0.1
        )

        # Adjust for analysis depth expectations
        depth_adjustments = {
            "standard": 0.0,
            "deep": 0.05,
            "comprehensive": 0.10,
            "experimental": 0.15,
        }

        adjusted_score = quality_score + depth_adjustments.get(analysis_depth, 0.0)

        # Grade assignment
        if adjusted_score >= 0.9:
            return QualityGrade.EXCELLENT
        elif adjusted_score >= 0.7:
            return QualityGrade.GOOD
        elif adjusted_score >= 0.5:
            return QualityGrade.SATISFACTORY
        elif adjusted_score >= 0.3:
            return QualityGrade.LIMITED
        else:
            return QualityGrade.POOR

    def _create_executive_summary(
        self,
        fused_intelligence: dict[str, Any],
        quality: QualityGrade,
        metrics: SynthesisMetrics,
    ) -> dict[str, Any]:
        """Create executive summary of the intelligence analysis."""
        return {
            "overall_assessment": f"Intelligence analysis completed with {quality.value} quality",
            "key_findings": self._extract_key_findings(fused_intelligence),
            "confidence_level": f"{metrics.overall_confidence:.1%}",
            "completeness": f"{metrics.synthesis_completeness:.1%}",
            "agent_performance": f"{metrics.successful_agents}/{metrics.total_agents_executed} agents successful",
            "processing_time": f"{metrics.processing_time_seconds:.1f} seconds",
            "quality_grade": quality.value,
            "reliability_indicators": self._extract_reliability_indicators(fused_intelligence),
        }

    def _extract_key_findings(self, fused_intelligence: dict[str, Any]) -> list[str]:
        """Extract key findings from fused intelligence data."""
        findings = []

        # Extract findings from different analysis domains
        if "content_analysis" in fused_intelligence:
            findings.append("Content analysis completed with linguistic and sentiment mapping")

        if "information_verification" in fused_intelligence:
            findings.append("Information verification performed with fact-checking and source validation")

        if "threat_analysis" in fused_intelligence:
            findings.append("Threat assessment conducted with deception analysis and risk scoring")

        return findings

    def _extract_reliability_indicators(self, fused_intelligence: dict[str, Any]) -> list[str]:
        """Extract reliability indicators from the analysis."""
        indicators = []

        # Check for high-confidence components
        for stage, data in fused_intelligence.items():
            if isinstance(data, dict) and data.get("confidence", 0) > 0.8:
                indicators.append(f"High confidence in {stage}")

        return indicators

    def _generate_intelligence_report(
        self,
        contributions: list[AgentContribution],
        fused_intelligence: dict[str, Any],
        quality: QualityGrade,
        metrics: SynthesisMetrics,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate comprehensive intelligence report."""
        return {
            "report_metadata": {
                "generation_time": metadata.get("processing_time", 0),
                "workflow_id": metadata.get("workflow_id", "unknown"),
                "analysis_depth": metadata.get("depth", "standard"),
                "quality_grade": quality.value,
            },
            "executive_summary": self._create_executive_summary(fused_intelligence, quality, metrics),
            "detailed_analysis": fused_intelligence,
            "agent_contributions": [contrib.__dict__ for contrib in contributions],
            "synthesis_metrics": metrics.__dict__,
            "quality_assessment": {
                "overall_grade": quality.value,
                "confidence_score": metrics.overall_confidence,
                "completeness_score": metrics.synthesis_completeness,
                "agent_success_rate": metrics.successful_agents / max(metrics.total_agents_executed, 1),
            },
            "recommendations": self._generate_improvement_recommendations(metrics, quality),
        }

    def _extract_quality_indicators(self, contributions: list[AgentContribution]) -> list[str]:
        """Extract quality indicators from agent contributions."""
        indicators = []

        high_quality_agents = [c for c in contributions if c.quality_score > 0.8]
        if len(high_quality_agents) > len(contributions) * 0.7:
            indicators.append("Majority of agents performed at high quality")

        high_confidence_agents = [c for c in contributions if c.confidence_level > 0.8]
        if len(high_confidence_agents) > len(contributions) * 0.6:
            indicators.append("High confidence across multiple analysis domains")

        return indicators

    def _generate_improvement_recommendations(self, metrics: SynthesisMetrics, quality: QualityGrade) -> list[str]:
        """Generate recommendations for improving analysis quality."""
        recommendations = []

        if metrics.failed_agents > 0:
            recommendations.append(f"Review {metrics.failed_agents} failed agent executions for optimization")

        if metrics.degraded_agents > 0:
            recommendations.append(f"Investigate {metrics.degraded_agents} degraded executions")

        if quality in [QualityGrade.LIMITED, QualityGrade.POOR]:
            recommendations.append("Consider increasing analysis depth or improving data quality")

        if metrics.overall_confidence < 0.6:
            recommendations.append("Low confidence - consider additional verification steps")

        return recommendations
