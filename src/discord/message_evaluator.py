"""
AI-driven message evaluation system for Discord bot response decisions.

This module implements intelligent decision-making for when the bot should respond
to Discord messages, using LLM-based evaluation with context awareness.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from platform.llm.providers.openrouter.adaptive_routing import AdaptiveRoutingManager
    from platform.prompts.engine import PromptEngine

    from domains.memory import MemoryService
logger = logging.getLogger(__name__)


@dataclass
class MessageContext:
    """Context information for message evaluation."""

    message_id: str
    channel_id: str
    guild_id: str
    user_id: str
    username: str
    content: str
    timestamp: float
    is_direct_mention: bool
    is_reply_to_bot: bool
    channel_type: str
    user_opt_in_status: bool
    recent_messages: list[dict[str, Any]]
    user_interaction_history: list[dict[str, Any]]


@dataclass
class EvaluationResult:
    """Result of message evaluation."""

    should_respond: bool
    confidence: float
    reasoning: str
    priority: str
    suggested_personality_traits: dict[str, float]
    context_relevance_score: float
    estimated_cost: float


class MessageContextBuilder:
    """Builds comprehensive context for message evaluation."""

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    async def build_context(
        self, message_data: dict[str, Any], recent_messages: list[dict[str, Any]], user_opt_in_status: bool
    ) -> MessageContext:
        """Build comprehensive message context for evaluation."""
        try:
            message_id = str(message_data.get("id", ""))
            channel_id = str(message_data.get("channel_id", ""))
            guild_id = str(message_data.get("guild_id", ""))
            user_id = str(message_data.get("author", {}).get("id", ""))
            username = message_data.get("author", {}).get("username", "unknown")
            content = message_data.get("content", "")
            timestamp = float(message_data.get("timestamp", 0))
            is_direct_mention = self._check_direct_mention(content, message_data)
            is_reply_to_bot = await self._check_reply_to_bot(message_data)
            channel_type = "text"
            user_interaction_history = await self._get_user_interaction_history(user_id, guild_id)
            return MessageContext(
                message_id=message_id,
                channel_id=channel_id,
                guild_id=guild_id,
                user_id=user_id,
                username=username,
                content=content,
                timestamp=timestamp,
                is_direct_mention=is_direct_mention,
                is_reply_to_bot=is_reply_to_bot,
                channel_type=channel_type,
                user_opt_in_status=user_opt_in_status,
                recent_messages=recent_messages,
                user_interaction_history=user_interaction_history,
            )
        except Exception as e:
            logger.error(f"Failed to build message context: {e}")
            raise

    def _check_direct_mention(self, content: str, message_data: dict[str, Any]) -> bool:
        """Check if message is a direct mention of the bot."""
        return "@bot" in content.lower() or "hey bot" in content.lower() or "bot," in content.lower()

    async def _check_reply_to_bot(self, message_data: dict[str, Any]) -> bool:
        """Check if message is a reply to the bot."""
        referenced_message = message_data.get("referenced_message")
        if not referenced_message:
            return False
        referenced_author = referenced_message.get("author", {})
        return referenced_author.get("bot", False)

    async def _get_user_interaction_history(self, user_id: str, guild_id: str) -> list[dict[str, Any]]:
        """Get user's recent interaction history with the bot."""
        try:
            result = await self.memory_service.search_memories(
                query=f"user:{user_id} guild:{guild_id}", tenant=guild_id, workspace="discord_interactions", limit=10
            )
            if result.success:
                return result.data.get("memories", [])
            else:
                logger.warning(f"Failed to get user interaction history: {result.error}")
                return []
        except Exception as e:
            logger.error(f"Error getting user interaction history: {e}")
            return []


