"""
Unit tests for the reward computation system.
"""

import pytest

from discord.personality.reward_computer import (
    InteractionMetrics,
    RewardComputer,
    RewardSignal,
)


class TestInteractionMetrics:
    """Test InteractionMetrics class."""

    def test_interaction_metrics_creation(self):
        """Test InteractionMetrics object creation."""
        metrics = InteractionMetrics(
            message_id="msg123",
            user_id="user123",
            guild_id="guild123",
            timestamp=1640995200.0,
            user_replies=2,
            user_reactions=["👍", "❤️"],
            follow_up_messages=1,
            conversation_continuation=True,
            time_to_first_reply=30.0,
            conversation_duration=300.0,
            message_length=50,
            response_length=80,
        )

        assert metrics.message_id == "msg123"
        assert metrics.user_id == "user123"
        assert metrics.guild_id == "guild123"
        assert metrics.timestamp == 1640995200.0
        assert metrics.user_replies == 2
        assert metrics.user_reactions == ["👍", "❤️"]
        assert metrics.follow_up_messages == 1
        assert metrics.conversation_continuation is True
        assert metrics.time_to_first_reply == 30.0
        assert metrics.conversation_duration == 300.0
        assert metrics.message_length == 50
        assert metrics.response_length == 80

    def test_interaction_metrics_to_dict(self):
        """Test InteractionMetrics serialization."""
        metrics = InteractionMetrics(
            message_id="msg123",
            user_id="user123",
            guild_id="guild123",
            timestamp=1640995200.0,
            user_replies=1,
            user_reactions=["👍"],
            follow_up_messages=0,
            conversation_continuation=False,
            time_to_first_reply=60.0,
            conversation_duration=120.0,
            message_length=30,
            response_length=40,
        )

        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert metrics_dict["message_id"] == "msg123"
        assert metrics_dict["user_id"] == "user123"
        assert metrics_dict["guild_id"] == "guild123"
        assert metrics_dict["timestamp"] == 1640995200.0
        assert metrics_dict["user_replies"] == 1
        assert metrics_dict["user_reactions"] == ["👍"]
        assert metrics_dict["follow_up_messages"] == 0
        assert metrics_dict["conversation_continuation"] is False
        assert metrics_dict["time_to_first_reply"] == 60.0
        assert metrics_dict["conversation_duration"] == 120.0
        assert metrics_dict["message_length"] == 30
        assert metrics_dict["response_length"] == 40


class TestRewardSignal:
    """Test RewardSignal class."""

    def test_reward_signal_creation(self):
        """Test RewardSignal object creation."""
        signal = RewardSignal(
            total_reward=0.85,
            engagement_reward=0.8,
            reaction_reward=0.9,
            continuation_reward=0.7,
            temporal_reward=0.8,
            content_quality_reward=0.9,
            confidence=0.85,
            breakdown={"engagement": 0.8, "reactions": 0.9, "continuation": 0.7, "temporal": 0.8, "content": 0.9},
        )

        assert signal.total_reward == 0.85
        assert signal.engagement_reward == 0.8
        assert signal.reaction_reward == 0.9
        assert signal.continuation_reward == 0.7
        assert signal.temporal_reward == 0.8
        assert signal.content_quality_reward == 0.9
        assert signal.confidence == 0.85
        assert signal.breakdown["engagement"] == 0.8

    def test_reward_signal_to_dict(self):
        """Test RewardSignal serialization."""
        signal = RewardSignal(
            total_reward=0.75,
            engagement_reward=0.7,
            reaction_reward=0.8,
            continuation_reward=0.6,
            temporal_reward=0.7,
            content_quality_reward=0.8,
            confidence=0.75,
            breakdown={"engagement": 0.7, "reactions": 0.8, "continuation": 0.6, "temporal": 0.7, "content": 0.8},
        )

        signal_dict = signal.to_dict()

        assert isinstance(signal_dict, dict)
        assert signal_dict["total_reward"] == 0.75
        assert signal_dict["engagement_reward"] == 0.7
        assert signal_dict["reaction_reward"] == 0.8
        assert signal_dict["continuation_reward"] == 0.6
        assert signal_dict["temporal_reward"] == 0.7
        assert signal_dict["content_quality_reward"] == 0.8
        assert signal_dict["confidence"] == 0.75
        assert signal_dict["breakdown"]["engagement"] == 0.7


