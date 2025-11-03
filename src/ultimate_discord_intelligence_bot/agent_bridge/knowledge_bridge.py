"""Agent Knowledge Bridge - Intelligent cross-agent knowledge sharing

This service enables agents to share insights, learn from each other's experiences,
and build upon collective knowledge for enhanced performance and decision-making.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from platform.core.step_result import StepResult
from typing import Any

from ultimate_discord_intelligence_bot.tenancy.context import current_tenant


logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Types of insights that can be shared"""

    SUCCESS_PATTERN = "success_pattern"
    FAILURE_ANALYSIS = "failure_analysis"
    OPTIMIZATION_TIP = "optimization_tip"
    BEST_PRACTICE = "best_practice"
    WARNING = "warning"
    DISCOVERY = "discovery"


class InsightPriority(Enum):
    """Priority levels for insights"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentInsight:
    """Insight shared by an agent"""

    insight_id: str
    agent_id: str
    agent_type: str
    insight_type: InsightType
    priority: InsightPriority
    title: str
    description: str
    context: dict[str, Any]
    tags: list[str]
    confidence_score: float
    validation_count: int = 0
    success_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InsightRequest:
    """Request for insights from other agents"""

    requesting_agent_id: str
    agent_type: str
    query: str
    context: dict[str, Any]
    insight_types: list[InsightType]
    max_results: int = 10
    min_confidence: float = 0.5
    tags: list[str] | None = None
    tenant_id: str | None = None
    workspace_id: str | None = None


@dataclass
class InsightResponse:
    """Response containing relevant insights"""

    insights: list[AgentInsight]
    total_found: int
    query_time_ms: float
    confidence_threshold: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeBridgeConfig:
    """Configuration for agent knowledge bridge"""

    enable_insight_sharing: bool = True
    enable_cross_agent_learning: bool = True
    enable_insight_validation: bool = True
    enable_automatic_sharing: bool = True
    max_insights_per_agent: int = 1000
    insight_retention_days: int = 30
    validation_threshold: int = 3
    learning_rate: float = 0.1
    confidence_threshold: float = 0.7
    similarity_threshold: float = 0.8
    max_concurrent_requests: int = 10
    cache_ttl: int = 300


class AgentKnowledgeBridge:
    """Intelligent agent knowledge sharing and learning system"""

    def __init__(self, config: KnowledgeBridgeConfig | None = None):
        self.config = config or KnowledgeBridgeConfig()
        self._initialized = False
        self._insights: dict[str, AgentInsight] = {}
        self._agent_insights: dict[str, set[str]] = {}
        self._insight_index: dict[str, set[str]] = {}
        self._validation_history: dict[str, list[dict[str, Any]]] = {}
        self._learning_cache: dict[str, Any] = {}
        self._initialize_bridge()

    def _initialize_bridge(self) -> None:
        """Initialize the knowledge bridge"""
        try:
            self._initialized = True
            logger.info("Agent Knowledge Bridge initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Agent Knowledge Bridge: {e}")
            self._initialized = False

    async def share_insight(
        self,
        agent_id: str,
        agent_type: str,
        insight_type: InsightType,
        title: str,
        description: str,
        context: dict[str, Any],
        tags: list[str],
        confidence_score: float,
        priority: InsightPriority = InsightPriority.NORMAL,
        expires_at: datetime | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Share an insight with other agents"""
        try:
            if not self._initialized:
                return StepResult.fail("Agent Knowledge Bridge not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            insight_id = f"{agent_id}:{int(datetime.now().timestamp() * 1000)}"
            insight = AgentInsight(
                insight_id=insight_id,
                agent_id=agent_id,
                agent_type=agent_type,
                insight_type=insight_type,
                priority=priority,
                title=title,
                description=description,
                context=context,
                tags=tags,
                confidence_score=confidence_score,
                expires_at=expires_at,
                metadata={
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "shared_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            self._insights[insight_id] = insight
            if agent_id not in self._agent_insights:
                self._agent_insights[agent_id] = set()
            self._agent_insights[agent_id].add(insight_id)
            for tag in tags:
                if tag not in self._insight_index:
                    self._insight_index[tag] = set()
                self._insight_index[tag].add(insight_id)
            await self._cleanup_expired_insights()
            logger.info(f"Insight shared by {agent_id}: {title}")
            return StepResult.ok(
                data={
                    "insight_id": insight_id,
                    "shared": True,
                    "tags_indexed": len(tags),
                    "confidence": confidence_score,
                }
            )
        except Exception as e:
            logger.error(f"Error sharing insight: {e}", exc_info=True)
            return StepResult.fail(f"Insight sharing failed: {e!s}")

    async def request_insights(
        self,
        requesting_agent_id: str,
        agent_type: str,
        query: str,
        context: dict[str, Any],
        insight_types: list[InsightType],
        max_results: int = 10,
        min_confidence: float = 0.5,
        tags: list[str] | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Request relevant insights from other agents"""
        try:
            if not self._initialized:
                return StepResult.fail("Agent Knowledge Bridge not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            start_time = datetime.now(timezone.utc)
            relevant_insights = await self._search_insights(
                query=query,
                context=context,
                insight_types=insight_types,
                min_confidence=min_confidence,
                tags=tags,
                requesting_agent_id=requesting_agent_id,
                max_results=max_results,
            )
            query_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            response = InsightResponse(
                insights=relevant_insights,
                total_found=len(relevant_insights),
                query_time_ms=query_time,
                confidence_threshold=min_confidence,
                metadata={
                    "query": query,
                    "requesting_agent": requesting_agent_id,
                    "agent_type": agent_type,
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                },
            )
            logger.info(f"Insights requested by {requesting_agent_id}: {len(relevant_insights)} found")
            return StepResult.ok(data=response)
        except Exception as e:
            logger.error(f"Error requesting insights: {e}", exc_info=True)
            return StepResult.fail(f"Insight request failed: {e!s}")

    async def validate_insight(
        self,
        insight_id: str,
        validating_agent_id: str,
        is_successful: bool,
        feedback: str | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Validate an insight based on experience"""
        try:
            if not self._initialized:
                return StepResult.fail("Agent Knowledge Bridge not initialized")
            if insight_id not in self._insights:
                return StepResult.fail(f"Insight {insight_id} not found")
            insight = self._insights[insight_id]
            validation_record = {
                "validating_agent": validating_agent_id,
                "is_successful": is_successful,
                "feedback": feedback,
                "validated_at": datetime.now(timezone.utc).isoformat(),
                "tenant_id": tenant_id,
                "workspace_id": workspace_id,
            }
            if insight_id not in self._validation_history:
                self._validation_history[insight_id] = []
            self._validation_history[insight_id].append(validation_record)
            insight.validation_count += 1
            if is_successful:
                insight.success_count += 1
            success_rate = insight.success_count / insight.validation_count
            insight.confidence_score = (insight.confidence_score + success_rate) / 2
            self._insights[insight_id] = insight
            logger.info(f"Insight {insight_id} validated by {validating_agent_id}: {is_successful}")
            return StepResult.ok(
                data={
                    "validated": True,
                    "insight_id": insight_id,
                    "validation_count": insight.validation_count,
                    "success_rate": success_rate,
                    "updated_confidence": insight.confidence_score,
                }
            )
        except Exception as e:
            logger.error(f"Error validating insight: {e}", exc_info=True)
            return StepResult.fail(f"Insight validation failed: {e!s}")

    async def get_agent_insights(
        self,
        agent_id: str,
        limit: int = 50,
        insight_types: list[InsightType] | None = None,
        min_confidence: float = 0.0,
    ) -> StepResult:
        """Get insights shared by a specific agent"""
        try:
            if not self._initialized:
                return StepResult.fail("Agent Knowledge Bridge not initialized")
            if agent_id not in self._agent_insights:
                return StepResult.ok(data={"insights": [], "total": 0})
            insight_ids = list(self._agent_insights[agent_id])
            insights = []
            for insight_id in insight_ids:
                if insight_id in self._insights:
                    insight = self._insights[insight_id]
                    if insight_types and insight.insight_type not in insight_types:
                        continue
                    if insight.confidence_score < min_confidence:
                        continue
                    insights.append(insight)
            insights.sort(key=lambda x: x.created_at, reverse=True)
            insights = insights[:limit]
            return StepResult.ok(data={"insights": insights, "total": len(insights), "agent_id": agent_id})
        except Exception as e:
            logger.error(f"Error getting agent insights: {e}", exc_info=True)
            return StepResult.fail(f"Agent insights retrieval failed: {e!s}")

    async def get_insight_statistics(
        self, tenant_id: str | None = None, workspace_id: str | None = None
    ) -> dict[str, Any]:
        """Get statistics about shared insights"""
        try:
            filtered_insights = []
            for insight in self._insights.values():
                if tenant_id and insight.metadata.get("tenant_id") != tenant_id:
                    continue
                if workspace_id and insight.metadata.get("workspace_id") != workspace_id:
                    continue
                filtered_insights.append(insight)
            if not filtered_insights:
                return {"total_insights": 0, "statistics": {}}
            total_insights = len(filtered_insights)
            type_counts = {}
            for insight in filtered_insights:
                type_name = insight.insight_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
            agent_type_counts = {}
            for insight in filtered_insights:
                agent_type = insight.agent_type
                agent_type_counts[agent_type] = agent_type_counts.get(agent_type, 0) + 1
            avg_confidence = sum(insight.confidence_score for insight in filtered_insights) / total_insights
            total_validations = sum(insight.validation_count for insight in filtered_insights)
            total_successes = sum(insight.success_count for insight in filtered_insights)
            return {
                "total_insights": total_insights,
                "total_validations": total_validations,
                "total_successes": total_successes,
                "success_rate": total_successes / max(total_validations, 1),
                "average_confidence": avg_confidence,
                "insight_types": type_counts,
                "agent_types": agent_type_counts,
                "top_tags": self._get_top_tags(filtered_insights),
                "recent_insights": len(
                    [i for i in filtered_insights if (datetime.now(timezone.utc) - i.created_at).days < 7]
                ),
            }
        except Exception as e:
            logger.error(f"Error getting insight statistics: {e}")
            return {"error": str(e)}

    async def _search_insights(
        self,
        query: str,
        context: dict[str, Any],
        insight_types: list[InsightType],
        min_confidence: float,
        tags: list[str] | None,
        requesting_agent_id: str,
        max_results: int,
    ) -> list[AgentInsight]:
        """Search for relevant insights"""
        try:
            candidate_insights = []
            for insight in self._insights.values():
                if insight.insight_type not in insight_types:
                    continue
                if insight.confidence_score < min_confidence:
                    continue
                if insight.agent_id == requesting_agent_id:
                    continue
                candidate_insights.append(insight)
            if tags:
                tag_filtered = []
                for insight in candidate_insights:
                    if any(tag in insight.tags for tag in tags):
                        tag_filtered.append(insight)
                candidate_insights = tag_filtered
            scored_insights = []
            for insight in candidate_insights:
                score = self._calculate_relevance_score(insight, query, context)
                scored_insights.append((score, insight))
            scored_insights.sort(key=lambda x: x[0], reverse=True)
            return [insight for score, insight in scored_insights[:max_results]]
        except Exception as e:
            logger.error(f"Error searching insights: {e}")
            return []

    def _calculate_relevance_score(self, insight: AgentInsight, query: str, context: dict[str, Any]) -> float:
        """Calculate relevance score for an insight"""
        try:
            score = 0.0
            score += insight.confidence_score * 0.3
            if self._text_similarity(query.lower(), insight.title.lower()) > 0.5:
                score += 0.3
            if self._text_similarity(query.lower(), insight.description.lower()) > 0.5:
                score += 0.2
            context_score = self._context_similarity(context, insight.context)
            score += context_score * 0.2
            if insight.validation_count > 0:
                success_rate = insight.success_count / insight.validation_count
                score += success_rate * 0.1
            priority_bonus = {
                InsightPriority.LOW: 0.0,
                InsightPriority.NORMAL: 0.05,
                InsightPriority.HIGH: 0.1,
                InsightPriority.CRITICAL: 0.15,
            }
            score += priority_bonus.get(insight.priority, 0.0)
            return min(1.0, score)
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.0

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        try:
            words1 = set(text1.split())
            words2 = set(text2.split())
            if not words1 or not words2:
                return 0.0
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union)
        except Exception:
            return 0.0

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

    def _get_top_tags(self, insights: list[AgentInsight], limit: int = 10) -> list[tuple]:
        """Get most common tags from insights"""
        try:
            tag_counts = {}
            for insight in insights:
                for tag in insight.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        except Exception:
            return []

    async def _cleanup_expired_insights(self) -> None:
        """Clean up expired insights"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_insights = []
            for insight_id, insight in self._insights.items():
                if insight.expires_at and insight.expires_at < current_time:
                    expired_insights.append(insight_id)
            for insight_id in expired_insights:
                insight = self._insights.pop(insight_id)
                if insight.agent_id in self._agent_insights:
                    self._agent_insights[insight.agent_id].discard(insight_id)
                for tag in insight.tags:
                    if tag in self._insight_index:
                        self._insight_index[tag].discard(insight_id)
            if expired_insights:
                logger.info(f"Cleaned up {len(expired_insights)} expired insights")
        except Exception as e:
            logger.error(f"Error cleaning up expired insights: {e}")

    def get_bridge_status(self) -> dict[str, Any]:
        """Get knowledge bridge status"""
        return {
            "initialized": self._initialized,
            "total_insights": len(self._insights),
            "total_agents": len(self._agent_insights),
            "total_tags": len(self._insight_index),
            "total_validations": sum(len(validations) for validations in self._validation_history.values()),
            "config": {
                "enable_insight_sharing": self.config.enable_insight_sharing,
                "enable_cross_agent_learning": self.config.enable_cross_agent_learning,
                "enable_insight_validation": self.config.enable_insight_validation,
                "max_insights_per_agent": self.config.max_insights_per_agent,
            },
        }
