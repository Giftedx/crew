"""
Personality state management system with vector embeddings and RL integration.

This module manages the bot's evolving personality traits using reinforcement
learning and vector storage for durable personality memory.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from ultimate_discord_intelligence_bot.services.memory_service import MemoryService
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class PersonalityTraits:
    """Core personality trait dimensions."""

    humor: float = 0.5  # 0.0 = serious, 1.0 = very humorous
    formality: float = 0.5  # 0.0 = casual, 1.0 = formal
    enthusiasm: float = 0.7  # 0.0 = low energy, 1.0 = high energy
    knowledge_confidence: float = 0.8  # 0.0 = uncertain, 1.0 = very confident
    debate_tolerance: float = 0.6  # 0.0 = avoid debate, 1.0 = embrace debate
    empathy: float = 0.7  # 0.0 = analytical, 1.0 = empathetic
    creativity: float = 0.6  # 0.0 = factual, 1.0 = creative
    directness: float = 0.5  # 0.0 = indirect, 1.0 = direct

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return asdict(self)

    def to_vector(self) -> np.ndarray:
        """Convert to numpy vector for ML operations."""
        return np.array(
            [
                self.humor,
                self.formality,
                self.enthusiasm,
                self.knowledge_confidence,
                self.debate_tolerance,
                self.empathy,
                self.creativity,
                self.directness,
            ]
        )

    @classmethod
    def from_vector(cls, vector: np.ndarray) -> PersonalityTraits:
        """Create from numpy vector."""
        # Ensure vector is the right length
        if len(vector) != 8:
            raise ValueError(f"Expected 8-dimensional vector, got {len(vector)}")

        # Clamp values to [0, 1] range
        clamped = np.clip(vector, 0.0, 1.0)

        return cls(
            humor=float(clamped[0]),
            formality=float(clamped[1]),
            enthusiasm=float(clamped[2]),
            knowledge_confidence=float(clamped[3]),
            debate_tolerance=float(clamped[4]),
            empathy=float(clamped[5]),
            creativity=float(clamped[6]),
            directness=float(clamped[7]),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PersonalityTraits:
        """Create from dictionary."""
        return cls(
            humor=float(data.get("humor", 0.5)),
            formality=float(data.get("formality", 0.5)),
            enthusiasm=float(data.get("enthusiasm", 0.7)),
            knowledge_confidence=float(data.get("knowledge_confidence", 0.8)),
            debate_tolerance=float(data.get("debate_tolerance", 0.6)),
            empathy=float(data.get("empathy", 0.7)),
            creativity=float(data.get("creativity", 0.6)),
            directness=float(data.get("directness", 0.5)),
        )


@dataclass
class PersonalityContext:
    """Context for personality adaptation."""

    channel_type: str  # "debate", "casual", "support", "general"
    time_of_day: str  # "morning", "afternoon", "evening", "night"
    user_history: np.ndarray  # User interaction history embedding
    message_sentiment: float  # -1.0 to 1.0
    conversation_length: int  # Number of messages in current thread
    guild_culture: str  # "academic", "casual", "professional", "gaming"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "channel_type": self.channel_type,
            "time_of_day": self.time_of_day,
            "user_history": self.user_history.tolist(),
            "message_sentiment": self.message_sentiment,
            "conversation_length": self.conversation_length,
            "guild_culture": self.guild_culture,
        }


class PersonalityStateManager:
    """Manages personality state with vector storage and RL integration."""

    def __init__(
        self,
        memory_service: MemoryService,
        learning_engine: Any,  # LearningEngine from core
    ):
        self.memory_service = memory_service
        self.learning_engine = learning_engine
        self.current_traits = PersonalityTraits()
        self._personality_history: list[tuple[float, PersonalityTraits]] = []

        # RL domain for personality optimization
        self.rl_domain = "discord_personality"
        self._init_rl_domain()

    def _init_rl_domain(self) -> None:
        """Initialize RL domain for personality optimization."""
        try:
            # Register personality domain with learning engine
            self.learning_engine.register_domain(
                self.rl_domain,
                policy="linucb",  # Contextual bandit
                priors=self.current_traits.to_dict(),
            )

            logger.info(f"Initialized RL domain: {self.rl_domain}")

        except Exception as e:
            logger.error(f"Failed to initialize RL domain: {e}")
            # Continue without RL - personality will be static

    async def load_personality(self, tenant: str, workspace: str) -> StepResult[PersonalityTraits]:
        """Load personality traits from memory storage."""
        try:
            # Search for latest personality state
            result = await self.memory_service.search_memories(
                query="personality_traits latest", tenant=tenant, workspace=workspace, limit=1
            )

            if result.success and result.data.get("memories"):
                memory = result.data["memories"][0]
                traits_data = memory.get("metadata", {}).get("traits", {})

                if traits_data:
                    self.current_traits = PersonalityTraits.from_dict(traits_data)

                    # Load personality history
                    await self._load_personality_history(tenant, workspace)

                    return StepResult.ok(data=self.current_traits)

            # No existing personality found, use defaults
            logger.info("No existing personality found, using defaults")
            await self._save_personality(tenant, workspace, self.current_traits)

            return StepResult.ok(data=self.current_traits)

        except Exception as e:
            logger.error(f"Failed to load personality: {e}")
            return StepResult.fail(f"Failed to load personality: {e!s}")

    async def _load_personality_history(self, tenant: str, workspace: str) -> None:
        """Load personality evolution history."""
        try:
            result = await self.memory_service.search_memories(
                query="personality_evolution",
                tenant=tenant,
                workspace=workspace,
                limit=50,  # Last 50 personality updates
            )

            if result.success and result.data.get("memories"):
                self._personality_history = []

                for memory in result.data["memories"]:
                    metadata = memory.get("metadata", {})
                    timestamp = metadata.get("timestamp", 0.0)
                    traits_data = metadata.get("traits", {})

                    if traits_data:
                        traits = PersonalityTraits.from_dict(traits_data)
                        self._personality_history.append((timestamp, traits))

                # Sort by timestamp
                self._personality_history.sort(key=lambda x: x[0])

                logger.info(f"Loaded {len(self._personality_history)} personality history entries")

        except Exception as e:
            logger.error(f"Failed to load personality history: {e}")

    async def _save_personality(self, tenant: str, workspace: str, traits: PersonalityTraits) -> None:
        """Save personality traits to memory storage."""
        try:
            import time

            timestamp = time.time()

            # Store current personality state
            await self.memory_service.store_memory(
                content=f"Personality traits: {traits.to_dict()}",
                metadata={"traits": traits.to_dict(), "timestamp": timestamp, "type": "personality_state"},
                tenant=tenant,
                workspace=workspace,
            )

            # Store in evolution history
            await self.memory_service.store_memory(
                content=f"Personality evolution at {timestamp}",
                metadata={"traits": traits.to_dict(), "timestamp": timestamp, "type": "personality_evolution"},
                tenant=tenant,
                workspace="personality_history",
            )

            # Update history cache
            self._personality_history.append((timestamp, traits))

            # Keep only recent history (last 100 entries)
            if len(self._personality_history) > 100:
                self._personality_history = self._personality_history[-100:]

        except Exception as e:
            logger.error(f"Failed to save personality: {e}")

    async def adapt_personality(
        self, context: PersonalityContext, reward: float, tenant: str, workspace: str
    ) -> StepResult[PersonalityTraits]:
        """Adapt personality based on context and reward."""
        try:
            # Get RL recommendation for personality adjustment
            action = await self._get_rl_recommendation(context)

            if not action.success:
                logger.warning(f"RL recommendation failed: {action.error}")
                return StepResult.ok(data=self.current_traits)

            # Apply personality adjustment
            new_traits = self._apply_personality_adjustment(self.current_traits, action.data, context)

            # Record RL feedback
            await self._record_rl_feedback(context, action.data, reward)

            # Update current traits
            self.current_traits = new_traits

            # Save updated personality
            await self._save_personality(tenant, workspace, new_traits)

            logger.info(f"Adapted personality: {new_traits.to_dict()}")

            return StepResult.ok(data=new_traits)

        except Exception as e:
            logger.error(f"Failed to adapt personality: {e}")
            return StepResult.fail(f"Personality adaptation failed: {e!s}")

    async def _get_rl_recommendation(self, context: PersonalityContext) -> StepResult[dict[str, Any]]:
        """Get RL recommendation for personality adjustment."""
        try:
            # Prepare context for RL
            rl_context = {
                "channel_type": context.channel_type,
                "time_of_day": context.time_of_day,
                "message_sentiment": context.message_sentiment,
                "conversation_length": context.conversation_length,
                "guild_culture": context.guild_culture,
            }

            # Add user history embedding (first 10 dimensions)
            user_history = context.user_history[:10] if len(context.user_history) > 10 else context.user_history
            rl_context.update({f"user_hist_{i}": float(user_history[i]) for i in range(len(user_history))})

            # Get recommendation from learning engine
            recommendation = self.learning_engine.recommend(
                domain=self.rl_domain,
                context=rl_context,
                candidates=[
                    "adjust_humor",
                    "adjust_formality",
                    "adjust_enthusiasm",
                    "adjust_confidence",
                    "adjust_empathy",
                    "maintain_current",
                ],
            )

            if recommendation.success:
                return StepResult.ok(data=recommendation.data)
            else:
                # Fallback to conservative adjustment
                return StepResult.ok(data={"action": "maintain_current", "adjustment": 0.0})

        except Exception as e:
            logger.error(f"RL recommendation error: {e}")
            return StepResult.ok(data={"action": "maintain_current", "adjustment": 0.0})

    def _apply_personality_adjustment(
        self, current_traits: PersonalityTraits, action: dict[str, Any], context: PersonalityContext
    ) -> PersonalityTraits:
        """Apply personality adjustment based on RL action."""
        try:
            # Create copy of current traits
            new_traits = PersonalityTraits(
                humor=current_traits.humor,
                formality=current_traits.formality,
                enthusiasm=current_traits.enthusiasm,
                knowledge_confidence=current_traits.knowledge_confidence,
                debate_tolerance=current_traits.debate_tolerance,
                empathy=current_traits.empathy,
                creativity=current_traits.creativity,
                directness=current_traits.directness,
            )

            action_type = action.get("action", "maintain_current")
            adjustment = float(action.get("adjustment", 0.0))

            # Apply adjustments based on action type
            if action_type == "adjust_humor":
                new_traits.humor = self._clamp_trait(current_traits.humor + adjustment)
            elif action_type == "adjust_formality":
                new_traits.formality = self._clamp_trait(current_traits.formality + adjustment)
            elif action_type == "adjust_enthusiasm":
                new_traits.enthusiasm = self._clamp_trait(current_traits.enthusiasm + adjustment)
            elif action_type == "adjust_confidence":
                new_traits.knowledge_confidence = self._clamp_trait(current_traits.knowledge_confidence + adjustment)
            elif action_type == "adjust_empathy":
                new_traits.empathy = self._clamp_trait(current_traits.empathy + adjustment)

            # Context-based adjustments
            new_traits = self._apply_context_adjustments(new_traits, context)

            return new_traits

        except Exception as e:
            logger.error(f"Failed to apply personality adjustment: {e}")
            return current_traits

    def _apply_context_adjustments(self, traits: PersonalityTraits, context: PersonalityContext) -> PersonalityTraits:
        """Apply context-based personality adjustments."""
        try:
            # Adjust based on channel type
            if context.channel_type == "debate":
                traits.debate_tolerance = min(1.0, traits.debate_tolerance + 0.1)
                traits.directness = min(1.0, traits.directness + 0.05)
            elif context.channel_type == "support":
                traits.empathy = min(1.0, traits.empathy + 0.1)
                traits.formality = max(0.0, traits.formality - 0.05)

            # Adjust based on time of day
            if context.time_of_day in ["evening", "night"]:
                traits.enthusiasm = max(0.0, traits.enthusiasm - 0.05)
                traits.humor = min(1.0, traits.humor + 0.05)

            # Adjust based on message sentiment
            if context.message_sentiment < -0.5:  # Negative sentiment
                traits.empathy = min(1.0, traits.empathy + 0.1)
                traits.humor = max(0.0, traits.humor - 0.1)
            elif context.message_sentiment > 0.5:  # Positive sentiment
                traits.enthusiasm = min(1.0, traits.enthusiasm + 0.05)
                traits.humor = min(1.0, traits.humor + 0.05)

            # Adjust based on guild culture
            if context.guild_culture == "academic":
                traits.formality = min(1.0, traits.formality + 0.1)
                traits.knowledge_confidence = min(1.0, traits.knowledge_confidence + 0.05)
            elif context.guild_culture == "casual":
                traits.formality = max(0.0, traits.formality - 0.1)
                traits.humor = min(1.0, traits.humor + 0.1)

            return traits

        except Exception as e:
            logger.error(f"Failed to apply context adjustments: {e}")
            return traits

    def _clamp_trait(self, value: float) -> float:
        """Clamp trait value to [0, 1] range."""
        return max(0.0, min(1.0, value))

    async def _record_rl_feedback(self, context: PersonalityContext, action: dict[str, Any], reward: float) -> None:
        """Record RL feedback for learning."""
        try:
            # Record feedback in learning engine
            self.learning_engine.record(domain=self.rl_domain, context=context.to_dict(), action=action, reward=reward)

        except Exception as e:
            logger.error(f"Failed to record RL feedback: {e}")

    async def get_personality_summary(self, tenant: str, workspace: str) -> StepResult[dict[str, Any]]:
        """Get comprehensive personality summary."""
        try:
            # Calculate personality drift over time
            drift_analysis = self._analyze_personality_drift()

            # Get trait distribution statistics
            trait_stats = self._calculate_trait_statistics()

            # Get recent adaptation history
            recent_adaptations = self._get_recent_adaptations()

            summary = {
                "current_traits": self.current_traits.to_dict(),
                "trait_statistics": trait_stats,
                "personality_drift": drift_analysis,
                "recent_adaptations": recent_adaptations,
                "total_adaptations": len(self._personality_history),
                "rl_domain": self.rl_domain,
            }

            return StepResult.ok(data=summary)

        except Exception as e:
            logger.error(f"Failed to get personality summary: {e}")
            return StepResult.fail(f"Failed to get personality summary: {e!s}")

    def _analyze_personality_drift(self) -> dict[str, Any]:
        """Analyze how personality has drifted over time."""
        if len(self._personality_history) < 2:
            return {"drift_magnitude": 0.0, "drift_direction": "stable"}

        try:
            # Get initial and current traits
            initial_traits = self._personality_history[0][1]
            current_traits = self.current_traits

            # Calculate drift vector
            initial_vector = initial_traits.to_vector()
            current_vector = current_traits.to_vector()
            drift_vector = current_vector - initial_vector

            # Calculate drift magnitude
            drift_magnitude = float(np.linalg.norm(drift_vector))

            # Determine drift direction
            if drift_magnitude < 0.1:
                direction = "stable"
            elif drift_magnitude < 0.3:
                direction = "gradual"
            else:
                direction = "significant"

            # Identify which traits changed most
            trait_changes = {}
            trait_names = [
                "humor",
                "formality",
                "enthusiasm",
                "knowledge_confidence",
                "debate_tolerance",
                "empathy",
                "creativity",
                "directness",
            ]

            for i, trait_name in enumerate(trait_names):
                trait_changes[trait_name] = float(drift_vector[i])

            # Find trait with largest change
            max_change_trait = max(trait_changes.items(), key=lambda x: abs(x[1]))

            return {
                "drift_magnitude": drift_magnitude,
                "drift_direction": direction,
                "trait_changes": trait_changes,
                "max_change_trait": max_change_trait[0],
                "max_change_value": max_change_trait[1],
            }

        except Exception as e:
            logger.error(f"Failed to analyze personality drift: {e}")
            return {"drift_magnitude": 0.0, "drift_direction": "error"}

    def _calculate_trait_statistics(self) -> dict[str, Any]:
        """Calculate statistics for personality traits."""
        if not self._personality_history:
            return {}

        try:
            # Extract trait vectors
            trait_vectors = [traits.to_vector() for _, traits in self._personality_history]
            trait_matrix = np.array(trait_vectors)

            trait_names = [
                "humor",
                "formality",
                "enthusiasm",
                "knowledge_confidence",
                "debate_tolerance",
                "empathy",
                "creativity",
                "directness",
            ]

            stats = {}
            for i, trait_name in enumerate(trait_names):
                trait_values = trait_matrix[:, i]
                stats[trait_name] = {
                    "mean": float(np.mean(trait_values)),
                    "std": float(np.std(trait_values)),
                    "min": float(np.min(trait_values)),
                    "max": float(np.max(trait_values)),
                    "current": float(self.current_traits.to_vector()[i]),
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to calculate trait statistics: {e}")
            return {}

    def _get_recent_adaptations(self, count: int = 10) -> list[dict[str, Any]]:
        """Get recent personality adaptations."""
        try:
            recent = self._personality_history[-count:]

            adaptations = []
            for timestamp, traits in recent:
                adaptations.append({"timestamp": timestamp, "traits": traits.to_dict()})

            return adaptations

        except Exception as e:
            logger.error(f"Failed to get recent adaptations: {e}")
            return []
