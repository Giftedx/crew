"""
Unit tests for the personality management system.
"""

from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from discord.personality.personality_manager import (
    PersonalityContext,
    PersonalityStateManager,
    PersonalityTraits,
)


class TestPersonalityTraits:
    """Test PersonalityTraits class."""

    def test_default_traits_creation(self):
        """Test default personality traits creation."""
        traits = PersonalityTraits()

        assert traits.humor == 0.5
        assert traits.formality == 0.5
        assert traits.enthusiasm == 0.7
        assert traits.knowledge_confidence == 0.8
        assert traits.debate_tolerance == 0.6
        assert traits.empathy == 0.7
        assert traits.creativity == 0.6
        assert traits.directness == 0.7

    def test_custom_traits_creation(self):
        """Test custom personality traits creation."""
        traits = PersonalityTraits(
            humor=0.9,
            formality=0.2,
            enthusiasm=0.95,
            knowledge_confidence=0.85,
            debate_tolerance=0.3,
            empathy=0.8,
            creativity=0.9,
            directness=0.6,
        )

        assert traits.humor == 0.9
        assert traits.formality == 0.2
        assert traits.enthusiasm == 0.95
        assert traits.knowledge_confidence == 0.85
        assert traits.debate_tolerance == 0.3
        assert traits.empathy == 0.8
        assert traits.creativity == 0.9
        assert traits.directness == 0.6

    def test_traits_clamping(self):
        """Test that traits are clamped to valid range."""
        traits = PersonalityTraits(
            humor=1.5,  # Should be clamped to 1.0
            formality=-0.5,  # Should be clamped to 0.0
            enthusiasm=0.8,
            knowledge_confidence=0.9,
            debate_tolerance=0.7,
            empathy=0.6,
            creativity=0.8,
            directness=0.7,
        )

        assert traits.humor == 1.0
        assert traits.formality == 0.0
        assert traits.enthusiasm == 0.8

    def test_traits_to_vector(self):
        """Test conversion of traits to vector."""
        traits = PersonalityTraits(
            humor=0.8,
            formality=0.3,
            enthusiasm=0.9,
            knowledge_confidence=0.85,
            debate_tolerance=0.4,
            empathy=0.7,
            creativity=0.8,
            directness=0.6,
        )

        vector = traits.to_vector()

        assert isinstance(vector, np.ndarray)
        assert len(vector) == 8
        assert vector[0] == 0.8  # humor
        assert vector[1] == 0.3  # formality
        assert vector[2] == 0.9  # enthusiasm
        assert vector[3] == 0.85  # knowledge_confidence
        assert vector[4] == 0.4  # debate_tolerance
        assert vector[5] == 0.7  # empathy
        assert vector[6] == 0.8  # creativity
        assert vector[7] == 0.6  # directness

    def test_traits_from_vector(self):
        """Test creation of traits from vector."""
        vector = np.array([0.8, 0.3, 0.9, 0.85, 0.4, 0.7, 0.8, 0.6])

        traits = PersonalityTraits.from_vector(vector)

        assert traits.humor == 0.8
        assert traits.formality == 0.3
        assert traits.enthusiasm == 0.9
        assert traits.knowledge_confidence == 0.85
        assert traits.debate_tolerance == 0.4
        assert traits.empathy == 0.7
        assert traits.creativity == 0.8
        assert traits.directness == 0.6

    def test_traits_from_dict(self):
        """Test creation of traits from dictionary."""
        data = {
            "humor": 0.9,
            "formality": 0.2,
            "enthusiasm": 0.95,
            "knowledge_confidence": 0.85,
            "debate_tolerance": 0.3,
            "empathy": 0.8,
            "creativity": 0.9,
            "directness": 0.6,
        }

        traits = PersonalityTraits.from_dict(data)

        assert traits.humor == 0.9
        assert traits.formality == 0.2
        assert traits.enthusiasm == 0.95
        assert traits.knowledge_confidence == 0.85
        assert traits.debate_tolerance == 0.3
        assert traits.empathy == 0.8
        assert traits.creativity == 0.9
        assert traits.directness == 0.6

    def test_traits_to_dict(self):
        """Test conversion of traits to dictionary."""
        traits = PersonalityTraits(
            humor=0.8,
            formality=0.3,
            enthusiasm=0.9,
            knowledge_confidence=0.85,
            debate_tolerance=0.4,
            empathy=0.7,
            creativity=0.8,
            directness=0.6,
        )

        traits_dict = traits.to_dict()

        assert isinstance(traits_dict, dict)
        assert traits_dict["humor"] == 0.8
        assert traits_dict["formality"] == 0.3
        assert traits_dict["enthusiasm"] == 0.9
        assert traits_dict["knowledge_confidence"] == 0.85
        assert traits_dict["debate_tolerance"] == 0.4
        assert traits_dict["empathy"] == 0.7
        assert traits_dict["creativity"] == 0.8
        assert traits_dict["directness"] == 0.6

    def test_traits_equality(self):
        """Test traits equality comparison."""
        traits1 = PersonalityTraits(humor=0.8, formality=0.3)
        traits2 = PersonalityTraits(humor=0.8, formality=0.3)
        traits3 = PersonalityTraits(humor=0.7, formality=0.3)

        assert traits1 == traits2
        assert traits1 != traits3

    def test_traits_hash(self):
        """Test traits hashing."""
        traits = PersonalityTraits(humor=0.8, formality=0.3)

        # Should be hashable
        hash(traits)