class ResponseDecisionAgent:
    """AI agent for making response decisions based on message context."""

    def __init__(
        self, routing_manager: AdaptiveRoutingManager, prompt_engine: PromptEngine, memory_service: MemoryService
    ):
        self.routing_manager = routing_manager
        self.prompt_engine = prompt_engine
        self.memory_service = memory_service

    async def evaluate_message(self, context: MessageContext) -> StepResult[EvaluationResult]:
        """Evaluate whether the bot should respond to a message."""
        try:
            evaluation_prompt = await self._build_evaluation_prompt(context)
            model_suggestion = await self.routing_manager.suggest_model(
                task_type="decision_making",
                context={"prompt_length": len(evaluation_prompt), "complexity": "medium", "requires_reasoning": True},
            )
            if not model_suggestion.success:
                return StepResult.fail(f"Failed to get model suggestion: {model_suggestion.error}")
            evaluation_result = await self._generate_evaluation(evaluation_prompt, model_suggestion.data)
            if not evaluation_result.success:
                return StepResult.fail(f"Failed to generate evaluation: {evaluation_result.error}")
            parsed_result = self._parse_evaluation_result(evaluation_result.data, context)
            return StepResult.ok(data=parsed_result)
        except Exception as e:
            logger.error(f"Error evaluating message: {e}")
            return StepResult.fail(f"Message evaluation failed: {e!s}")

    async def _build_evaluation_prompt(self, context: MessageContext) -> str:
        """Build comprehensive evaluation prompt."""
        relevant_context = await self._get_relevant_context(context)
        prompt = f"""\nYou are an AI assistant evaluating whether a Discord bot should respond to a message.\n\nMESSAGE TO EVALUATE:\nUser: {context.username} (ID: {context.user_id})\nChannel: {context.channel_id}\nContent: "{context.content}"\nTimestamp: {context.timestamp}\nDirect Mention: {context.is_direct_mention}\nReply to Bot: {context.is_reply_to_bot}\nUser Opted In: {context.user_opt_in_status}\n\nRECENT CHANNEL CONTEXT:\n{self._format_recent_messages(context.recent_messages)}\n\nUSER INTERACTION HISTORY:\n{self._format_interaction_history(context.user_interaction_history)}\n\nRELEVANT KNOWLEDGE CONTEXT:\n{relevant_context}\n\nEVALUATION CRITERIA:\n1. Direct mentions or replies to bot (HIGH priority)\n2. Conversation relevance to bot's knowledge domains\n3. User opt-in status and engagement history\n4. Channel context and conversation flow\n5. Personality appropriateness and timing\n\nPlease evaluate and respond with a JSON object containing:\n{{\n    "should_respond": boolean,\n    "confidence": float (0.0-1.0),\n    "reasoning": "detailed explanation",\n    "priority": "high|medium|low",\n    "suggested_personality_traits": {{\n        "humor": float (0.0-1.0),\n        "formality": float (0.0-1.0),\n        "enthusiasm": float (0.0-1.0),\n        "knowledge_confidence": float (0.0-1.0),\n        "debate_tolerance": float (0.0-1.0)\n    }},\n    "context_relevance_score": float (0.0-1.0)\n}}\n\nFocus on natural conversation flow and avoid over-responding while maintaining helpfulness.\n"""
        return prompt

    async def _get_relevant_context(self, context: MessageContext) -> str:
        """Get relevant context from memory for evaluation."""
        try:
            result = await self.memory_service.search_memories(
                query=context.content, tenant=context.guild_id, workspace="general", limit=5
            )
            if result.success and result.data.get("memories"):
                memories = result.data["memories"]
                context_text = "\n".join([f"- {mem.get('content', '')}" for mem in memories])
                return f"Relevant knowledge:\n{context_text}"
            else:
                return "No relevant knowledge found."
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return "Error retrieving context."

    def _format_recent_messages(self, messages: list[dict[str, Any]]) -> str:
        """Format recent messages for context."""
        if not messages:
            return "No recent messages."
        formatted = []
        for msg in messages[-5:]:
            author = msg.get("author", {}).get("username", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{author}: {content}")
        return "\n".join(formatted)

    def _format_interaction_history(self, history: list[dict[str, Any]]) -> str:
        """Format user interaction history."""
        if not history:
            return "No previous interactions with bot."
        formatted = []
        for interaction in history[-3:]:
            content = interaction.get("content", "")
            timestamp = interaction.get("timestamp", "")
            formatted.append(f"[{timestamp}] {content}")
        return "\n".join(formatted)

    async def _generate_evaluation(self, prompt: str, model_info: dict[str, Any]) -> StepResult[str]:
        """Generate evaluation using LLM."""
        try:
            result = await self.prompt_engine.generate_response(
                prompt=prompt, model=model_info.get("model"), max_tokens=500, temperature=0.3
            )
            if result.success:
                return StepResult.ok(data=result.data)
            else:
                return StepResult.fail(f"LLM generation failed: {result.error}")
        except Exception as e:
            logger.error(f"Error generating evaluation: {e}")
            return StepResult.fail(f"Evaluation generation failed: {e!s}")

    def _parse_evaluation_result(self, llm_response: str, context: MessageContext) -> EvaluationResult:
        """Parse and validate LLM evaluation result."""
        try:
            import json

            json_start = llm_response.find("{")
            json_end = llm_response.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            json_str = llm_response[json_start:json_end]
            data = json.loads(json_str)
            should_respond = bool(data.get("should_respond", False))
            confidence = float(data.get("confidence", 0.5))
            reasoning = str(data.get("reasoning", "No reasoning provided"))
            priority = str(data.get("priority", "medium"))
            context_relevance_score = float(data.get("context_relevance_score", 0.5))
            personality_traits = data.get("suggested_personality_traits", {})
            default_traits = {
                "humor": 0.5,
                "formality": 0.5,
                "enthusiasm": 0.7,
                "knowledge_confidence": 0.8,
                "debate_tolerance": 0.6,
            }
            for trait, default_value in default_traits.items():
                if trait not in personality_traits:
                    personality_traits[trait] = default_value
                else:
                    personality_traits[trait] = float(personality_traits[trait])
            estimated_cost = self._estimate_evaluation_cost(llm_response, context)
            return EvaluationResult(
                should_respond=should_respond,
                confidence=confidence,
                reasoning=reasoning,
                priority=priority,
                suggested_personality_traits=personality_traits,
                context_relevance_score=context_relevance_score,
                estimated_cost=estimated_cost,
            )
        except Exception as e:
            logger.error(f"Error parsing evaluation result: {e}")
            return EvaluationResult(
                should_respond=False,
                confidence=0.0,
                reasoning=f"Parse error: {e!s}",
                priority="low",
                suggested_personality_traits={
                    "humor": 0.5,
                    "formality": 0.5,
                    "enthusiasm": 0.7,
                    "knowledge_confidence": 0.8,
                    "debate_tolerance": 0.6,
                },
                context_relevance_score=0.0,
                estimated_cost=0.0,
            )

    def _estimate_evaluation_cost(self, llm_response: str, context: MessageContext) -> float:
        """Estimate the cost of this evaluation."""
        input_tokens = len(context.content.split()) * 1.3
        output_tokens = len(llm_response.split()) * 1.3
        input_cost = input_tokens / 1000 * 0.001
        output_cost = output_tokens / 1000 * 0.002
        return input_cost + output_cost


class MessageEvaluator:
    """Main message evaluation orchestrator."""

    def __init__(
        self, routing_manager: AdaptiveRoutingManager, prompt_engine: PromptEngine, memory_service: MemoryService
    ):
        self.context_builder = MessageContextBuilder(memory_service)
        self.decision_agent = ResponseDecisionAgent(routing_manager, prompt_engine, memory_service)
        self.memory_service = memory_service
        try:
            from discord.reasoning.hierarchical_reasoner import HierarchicalReasoningEngine
            from ultimate_discord_intelligence_bot.knowledge.context_builder import UnifiedContextBuilder
            from ultimate_discord_intelligence_bot.knowledge.retrieval_engine import UnifiedRetrievalEngine

            retrieval_engine = UnifiedRetrievalEngine()
            context_builder = UnifiedContextBuilder()
            self.hierarchical_reasoner = HierarchicalReasoningEngine(
                routing_manager=routing_manager,
                prompt_engine=prompt_engine,
                memory_service=memory_service,
                retrieval_engine=retrieval_engine,
                context_builder=context_builder,
            )
            self._use_hierarchical_reasoning = True
        except Exception as e:
            logger.warning(f"Hierarchical reasoning engine not available: {e}, using basic evaluation")
            self.hierarchical_reasoner = None
            self._use_hierarchical_reasoning = False

    async def evaluate_discord_message(
        self, message_data: dict[str, Any], recent_messages: list[dict[str, Any]], user_opt_in_status: bool
    ) -> StepResult[EvaluationResult]:
        """Evaluate whether bot should respond to Discord message."""
        try:
            if self._use_hierarchical_reasoning and self.hierarchical_reasoner:
                reasoning_result = await self.hierarchical_reasoner.reason(
                    message_data=message_data, recent_messages=recent_messages, user_opt_in_status=user_opt_in_status
                )
                if reasoning_result.success:
                    reasoning = reasoning_result.data
                    personality_traits = {
                        "humor": 0.5,
                        "formality": 0.5,
                        "enthusiasm": 0.7,
                        "knowledge_confidence": min(0.9, reasoning.confidence + 0.2),
                        "debate_tolerance": 0.6,
                    }
                    estimated_cost = 0.001 if reasoning.requires_crewmai else 0.0005
                    evaluation_result = EvaluationResult(
                        should_respond=reasoning.should_respond,
                        confidence=reasoning.confidence,
                        reasoning=reasoning.context_summary,
                        priority="high" if reasoning.priority >= 7 else "medium" if reasoning.priority >= 4 else "low",
                        suggested_personality_traits=personality_traits,
                        context_relevance_score=reasoning.confidence,
                        estimated_cost=estimated_cost,
                    )
                    from discord.message_evaluator import MessageContext

                    context = MessageContext(
                        message_id=str(message_data.get("id", "")),
                        channel_id=str(message_data.get("channel_id", "")),
                        guild_id=str(message_data.get("guild_id", "")),
                        user_id=str(message_data.get("author", {}).get("id", "")),
                        username=message_data.get("author", {}).get("username", "unknown"),
                        content=message_data.get("content", ""),
                        timestamp=float(message_data.get("timestamp", 0)),
                        is_direct_mention=bool(message_data.get("mentions")),
                        is_reply_to_bot=False,
                        channel_type="text",
                        user_opt_in_status=user_opt_in_status,
                        recent_messages=recent_messages,
                        user_interaction_history=[],
                    )
                    await self._store_evaluation(context, evaluation_result)
                    return StepResult.ok(data=evaluation_result)
                else:
                    logger.warning(
                        f"Hierarchical reasoning failed: {reasoning_result.error}, falling back to basic evaluation"
                    )
            context = await self.context_builder.build_context(message_data, recent_messages, user_opt_in_status)
            evaluation = await self.decision_agent.evaluate_message(context)
            if not evaluation.success:
                return StepResult.fail(f"Evaluation failed: {evaluation.error}")
            await self._store_evaluation(context, evaluation.data)
            return StepResult.ok(data=evaluation.data)
        except Exception as e:
            logger.error(f"Error in message evaluation: {e}")
            return StepResult.fail(f"Message evaluation failed: {e!s}")

    async def _store_evaluation(self, context: MessageContext, result: EvaluationResult) -> None:
        """Store evaluation result in memory for future learning."""
        try:
            evaluation_data = {
                "message_id": context.message_id,
                "user_id": context.user_id,
                "guild_id": context.guild_id,
                "content": context.content,
                "should_respond": result.should_respond,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "priority": result.priority,
                "personality_traits": result.suggested_personality_traits,
                "context_relevance_score": result.context_relevance_score,
                "estimated_cost": result.estimated_cost,
                "timestamp": context.timestamp,
            }
            await self.memory_service.store_memory(
                content=f"Message evaluation: {context.content}",
                metadata=evaluation_data,
                tenant=context.guild_id,
                workspace="message_evaluations",
            )
        except Exception as e:
            logger.error(f"Failed to store evaluation: {e}")