class TestRewardWeights:
    """Test RewardWeights class."""

    def test_default_reward_weights(self):
        """Test default reward weights."""
        weights = RewardWeights()

        assert weights.engagement == 0.3
        assert weights.reactions == 0.25
        assert weights.continuation == 0.2
        assert weights.temporal == 0.15
        assert weights.content_quality == 0.1

    def test_custom_reward_weights(self):
        """Test custom reward weights."""
        weights = RewardWeights(engagement=0.4, reactions=0.3, continuation=0.2, temporal=0.05, content_quality=0.05)

        assert weights.engagement == 0.4
        assert weights.reactions == 0.3
        assert weights.continuation == 0.2
        assert weights.temporal == 0.05
        assert weights.content_quality == 0.05

    def test_reward_weights_normalization(self):
        """Test reward weights normalization."""
        weights = RewardWeights(engagement=0.5, reactions=0.3, continuation=0.2, temporal=0.1, content_quality=0.1)

        normalized = weights.normalize()

        # Should sum to 1.0
        total = (
            normalized.engagement
            + normalized.reactions
            + normalized.continuation
            + normalized.temporal
            + normalized.content_quality
        )
        assert abs(total - 1.0) < 0.001


class TestRewardThresholds:
    """Test RewardThresholds class."""

    def test_default_reward_thresholds(self):
        """Test default reward thresholds."""
        thresholds = RewardThresholds()

        assert thresholds.excellent == 0.8
        assert thresholds.good == 0.6
        assert thresholds.average == 0.4
        assert thresholds.poor == 0.2

    def test_custom_reward_thresholds(self):
        """Test custom reward thresholds."""
        thresholds = RewardThresholds(excellent=0.9, good=0.7, average=0.5, poor=0.3)

        assert thresholds.excellent == 0.9
        assert thresholds.good == 0.7
        assert thresholds.average == 0.5
        assert thresholds.poor == 0.3


