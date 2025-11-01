"""
Unified conversational pipeline for Discord AI chatbot.

This module orchestrates the complete flow from message reception to response
generation, integrating message evaluation, personality adaptation, memory
retrieval, and response generation.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ultimate_discord_intelligence_bot.step_result import StepResult

from .message_evaluator import EvaluationResult, MessageEvaluator
from .opt_in_manager import OptInManager
from .personality.personality_manager import PersonalityContext, PersonalityStateManager
from .personality.reward_computer import InteractionMetrics, RewardComputer


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.services.memory_service import MemoryService
    from ultimate_discord_intelligence_bot.services.openrouter_service.adaptive_routing import AdaptiveRoutingManager
    from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine


logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the conversational pipeline."""

    max_response_length: int = 2000
    context_window_messages: int = 50
    response_probability_threshold: float = 0.7
    personality_adaptation_enabled: bool = True
    memory_retrieval_enabled: bool = True
    cost_estimation_enabled: bool = True
    max_cost_per_interaction: float = 0.01  # USD


@dataclass
class PipelineContext:
    """Context for pipeline execution."""

    message_data: dict[str, Any]
    guild_id: str
    channel_id: str
    user_id: str
    recent_messages: list[dict[str, Any]]
    user_opt_in_status: bool
    personality_context: PersonalityContext
    estimated_cost: float = 0.0


@dataclass
class PipelineResult:
    """Result of pipeline execution."""

    should_respond: bool
    response_content: str | None = None
    confidence: float = 0.0
    reasoning: str = ""
    personality_traits: dict[str, float] | None = None
    memory_retrieved: list[dict[str, Any]] = None
    cost_actual: float = 0.0
    processing_time: float = 0.0

    def __post_init__(self):
        if self.memory_retrieved is None:
            self.memory_retrieved = []


