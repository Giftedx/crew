"""Agent Bridge - Unified interface for cross-agent knowledge sharing

This service provides a unified interface for all agent knowledge sharing,
learning, and collective intelligence capabilities.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ultimate_discord_intelligence_bot.step_result import StepResult

from .collective_intelligence import (
    CollectiveIntelligenceConfig,
    CollectiveIntelligenceService,
    IntelligenceLevel,
    SynthesisResponse,
    SynthesisType,
)
from .cross_agent_learning import (
    CrossAgentLearningConfig,
    CrossAgentLearningService,
    LearningType,
)
from .knowledge_bridge import (
    AgentKnowledgeBridge,
    InsightPriority,
    InsightType,
    KnowledgeBridgeConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentBridgeConfig:
    """Configuration for the unified agent bridge"""

    # Knowledge bridge settings
    enable_knowledge_sharing: bool = True
    enable_insight_validation: bool = True
    enable_cross_agent_learning: bool = True

    # Learning settings
    enable_pattern_extraction: bool = True
    enable_adaptive_learning: bool = True
    enable_collaborative_learning: bool = True

    # Collective intelligence settings
    enable_synthesis: bool = True
    enable_consensus_tracking: bool = True
    enable_expert_weighting: bool = True

    # Performance settings
    max_concurrent_operations: int = 20
    operation_timeout: int = 60  # seconds
    enable_caching: bool = True
    cache_ttl: int = 900  # 15 minutes

    # Integration settings
    auto_share_insights: bool = True
    auto_extract_patterns: bool = True
    auto_synthesize_intelligence: bool = True


class AgentBridge:
    """Unified interface for cross-agent knowledge sharing and learning"""

    def __init__(self, config: Optional[AgentBridgeConfig] = None):
        self.config = config or AgentBridgeConfig()
        self._initialized = False

        # Initialize sub-services
        self._knowledge_bridge = None
        self._learning_service = None
        self._collective_intelligence = None

        # Initialize bridge
        self._initialize_bridge()

    def _initialize_bridge(self) -> None:
        """Initialize the unified agent bridge"""
        try:
            # Initialize knowledge bridge
            if self.config.enable_knowledge_sharing:
                knowledge_config = KnowledgeBridgeConfig(
                    enable_insight_sharing=self.config.enable_knowledge_sharing,
                    enable_cross_agent_learning=self.config.enable_cross_agent_learning,
                    enable_insight_validation=self.config.enable_insight_validation,
                    enable_automatic_sharing=self.config.auto_share_insights,
                )
                self._knowledge_bridge = AgentKnowledgeBridge(knowledge_config)

            # Initialize learning service
            if self.config.enable_cross_agent_learning:
                learning_config = CrossAgentLearningConfig(
                    enable_learning=self.config.enable_cross_agent_learning,
                    enable_pattern_extraction=self.config.enable_pattern_extraction,
                    enable_adaptive_learning=self.config.enable_adaptive_learning,
                    enable_collaborative_learning=self.config.enable_collaborative_learning,
                )
                self._learning_service = CrossAgentLearningService(learning_config)

            # Initialize collective intelligence
            if self.config.enable_synthesis:
                collective_config = CollectiveIntelligenceConfig(
                    enable_synthesis=self.config.enable_synthesis,
                    enable_consensus_tracking=self.config.enable_consensus_tracking,
                    enable_expert_weighting=self.config.enable_expert_weighting,
                )
                self._collective_intelligence = CollectiveIntelligenceService(
                    collective_config
                )

            self._initialized = True
            logger.info("Agent Bridge initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Agent Bridge: {e}")
            self._initialized = False

    async def share_insight(
        self,
        agent_id: str,
        agent_type: str,
        insight_type: InsightType,
        title: str,
        description: str,
        context: Dict[str, Any],
        tags: List[str],
        confidence_score: float,
        priority: InsightPriority = InsightPriority.NORMAL,
        expires_at: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Share an insight with other agents"""
        try:
            if not self._initialized or not self._knowledge_bridge:
                return StepResult.fail(
                    "Agent Bridge not initialized or knowledge sharing disabled"
                )

            return await self._knowledge_bridge.share_insight(
                agent_id=agent_id,
                agent_type=agent_type,
                insight_type=insight_type,
                title=title,
                description=description,
                context=context,
                tags=tags,
                confidence_score=confidence_score,
                priority=priority,
                expires_at=expires_at,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )

        except Exception as e:
            logger.error(f"Error sharing insight through agent bridge: {e}")
            return StepResult.fail(f"Insight sharing failed: {str(e)}")

    async def request_insights(
        self,
        requesting_agent_id: str,
        agent_type: str,
        query: str,
        context: Dict[str, Any],
        insight_types: List[InsightType],
        max_results: int = 10,
        min_confidence: float = 0.5,
        tags: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Request relevant insights from other agents"""
        try:
            if not self._initialized or not self._knowledge_bridge:
                return StepResult.fail(
                    "Agent Bridge not initialized or knowledge sharing disabled"
                )

            return await self._knowledge_bridge.request_insights(
                requesting_agent_id=requesting_agent_id,
                agent_type=agent_type,
                query=query,
                context=context,
                insight_types=insight_types,
                max_results=max_results,
                min_confidence=min_confidence,
                tags=tags,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )

        except Exception as e:
            logger.error(f"Error requesting insights through agent bridge: {e}")
            return StepResult.fail(f"Insight request failed: {str(e)}")

    async def learn_from_experience(
        self,
        agent_id: str,
        agent_type: str,
        experience_type: LearningType,
        context: Dict[str, Any],
        outcome: Dict[str, Any],
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Learn from an agent's experience"""
        try:
            if not self._initialized or not self._learning_service:
                return StepResult.fail(
                    "Agent Bridge not initialized or learning disabled"
                )

            result = await self._learning_service.learn_from_experience(
                agent_id=agent_id,
                agent_type=agent_type,
                experience_type=experience_type,
                context=context,
                outcome=outcome,
                success=success,
                metadata=metadata,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )

            # Auto-extract patterns if enabled
            if result.success and self.config.auto_extract_patterns:
                await self._learning_service._extract_patterns(agent_id, agent_type)

            return result

        except Exception as e:
            logger.error(f"Error learning from experience through agent bridge: {e}")
            return StepResult.fail(f"Experience learning failed: {str(e)}")

    async def get_learning_patterns(
        self,
        requesting_agent_id: str,
        agent_type: str,
        context: Dict[str, Any],
        learning_types: List[LearningType],
        min_confidence: float = 0.6,
        max_patterns: int = 20,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Get relevant learning patterns for an agent"""
        try:
            if not self._initialized or not self._learning_service:
                return StepResult.fail(
                    "Agent Bridge not initialized or learning disabled"
                )

            return await self._learning_service.get_learning_patterns(
                requesting_agent_id=requesting_agent_id,
                agent_type=agent_type,
                context=context,
                learning_types=learning_types,
                min_confidence=min_confidence,
                max_patterns=max_patterns,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )

        except Exception as e:
            logger.error(f"Error getting learning patterns through agent bridge: {e}")
            return StepResult.fail(f"Learning pattern retrieval failed: {str(e)}")

    async def synthesize_collective_intelligence(
        self,
        requesting_agent_id: str,
        synthesis_type: SynthesisType,
        target_intelligence_level: IntelligenceLevel,
        contributing_agents: List[str],
        query: str,
        context: Dict[str, Any],
        min_contributions: int = 3,
        consensus_threshold: float = 0.7,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Synthesize collective intelligence from multiple agents"""
        try:
            if not self._initialized or not self._collective_intelligence:
                return StepResult.fail(
                    "Agent Bridge not initialized or synthesis disabled"
                )

            result = (
                await self._collective_intelligence.synthesize_collective_intelligence(
                    requesting_agent_id=requesting_agent_id,
                    synthesis_type=synthesis_type,
                    target_intelligence_level=target_intelligence_level,
                    contributing_agents=contributing_agents,
                    query=query,
                    context=context,
                    min_contributions=min_contributions,
                    consensus_threshold=consensus_threshold,
                    tenant_id=tenant_id,
                    workspace_id=workspace_id,
                )
            )

            # Auto-share insights if enabled and synthesis was successful
            if result.success and self.config.auto_share_insights:
                await self._auto_share_synthesis_insights(
                    result.data, requesting_agent_id
                )

            return result

        except Exception as e:
            logger.error(
                f"Error synthesizing collective intelligence through agent bridge: {e}"
            )
            return StepResult.fail(
                f"Collective intelligence synthesis failed: {str(e)}"
            )

    async def contribute_to_synthesis(
        self,
        agent_id: str,
        agent_type: str,
        contribution_type: str,
        data: Dict[str, Any],
        confidence: float,
        expertise_level: float,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Contribute data to collective intelligence synthesis"""
        try:
            if not self._initialized or not self._collective_intelligence:
                return StepResult.fail(
                    "Agent Bridge not initialized or synthesis disabled"
                )

            return await self._collective_intelligence.contribute_to_synthesis(
                agent_id=agent_id,
                agent_type=agent_type,
                contribution_type=contribution_type,
                data=data,
                confidence=confidence,
                expertise_level=expertise_level,
                metadata=metadata,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )

        except Exception as e:
            logger.error(f"Error contributing to synthesis through agent bridge: {e}")
            return StepResult.fail(f"Contribution failed: {str(e)}")

    async def validate_insight(
        self,
        insight_id: str,
        validating_agent_id: str,
        is_successful: bool,
        feedback: Optional[str] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Validate an insight based on experience"""
        try:
            if not self._initialized:
                return StepResult.fail("Agent Bridge not initialized")

            # Try knowledge bridge first
            if self._knowledge_bridge:
                result = await self._knowledge_bridge.validate_insight(
                    insight_id=insight_id,
                    validating_agent_id=validating_agent_id,
                    is_successful=is_successful,
                    feedback=feedback,
                    tenant_id=tenant_id,
                    workspace_id=workspace_id,
                )
                if result.success:
                    return result

            # Try collective intelligence if knowledge bridge fails
            if self._collective_intelligence:
                return await self._collective_intelligence.validate_collective_insight(
                    insight_id=insight_id,
                    validating_agent_id=validating_agent_id,
                    validation_data={"feedback": feedback} if feedback else {},
                    is_valid=is_successful,
                    feedback=feedback,
                    tenant_id=tenant_id,
                    workspace_id=workspace_id,
                )

            return StepResult.fail("No validation service available")

        except Exception as e:
            logger.error(f"Error validating insight through agent bridge: {e}")
            return StepResult.fail(f"Insight validation failed: {str(e)}")

    async def get_agent_knowledge_summary(
        self,
        agent_id: str,
        days: int = 30,
        include_insights: bool = True,
        include_learning: bool = True,
        include_synthesis: bool = True,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Get comprehensive knowledge summary for an agent"""
        try:
            if not self._initialized:
                return StepResult.fail("Agent Bridge not initialized")

            summary = {
                "agent_id": agent_id,
                "summary_period_days": days,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Get insights summary
            if include_insights and self._knowledge_bridge:
                insights_result = await self._knowledge_bridge.get_agent_insights(
                    agent_id=agent_id, limit=100
                )
                if insights_result.success:
                    summary["insights"] = insights_result.data

            # Get learning summary
            if include_learning and self._learning_service:
                learning_result = (
                    await self._learning_service.get_agent_learning_summary(
                        agent_id=agent_id, days=days
                    )
                )
                if learning_result.success:
                    summary["learning"] = learning_result.data

            # Get synthesis participation
            if include_synthesis and self._collective_intelligence:
                # This would require implementing a method to get agent's synthesis participation
                summary["synthesis_participation"] = "Feature not yet implemented"

            return StepResult.ok(data=summary)

        except Exception as e:
            logger.error(f"Error getting agent knowledge summary: {e}")
            return StepResult.fail(f"Knowledge summary retrieval failed: {str(e)}")

    async def get_bridge_statistics(
        self, tenant_id: Optional[str] = None, workspace_id: Optional[str] = None
    ) -> StepResult:
        """Get comprehensive statistics from all bridge services"""
        try:
            if not self._initialized:
                return StepResult.fail("Agent Bridge not initialized")

            statistics = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "bridge_status": "initialized",
            }

            # Get knowledge bridge statistics
            if self._knowledge_bridge:
                statistics["knowledge_bridge"] = (
                    self._knowledge_bridge.get_bridge_status()
                )

            # Get learning service statistics
            if self._learning_service:
                statistics["learning_service"] = (
                    self._learning_service.get_learning_status()
                )

            # Get collective intelligence statistics
            if self._collective_intelligence:
                statistics["collective_intelligence"] = (
                    self._collective_intelligence.get_collective_intelligence_status()
                )

            # Get overall bridge statistics
            statistics["overall"] = {
                "services_initialized": sum(
                    [
                        self._knowledge_bridge is not None,
                        self._learning_service is not None,
                        self._collective_intelligence is not None,
                    ]
                ),
                "total_services": 3,
                "config": {
                    "enable_knowledge_sharing": self.config.enable_knowledge_sharing,
                    "enable_cross_agent_learning": self.config.enable_cross_agent_learning,
                    "enable_synthesis": self.config.enable_synthesis,
                    "auto_share_insights": self.config.auto_share_insights,
                    "auto_extract_patterns": self.config.auto_extract_patterns,
                    "auto_synthesize_intelligence": self.config.auto_synthesize_intelligence,
                },
            }

            return StepResult.ok(data=statistics)

        except Exception as e:
            logger.error(f"Error getting bridge statistics: {e}")
            return StepResult.fail(f"Statistics retrieval failed: {str(e)}")

    async def _auto_share_synthesis_insights(
        self, synthesis_response: SynthesisResponse, requesting_agent_id: str
    ) -> None:
        """Automatically share insights from synthesis results"""
        try:
            if not self._knowledge_bridge or not self.config.auto_share_insights:
                return

            collective_insight = synthesis_response.collective_insight

            # Share the collective insight
            await self._knowledge_bridge.share_insight(
                agent_id=requesting_agent_id,
                agent_type="collective_intelligence",
                insight_type=InsightType.DISCOVERY,
                title=f"Collective Intelligence: {collective_insight.insight_id}",
                description=f"Synthesized insight from {len(collective_insight.contributing_agents)} agents using {collective_insight.synthesis_type.value}",
                context=collective_insight.insight_data,
                tags=[
                    "collective_intelligence",
                    "synthesis",
                    collective_insight.synthesis_type.value,
                ],
                confidence_score=collective_insight.confidence,
                priority=InsightPriority.HIGH
                if collective_insight.consensus_score >= 0.8
                else InsightPriority.NORMAL,
                metadata={
                    "synthesis_type": collective_insight.synthesis_type.value,
                    "intelligence_level": collective_insight.intelligence_level.value,
                    "contributing_agents": collective_insight.contributing_agents,
                    "consensus_score": collective_insight.consensus_score,
                },
            )

            logger.info(
                f"Auto-shared synthesis insight: {collective_insight.insight_id}"
            )

        except Exception as e:
            logger.error(f"Error auto-sharing synthesis insights: {e}")

    def get_bridge_status(self) -> Dict[str, Any]:
        """Get agent bridge status"""
        return {
            "initialized": self._initialized,
            "knowledge_bridge_available": self._knowledge_bridge is not None,
            "learning_service_available": self._learning_service is not None,
            "collective_intelligence_available": self._collective_intelligence
            is not None,
            "config": {
                "enable_knowledge_sharing": self.config.enable_knowledge_sharing,
                "enable_cross_agent_learning": self.config.enable_cross_agent_learning,
                "enable_synthesis": self.config.enable_synthesis,
                "auto_share_insights": self.config.auto_share_insights,
                "auto_extract_patterns": self.config.auto_extract_patterns,
                "auto_synthesize_intelligence": self.config.auto_synthesize_intelligence,
            },
        }