class TestPersonalityContext:
    """Test PersonalityContext class."""

    def test_personality_context_creation(self):
        """Test PersonalityContext creation."""
        context = PersonalityContext(
            channel_type="casual",
            time_of_day="afternoon",
            user_history=[],
            message_sentiment=0.5,
            conversation_length=5,
            guild_culture="gaming",
        )

        assert context.channel_type == "casual"
        assert context.time_of_day == "afternoon"
        assert context.user_history == []
        assert context.message_sentiment == 0.5
        assert context.conversation_length == 5
        assert context.guild_culture == "gaming"

    def test_personality_context_to_dict(self):
        """Test PersonalityContext serialization."""
        context = PersonalityContext(
            channel_type="casual",
            time_of_day="afternoon",
            user_history=[{"interaction": "previous"}],
            message_sentiment=0.5,
            conversation_length=5,
            guild_culture="gaming",
        )

        context_dict = context.to_dict()

        assert isinstance(context_dict, dict)
        assert context_dict["channel_type"] == "casual"
        assert context_dict["time_of_day"] == "afternoon"
        assert context_dict["message_sentiment"] == 0.5
        assert context_dict["conversation_length"] == 5
        assert context_dict["guild_culture"] == "gaming"


class TestPersonalityMetrics:
    """Test PersonalityMetrics class."""

    def test_personality_metrics_creation(self):
        """Test PersonalityMetrics creation."""
        metrics = PersonalityMetrics(
            adaptation_count=10,
            last_adaptation=1640995200.0,
            success_rate=0.85,
            engagement_score=0.9,
            user_satisfaction=0.8,
        )

        assert metrics.adaptation_count == 10
        assert metrics.last_adaptation == 1640995200.0
        assert metrics.success_rate == 0.85
        assert metrics.engagement_score == 0.9
        assert metrics.user_satisfaction == 0.8

    def test_personality_metrics_to_dict(self):
        """Test PersonalityMetrics serialization."""
        metrics = PersonalityMetrics(
            adaptation_count=5,
            last_adaptation=1640995200.0,
            success_rate=0.75,
            engagement_score=0.8,
            user_satisfaction=0.7,
        )

        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert metrics_dict["adaptation_count"] == 5
        assert metrics_dict["last_adaptation"] == 1640995200.0
        assert metrics_dict["success_rate"] == 0.75
        assert metrics_dict["engagement_score"] == 0.8
        assert metrics_dict["user_satisfaction"] == 0.7


