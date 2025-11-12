"""Collective Intelligence System - Multi-agent knowledge synthesis

This service enables agents to work together to build collective intelligence,
synthesizing insights from multiple agents for enhanced decision-making.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant


logger = logging.getLogger(__name__)


class SynthesisType(Enum):
    """Types of collective intelligence synthesis"""

    CONSENSUS = "consensus"
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    EXPERT_CONSENSUS = "expert_consensus"
    HIERARCHICAL_SYNTHESIS = "hierarchical_synthesis"
    ADAPTIVE_SYNTHESIS = "adaptive_synthesis"


class IntelligenceLevel(Enum):
    """Levels of collective intelligence"""

    INDIVIDUAL = "individual"
    GROUP = "group"
    TEAM = "team"
    ORGANIZATIONAL = "organizational"
    COLLECTIVE = "collective"


@dataclass
class AgentContribution:
    """Contribution from an individual agent"""

    agent_id: str
    agent_type: str
    contribution_type: str
    data: dict[str, Any]
    confidence: float
    expertise_level: float
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectiveInsight:
    """Synthesized insight from multiple agents"""

    insight_id: str
    synthesis_type: SynthesisType
    intelligence_level: IntelligenceLevel
    contributing_agents: list[str]
    consensus_score: float
    confidence: float
    insight_data: dict[str, Any]
    validation_status: str
    created_at: datetime
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SynthesisRequest:
    """Request for collective intelligence synthesis"""

    requesting_agent_id: str
    synthesis_type: SynthesisType
    target_intelligence_level: IntelligenceLevel
    contributing_agents: list[str]
    query: str
    context: dict[str, Any]
    min_contributions: int = 3
    consensus_threshold: float = 0.7
    tenant_id: str | None = None
    workspace_id: str | None = None


@dataclass
class SynthesisResponse:
    """Response with synthesized collective intelligence"""

    collective_insight: CollectiveInsight
    individual_contributions: list[AgentContribution]
    synthesis_metrics: dict[str, Any]
    recommendations: list[str]
    confidence_breakdown: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectiveIntelligenceConfig:
    """Configuration for collective intelligence system"""

    enable_synthesis: bool = True
    enable_ethic_validation: bool = True
    enable_consensus_tracking: bool = True
    enable_expert_weighting: bool = True
    default_consensus_threshold: float = 0.7
    min_contributions_for_synthesis: int = 3
    max_contributions_per_synthesis: int = 20
    expertise_weight_factor: float = 0.3
    confidence_weight_factor: float = 0.4
    recency_weight_factor: float = 0.3
    synthesis_timeout: int = 30
    max_concurrent_syntheses: int = 10
    cache_synthesis_results: bool = True
    synthesis_cache_ttl: int = 600


class CollectiveIntelligenceService:
    """Collective intelligence synthesis and management service"""

    def __init__(self, config: CollectiveIntelligenceConfig | None = None):
        self.config = config or CollectiveIntelligenceConfig()
        self._initialized = False
        self._collective_insights: dict[str, CollectiveInsight] = {}
        self._agent_contributions: dict[str, list[AgentContribution]] = {}
        self._synthesis_cache: dict[str, Any] = {}
        self._consensus_tracker: dict[str, list[dict[str, Any]]] = {}
        self._expert_weights: dict[str, float] = {}
        self._initialize_service()

    def _initialize_service(self) -> None:
        """Initialize the collective intelligence service"""
        try:
            self._initialized = True
            logger.info("Collective Intelligence Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Collective Intelligence Service: {e}")
            self._initialized = False

    async def synthesize_collective_intelligence(
        self,
        requesting_agent_id: str,
        synthesis_type: SynthesisType,
        target_intelligence_level: IntelligenceLevel,
        contributing_agents: list[str],
        query: str,
        context: dict[str, Any],
        min_contributions: int = 3,
        consensus_threshold: float = 0.7,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Synthesize collective intelligence from multiple agents"""
        try:
            if not self._initialized:
                return StepResult.fail("Collective Intelligence Service not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            cache_key = self._generate_cache_key(
                synthesis_type, target_intelligence_level, contributing_agents, query, context
            )
            if self.config.cache_synthesis_results and cache_key in self._synthesis_cache:
                cached_result = self._synthesis_cache[cache_key]
                if datetime.now(timezone.utc) - cached_result["timestamp"] < timedelta(
                    seconds=self.config.synthesis_cache_ttl
                ):
                    logger.info(f"Returning cached synthesis result for {query}")
                    return StepResult.ok(data=cached_result["response"])
            contributions = await self._gather_agent_contributions(
                contributing_agents=contributing_agents,
                query=query,
                context=context,
                min_contributions=min_contributions,
            )
            if len(contributions) < min_contributions:
                return StepResult.fail(f"Insufficient contributions: {len(contributions)} < {min_contributions}")
            collective_insight = await self._perform_synthesis(
                contributions=contributions,
                synthesis_type=synthesis_type,
                target_intelligence_level=target_intelligence_level,
                consensus_threshold=consensus_threshold,
                query=query,
                context=context,
            )
            synthesis_metrics = await self._calculate_synthesis_metrics(
                contributions=contributions, collective_insight=collective_insight
            )
            recommendations = await self._generate_synthesis_recommendations(
                collective_insight=collective_insight, contributions=contributions, context=context
            )
            confidence_breakdown = self._calculate_confidence_breakdown(contributions)
            response = SynthesisResponse(
                collective_insight=collective_insight,
                individual_contributions=contributions,
                synthesis_metrics=synthesis_metrics,
                recommendations=recommendations,
                confidence_breakdown=confidence_breakdown,
                metadata={
                    "synthesis_type": synthesis_type.value,
                    "intelligence_level": target_intelligence_level.value,
                    "contributing_agents": contributing_agents,
                    "query": query,
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                },
            )
            self._collective_insights[collective_insight.insight_id] = collective_insight
            for contribution in contributions:
                if contribution.agent_id not in self._agent_contributions:
                    self._agent_contributions[contribution.agent_id] = []
                self._agent_contributions[contribution.agent_id].append(contribution)
            if self.config.cache_synthesis_results:
                self._synthesis_cache[cache_key] = {"response": response, "timestamp": datetime.now(timezone.utc)}
            logger.info(f"Collective intelligence synthesized: {collective_insight.insight_id}")
            return StepResult.ok(data=response)
        except Exception as e:
            logger.error(f"Error synthesizing collective intelligence: {e}", exc_info=True)
            return StepResult.fail(f"Collective intelligence synthesis failed: {e!s}")

    async def contribute_to_synthesis(
        self,
        agent_id: str,
        agent_type: str,
        contribution_type: str,
        data: dict[str, Any],
        confidence: float,
        expertise_level: float,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Contribute data to collective intelligence synthesis"""
        try:
            if not self._initialized:
                return StepResult.fail("Collective Intelligence Service not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            contribution = AgentContribution(
                agent_id=agent_id,
                agent_type=agent_type,
                contribution_type=contribution_type,
                data=data,
                confidence=confidence,
                expertise_level=expertise_level,
                timestamp=datetime.now(timezone.utc),
                metadata={"tenant_id": tenant_id, "workspace_id": workspace_id, **(metadata or {})},
            )
            if agent_id not in self._agent_contributions:
                self._agent_contributions[agent_id] = []
            self._agent_contributions[agent_id].append(contribution)
            if self.config.enable_expert_weighting:
                await self._update_expert_weights(agent_id, expertise_level, confidence)
            logger.info(f"Contribution received from {agent_id}: {contribution_type}")
            return StepResult.ok(
                data={
                    "contributed": True,
                    "agent_id": agent_id,
                    "contribution_type": contribution_type,
                    "confidence": confidence,
                    "expertise_level": expertise_level,
                }
            )
        except Exception as e:
            logger.error(f"Error contributing to synthesis: {e}", exc_info=True)
            return StepResult.fail(f"Contribution failed: {e!s}")

    async def validate_collective_insight(
        self,
        insight_id: str,
        validating_agent_id: str,
        validation_data: dict[str, Any],
        is_valid: bool,
        feedback: str | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Validate a collective insight"""
        try:
            if not self._initialized:
                return StepResult.fail("Collective Intelligence Service not initialized")
            if insight_id not in self._collective_insights:
                return StepResult.fail(f"Collective insight {insight_id} not found")
            insight = self._collective_insights[insight_id]
            validation_record = {
                "validating_agent": validating_agent_id,
                "validation_data": validation_data,
                "is_valid": is_valid,
                "feedback": feedback,
                "validated_at": datetime.now(timezone.utc).isoformat(),
                "tenant_id": tenant_id,
                "workspace_id": workspace_id,
            }
            if insight_id not in self._consensus_tracker:
                self._consensus_tracker[insight_id] = []
            self._consensus_tracker[insight_id].append(validation_record)
            validations = self._consensus_tracker[insight_id]
            valid_count = len([v for v in validations if v["is_valid"]])
            total_validations = len(validations)
            if total_validations >= 3:
                consensus_ratio = valid_count / total_validations
                if consensus_ratio >= 0.7:
                    insight.validation_status = "validated"
                elif consensus_ratio >= 0.4:
                    insight.validation_status = "disputed"
                else:
                    insight.validation_status = "rejected"
                insight.last_updated = datetime.now(timezone.utc)
                self._collective_insights[insight_id] = insight
            logger.info(f"Collective insight {insight_id} validated by {validating_agent_id}: {is_valid}")
            return StepResult.ok(
                data={
                    "validated": True,
                    "insight_id": insight_id,
                    "validation_status": insight.validation_status,
                    "consensus_ratio": valid_count / total_validations if total_validations > 0 else 0,
                    "total_validations": total_validations,
                }
            )
        except Exception as e:
            logger.error(f"Error validating collective insight: {e}", exc_info=True)
            return StepResult.fail(f"Collective insight validation failed: {e!s}")

    async def get_collective_intelligence_summary(
        self,
        days: int = 30,
        intelligence_level: IntelligenceLevel | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Get summary of collective intelligence activities"""
        try:
            if not self._initialized:
                return StepResult.fail("Collective Intelligence Service not initialized")
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            filtered_insights = []
            for insight in self._collective_insights.values():
                if insight.created_at < cutoff_date:
                    continue
                if intelligence_level and insight.intelligence_level != intelligence_level:
                    continue
                if tenant_id and insight.metadata.get("tenant_id") != tenant_id:
                    continue
                if workspace_id and insight.metadata.get("workspace_id") != workspace_id:
                    continue
                filtered_insights.append(insight)
            if not filtered_insights:
                return StepResult.ok(data={"summary": "No collective intelligence activities found"})
            total_insights = len(filtered_insights)
            synthesis_type_counts = {}
            for insight in filtered_insights:
                type_name = insight.synthesis_type.value
                synthesis_type_counts[type_name] = synthesis_type_counts.get(type_name, 0) + 1
            intelligence_level_counts = {}
            for insight in filtered_insights:
                level_name = insight.intelligence_level.value
                intelligence_level_counts[level_name] = intelligence_level_counts.get(level_name, 0) + 1
            avg_consensus_score = sum(insight.consensus_score for insight in filtered_insights) / total_insights
            avg_confidence = sum(insight.confidence for insight in filtered_insights) / total_insights
            validation_status_counts = {}
            for insight in filtered_insights:
                status = insight.validation_status
                validation_status_counts[status] = validation_status_counts.get(status, 0) + 1
            participating_agents = set()
            for insight in filtered_insights:
                participating_agents.update(insight.contributing_agents)
            return StepResult.ok(
                data={
                    "summary": {
                        "total_insights": total_insights,
                        "participating_agents": len(participating_agents),
                        "synthesis_types": synthesis_type_counts,
                        "intelligence_levels": intelligence_level_counts,
                        "validation_status": validation_status_counts,
                        "average_consensus_score": avg_consensus_score,
                        "average_confidence": avg_confidence,
                        "recent_activity": len(
                            [i for i in filtered_insights if (datetime.now(timezone.utc) - i.created_at).days < 7]
                        ),
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error getting collective intelligence summary: {e}", exc_info=True)
            return StepResult.fail(f"Summary retrieval failed: {e!s}")

    async def _gather_agent_contributions(
        self, contributing_agents: list[str], query: str, context: dict[str, Any], min_contributions: int
    ) -> list[AgentContribution]:
        """Gather contributions from specified agents"""
        try:
            contributions = []
            for agent_id in contributing_agents:
                if agent_id in self._agent_contributions:
                    recent_contributions = [
                        c
                        for c in self._agent_contributions[agent_id]
                        if (datetime.now(timezone.utc) - c.timestamp).seconds < 3600
                    ]
                    relevant_contributions = self._filter_relevant_contributions(recent_contributions, query, context)
                    contributions.extend(relevant_contributions)
            contributions.sort(key=lambda c: c.confidence * c.expertise_level, reverse=True)
            return contributions[: self.config.max_contributions_per_synthesis]
        except Exception as e:
            logger.error(f"Error gathering agent contributions: {e}")
            return []

    def _filter_relevant_contributions(
        self, contributions: list[AgentContribution], query: str, context: dict[str, Any]
    ) -> list[AgentContribution]:
        """Filter contributions relevant to the query"""
        try:
            relevant_contributions = []
            for contribution in contributions:
                relevance_score = self._calculate_contribution_relevance(contribution, query, context)
                if relevance_score >= 0.5:
                    relevant_contributions.append(contribution)
            return relevant_contributions
        except Exception as e:
            logger.error(f"Error filtering relevant contributions: {e}")
            return []

    def _calculate_contribution_relevance(
        self, contribution: AgentContribution, query: str, context: dict[str, Any]
    ) -> float:
        """Calculate relevance score for a contribution"""
        try:
            score = 0.0
            score += contribution.confidence * 0.3
            score += contribution.expertise_level * 0.2
            if query.lower() in contribution.contribution_type.lower():
                score += 0.3
            if contribution.data:
                context_similarity = self._context_similarity(context, contribution.data)
                score += context_similarity * 0.2
            return min(1.0, score)
        except Exception as e:
            logger.error(f"Error calculating contribution relevance: {e}")
            return 0.0

    async def _perform_synthesis(
        self,
        contributions: list[AgentContribution],
        synthesis_type: SynthesisType,
        target_intelligence_level: IntelligenceLevel,
        consensus_threshold: float,
        query: str,
        context: dict[str, Any],
    ) -> CollectiveInsight:
        """Perform the actual synthesis of contributions"""
        try:
            insight_id = f"collective:{synthesis_type.value}:{int(datetime.now().timestamp())}"
            if synthesis_type == SynthesisType.CONSENSUS:
                insight_data, consensus_score = await self._consensus_synthesis(contributions)
            elif synthesis_type == SynthesisType.MAJORITY_VOTE:
                insight_data, consensus_score = await self._majority_vote_synthesis(contributions)
            elif synthesis_type == SynthesisType.WEIGHTED_AVERAGE:
                insight_data, consensus_score = await self._weighted_average_synthesis(contributions)
            elif synthesis_type == SynthesisType.EXPERT_CONSENSUS:
                insight_data, consensus_score = await self._expert_consensus_synthesis(contributions)
            elif synthesis_type == SynthesisType.HIERARCHICAL_SYNTHESIS:
                insight_data, consensus_score = await self._hierarchical_synthesis(contributions)
            else:
                insight_data, consensus_score = await self._adaptive_synthesis(contributions)
            confidence = self._calculate_overall_confidence(contributions, consensus_score)
            collective_insight = CollectiveInsight(
                insight_id=insight_id,
                synthesis_type=synthesis_type,
                intelligence_level=target_intelligence_level,
                contributing_agents=[c.agent_id for c in contributions],
                consensus_score=consensus_score,
                confidence=confidence,
                insight_data=insight_data,
                validation_status="pending",
                created_at=datetime.now(timezone.utc),
                metadata={
                    "query": query,
                    "context_keys": list(context.keys()),
                    "contribution_count": len(contributions),
                },
            )
            return collective_insight
        except Exception as e:
            logger.error(f"Error performing synthesis: {e}")
            return CollectiveInsight(
                insight_id=f"error:{int(datetime.now().timestamp())}",
                synthesis_type=synthesis_type,
                intelligence_level=target_intelligence_level,
                contributing_agents=[],
                consensus_score=0.0,
                confidence=0.0,
                insight_data={"error": str(e)},
                validation_status="error",
                created_at=datetime.now(timezone.utc),
            )

    async def _consensus_synthesis(self, contributions: list[AgentContribution]) -> tuple[dict[str, Any], float]:
        """Perform consensus-based synthesis"""
        try:
            common_elements = {}
            total_contributions = len(contributions)
            for contribution in contributions:
                for key, value in contribution.data.items():
                    if key not in common_elements:
                        common_elements[key] = []
                    common_elements[key].append(value)
            consensus_data = {}
            consensus_scores = []
            for key, values in common_elements.items():
                if len(values) >= total_contributions * 0.6:
                    most_common = max(set(values), key=values.count)
                    agreement_ratio = values.count(most_common) / len(values)
                    consensus_data[key] = most_common
                    consensus_scores.append(agreement_ratio)
            overall_consensus = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
            return (consensus_data, overall_consensus)
        except Exception as e:
            logger.error(f"Error in consensus synthesis: {e}")
            return ({}, 0.0)

    async def _majority_vote_synthesis(self, contributions: list[AgentContribution]) -> tuple[dict[str, Any], float]:
        """Perform majority vote synthesis"""
        try:
            votes = {}
            for contribution in contributions:
                for key, value in contribution.data.items():
                    if key not in votes:
                        votes[key] = {}
                    vote_key = str(value)
                    votes[key][vote_key] = votes[key].get(vote_key, 0) + 1
            majority_data = {}
            consensus_scores = []
            for key, vote_counts in votes.items():
                total_votes = sum(vote_counts.values())
                majority_vote = max(vote_counts.items(), key=lambda x: x[1])
                majority_data[key] = majority_vote[0]
                consensus_scores.append(majority_vote[1] / total_votes)
            overall_consensus = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
            return (majority_data, overall_consensus)
        except Exception as e:
            logger.error(f"Error in majority vote synthesis: {e}")
            return ({}, 0.0)

    async def _weighted_average_synthesis(self, contributions: list[AgentContribution]) -> tuple[dict[str, Any], float]:
        """Perform weighted average synthesis"""
        try:
            weights = []
            for contribution in contributions:
                weight = (
                    contribution.confidence * self.config.confidence_weight_factor
                    + contribution.expertise_level * self.config.expertise_weight_factor
                )
                weights.append(weight)
            total_weight = sum(weights)
            if total_weight == 0:
                return ({}, 0.0)
            normalized_weights = [w / total_weight for w in weights]
            weighted_data = {}
            consensus_scores = []
            numeric_keys = set()
            for contribution in contributions:
                for key, value in contribution.data.items():
                    if isinstance(value, (int, float)):
                        numeric_keys.add(key)
            for key in numeric_keys:
                weighted_sum = 0.0
                for i, contribution in enumerate(contributions):
                    if key in contribution.data and isinstance(contribution.data[key], (int, float)):
                        weighted_sum += contribution.data[key] * normalized_weights[i]
                weighted_data[key] = weighted_sum
                consensus_scores.append(0.8)
            overall_consensus = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
            return (weighted_data, overall_consensus)
        except Exception as e:
            logger.error(f"Error in weighted average synthesis: {e}")
            return ({}, 0.0)

    async def _expert_consensus_synthesis(self, contributions: list[AgentContribution]) -> tuple[dict[str, Any], float]:
        """Perform expert consensus synthesis"""
        try:
            expert_contributions = []
            for contribution in contributions:
                if contribution.expertise_level >= 0.7:
                    expert_contributions.append(contribution)
            if not expert_contributions:
                return await self._consensus_synthesis(contributions)
            return await self._consensus_synthesis(expert_contributions)
        except Exception as e:
            logger.error(f"Error in expert consensus synthesis: {e}")
            return ({}, 0.0)

    async def _hierarchical_synthesis(self, contributions: list[AgentContribution]) -> tuple[dict[str, Any], float]:
        """Perform hierarchical synthesis"""
        try:
            hierarchy_groups = {}
            for contribution in contributions:
                agent_type = contribution.agent_type
                if agent_type not in hierarchy_groups:
                    hierarchy_groups[agent_type] = []
                hierarchy_groups[agent_type].append(contribution)
            hierarchy_levels = {
                "executive_supervisor": 5,
                "mission_orchestrator": 4,
                "workflow_manager": 3,
                "debate_analyst": 2,
                "fact_checker": 2,
                "content_ingestion": 1,
            }
            sorted_groups = sorted(hierarchy_groups.items(), key=lambda x: hierarchy_levels.get(x[0], 0), reverse=True)
            final_data = {}
            consensus_scores = []
            for _agent_type, group_contributions in sorted_groups:
                group_data, group_consensus = await self._consensus_synthesis(group_contributions)
                final_data.update(group_data)
                consensus_scores.append(group_consensus)
            overall_consensus = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
            return (final_data, overall_consensus)
        except Exception as e:
            logger.error(f"Error in hierarchical synthesis: {e}")
            return ({}, 0.0)

    async def _adaptive_synthesis(self, contributions: list[AgentContribution]) -> tuple[dict[str, Any], float]:
        """Perform adaptive synthesis based on context"""
        try:
            avg_confidence = sum(c.confidence for c in contributions) / len(contributions)
            avg_expertise = sum(c.expertise_level for c in contributions) / len(contributions)
            confidence_variance = sum((c.confidence - avg_confidence) ** 2 for c in contributions) / len(contributions)
            if confidence_variance < 0.1 and avg_confidence > 0.8:
                return await self._consensus_synthesis(contributions)
            elif avg_expertise > 0.7:
                return await self._expert_consensus_synthesis(contributions)
            elif len({c.agent_type for c in contributions}) > 3:
                return await self._hierarchical_synthesis(contributions)
            else:
                return await self._weighted_average_synthesis(contributions)
        except Exception as e:
            logger.error(f"Error in adaptive synthesis: {e}")
            return ({}, 0.0)

    def _calculate_overall_confidence(self, contributions: list[AgentContribution], consensus_score: float) -> float:
        """Calculate overall confidence for the synthesis"""
        try:
            weighted_confidence = 0.0
            total_weight = 0.0
            for contribution in contributions:
                weight = contribution.confidence * contribution.expertise_level
                weighted_confidence += contribution.confidence * weight
                total_weight += weight
            avg_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.0
            overall_confidence = avg_confidence * 0.6 + consensus_score * 0.4
            return min(1.0, overall_confidence)
        except Exception as e:
            logger.error(f"Error calculating overall confidence: {e}")
            return 0.0

    async def _calculate_synthesis_metrics(
        self, contributions: list[AgentContribution], collective_insight: CollectiveInsight
    ) -> dict[str, Any]:
        """Calculate metrics for the synthesis process"""
        try:
            return {
                "contribution_count": len(contributions),
                "agent_diversity": len({c.agent_type for c in contributions}),
                "average_confidence": sum(c.confidence for c in contributions) / len(contributions),
                "average_expertise": sum(c.expertise_level for c in contributions) / len(contributions),
                "consensus_score": collective_insight.consensus_score,
                "synthesis_confidence": collective_insight.confidence,
                "synthesis_type": collective_insight.synthesis_type.value,
                "intelligence_level": collective_insight.intelligence_level.value,
            }
        except Exception as e:
            logger.error(f"Error calculating synthesis metrics: {e}")
            return {}

    async def _generate_synthesis_recommendations(
        self, collective_insight: CollectiveInsight, contributions: list[AgentContribution], context: dict[str, Any]
    ) -> list[str]:
        """Generate recommendations based on synthesis results"""
        try:
            recommendations = []
            if collective_insight.consensus_score >= 0.8:
                recommendations.append("High consensus achieved - recommendations are highly reliable")
            elif collective_insight.consensus_score >= 0.6:
                recommendations.append("Moderate consensus - recommendations are generally reliable")
            else:
                recommendations.append("Low consensus - recommendations should be used with caution")
            if collective_insight.confidence >= 0.8:
                recommendations.append("High confidence synthesis - strong recommendation to proceed")
            elif collective_insight.confidence >= 0.6:
                recommendations.append("Moderate confidence synthesis - proceed with monitoring")
            else:
                recommendations.append("Low confidence synthesis - consider additional input")
            agent_types = {c.agent_type for c in contributions}
            if len(agent_types) >= 4:
                recommendations.append("High agent diversity - comprehensive perspective achieved")
            elif len(agent_types) >= 2:
                recommendations.append("Moderate agent diversity - good perspective coverage")
            else:
                recommendations.append("Limited agent diversity - consider additional perspectives")
            return recommendations
        except Exception as e:
            logger.error(f"Error generating synthesis recommendations: {e}")
            return []

    def _calculate_confidence_breakdown(self, contributions: list[AgentContribution]) -> dict[str, float]:
        """Calculate confidence breakdown by agent type"""
        try:
            breakdown = {}
            for contribution in contributions:
                agent_type = contribution.agent_type
                if agent_type not in breakdown:
                    breakdown[agent_type] = []
                breakdown[agent_type].append(contribution.confidence)
            for agent_type, confidences in breakdown.items():
                breakdown[agent_type] = sum(confidences) / len(confidences)
            return breakdown
        except Exception as e:
            logger.error(f"Error calculating confidence breakdown: {e}")
            return {}

    async def _update_expert_weights(self, agent_id: str, expertise_level: float, confidence: float) -> None:
        """Update expert weights for agent"""
        try:
            new_weight = expertise_level * 0.6 + confidence * 0.4
            if agent_id in self._expert_weights:
                current_weight = self._expert_weights[agent_id]
                self._expert_weights[agent_id] = current_weight + self.config.learning_rate * (
                    new_weight - current_weight
                )
            else:
                self._expert_weights[agent_id] = new_weight
        except Exception as e:
            logger.error(f"Error updating expert weights: {e}")

    def _generate_cache_key(
        self,
        synthesis_type: SynthesisType,
        intelligence_level: IntelligenceLevel,
        contributing_agents: list[str],
        query: str,
        context: dict[str, Any],
    ) -> str:
        """Generate cache key for synthesis request"""
        try:
            key_components = [
                synthesis_type.value,
                intelligence_level.value,
                sorted(contributing_agents),
                query,
                sorted(context.items()),
            ]
            import hashlib

            key_string = str(key_components)
            return hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()
        except Exception as e:
            logger.error(f"Error generating cache key: {e}")
            return f"error:{int(datetime.now().timestamp())}"

    def _context_similarity(self, context1: dict[str, Any], context2: dict[str, Any]) -> float:
        """Calculate context similarity"""
        try:
            if not context1 or not context2:
                return 0.0
            common_keys = set(context1.keys()).intersection(set(context2.keys()))
            if not common_keys:
                return 0.0
            matches = 0
            for key in common_keys:
                if context1[key] == context2[key]:
                    matches += 1
            return matches / len(common_keys)
        except Exception:
            return 0.0

    def get_collective_intelligence_status(self) -> dict[str, Any]:
        """Get collective intelligence service status"""
        return {
            "initialized": self._initialized,
            "total_insights": len(self._collective_insights),
            "total_contributions": sum(len(contributions) for contributions in self._agent_contributions.values()),
            "total_agents": len(self._agent_contributions),
            "total_validations": sum(len(validations) for validations in self._consensus_tracker.values()),
            "cache_entries": len(self._synthesis_cache),
            "expert_weights": len(self._expert_weights),
            "config": {
                "enable_synthesis": self.config.enable_synthesis,
                "enable_consensus_tracking": self.config.enable_consensus_tracking,
                "enable_expert_weighting": self.config.enable_expert_weighting,
                "default_consensus_threshold": self.config.default_consensus_threshold,
            },
        }