class TestRewardComputer:
    """Test RewardComputer class."""

    @pytest.fixture
    def reward_computer(self):
        """Create RewardComputer instance."""
        return RewardComputer()

    @pytest.fixture
    def sample_metrics_high_engagement(self):
        """Sample metrics with high engagement."""
        return InteractionMetrics(
            message_id="msg123",
            user_id="user123",
            guild_id="guild123",
            timestamp=1640995200.0,
            user_replies=3,
            user_reactions=["👍", "❤️", "🔥"],
            follow_up_messages=2,
            conversation_continuation=True,
            time_to_first_reply=15.0,
            conversation_duration=600.0,
            message_length=80,
            response_length=120,
        )

    @pytest.fixture
    def sample_metrics_low_engagement(self):
        """Sample metrics with low engagement."""
        return InteractionMetrics(
            message_id="msg456",
            user_id="user456",
            guild_id="guild456",
            timestamp=1640995200.0,
            user_replies=0,
            user_reactions=[],
            follow_up_messages=0,
            conversation_continuation=False,
            time_to_first_reply=300.0,
            conversation_duration=60.0,
            message_length=10,
            response_length=5,
        )

    @pytest.fixture
    def sample_metrics_medium_engagement(self):
        """Sample metrics with medium engagement."""
        return InteractionMetrics(
            message_id="msg789",
            user_id="user789",
            guild_id="guild789",
            timestamp=1640995200.0,
            user_replies=1,
            user_reactions=["👍"],
            follow_up_messages=1,
            conversation_continuation=True,
            time_to_first_reply=120.0,
            conversation_duration=300.0,
            message_length=40,
            response_length=60,
        )

    def test_engagement_reward_calculation_high(self, reward_computer, sample_metrics_high_engagement):
        """Test engagement reward calculation with high engagement."""
        reward = reward_computer._compute_engagement_reward(sample_metrics_high_engagement)

        assert 0.0 <= reward <= 1.0
        assert reward > 0.7  # Should be high for good engagement

    def test_engagement_reward_calculation_low(self, reward_computer, sample_metrics_low_engagement):
        """Test engagement reward calculation with low engagement."""
        reward = reward_computer._compute_engagement_reward(sample_metrics_low_engagement)

        assert 0.0 <= reward <= 1.0
        assert reward < 0.3  # Should be low for poor engagement

    def test_reaction_reward_calculation_positive(self, reward_computer):
        """Test reaction reward calculation with positive reactions."""
        metrics = InteractionMetrics(
            message_id="msg123",
            user_id="user123",
            guild_id="guild123",
            timestamp=1640995200.0,
            user_replies=0,
            user_reactions=["👍", "❤️", "🔥"],
            follow_up_messages=0,
            conversation_continuation=False,
            time_to_first_reply=0.0,
            conversation_duration=0.0,
            message_length=0,
            response_length=0,
        )

        reward = reward_computer._compute_reaction_reward(metrics)

        assert 0.0 <= reward <= 1.0
        assert reward > 0.8  # Should be high for positive reactions

    def test_reaction_reward_calculation_negative(self, reward_computer):
        """Test reaction reward calculation with negative reactions."""
        metrics = InteractionMetrics(
            message_id="msg123",
            user_id="user123",
            guild_id="guild123",
            timestamp=1640995200.0,
            user_replies=0,
            user_reactions=["👎", "😠"],
            follow_up_messages=0,
            conversation_continuation=False,
            time_to_first_reply=0.0,
            conversation_duration=0.0,
            message_length=0,
            response_length=0,
        )

        reward = reward_computer._compute_reaction_reward(metrics)

        assert 0.0 <= reward <= 1.0
        assert reward < 0.2  # Should be low for negative reactions

    def test_reaction_reward_calculation_mixed(self, reward_computer):
        """Test reaction reward calculation with mixed reactions."""
        metrics = InteractionMetrics(
            message_id="msg123",
            user_id="user123",
            guild_id="guild123",
            timestamp=1640995200.0,
            user_replies=0,
            user_reactions=["👍", "👎"],
            follow_up_messages=0,
            conversation_continuation=False,
            time_to_first_reply=0.0,
            conversation_duration=0.0,
            message_length=0,
            response_length=0,
        )

        reward = reward_computer._compute_reaction_reward(metrics)

        assert 0.0 <= reward <= 1.0
        assert 0.3 < reward < 0.7  # Should be medium for mixed reactions

    def test_continuation_reward_calculation_good(self, reward_computer, sample_metrics_high_engagement):
        """Test continuation reward calculation with good continuation."""
        reward = reward_computer._compute_continuation_reward(sample_metrics_high_engagement)

        assert 0.0 <= reward <= 1.0
        assert reward > 0.6  # Should be good for quick reply and continuation

    def test_continuation_reward_calculation_poor(self, reward_computer, sample_metrics_low_engagement):
        """Test continuation reward calculation with poor continuation."""
        reward = reward_computer._compute_continuation_reward(sample_metrics_low_engagement)

        assert 0.0 <= reward <= 1.0
        assert reward < 0.4  # Should be poor for slow/no reply

    def test_temporal_reward_calculation(self, reward_computer):
        """Test temporal reward calculation."""
        # Test good temporal pattern (quick reply, good duration)
        metrics_good = InteractionMetrics(
            message_id="msg123",
            user_id="user123",
            guild_id="guild123",
            timestamp=1640995200.0,
            user_replies=0,
            user_reactions=[],
            follow_up_messages=0,
            conversation_continuation=False,
            time_to_first_reply=30.0,  # Quick reply
            conversation_duration=300.0,  # Good duration
            message_length=0,
            response_length=0,
        )

        reward_good = reward_computer._compute_temporal_reward(metrics_good)

        # Test poor temporal pattern (slow reply, short duration)
        metrics_poor = InteractionMetrics(
            message_id="msg456",
            user_id="user456",
            guild_id="guild456",
            timestamp=1640995200.0,
            user_replies=0,
            user_reactions=[],
            follow_up_messages=0,
            conversation_continuation=False,
            time_to_first_reply=600.0,  # Slow reply
            conversation_duration=30.0,  # Short duration
            message_length=0,
            response_length=0,
        )

        reward_poor = reward_computer._compute_temporal_reward(metrics_poor)

        assert 0.0 <= reward_good <= 1.0
        assert 0.0 <= reward_poor <= 1.0
        assert reward_good > reward_poor  # Good pattern should score higher

    def test_content_quality_reward_calculation(self, reward_computer):
        """Test content quality reward calculation."""
        # Test good content quality (appropriate lengths)
        metrics_good = InteractionMetrics(
            message_id="msg123",
            user_id="user123",
            guild_id="guild123",
            timestamp=1640995200.0,
            user_replies=0,
            user_reactions=[],
            follow_up_messages=0,
            conversation_continuation=False,
            time_to_first_reply=0.0,
            conversation_duration=0.0,
            message_length=50,  # Good message length
            response_length=80,  # Good response length
        )

        reward_good = reward_computer._compute_content_quality_reward(metrics_good)

        # Test poor content quality (too short)
        metrics_poor = InteractionMetrics(
            message_id="msg456",
            user_id="user456",
            guild_id="guild456",
            timestamp=1640995200.0,
            user_replies=0,
            user_reactions=[],
            follow_up_messages=0,
            conversation_continuation=False,
            time_to_first_reply=0.0,
            conversation_duration=0.0,
            message_length=5,  # Too short
            response_length=10,  # Too short
        )

        reward_poor = reward_computer._compute_content_quality_reward(metrics_poor)

        assert 0.0 <= reward_good <= 1.0
        assert 0.0 <= reward_poor <= 1.0
        assert reward_good > reward_poor  # Good content should score higher

    def test_confidence_calculation(self, reward_computer, sample_metrics_high_engagement):
        """Test confidence calculation."""
        confidence = reward_computer._compute_confidence(sample_metrics_high_engagement)

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should have good confidence with comprehensive metrics

    def test_confidence_calculation_minimal_data(self, reward_computer, sample_metrics_low_engagement):
        """Test confidence calculation with minimal data."""
        confidence = reward_computer._compute_confidence(sample_metrics_low_engagement)

        assert 0.0 <= confidence <= 1.0
        assert confidence < 0.5  # Should have lower confidence with minimal data

    @pytest.mark.asyncio
    async def test_complete_reward_computation_high(self, reward_computer, sample_metrics_high_engagement):
        """Test complete reward computation with high engagement."""
        result = await reward_computer.compute_reward(sample_metrics_high_engagement)

        assert result.success is True
        assert isinstance(result.data, RewardSignal)
        assert 0.0 <= result.data.total_reward <= 1.0
        assert result.data.total_reward > 0.7  # Should be high
        assert 0.0 <= result.data.confidence <= 1.0
        assert result.data.confidence > 0.7  # Should have good confidence

    @pytest.mark.asyncio
    async def test_complete_reward_computation_low(self, reward_computer, sample_metrics_low_engagement):
        """Test complete reward computation with low engagement."""
        result = await reward_computer.compute_reward(sample_metrics_low_engagement)

        assert result.success is True
        assert isinstance(result.data, RewardSignal)
        assert 0.0 <= result.data.total_reward <= 1.0
        assert result.data.total_reward < 0.3  # Should be low
        assert 0.0 <= result.data.confidence <= 1.0
        assert result.data.confidence < 0.5  # Should have lower confidence

    @pytest.mark.asyncio
    async def test_complete_reward_computation_medium(self, reward_computer, sample_metrics_medium_engagement):
        """Test complete reward computation with medium engagement."""
        result = await reward_computer.compute_reward(sample_metrics_medium_engagement)

        assert result.success is True
        assert isinstance(result.data, RewardSignal)
        assert 0.0 <= result.data.total_reward <= 1.0
        assert 0.3 <= result.data.total_reward <= 0.7  # Should be medium
        assert 0.0 <= result.data.confidence <= 1.0
        assert 0.4 <= result.data.confidence <= 0.8  # Should have medium confidence

    def test_reward_breakdown_calculation(self, reward_computer, sample_metrics_high_engagement):
        """Test reward breakdown calculation."""
        breakdown = reward_computer._calculate_reward_breakdown(sample_metrics_high_engagement)

        assert isinstance(breakdown, dict)
        assert "engagement" in breakdown
        assert "reactions" in breakdown
        assert "continuation" in breakdown
        assert "temporal" in breakdown
        assert "content" in breakdown

        # All breakdown values should be between 0 and 1
        for value in breakdown.values():
            assert 0.0 <= value <= 1.0

    def test_weighted_reward_calculation(self, reward_computer):
        """Test weighted reward calculation."""
        breakdown = {"engagement": 0.8, "reactions": 0.9, "continuation": 0.7, "temporal": 0.6, "content": 0.8}

        weighted_reward = reward_computer._calculate_weighted_reward(breakdown)

        assert 0.0 <= weighted_reward <= 1.0
        # Should be close to weighted average
        assert 0.7 <= weighted_reward <= 0.8

    def test_reward_categorization(self, reward_computer):
        """Test reward categorization."""
        # Test different reward levels
        assert reward_computer._categorize_reward(0.9) == "excellent"
        assert reward_computer._categorize_reward(0.7) == "good"
        assert reward_computer._categorize_reward(0.5) == "average"
        assert reward_computer._categorize_reward(0.3) == "poor"
        assert reward_computer._categorize_reward(0.1) == "poor"

    def test_positive_reaction_detection(self, reward_computer):
        """Test positive reaction detection."""
        positive_reactions = ["👍", "❤️", "🔥", "🎉", "👏", "💯", "✅", "🌟", "🚀", "💪"]

        for reaction in positive_reactions:
            assert reward_computer._is_positive_reaction(reaction) is True

    def test_negative_reaction_detection(self, reward_computer):
        """Test negative reaction detection."""
        negative_reactions = ["👎", "😠", "😞", "😢", "😡", "🤮", "💩", "❌", "🚫"]

        for reaction in negative_reactions:
            assert reward_computer._is_negative_reaction(reaction) is True

    def test_neutral_reaction_detection(self, reward_computer):
        """Test neutral reaction detection."""
        neutral_reactions = ["🤔", "😐", "😑", "🙄", "😶", "🤷", "🤨"]

        for reaction in neutral_reactions:
            assert reward_computer._is_neutral_reaction(reaction) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
