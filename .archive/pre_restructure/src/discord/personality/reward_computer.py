"""
Reward signal computation for personality evolution.

This module computes reward signals from user reactions and engagement metrics
to guide personality adaptation through reinforcement learning.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class InteractionMetrics:
    """Metrics for a single interaction."""

    message_id: str
    user_id: str
    guild_id: str
    timestamp: float
    bot_response_id: str | None = None

    # User engagement metrics
    user_replies: int = 0
    user_reactions: list[str] = None
    follow_up_messages: int = 0
    conversation_continuation: bool = False

    # Temporal metrics
    time_to_first_reply: float | None = None  # seconds
    conversation_duration: float | None = None  # seconds

    # Content metrics
    message_length: int = 0
    response_length: int = 0

    def __post_init__(self):
        if self.user_reactions is None:
            self.user_reactions = []


@dataclass
class RewardSignal:
    """Computed reward signal for personality adaptation."""

    total_reward: float
    engagement_reward: float
    reaction_reward: float
    continuation_reward: float
    temporal_reward: float
    content_reward: float

    # Metadata
    confidence: float
    reasoning: str
    metrics: InteractionMetrics


class RewardComputer:
    """Computes reward signals from user interactions."""

    def __init__(self):
        # Reward weights for different signal types
        self.weights = {"engagement": 0.3, "reaction": 0.25, "continuation": 0.2, "temporal": 0.15, "content": 0.1}

        # Reward thresholds and scaling factors
        self.thresholds = {
            "quick_reply": 60.0,  # seconds
            "good_reaction": 0.6,  # positive reaction threshold
            "long_conversation": 300.0,  # seconds
            "min_message_length": 10,  # characters
            "good_response_length": 50,  # characters
        }

        # Positive reaction emojis (Discord emoji names)
        self.positive_reactions = {
            "👍",
            "❤️",
            "😊",
            "😂",
            "🔥",
            "✨",
            "💯",
            "🎉",
            "thumbsup",
            "heart",
            "smile",
            "joy",
            "fire",
            "sparkles",
            "100",
            "tada",
        }

        # Negative reaction emojis
        self.negative_reactions = {"👎", "😞", "😠", "💔", "thumbsdown", "disappointed", "angry", "broken_heart"}

    async def compute_reward(
        self, metrics: InteractionMetrics, context: dict[str, Any] | None = None
    ) -> StepResult[RewardSignal]:
        """Compute comprehensive reward signal from interaction metrics."""

        try:
            # Compute individual reward components
            engagement_reward = self._compute_engagement_reward(metrics)
            reaction_reward = self._compute_reaction_reward(metrics)
            continuation_reward = self._compute_continuation_reward(metrics)
            temporal_reward = self._compute_temporal_reward(metrics)
            content_reward = self._compute_content_reward(metrics)

            # Compute weighted total reward
            total_reward = (
                engagement_reward * self.weights["engagement"]
                + reaction_reward * self.weights["reaction"]
                + continuation_reward * self.weights["continuation"]
                + temporal_reward * self.weights["temporal"]
                + content_reward * self.weights["content"]
            )

            # Compute confidence based on data availability
            confidence = self._compute_confidence(metrics)

            # Generate reasoning
            reasoning = self._generate_reasoning(
                metrics, engagement_reward, reaction_reward, continuation_reward, temporal_reward, content_reward
            )

            reward_signal = RewardSignal(
                total_reward=total_reward,
                engagement_reward=engagement_reward,
                reaction_reward=reaction_reward,
                continuation_reward=continuation_reward,
                temporal_reward=temporal_reward,
                content_reward=content_reward,
                confidence=confidence,
                reasoning=reasoning,
                metrics=metrics,
            )

            return StepResult.ok(data=reward_signal)

        except Exception as e:
            logger.error(f"Failed to compute reward: {e}")
            return StepResult.fail(f"Reward computation failed: {e!s}")

    def _compute_engagement_reward(self, metrics: InteractionMetrics) -> float:
        """Compute reward based on user engagement."""
        try:
            reward = 0.0

            # User replies (high value signal)
            if metrics.user_replies > 0:
                # Logarithmic scaling to prevent gaming
                reward += min(1.0, 0.8 * (1 + 0.5 * metrics.user_replies))

            # Follow-up messages
            if metrics.follow_up_messages > 0:
                reward += min(0.5, 0.3 * metrics.follow_up_messages)

            # Conversation continuation
            if metrics.conversation_continuation:
                reward += 0.4

            return min(1.0, reward)

        except Exception as e:
            logger.error(f"Error computing engagement reward: {e}")
            return 0.0

    def _compute_reaction_reward(self, metrics: InteractionMetrics) -> float:
        """Compute reward based on user reactions."""
        try:
            if not metrics.user_reactions:
                return 0.0

            reward = 0.0
            positive_count = 0
            negative_count = 0

            for reaction in metrics.user_reactions:
                # Normalize reaction name
                reaction_name = reaction.lower().strip()

                if reaction_name in self.positive_reactions:
                    positive_count += 1
                elif reaction_name in self.negative_reactions:
                    negative_count += 1

            # Compute net reaction score
            total_reactions = positive_count + negative_count
            if total_reactions > 0:
                net_score = (positive_count - negative_count) / total_reactions

                # Scale to [0, 1] range
                reward = (net_score + 1.0) / 2.0

            # Bonus for multiple positive reactions
            if positive_count > 1:
                reward = min(1.0, reward + 0.2 * (positive_count - 1))

            return reward

        except Exception as e:
            logger.error(f"Error computing reaction reward: {e}")
            return 0.0

    def _compute_continuation_reward(self, metrics: InteractionMetrics) -> float:
        """Compute reward based on conversation continuation."""
        try:
            reward = 0.0

            # Quick reply bonus (within 60 seconds)
            if (
                metrics.time_to_first_reply is not None
                and metrics.time_to_first_reply <= self.thresholds["quick_reply"]
            ):
                reward += 0.6

            # Multiple replies bonus
            if metrics.user_replies > 1:
                reward += min(0.4, 0.2 * (metrics.user_replies - 1))

            # Long conversation bonus
            if (
                metrics.conversation_duration is not None
                and metrics.conversation_duration >= self.thresholds["long_conversation"]
            ):
                reward += 0.3

            return min(1.0, reward)

        except Exception as e:
            logger.error(f"Error computing continuation reward: {e}")
            return 0.0

    def _compute_temporal_reward(self, metrics: InteractionMetrics) -> float:
        """Compute reward based on temporal patterns."""
        try:
            reward = 0.0
            current_time = time.time()
            time_since_interaction = current_time - metrics.timestamp

            # Recency bonus (recent interactions are more valuable)
            if time_since_interaction < 3600:  # Within 1 hour
                reward += 0.5
            elif time_since_interaction < 86400:  # Within 24 hours
                reward += 0.3
            else:
                reward += 0.1

            # Time of day bonus (evening interactions might be more valuable)
            import datetime

            hour = datetime.datetime.fromtimestamp(metrics.timestamp).hour

            if 18 <= hour <= 23:  # Evening
                reward += 0.2
            elif 12 <= hour <= 17:  # Afternoon
                reward += 0.1

            return min(1.0, reward)

        except Exception as e:
            logger.error(f"Error computing temporal reward: {e}")
            return 0.0

    def _compute_content_reward(self, metrics: InteractionMetrics) -> float:
        """Compute reward based on content quality."""
        try:
            reward = 0.0

            # Message length bonus (not too short, not too long)
            if metrics.message_length >= self.thresholds["min_message_length"]:
                reward += 0.3

            # Response length bonus (substantial responses are better)
            if metrics.response_length >= self.thresholds["good_response_length"]:
                reward += 0.4

            # Balance bonus (response length similar to message length)
            if metrics.message_length > 0 and metrics.response_length > 0:
                length_ratio = min(
                    metrics.response_length / metrics.message_length, metrics.message_length / metrics.response_length
                )
                reward += 0.3 * length_ratio

            return min(1.0, reward)

        except Exception as e:
            logger.error(f"Error computing content reward: {e}")
            return 0.0

    def _compute_confidence(self, metrics: InteractionMetrics) -> float:
        """Compute confidence in the reward signal."""
        try:
            confidence = 0.5  # Base confidence

            # Increase confidence with more data points
            if metrics.user_replies > 0:
                confidence += 0.2

            if metrics.user_reactions:
                confidence += 0.15

            if metrics.time_to_first_reply is not None:
                confidence += 0.1

            if metrics.conversation_duration is not None:
                confidence += 0.1

            # Decrease confidence if data is too old
            current_time = time.time()
            age_hours = (current_time - metrics.timestamp) / 3600

            if age_hours > 24:
                confidence *= 0.8
            elif age_hours > 168:  # 1 week
                confidence *= 0.6

            return min(1.0, confidence)

        except Exception as e:
            logger.error(f"Error computing confidence: {e}")
            return 0.5

    def _generate_reasoning(
        self,
        metrics: InteractionMetrics,
        engagement_reward: float,
        reaction_reward: float,
        continuation_reward: float,
        temporal_reward: float,
        content_reward: float,
    ) -> str:
        """Generate human-readable reasoning for the reward."""
        try:
            reasons = []

            # Engagement reasoning
            if engagement_reward > 0.7:
                reasons.append("High user engagement with multiple replies")
            elif engagement_reward > 0.4:
                reasons.append("Moderate user engagement")
            elif engagement_reward < 0.2:
                reasons.append("Low user engagement")

            # Reaction reasoning
            if reaction_reward > 0.7:
                reasons.append("Positive user reactions")
            elif reaction_reward < 0.3:
                reasons.append("Negative or no user reactions")

            # Continuation reasoning
            if continuation_reward > 0.6:
                reasons.append("Quick response and conversation continuation")
            elif continuation_reward < 0.3:
                reasons.append("No conversation continuation")

            # Temporal reasoning
            if temporal_reward > 0.7:
                reasons.append("Good timing for interaction")

            # Content reasoning
            if content_reward > 0.6:
                reasons.append("Good content quality and length balance")

            if not reasons:
                reasons.append("Neutral interaction with no strong signals")

            return "; ".join(reasons)

        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return "Error generating reasoning"

    async def compute_batch_rewards(self, metrics_list: list[InteractionMetrics]) -> StepResult[list[RewardSignal]]:
        """Compute rewards for a batch of interactions."""
        try:
            rewards = []

            for metrics in metrics_list:
                reward_result = await self.compute_reward(metrics)

                if reward_result.success:
                    rewards.append(reward_result.data)
                else:
                    logger.warning(f"Failed to compute reward for interaction {metrics.message_id}")
                    # Add neutral reward for failed computations
                    neutral_reward = RewardSignal(
                        total_reward=0.0,
                        engagement_reward=0.0,
                        reaction_reward=0.0,
                        continuation_reward=0.0,
                        temporal_reward=0.0,
                        content_reward=0.0,
                        confidence=0.0,
                        reasoning="Failed to compute reward",
                        metrics=metrics,
                    )
                    rewards.append(neutral_reward)

            return StepResult.ok(data=rewards)

        except Exception as e:
            logger.error(f"Failed to compute batch rewards: {e}")
            return StepResult.fail(f"Batch reward computation failed: {e!s}")

    def get_reward_statistics(self, rewards: list[RewardSignal]) -> dict[str, Any]:
        """Get statistics for a collection of reward signals."""
        try:
            if not rewards:
                return {}

            total_rewards = [r.total_reward for r in rewards]
            engagement_rewards = [r.engagement_reward for r in rewards]
            reaction_rewards = [r.reaction_reward for r in rewards]
            continuation_rewards = [r.continuation_reward for r in rewards]

            return {
                "total_interactions": len(rewards),
                "average_total_reward": sum(total_rewards) / len(total_rewards),
                "average_engagement_reward": sum(engagement_rewards) / len(engagement_rewards),
                "average_reaction_reward": sum(reaction_rewards) / len(reaction_rewards),
                "average_continuation_reward": sum(continuation_rewards) / len(continuation_rewards),
                "high_reward_interactions": sum(1 for r in total_rewards if r > 0.7),
                "low_reward_interactions": sum(1 for r in total_rewards if r < 0.3),
                "average_confidence": sum(r.confidence for r in rewards) / len(rewards),
            }

        except Exception as e:
            logger.error(f"Failed to compute reward statistics: {e}")
            return {}

    async def monitor_ongoing_interaction(
        self, message_id: str, user_id: str, guild_id: str
    ) -> StepResult[InteractionMetrics]:
        """Monitor an ongoing interaction for reward computation."""
        try:
            # This would integrate with Discord event monitoring
            # For now, return a placeholder implementation

            current_time = time.time()

            metrics = InteractionMetrics(
                message_id=message_id, user_id=user_id, guild_id=guild_id, timestamp=current_time
            )

            # In a real implementation, this would:
            # 1. Monitor Discord events for replies, reactions
            # 2. Track conversation continuation
            # 3. Measure temporal metrics
            # 4. Analyze content quality

            return StepResult.ok(data=metrics)

        except Exception as e:
            logger.error(f"Failed to monitor interaction: {e}")
            return StepResult.fail(f"Interaction monitoring failed: {e!s}")
