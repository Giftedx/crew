"""Hierarchical Reasoning Engine with 4 layers for Discord message processing.

This module implements a 4-layer reasoning architecture:
1. Pre-processing Layer: Token interpretation, filtering, normalization
2. Context Analysis Layer: Memory retrieval, context building, relevance scoring
3. Decision Making Layer: Response decision, priority determination, agent routing
4. Response Generation Layer: Content generation, formatting, validation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.step_result import StepResult

from .adaptive_decision_tree import AdaptiveDecisionTree
from .token_interpreter import ContextualTokenInterpreter


if TYPE_CHECKING:
    from platform.llm.providers.openrouter.adaptive_routing import AdaptiveRoutingManager
    from platform.prompts.engine import PromptEngine

    from domains.memory import MemoryService
    from ultimate_discord_intelligence_bot.knowledge.context_builder import UnifiedContextBuilder
    from ultimate_discord_intelligence_bot.knowledge.retrieval_engine import UnifiedRetrievalEngine

    from .token_interpreter import InterpretedTokens
logger = logging.getLogger(__name__)


@dataclass
class ReasoningContext:
    """Context for reasoning process."""

    message_data: dict[str, Any]
    interpreted_tokens: InterpretedTokens | None = None
    retrieved_context: list[dict[str, Any]] = field(default_factory=list)
    unified_context: Any | None = None
    reasoning_trace: list[dict[str, Any]] = field(default_factory=list)
    confidence_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class ReasoningResult:
    """Result of hierarchical reasoning process."""

    should_respond: bool
    confidence: float
    reasoning_steps: list[dict[str, Any]]
    recommended_action: str
    priority: int
    context_summary: str
    requires_crewmai: bool = False
    suggested_agents: list[str] = field(default_factory=list)


class HierarchicalReasoningEngine:
    """4-layer hierarchical reasoning engine for Discord message processing."""

    def __init__(
        self,
        routing_manager: AdaptiveRoutingManager,
        prompt_engine: PromptEngine,
        memory_service: MemoryService,
        retrieval_engine: UnifiedRetrievalEngine | None = None,
        context_builder: UnifiedContextBuilder | None = None,
    ):
        """Initialize hierarchical reasoning engine with dependencies."""
        self.routing_manager = routing_manager
        self.prompt_engine = prompt_engine
        self.memory_service = memory_service
        self.retrieval_engine = retrieval_engine
        self.context_builder = context_builder
        self.token_interpreter = ContextualTokenInterpreter()
        self.decision_tree = AdaptiveDecisionTree(routing_manager, prompt_engine)

    async def reason(
        self, message_data: dict[str, Any], recent_messages: list[dict[str, Any]], user_opt_in_status: bool
    ) -> StepResult[ReasoningResult]:
        """Execute complete hierarchical reasoning process.

        Args:
            message_data: Discord message data
            recent_messages: Recent conversation history
            user_opt_in_status: Whether user has opted in to AI interactions

        Returns:
            StepResult with ReasoningResult containing decision and reasoning trace
        """
        try:
            reasoning_ctx = ReasoningContext(message_data=message_data)
            preprocess_result = await self._preprocess_layer(message_data, reasoning_ctx)
            if not preprocess_result.success:
                return StepResult.fail(f"Pre-processing failed: {preprocess_result.error}")
            if reasoning_ctx.interpreted_tokens and reasoning_ctx.interpreted_tokens.action.action_type == "ignore":
                return StepResult.ok(
                    data=ReasoningResult(
                        should_respond=False,
                        confidence=1.0,
                        reasoning_steps=reasoning_ctx.reasoning_trace,
                        recommended_action="ignore",
                        priority=0,
                        context_summary="Message marked for ignoring",
                    )
                )
            context_result = await self._context_analysis_layer(
                message_data, recent_messages, reasoning_ctx, user_opt_in_status
            )
            if not context_result.success:
                logger.warning(f"Context analysis failed: {context_result.error}, continuing with limited context")
            if reasoning_ctx.interpreted_tokens:
                decision_tree_result = await self.decision_tree.evaluate(
                    interpreted_tokens=reasoning_ctx.interpreted_tokens,
                    message_metadata={
                        "mentions": message_data.get("mentions", []),
                        "user_opt_in_status": user_opt_in_status,
                    },
                )
                if decision_tree_result.success:
                    tree_path = decision_tree_result.data
                    decision = {
                        "should_respond": tree_path.final_decision.get("action") != "skip_response",
                        "confidence": tree_path.confidence,
                        "reasoning": tree_path.reasoning,
                        "used_llm": tree_path.used_llm,
                    }
                    reasoning_ctx.reasoning_trace.append(
                        {
                            "layer": "decision_making",
                            "method": "adaptive_decision_tree",
                            "path": tree_path.nodes_visited,
                            "decision": decision,
                        }
                    )
                else:
                    decision_result = await self._decision_making_layer(message_data, reasoning_ctx, user_opt_in_status)
                    if not decision_result.success:
                        return StepResult.fail(f"Decision making failed: {decision_result.error}")
                    decision = decision_result.data
            else:
                decision_result = await self._decision_making_layer(message_data, reasoning_ctx, user_opt_in_status)
                if not decision_result.success:
                    return StepResult.fail(f"Decision making failed: {decision_result.error}")
                decision = decision_result.data
            planning_result = await self._response_generation_layer_planning(reasoning_ctx, decision)
            if not planning_result.success:
                logger.warning(f"Response planning reported issue: {planning_result.error}")
            reasoning_result = ReasoningResult(
                should_respond=decision.get("should_respond", False),
                confidence=decision.get("confidence", 0.0),
                reasoning_steps=reasoning_ctx.reasoning_trace,
                recommended_action=reasoning_ctx.interpreted_tokens.action.action_type
                if reasoning_ctx.interpreted_tokens
                else "respond",
                priority=reasoning_ctx.interpreted_tokens.action.priority if reasoning_ctx.interpreted_tokens else 0,
                context_summary=self._build_context_summary(reasoning_ctx),
                requires_crewmai=reasoning_ctx.interpreted_tokens.action.requires_crewmai
                if reasoning_ctx.interpreted_tokens
                else False,
                suggested_agents=reasoning_ctx.interpreted_tokens.action.suggested_agents
                if reasoning_ctx.interpreted_tokens
                else [],
            )
            return StepResult.ok(data=reasoning_result)
        except Exception as e:
            logger.error(f"Hierarchical reasoning failed: {e}", exc_info=True)
            return StepResult.fail(f"Reasoning process failed: {e!s}")

    async def _preprocess_layer(self, message_data: dict[str, Any], ctx: ReasoningContext) -> StepResult:
        """Layer 1: Pre-processing - token interpretation and normalization."""
        try:
            content = message_data.get("content", "")
            interpreted = self.token_interpreter.interpret(content, message_data)
            ctx.interpreted_tokens = interpreted
            ctx.reasoning_trace.append(
                {
                    "layer": "preprocessing",
                    "action": "token_interpretation",
                    "intent": interpreted.intent.primary_intent,
                    "confidence": interpreted.confidence_score,
                }
            )
            ctx.confidence_scores["interpretation"] = interpreted.confidence_score
            return StepResult.ok(data={"interpreted": True})
        except Exception as e:
            logger.error(f"Pre-processing layer failed: {e}")
            return StepResult.fail(f"Pre-processing failed: {e!s}")

    async def _context_analysis_layer(
        self,
        message_data: dict[str, Any],
        recent_messages: list[dict[str, Any]],
        ctx: ReasoningContext,
        user_opt_in_status: bool,
    ) -> StepResult:
        """Layer 2: Context Analysis - memory retrieval and context building."""
        try:
            content = message_data.get("content", "")
            guild_id = str(message_data.get("guild_id", ""))
            if not ctx.interpreted_tokens:
                return StepResult.fail("No interpreted tokens available for context analysis")
            if self.retrieval_engine:
                from ultimate_discord_intelligence_bot.knowledge.retrieval_engine import RetrievalQuery

                query = RetrievalQuery(
                    text=content, intent=ctx.interpreted_tokens.intent.primary_intent, limit=10, min_confidence=0.5
                )
                retrieval_result = await self.retrieval_engine.retrieve(
                    query=query, unified_memory_service=self.memory_service, tenant_id=guild_id, workspace_id="discord"
                )
                if retrieval_result.success:
                    results = retrieval_result.data.get("results", [])
                    ctx.retrieved_context = [
                        {
                            "content": r.content if hasattr(r, "content") else str(r),
                            "confidence": getattr(r, "confidence", 0.5),
                            "source": getattr(r, "source", "memory"),
                        }
                        for r in results
                    ]
            else:
                search_result = await self.memory_service.search_memories(
                    query=content, tenant=guild_id, workspace="discord_interactions", limit=10
                )
                if search_result.success:
                    memories = search_result.data.get("memories", [])
                    ctx.retrieved_context = [
                        {
                            "content": mem.get("content", ""),
                            "confidence": mem.get("confidence", 0.5),
                            "source": "memory",
                        }
                        for mem in memories
                    ]
            if self.context_builder:
                from ultimate_discord_intelligence_bot.knowledge.context_builder import ContextRequest

                context_request = ContextRequest(
                    agent_id="discord_bot",
                    task_type="conversation",
                    query=content,
                    current_context={"recent_messages": recent_messages, "user_opt_in": user_opt_in_status},
                    max_context_length=4000,
                )
                build_result = await self.context_builder.build_context(
                    request=context_request,
                    unified_memory_service=self.memory_service,
                    retrieval_engine=self.retrieval_engine,
                    tenant_id=guild_id,
                    workspace_id="discord",
                )
                if build_result.success:
                    ctx.unified_context = build_result.data
            ctx.reasoning_trace.append(
                {
                    "layer": "context_analysis",
                    "action": "memory_retrieval",
                    "contexts_retrieved": len(ctx.retrieved_context),
                    "has_unified_context": ctx.unified_context is not None,
                }
            )
            relevance_score = self._calculate_context_relevance(ctx)
            ctx.confidence_scores["context_relevance"] = relevance_score
            return StepResult.ok(data={"context_retrieved": True, "relevance_score": relevance_score})
        except Exception as e:
            logger.error(f"Context analysis layer failed: {e}")
            return StepResult.fail(f"Context analysis failed: {e!s}")

    async def _decision_making_layer(
        self, message_data: dict[str, Any], ctx: ReasoningContext, user_opt_in_status: bool
    ) -> StepResult[dict[str, Any]]:
        """Layer 3: Decision Making - determine if/when/how to respond."""
        try:
            if not ctx.interpreted_tokens:
                return StepResult.fail("No interpreted tokens for decision making")
            tokens = ctx.interpreted_tokens
            if tokens.action.action_type == "ignore":
                return StepResult.ok(
                    data={"should_respond": False, "confidence": 1.0, "reasoning": "Message marked for ignoring"}
                )
            if (
                not user_opt_in_status
                and tokens.context.urgency != "critical"
                and not message_data.get("mentions")
                and tokens.action.priority < 7
            ):
                return StepResult.ok(
                    data={
                        "should_respond": False,
                        "confidence": 0.8,
                        "reasoning": "User not opted in and message not high priority",
                    }
                )
            should_respond = True
            confidence = tokens.confidence_score
            if tokens.context.urgency in ["critical", "high"]:
                should_respond = True
                confidence = min(1.0, confidence + 0.2)
            if tokens.intent.primary_intent in ["question", "command", "request"]:
                should_respond = True
                confidence = min(1.0, confidence + 0.1)
            elif tokens.intent.primary_intent == "greeting":
                should_respond = True
                confidence = 0.9
            elif tokens.intent.primary_intent == "statement" and tokens.action.priority < 3:
                should_respond = False
                confidence = 0.6
            ctx.reasoning_trace.append(
                {
                    "layer": "decision_making",
                    "action": "response_decision",
                    "should_respond": should_respond,
                    "confidence": confidence,
                    "factors": {
                        "intent": tokens.intent.primary_intent,
                        "urgency": tokens.context.urgency,
                        "priority": tokens.action.priority,
                        "opt_in": user_opt_in_status,
                    },
                }
            )
            ctx.confidence_scores["decision"] = confidence
            return StepResult.ok(
                data={
                    "should_respond": should_respond,
                    "confidence": confidence,
                    "reasoning": f"Intent: {tokens.intent.primary_intent}, Urgency: {tokens.context.urgency}, Priority: {tokens.action.priority}",
                }
            )
        except Exception as e:
            logger.error(f"Decision making layer failed: {e}")
            return StepResult.fail(f"Decision making failed: {e!s}")

    async def _response_generation_layer_planning(self, ctx: ReasoningContext, decision: dict[str, Any]) -> StepResult:
        """Layer 4: Response Generation planning (actual generation happens in pipeline)."""
        try:
            if not ctx.interpreted_tokens:
                return StepResult.fail("No interpreted tokens for response planning")
            tokens = ctx.interpreted_tokens
            strategy = "direct"
            if tokens.action.requires_crewmai:
                strategy = "crewai_delegation"
            elif tokens.action.requires_knowledge:
                strategy = "knowledge_enhanced"
            elif len(ctx.retrieved_context) > 0:
                strategy = "context_enhanced"
            ctx.reasoning_trace.append(
                {
                    "layer": "response_generation_planning",
                    "action": "strategy_selection",
                    "strategy": strategy,
                    "requires_crewmai": tokens.action.requires_crewmai,
                    "requires_knowledge": tokens.action.requires_knowledge,
                }
            )
            return StepResult.ok(data={"strategy": strategy})
        except Exception as e:
            logger.error(f"Response generation planning failed: {e}")
            return StepResult.fail(f"Response planning failed: {e!s}")

    def _calculate_context_relevance(self, ctx: ReasoningContext) -> float:
        """Calculate how relevant the retrieved context is."""
        if not ctx.retrieved_context:
            return 0.0
        confidences = [c.get("confidence", 0.0) for c in ctx.retrieved_context]
        if confidences:
            return sum(confidences) / len(confidences)
        return 0.0

    def _build_context_summary(self, ctx: ReasoningContext) -> str:
        """Build a summary of the reasoning context."""
        summary_parts: list[str] = []
        if ctx.interpreted_tokens:
            summary_parts.append(f"Intent: {ctx.interpreted_tokens.intent.primary_intent}")
            summary_parts.append(f"Action: {ctx.interpreted_tokens.action.action_type}")
            summary_parts.append(f"Priority: {ctx.interpreted_tokens.action.priority}")
        if ctx.retrieved_context:
            summary_parts.append(f"Context items: {len(ctx.retrieved_context)}")
        if ctx.unified_context:
            summary_parts.append("Unified context available")
        return "; ".join(summary_parts) if summary_parts else "Minimal context"