class TestPersonalityStateManager:
    """Test PersonalityStateManager class."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        memory_service = AsyncMock()
        learning_engine = MagicMock()

        return memory_service, learning_engine

    @pytest.fixture
    def personality_manager(self, mock_services):
        """Create PersonalityStateManager instance."""
        memory_service, learning_engine = mock_services
        return PersonalityStateManager(memory_service, learning_engine)

    def test_default_personality_loading(self, personality_manager):
        """Test loading default personality."""
        traits = personality_manager._load_default_personality()

        assert isinstance(traits, PersonalityTraits)
        assert traits.humor == 0.5
        assert traits.formality == 0.5
        assert traits.enthusiasm == 0.7

    def test_personality_adaptation_algorithm(self, personality_manager):
        """Test personality adaptation algorithm."""
        current_traits = PersonalityTraits(
            humor=0.5,
            formality=0.5,
            enthusiasm=0.7,
            knowledge_confidence=0.8,
            debate_tolerance=0.6,
            empathy=0.7,
            creativity=0.6,
            directness=0.7,
        )

        context = PersonalityContext(
            channel_type="casual",
            time_of_day="evening",
            user_history=[],
            message_sentiment=0.8,
            conversation_length=3,
            guild_culture="gaming",
        )

        reward = 0.9

        adapted_traits = personality_manager._adapt_personality_algorithm(current_traits, context, reward)

        assert isinstance(adapted_traits, PersonalityTraits)
        # Should have some changes based on the algorithm
        assert adapted_traits != current_traits

    def test_personality_adaptation_with_positive_reward(self, personality_manager):
        """Test personality adaptation with positive reward."""
        current_traits = PersonalityTraits(humor=0.5, formality=0.5)
        context = PersonalityContext(
            channel_type="casual",
            time_of_day="afternoon",
            user_history=[],
            message_sentiment=0.8,
            conversation_length=2,
            guild_culture="casual",
        )

        # High positive reward should increase humor in casual context
        adapted_traits = personality_manager._adapt_personality_algorithm(current_traits, context, 0.9)

        # In casual context with positive reward, humor might increase
        assert adapted_traits.humor >= current_traits.humor

    def test_personality_adaptation_with_negative_reward(self, personality_manager):
        """Test personality adaptation with negative reward."""
        current_traits = PersonalityTraits(humor=0.8, formality=0.3)
        context = PersonalityContext(
            channel_type="formal",
            time_of_day="morning",
            user_history=[],
            message_sentiment=-0.5,
            conversation_length=1,
            guild_culture="professional",
        )

        # Negative reward in formal context should reduce humor
        adapted_traits = personality_manager._adapt_personality_algorithm(current_traits, context, -0.5)

        # In formal context with negative reward, humor might decrease
        assert adapted_traits.humor <= current_traits.humor

    @pytest.mark.asyncio
    async def test_personality_loading_from_memory(self, personality_manager):
        """Test loading personality from memory."""
        # Mock memory service response
        personality_manager.memory_service.search_memories.return_value = AsyncMock(
            success=True,
            data={
                "memories": [
                    {
                        "metadata": {
                            "traits": {
                                "humor": 0.8,
                                "formality": 0.3,
                                "enthusiasm": 0.9,
                                "knowledge_confidence": 0.85,
                                "debate_tolerance": 0.4,
                                "empathy": 0.7,
                                "creativity": 0.8,
                                "directness": 0.6,
                            }
                        }
                    }
                ]
            },
        )

        result = await personality_manager.load_personality("tenant", "workspace")

        assert result.success is True
        assert isinstance(result.data, PersonalityTraits)
        assert result.data.humor == 0.8
        assert result.data.formality == 0.3

    @pytest.mark.asyncio
    async def test_personality_loading_default_on_failure(self, personality_manager):
        """Test loading default personality when memory fails."""
        # Mock memory service failure
        personality_manager.memory_service.search_memories.return_value = AsyncMock(
            success=False, error="Memory service unavailable"
        )

        result = await personality_manager.load_personality("tenant", "workspace")

        assert result.success is True  # Should fallback to default
        assert isinstance(result.data, PersonalityTraits)
        assert result.data.humor == 0.5  # Default value

    @pytest.mark.asyncio
    async def test_personality_saving(self, personality_manager):
        """Test saving personality to memory."""
        traits = PersonalityTraits(
            humor=0.8,
            formality=0.3,
            enthusiasm=0.9,
            knowledge_confidence=0.85,
            debate_tolerance=0.4,
            empathy=0.7,
            creativity=0.8,
            directness=0.6,
        )

        # Mock memory service
        personality_manager.memory_service.store_memory.return_value = AsyncMock(
            success=True, data={"memory_id": "mem123"}
        )

        result = await personality_manager.save_personality(traits, "tenant", "workspace")

        assert result.success is True
        assert result.data["action"] == "personality_saved"
        assert result.data["memory_id"] == "mem123"

    @pytest.mark.asyncio
    async def test_personality_adaptation_workflow(self, personality_manager):
        """Test complete personality adaptation workflow."""
        # Mock RL recommendation
        personality_manager._get_rl_recommendation = AsyncMock(
            return_value=AsyncMock(success=True, data={"action": "adjust_humor", "adjustment": 0.1})
        )

        # Mock memory service
        personality_manager.memory_service.store_memory = AsyncMock(
            return_value=AsyncMock(success=True, data={"memory_id": "mem123"})
        )

        context = PersonalityContext(
            channel_type="casual",
            time_of_day="afternoon",
            user_history=[],
            message_sentiment=0.8,
            conversation_length=3,
            guild_culture="gaming",
        )

        result = await personality_manager.adapt_personality(
            context=context, reward=0.8, tenant="tenant", workspace="workspace"
        )

        assert result.success is True
        assert isinstance(result.data, PersonalityTraits)

    def test_personality_consistency_check(self, personality_manager):
        """Test personality consistency validation."""
        # Valid traits
        valid_traits = PersonalityTraits(
            humor=0.5,
            formality=0.5,
            enthusiasm=0.7,
            knowledge_confidence=0.8,
            debate_tolerance=0.6,
            empathy=0.7,
            creativity=0.6,
            directness=0.7,
        )

        is_consistent = personality_manager._validate_personality_consistency(valid_traits)
        assert is_consistent is True

        # Invalid traits (extreme values)
        invalid_traits = PersonalityTraits(
            humor=2.0,  # Invalid range
            formality=-1.0,  # Invalid range
            enthusiasm=0.7,
            knowledge_confidence=0.8,
            debate_tolerance=0.6,
            empathy=0.7,
            creativity=0.6,
            directness=0.7,
        )

        is_consistent = personality_manager._validate_personality_consistency(invalid_traits)
        assert is_consistent is False

    def test_personality_trait_bounds(self, personality_manager):
        """Test personality trait bounds validation."""
        # Test normal bounds
        traits = PersonalityTraits(humor=0.5, formality=0.5)
        bounds_ok = personality_manager._check_trait_bounds(traits)
        assert bounds_ok is True

        # Test out of bounds
        traits = PersonalityTraits(humor=1.5, formality=-0.5)
        bounds_ok = personality_manager._check_trait_bounds(traits)
        assert bounds_ok is False

    @pytest.mark.asyncio
    async def test_rl_recommendation_integration(self, personality_manager):
        """Test RL recommendation integration."""
        # Mock learning engine
        personality_manager.learning_engine.get_recommendation = MagicMock(
            return_value={"action": "adjust_enthusiasm", "adjustment": 0.05}
        )

        context = PersonalityContext(
            channel_type="casual",
            time_of_day="afternoon",
            user_history=[],
            message_sentiment=0.8,
            conversation_length=3,
            guild_culture="gaming",
        )

        result = await personality_manager._get_rl_recommendation(context, 0.8)

        assert result.success is True
        assert result.data["action"] == "adjust_enthusiasm"
        assert result.data["adjustment"] == 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