class ConversationalPipeline:
    """Main conversational pipeline orchestrator."""

    def __init__(
        self,
        routing_manager: AdaptiveRoutingManager,
        prompt_engine: PromptEngine,
        memory_service: MemoryService,
        learning_engine: Any,  # LearningEngine from core
        config: PipelineConfig | None = None,
    ):
        self.routing_manager = routing_manager
        self.prompt_engine = prompt_engine
        self.memory_service = memory_service
        self.learning_engine = learning_engine

        self.config = config or PipelineConfig()

        # Initialize components
        self.message_evaluator = MessageEvaluator(routing_manager, prompt_engine, memory_service)
        self.opt_in_manager = OptInManager()
        self.personality_manager = PersonalityStateManager(memory_service, learning_engine)
        self.reward_computer = RewardComputer()

        # Load personality for each guild
        self._guild_personalities: dict[str, PersonalityStateManager] = {}
        self._background_tasks: set[asyncio.Task[Any]] = set()

    async def process_message(
        self, message_data: dict[str, Any], recent_messages: list[dict[str, Any]]
    ) -> StepResult[PipelineResult]:
        """Process a Discord message through the complete pipeline."""

        start_time = time.time()

        try:
            # Extract basic information
            guild_id = str(message_data.get("guild_id", ""))
            channel_id = str(message_data.get("channel_id", ""))
            user_id = str(message_data.get("author", {}).get("id", ""))

            if not guild_id or not user_id:
                return StepResult.fail("Invalid message data: missing guild_id or user_id")

            # Step 1: Check user opt-in status
            opt_in_result = await self.opt_in_manager.get_user_status(user_id, guild_id)
            if not opt_in_result.success:
                logger.warning(f"Failed to get user opt-in status: {opt_in_result.error}")
                user_opt_in_status = False
            else:
                user_opt_in_status = opt_in_result.data.get("opted_in", False)

            # If user hasn't opted in, skip processing unless it's a direct mention
            if not user_opt_in_status and not self._is_direct_mention(message_data):
                return StepResult.ok(
                    data=PipelineResult(should_respond=False, reasoning="User has not opted in to AI interactions")
                )

            # Step 2: Build pipeline context
            personality_context = await self._build_personality_context(message_data, recent_messages)

            pipeline_context = PipelineContext(
                message_data=message_data,
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                recent_messages=recent_messages,
                user_opt_in_status=user_opt_in_status,
                personality_context=personality_context,
            )

            # Step 3: Evaluate message for response decision
            evaluation_result = await self.message_evaluator.evaluate_discord_message(
                message_data, recent_messages, user_opt_in_status
            )

            if not evaluation_result.success:
                logger.error(f"Message evaluation failed: {evaluation_result.error}")
                return StepResult.fail(f"Message evaluation failed: {evaluation_result.error}")

            evaluation = evaluation_result.data

            # Step 4: Check if we should respond
            if not evaluation.should_respond:
                return StepResult.ok(
                    data=PipelineResult(
                        should_respond=False,
                        confidence=evaluation.confidence,
                        reasoning=evaluation.reasoning,
                        processing_time=time.time() - start_time,
                    )
                )

            # Step 5: Estimate cost
            cost_estimate = await self._estimate_interaction_cost(pipeline_context, evaluation)
            if cost_estimate > self.config.max_cost_per_interaction:
                logger.warning(f"Interaction cost too high: ${cost_estimate:.4f}")
                return StepResult.ok(
                    data=PipelineResult(
                        should_respond=False,
                        reasoning="Interaction cost exceeds threshold",
                        cost_actual=cost_estimate,
                        processing_time=time.time() - start_time,
                    )
                )

            pipeline_context.estimated_cost = cost_estimate

            # Step 6: Retrieve relevant context from memory
            memory_context = await self._retrieve_memory_context(pipeline_context)

            # Step 7: Get personality traits for this interaction
            personality_traits = await self._get_personality_traits(guild_id, personality_context)

            # Step 8: Generate response
            response_result = await self._generate_response(
                pipeline_context, evaluation, memory_context, personality_traits
            )

            if not response_result.success:
                return StepResult.fail(f"Response generation failed: {response_result.error}")

            response_content = response_result.data

            # Step 9: Post-process response
            final_response = await self._post_process_response(response_content, personality_traits)

            # Step 10: Store interaction in memory
            await self._store_interaction(pipeline_context, evaluation, final_response)

            # Step 11: Start monitoring for reward signals
            task = asyncio.create_task(self._monitor_interaction_rewards(pipeline_context, evaluation, final_response))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            processing_time = time.time() - start_time

            return StepResult.ok(
                data=PipelineResult(
                    should_respond=True,
                    response_content=final_response,
                    confidence=evaluation.confidence,
                    reasoning=evaluation.reasoning,
                    personality_traits=personality_traits,
                    memory_retrieved=memory_context,
                    cost_actual=cost_estimate,
                    processing_time=processing_time,
                )
            )

        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            return StepResult.fail(f"Pipeline processing failed: {e!s}")

    def _is_direct_mention(self, message_data: dict[str, Any]) -> bool:
        """Check if message is a direct mention of the bot."""
        content = message_data.get("content", "").lower()
        return (
            "@bot" in content
            or "hey bot" in content
            or "bot," in content
            or message_data.get("referenced_message") is not None
        )

    async def _build_personality_context(
        self, message_data: dict[str, Any], recent_messages: list[dict[str, Any]]
    ) -> PersonalityContext:
        """Build personality context for the interaction."""
        try:
            # Determine channel type (simplified)
            channel_type = "general"  # Could be enhanced with actual Discord channel type detection

            # Determine time of day
            import datetime

            current_hour = datetime.datetime.now().hour
            if 6 <= current_hour < 12:
                time_of_day = "morning"
            elif 12 <= current_hour < 18:
                time_of_day = "afternoon"
            elif 18 <= current_hour < 22:
                time_of_day = "evening"
            else:
                time_of_day = "night"

            # Get user history embedding (placeholder)
            user_history = np.zeros(10)  # Would be actual embedding in real implementation

            # Estimate message sentiment (placeholder)
            message_sentiment = 0.0  # Would use actual sentiment analysis

            # Count conversation length
            conversation_length = len(recent_messages)

            # Determine guild culture (placeholder)
            guild_culture = "casual"  # Would be determined from guild settings/history

            return PersonalityContext(
                channel_type=channel_type,
                time_of_day=time_of_day,
                user_history=user_history,
                message_sentiment=message_sentiment,
                conversation_length=conversation_length,
                guild_culture=guild_culture,
            )

        except Exception as e:
            logger.error(f"Failed to build personality context: {e}")
            # Return default context
            return PersonalityContext(
                channel_type="general",
                time_of_day="afternoon",
                user_history=np.zeros(10),
                message_sentiment=0.0,
                conversation_length=1,
                guild_culture="casual",
            )

    async def _estimate_interaction_cost(self, context: PipelineContext, evaluation: EvaluationResult) -> float:
        """Estimate the cost of this interaction."""
        try:
            if not self.config.cost_estimation_enabled:
                return 0.0

            # Estimate input tokens
            message_content = context.message_data.get("content", "")
            context_content = "\n".join([msg.get("content", "") for msg in context.recent_messages])

            input_tokens = len((message_content + context_content).split()) * 1.3

            # Estimate output tokens (response)
            output_tokens = self.config.max_response_length / 4 * 1.3  # Rough estimate

            # Get cost estimation from routing manager
            cost_result = await self.routing_manager.estimate_cost(
                model=evaluation.suggested_personality_traits.get("model", "gpt-4o-mini"),
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
            )

            if cost_result.success:
                return cost_result.data.get("estimated_cost", 0.0)
            else:
                # Fallback estimation
                return (input_tokens / 1000) * 0.001 + (output_tokens / 1000) * 0.002

        except Exception as e:
            logger.error(f"Failed to estimate interaction cost: {e}")
            return 0.0

    async def _retrieve_memory_context(self, context: PipelineContext) -> list[dict[str, Any]]:
        """Retrieve relevant context from memory."""
        try:
            if not self.config.memory_retrieval_enabled:
                return []

            message_content = context.message_data.get("content", "")

            # Search for relevant memories
            result = await self.memory_service.search_memories(
                query=message_content, tenant=context.guild_id, workspace="general", limit=5
            )

            if result.success and result.data.get("memories"):
                return result.data["memories"]
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to retrieve memory context: {e}")
            return []

    async def _get_personality_traits(self, guild_id: str, personality_context: PersonalityContext) -> dict[str, float]:
        """Get personality traits for the interaction."""
        try:
            # Get or create personality manager for this guild
            if guild_id not in self._guild_personalities:
                self._guild_personalities[guild_id] = PersonalityStateManager(self.memory_service, self.learning_engine)

                # Load existing personality
                await self._guild_personalities[guild_id].load_personality(
                    tenant=guild_id, workspace="discord_personality"
                )

            personality_manager = self._guild_personalities[guild_id]

            # Get current traits
            current_traits = personality_manager.current_traits

            # Apply context-based adjustments
            adjusted_traits = self._apply_context_adjustments(current_traits, personality_context)

            return adjusted_traits.to_dict()

        except Exception as e:
            logger.error(f"Failed to get personality traits: {e}")
            # Return default traits
            return {
                "humor": 0.5,
                "formality": 0.5,
                "enthusiasm": 0.7,
                "knowledge_confidence": 0.8,
                "debate_tolerance": 0.6,
                "empathy": 0.7,
                "creativity": 0.6,
                "directness": 0.5,
            }

    def _apply_context_adjustments(self, traits, context: PersonalityContext):
        """Apply context-based adjustments to personality traits."""
        try:
            # Create copy of traits
            adjusted = traits

            # Adjust based on channel type
            if context.channel_type == "debate":
                adjusted.debate_tolerance = min(1.0, adjusted.debate_tolerance + 0.1)
                adjusted.directness = min(1.0, adjusted.directness + 0.05)
            elif context.channel_type == "support":
                adjusted.empathy = min(1.0, adjusted.empathy + 0.1)
                adjusted.formality = max(0.0, adjusted.formality - 0.05)

            # Adjust based on time of day
            if context.time_of_day in ["evening", "night"]:
                adjusted.enthusiasm = max(0.0, adjusted.enthusiasm - 0.05)
                adjusted.humor = min(1.0, adjusted.humor + 0.05)

            return adjusted

        except Exception as e:
            logger.error(f"Failed to apply context adjustments: {e}")
            return traits

    async def _generate_response(
        self,
        context: PipelineContext,
        evaluation: EvaluationResult,
        memory_context: list[dict[str, Any]],
        personality_traits: dict[str, float],
    ) -> StepResult[str]:
        """Generate response using LLM with personality and context."""
        try:
            # Build response prompt
            prompt = await self._build_response_prompt(context, evaluation, memory_context, personality_traits)

            # Get optimal model for response generation
            model_suggestion = await self.routing_manager.suggest_model(
                task_type="response_generation",
                context={
                    "prompt_length": len(prompt),
                    "personality_traits": personality_traits,
                    "complexity": "medium",
                },
            )

            if not model_suggestion.success:
                return StepResult.fail(f"Failed to get model suggestion: {model_suggestion.error}")

            # Generate response
            response_result = await self.prompt_engine.generate_response(
                prompt=prompt,
                model=model_suggestion.data.get("model"),
                max_tokens=self.config.max_response_length,
                temperature=0.7,  # Slightly creative for personality
            )

            if response_result.success:
                return StepResult.ok(data=response_result.data)
            else:
                return StepResult.fail(f"Response generation failed: {response_result.error}")

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return StepResult.fail(f"Response generation failed: {e!s}")

    async def _build_response_prompt(
        self,
        context: PipelineContext,
        evaluation: EvaluationResult,
        memory_context: list[dict[str, Any]],
        personality_traits: dict[str, float],
    ) -> str:
        """Build comprehensive response prompt."""

        message_content = context.message_data.get("content", "")
        username = context.message_data.get("author", {}).get("username", "User")

        # Format memory context
        memory_text = ""
        if memory_context:
            memory_text = "\n".join([f"- {mem.get('content', '')}" for mem in memory_context])

        # Format recent messages
        recent_text = ""
        if context.recent_messages:
            recent_text = "\n".join(
                [
                    f"{msg.get('author', {}).get('username', 'User')}: {msg.get('content', '')}"
                    for msg in context.recent_messages[-5:]  # Last 5 messages
                ]
            )

        # Personality instructions
        personality_instructions = self._generate_personality_instructions(personality_traits)

        prompt = f"""
You are a Discord AI assistant with an evolving personality. Respond naturally to the user's message.

PERSONALITY TRAITS:
{personality_instructions}

CURRENT MESSAGE:
{username}: "{message_content}"

RECENT CONVERSATION:
{recent_text}

RELEVANT KNOWLEDGE:
{memory_text}

RESPONSE GUIDELINES:
- Respond naturally and conversationally
- Match your personality traits
- Be helpful and engaging
- Keep responses concise but meaningful
- Use Discord-appropriate formatting
- Don't repeat information unnecessarily

Generate a natural Discord response:
"""

        return prompt

    def _generate_personality_instructions(self, traits: dict[str, float]) -> str:
        """Generate personality instructions for the prompt."""
        instructions = []

        # Humor level
        if traits["humor"] > 0.7:
            instructions.append("- Be playful and use humor frequently")
        elif traits["humor"] < 0.3:
            instructions.append("- Be serious and avoid jokes")
        else:
            instructions.append("- Use humor occasionally and appropriately")

        # Formality
        if traits["formality"] > 0.7:
            instructions.append("- Use formal language and proper grammar")
        elif traits["formality"] < 0.3:
            instructions.append("- Use casual, relaxed language")
        else:
            instructions.append("- Use balanced, conversational language")

        # Enthusiasm
        if traits["enthusiasm"] > 0.7:
            instructions.append("- Be energetic and enthusiastic")
        elif traits["enthusiasm"] < 0.3:
            instructions.append("- Be calm and measured")
        else:
            instructions.append("- Be moderately enthusiastic")

        # Knowledge confidence
        if traits["knowledge_confidence"] > 0.7:
            instructions.append("- Express confidence in your knowledge")
        elif traits["knowledge_confidence"] < 0.3:
            instructions.append("- Express uncertainty when appropriate")
        else:
            instructions.append("- Balance confidence with humility")

        # Empathy
        if traits["empathy"] > 0.7:
            instructions.append("- Show empathy and emotional understanding")
        elif traits["empathy"] < 0.3:
            instructions.append("- Focus on factual analysis")
        else:
            instructions.append("- Balance empathy with objectivity")

        return "\n".join(instructions)

    async def _post_process_response(self, response: str, personality_traits: dict[str, float]) -> str:
        """Post-process response for Discord formatting and length."""
        try:
            # Trim to max length
            if len(response) > self.config.max_response_length:
                response = response[: self.config.max_response_length - 3] + "..."

            # Apply personality-based formatting
            if personality_traits["enthusiasm"] > 0.7:
                # Add enthusiasm markers occasionally
                pass  # Could add emojis or exclamation marks

            if personality_traits["formality"] < 0.3:
                # Ensure casual formatting
                response = response.replace("I will", "I'll").replace("cannot", "can't")

            return response.strip()

        except Exception as e:
            logger.error(f"Failed to post-process response: {e}")
            return response

    async def _store_interaction(self, context: PipelineContext, evaluation: EvaluationResult, response: str) -> None:
        """Store interaction in memory for future learning."""
        try:
            interaction_data = {
                "message_id": context.message_data.get("id"),
                "user_id": context.user_id,
                "guild_id": context.guild_id,
                "channel_id": context.channel_id,
                "message_content": context.message_data.get("content"),
                "bot_response": response,
                "evaluation": evaluation.reasoning,
                "personality_traits": evaluation.suggested_personality_traits,
                "timestamp": time.time(),
            }

            # Store in memory service
            await self.memory_service.store_memory(
                content=f"Discord interaction: {context.message_data.get('content', '')}",
                metadata=interaction_data,
                tenant=context.guild_id,
                workspace="discord_interactions",
            )

            # Record in opt-in manager
            await self.opt_in_manager.record_interaction(
                user_id=context.user_id,
                guild_id=context.guild_id,
                message_id=context.message_data.get("id"),
                interaction_type="ai_response",
                content=context.message_data.get("content"),
                bot_response=response,
            )

        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")

    async def _monitor_interaction_rewards(
        self, context: PipelineContext, evaluation: EvaluationResult, response: str
    ) -> None:
        """Monitor interaction for reward signals and update personality."""
        try:
            if not self.config.personality_adaptation_enabled:
                return

            # Create interaction metrics
            metrics = InteractionMetrics(
                message_id=context.message_data.get("id", ""),
                user_id=context.user_id,
                guild_id=context.guild_id,
                timestamp=time.time(),
            )

            # Monitor for user reactions and replies (simplified)
            # In a real implementation, this would integrate with Discord event monitoring

            # For now, simulate reward computation after a delay
            await asyncio.sleep(300)  # Wait 5 minutes for user engagement

            # Compute reward (this would be based on actual user engagement)
            reward_result = await self.reward_computer.compute_reward(metrics)

            if reward_result.success:
                reward = reward_result.data

                # Adapt personality based on reward
                personality_manager = self._guild_personalities.get(context.guild_id)
                if personality_manager:
                    await personality_manager.adapt_personality(
                        context=context.personality_context,
                        reward=reward.total_reward,
                        tenant=context.guild_id,
                        workspace="discord_personality",
                    )

        except Exception as e:
            logger.error(f"Failed to monitor interaction rewards: {e}")

    async def get_pipeline_status(self, guild_id: str) -> StepResult[dict[str, Any]]:
        """Get pipeline status and statistics for a guild."""
        try:
            status = {
                "guild_id": guild_id,
                "config": self.config.__dict__,
                "personality_loaded": guild_id in self._guild_personalities,
            }

            # Get opt-in statistics
            opt_in_stats = await self.opt_in_manager.get_guild_opt_in_stats(guild_id)
            if opt_in_stats.success:
                status["opt_in_stats"] = opt_in_stats.data

            # Get personality summary
            if guild_id in self._guild_personalities:
                personality_summary = await self._guild_personalities[guild_id].get_personality_summary(
                    tenant=guild_id, workspace="discord_personality"
                )
                if personality_summary.success:
                    status["personality"] = personality_summary.data

            return StepResult.ok(data=status)

        except Exception as e:
            logger.error(f"Failed to get pipeline status: {e}")
            return StepResult.fail(f"Failed to get pipeline status: {e!s}")
