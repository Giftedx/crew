"""Agent Bridge Tools - CrewAI tools for cross-agent knowledge sharing

This module provides CrewAI-compatible tools for agents to interact with
the agent bridge system for knowledge sharing, learning, and collective intelligence.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from crewai.tools import BaseTool
from pydantic import Field

from ultimate_discord_intelligence_bot.agent_bridge import (
    AgentBridge,
    AgentBridgeConfig,
    InsightPriority,
    InsightType,
    IntelligenceLevel,
    LearningType,
    SynthesisType,
)
from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


class AgentBridgeTool(BaseTool):
    """Tool for agents to interact with the agent bridge system"""

    name: str = "agent_bridge_tool"
    description: str = (
        "Share insights, learn from experiences, and collaborate with other agents. "
        "Enables cross-agent knowledge sharing and collective intelligence."
    )

    # Configuration
    bridge_config: Optional[AgentBridgeConfig] = Field(
        default=None, description="Agent bridge configuration"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize agent bridge
        self._agent_bridge = AgentBridge(self.bridge_config)

    def _run(
        self,
        operation: str,
        agent_id: str,
        agent_type: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> str:
        """Execute agent bridge operations"""
        try:
            if operation == "share_insight":
                return self._share_insight(agent_id, agent_type, data, **kwargs)
            elif operation == "request_insights":
                return self._request_insights(agent_id, agent_type, data, **kwargs)
            elif operation == "learn_from_experience":
                return self._learn_from_experience(agent_id, agent_type, data, **kwargs)
            elif operation == "get_learning_patterns":
                return self._get_learning_patterns(agent_id, agent_type, data, **kwargs)
            elif operation == "synthesize_intelligence":
                return self._synthesize_intelligence(
                    agent_id, agent_type, data, **kwargs
                )
            elif operation == "contribute_to_synthesis":
                return self._contribute_to_synthesis(
                    agent_id, agent_type, data, **kwargs
                )
            elif operation == "validate_insight":
                return self._validate_insight(agent_id, agent_type, data, **kwargs)
            elif operation == "get_knowledge_summary":
                return self._get_knowledge_summary(agent_id, agent_type, data, **kwargs)
            elif operation == "get_bridge_statistics":
                return self._get_bridge_statistics(agent_id, agent_type, data, **kwargs)
            else:
                return StepResult.fail(f"Unknown operation: {operation}").to_string()

        except Exception as e:
            logger.error(f"Error in agent bridge tool: {e}")
            return StepResult.fail(
                f"Agent bridge operation failed: {str(e)}"
            ).to_string()

    def _share_insight(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Share an insight with other agents"""
        try:
            # Extract parameters
            insight_type = InsightType(data.get("insight_type", "discovery"))
            title = data.get("title", "")
            description = data.get("description", "")
            context = data.get("context", {})
            tags = data.get("tags", [])
            confidence_score = float(data.get("confidence_score", 0.5))
            priority = InsightPriority(data.get("priority", "normal"))

            # Share insight
            import asyncio

            result = asyncio.run(
                self._agent_bridge.share_insight(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    insight_type=insight_type,
                    title=title,
                    description=description,
                    context=context,
                    tags=tags,
                    confidence_score=confidence_score,
                    priority=priority,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error sharing insight: {e}")
            return StepResult.fail(f"Insight sharing failed: {str(e)}").to_string()

    def _request_insights(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Request relevant insights from other agents"""
        try:
            # Extract parameters
            query = data.get("query", "")
            context = data.get("context", {})
            insight_types = [
                InsightType(t) for t in data.get("insight_types", ["discovery"])
            ]
            max_results = int(data.get("max_results", 10))
            min_confidence = float(data.get("min_confidence", 0.5))
            tags = data.get("tags")

            # Request insights
            import asyncio

            result = asyncio.run(
                self._agent_bridge.request_insights(
                    requesting_agent_id=agent_id,
                    agent_type=agent_type,
                    query=query,
                    context=context,
                    insight_types=insight_types,
                    max_results=max_results,
                    min_confidence=min_confidence,
                    tags=tags,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error requesting insights: {e}")
            return StepResult.fail(f"Insight request failed: {str(e)}").to_string()

    def _learn_from_experience(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Learn from an agent's experience"""
        try:
            # Extract parameters
            experience_type = LearningType(
                data.get("experience_type", "success_pattern")
            )
            context = data.get("context", {})
            outcome = data.get("outcome", {})
            success = bool(data.get("success", True))
            metadata = data.get("metadata")

            # Learn from experience
            import asyncio

            result = asyncio.run(
                self._agent_bridge.learn_from_experience(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    experience_type=experience_type,
                    context=context,
                    outcome=outcome,
                    success=success,
                    metadata=metadata,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error learning from experience: {e}")
            return StepResult.fail(f"Experience learning failed: {str(e)}").to_string()

    def _get_learning_patterns(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Get relevant learning patterns for an agent"""
        try:
            # Extract parameters
            context = data.get("context", {})
            learning_types = [
                LearningType(t) for t in data.get("learning_types", ["success_pattern"])
            ]
            min_confidence = float(data.get("min_confidence", 0.6))
            max_patterns = int(data.get("max_patterns", 20))

            # Get learning patterns
            import asyncio

            result = asyncio.run(
                self._agent_bridge.get_learning_patterns(
                    requesting_agent_id=agent_id,
                    agent_type=agent_type,
                    context=context,
                    learning_types=learning_types,
                    min_confidence=min_confidence,
                    max_patterns=max_patterns,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error getting learning patterns: {e}")
            return StepResult.fail(
                f"Learning pattern retrieval failed: {str(e)}"
            ).to_string()

    def _synthesize_intelligence(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Synthesize collective intelligence from multiple agents"""
        try:
            # Extract parameters
            synthesis_type = SynthesisType(data.get("synthesis_type", "consensus"))
            target_intelligence_level = IntelligenceLevel(
                data.get("intelligence_level", "team")
            )
            contributing_agents = data.get("contributing_agents", [])
            query = data.get("query", "")
            context = data.get("context", {})
            min_contributions = int(data.get("min_contributions", 3))
            consensus_threshold = float(data.get("consensus_threshold", 0.7))

            # Synthesize intelligence
            import asyncio

            result = asyncio.run(
                self._agent_bridge.synthesize_collective_intelligence(
                    requesting_agent_id=agent_id,
                    synthesis_type=synthesis_type,
                    target_intelligence_level=target_intelligence_level,
                    contributing_agents=contributing_agents,
                    query=query,
                    context=context,
                    min_contributions=min_contributions,
                    consensus_threshold=consensus_threshold,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error synthesizing intelligence: {e}")
            return StepResult.fail(
                f"Intelligence synthesis failed: {str(e)}"
            ).to_string()

    def _contribute_to_synthesis(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Contribute data to collective intelligence synthesis"""
        try:
            # Extract parameters
            contribution_type = data.get("contribution_type", "")
            contribution_data = data.get("data", {})
            confidence = float(data.get("confidence", 0.5))
            expertise_level = float(data.get("expertise_level", 0.5))
            metadata = data.get("metadata")

            # Contribute to synthesis
            import asyncio

            result = asyncio.run(
                self._agent_bridge.contribute_to_synthesis(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    contribution_type=contribution_type,
                    data=contribution_data,
                    confidence=confidence,
                    expertise_level=expertise_level,
                    metadata=metadata,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error contributing to synthesis: {e}")
            return StepResult.fail(f"Contribution failed: {str(e)}").to_string()

    def _validate_insight(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Validate an insight based on experience"""
        try:
            # Extract parameters
            insight_id = data.get("insight_id", "")
            is_successful = bool(data.get("is_successful", True))
            feedback = data.get("feedback")

            # Validate insight
            import asyncio

            result = asyncio.run(
                self._agent_bridge.validate_insight(
                    insight_id=insight_id,
                    validating_agent_id=agent_id,
                    is_successful=is_successful,
                    feedback=feedback,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error validating insight: {e}")
            return StepResult.fail(f"Insight validation failed: {str(e)}").to_string()

    def _get_knowledge_summary(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Get comprehensive knowledge summary for an agent"""
        try:
            # Extract parameters
            days = int(data.get("days", 30))
            include_insights = bool(data.get("include_insights", True))
            include_learning = bool(data.get("include_learning", True))
            include_synthesis = bool(data.get("include_synthesis", True))

            # Get knowledge summary
            import asyncio

            result = asyncio.run(
                self._agent_bridge.get_agent_knowledge_summary(
                    agent_id=agent_id,
                    days=days,
                    include_insights=include_insights,
                    include_learning=include_learning,
                    include_synthesis=include_synthesis,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error getting knowledge summary: {e}")
            return StepResult.fail(
                f"Knowledge summary retrieval failed: {str(e)}"
            ).to_string()

    def _get_bridge_statistics(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Get comprehensive statistics from all bridge services"""
        try:
            # Get bridge statistics
            import asyncio

            result = asyncio.run(self._agent_bridge.get_bridge_statistics())
            return result.to_string()

        except Exception as e:
            logger.error(f"Error getting bridge statistics: {e}")
            return StepResult.fail(f"Statistics retrieval failed: {str(e)}").to_string()


class InsightSharingTool(BaseTool):
    """Specialized tool for sharing insights with other agents"""

    name: str = "insight_sharing_tool"
    description: str = (
        "Share insights, discoveries, and best practices with other agents. "
        "Enables knowledge transfer and collaborative learning."
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._agent_bridge = AgentBridge()

    def _run(
        self,
        agent_id: str,
        agent_type: str,
        insight_type: str,
        title: str,
        description: str,
        context: str,
        tags: str,
        confidence_score: float = 0.5,
        priority: str = "normal",
    ) -> str:
        """Share an insight with other agents"""
        try:
            # Parse context and tags
            import json

            try:
                context_dict = json.loads(context) if context else {}
            except json.JSONDecodeError:
                context_dict = {"raw_context": context}

            try:
                tags_list = json.loads(tags) if tags else []
            except json.JSONDecodeError:
                tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

            # Share insight
            import asyncio

            result = asyncio.run(
                self._agent_bridge.share_insight(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    insight_type=InsightType(insight_type),
                    title=title,
                    description=description,
                    context=context_dict,
                    tags=tags_list,
                    confidence_score=confidence_score,
                    priority=InsightPriority(priority),
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error sharing insight: {e}")
            return StepResult.fail(f"Insight sharing failed: {str(e)}").to_string()


class LearningTool(BaseTool):
    """Specialized tool for learning from experiences and patterns"""

    name: str = "learning_tool"
    description: str = (
        "Learn from experiences and access learning patterns from other agents. "
        "Enables adaptive learning and knowledge transfer."
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._agent_bridge = AgentBridge()

    def _run(self, operation: str, agent_id: str, agent_type: str, **kwargs) -> str:
        """Execute learning operations"""
        try:
            if operation == "learn_from_experience":
                return self._learn_from_experience(agent_id, agent_type, **kwargs)
            elif operation == "get_learning_patterns":
                return self._get_learning_patterns(agent_id, agent_type, **kwargs)
            else:
                return StepResult.fail(
                    f"Unknown learning operation: {operation}"
                ).to_string()

        except Exception as e:
            logger.error(f"Error in learning tool: {e}")
            return StepResult.fail(f"Learning operation failed: {str(e)}").to_string()

    def _learn_from_experience(
        self,
        agent_id: str,
        agent_type: str,
        experience_type: str,
        context: str,
        outcome: str,
        success: bool,
        metadata: str = "",
    ) -> str:
        """Learn from an agent's experience"""
        try:
            # Parse context, outcome, and metadata
            import json

            try:
                context_dict = json.loads(context) if context else {}
            except json.JSONDecodeError:
                context_dict = {"raw_context": context}

            try:
                outcome_dict = json.loads(outcome) if outcome else {}
            except json.JSONDecodeError:
                outcome_dict = {"raw_outcome": outcome}

            try:
                metadata_dict = json.loads(metadata) if metadata else {}
            except json.JSONDecodeError:
                metadata_dict = {"raw_metadata": metadata}

            # Learn from experience
            import asyncio

            result = asyncio.run(
                self._agent_bridge.learn_from_experience(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    experience_type=LearningType(experience_type),
                    context=context_dict,
                    outcome=outcome_dict,
                    success=success,
                    metadata=metadata_dict,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error learning from experience: {e}")
            return StepResult.fail(f"Experience learning failed: {str(e)}").to_string()

    def _get_learning_patterns(
        self,
        agent_id: str,
        agent_type: str,
        context: str,
        learning_types: str,
        min_confidence: float = 0.6,
        max_patterns: int = 20,
    ) -> str:
        """Get relevant learning patterns for an agent"""
        try:
            # Parse context and learning types
            import json

            try:
                context_dict = json.loads(context) if context else {}
            except json.JSONDecodeError:
                context_dict = {"raw_context": context}

            try:
                learning_types_list = (
                    json.loads(learning_types) if learning_types else []
                )
            except json.JSONDecodeError:
                learning_types_list = [
                    lt.strip() for lt in learning_types.split(",") if lt.strip()
                ]

            # Convert to LearningType enums
            learning_type_enums = [LearningType(lt) for lt in learning_types_list]

            # Get learning patterns
            import asyncio

            result = asyncio.run(
                self._agent_bridge.get_learning_patterns(
                    requesting_agent_id=agent_id,
                    agent_type=agent_type,
                    context=context_dict,
                    learning_types=learning_type_enums,
                    min_confidence=min_confidence,
                    max_patterns=max_patterns,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error getting learning patterns: {e}")
            return StepResult.fail(
                f"Learning pattern retrieval failed: {str(e)}"
            ).to_string()


class CollectiveIntelligenceTool(BaseTool):
    """Specialized tool for collective intelligence synthesis"""

    name: str = "collective_intelligence_tool"
    description: str = (
        "Synthesize collective intelligence from multiple agents. "
        "Enables collaborative decision-making and knowledge synthesis."
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._agent_bridge = AgentBridge()

    def _run(self, operation: str, agent_id: str, agent_type: str, **kwargs) -> str:
        """Execute collective intelligence operations"""
        try:
            if operation == "synthesize":
                return self._synthesize_intelligence(agent_id, agent_type, **kwargs)
            elif operation == "contribute":
                return self._contribute_to_synthesis(agent_id, agent_type, **kwargs)
            else:
                return StepResult.fail(
                    f"Unknown collective intelligence operation: {operation}"
                ).to_string()

        except Exception as e:
            logger.error(f"Error in collective intelligence tool: {e}")
            return StepResult.fail(
                f"Collective intelligence operation failed: {str(e)}"
            ).to_string()

    def _synthesize_intelligence(
        self,
        agent_id: str,
        agent_type: str,
        synthesis_type: str,
        intelligence_level: str,
        contributing_agents: str,
        query: str,
        context: str,
        min_contributions: int = 3,
        consensus_threshold: float = 0.7,
    ) -> str:
        """Synthesize collective intelligence from multiple agents"""
        try:
            # Parse contributing agents and context
            import json

            try:
                contributing_agents_list = (
                    json.loads(contributing_agents) if contributing_agents else []
                )
            except json.JSONDecodeError:
                contributing_agents_list = [
                    agent.strip()
                    for agent in contributing_agents.split(",")
                    if agent.strip()
                ]

            try:
                context_dict = json.loads(context) if context else {}
            except json.JSONDecodeError:
                context_dict = {"raw_context": context}

            # Synthesize intelligence
            import asyncio

            result = asyncio.run(
                self._agent_bridge.synthesize_collective_intelligence(
                    requesting_agent_id=agent_id,
                    synthesis_type=SynthesisType(synthesis_type),
                    target_intelligence_level=IntelligenceLevel(intelligence_level),
                    contributing_agents=contributing_agents_list,
                    query=query,
                    context=context_dict,
                    min_contributions=min_contributions,
                    consensus_threshold=consensus_threshold,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error synthesizing intelligence: {e}")
            return StepResult.fail(
                f"Intelligence synthesis failed: {str(e)}"
            ).to_string()

    def _contribute_to_synthesis(
        self,
        agent_id: str,
        agent_type: str,
        contribution_type: str,
        data: str,
        confidence: float,
        expertise_level: float,
        metadata: str = "",
    ) -> str:
        """Contribute data to collective intelligence synthesis"""
        try:
            # Parse data and metadata
            import json

            try:
                data_dict = json.loads(data) if data else {}
            except json.JSONDecodeError:
                data_dict = {"raw_data": data}

            try:
                metadata_dict = json.loads(metadata) if metadata else {}
            except json.JSONDecodeError:
                metadata_dict = {"raw_metadata": metadata}

            # Contribute to synthesis
            import asyncio

            result = asyncio.run(
                self._agent_bridge.contribute_to_synthesis(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    contribution_type=contribution_type,
                    data=data_dict,
                    confidence=confidence,
                    expertise_level=expertise_level,
                    metadata=metadata_dict,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error contributing to synthesis: {e}")
            return StepResult.fail(f"Contribution failed: {str(e)}").to_string()
