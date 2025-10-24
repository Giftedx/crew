"""
Comprehensive test suite for Discord AI integration components.

This module tests all Discord AI functionality including message evaluation,
personality management, reward computation, and conversational pipeline.
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from performance_optimization.src.discord.conversational_pipeline import ConversationalPipeline, PipelineContext
from performance_optimization.src.discord.mcp_integration import MCPIntegrationLayer

# Import the Discord AI components
from performance_optimization.src.discord.message_evaluator import EvaluationResult, MessageContext, MessageEvaluator
from performance_optimization.src.discord.opt_in_manager import OptInManager
from performance_optimization.src.discord.personality.personality_manager import (
    PersonalityContext,
    PersonalityStateManager,
    PersonalityTraits,
)
from performance_optimization.src.discord.personality.reward_computer import (
    InteractionMetrics,
    RewardComputer,
    RewardSignal,
)


class TestMessageEvaluator:
    """Test suite for message evaluation system."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        routing_manager = AsyncMock()
        prompt_engine = AsyncMock()
        memory_service = AsyncMock()

        return routing_manager, prompt_engine, memory_service

    @pytest.fixture
    def message_evaluator(self, mock_services):
        """Create message evaluator instance."""
        routing_manager, prompt_engine, memory_service = mock_services
        return MessageEvaluator(routing_manager, prompt_engine, memory_service)

    @pytest.fixture
    def sample_message_data(self):
        """Sample Discord message data for testing."""
        return {
            "id": "123456789",
            "channel_id": "987654321",
            "guild_id": "111222333",
            "author": {"id": "444555666", "username": "testuser"},
            "content": "Hello bot, how are you today?",
            "timestamp": 1640995200.0,
        }

    @pytest.fixture
    def sample_recent_messages(self):
        """Sample recent messages for context."""
        return [
            {"author": {"username": "user1"}, "content": "Previous message 1"},
            {"author": {"username": "user2"}, "content": "Previous message 2"},
        ]

    @pytest.mark.asyncio
    async def test_message_context_building(self, message_evaluator, sample_message_data, sample_recent_messages):
        """Test message context building."""
        # Mock memory service response
        message_evaluator.memory_service.search_memories.return_value = AsyncMock(success=True, data={"memories": []})

        context = await message_evaluator.context_builder.build_context(
            sample_message_data, sample_recent_messages, True
        )

        assert isinstance(context, MessageContext)
        assert context.message_id == "123456789"
        assert context.user_id == "444555666"
        assert context.guild_id == "111222333"
        assert context.user_opt_in_status is True
        assert len(context.recent_messages) == 2

    @pytest.mark.asyncio
    async def test_direct_mention_detection(self, message_evaluator, sample_message_data):
        """Test direct mention detection."""
        context_builder = message_evaluator.context_builder

        # Test direct mention
        is_mention = context_builder._check_direct_mention("@bot help me", sample_message_data)
        assert is_mention is True

        # Test non-mention
        is_mention = context_builder._check_direct_mention("regular message", sample_message_data)
        assert is_mention is False

    @pytest.mark.asyncio
    async def test_message_evaluation_process(self, message_evaluator, sample_message_data, sample_recent_messages):
        """Test complete message evaluation process."""
        # Mock all service responses
        message_evaluator.routing_manager.suggest_model.return_value = AsyncMock(
            success=True, data={"model": "gpt-4o-mini"}
        )

        message_evaluator.prompt_engine.generate_response.return_value = AsyncMock(
            success=True,
            data='{"should_respond": true, "confidence": 0.8, "reasoning": "Direct mention", "priority": "high", "suggested_personality_traits": {"humor": 0.5, "formality": 0.3, "enthusiasm": 0.7, "knowledge_confidence": 0.8, "debate_tolerance": 0.6}, "context_relevance_score": 0.9}',
        )

        message_evaluator.memory_service.search_memories.return_value = AsyncMock(success=True, data={"memories": []})

        result = await message_evaluator.evaluate_discord_message(sample_message_data, sample_recent_messages, True)

        assert result.success is True
        assert isinstance(result.data, EvaluationResult)
        assert result.data.should_respond is True
        assert result.data.confidence == 0.8


class TestOptInManager:
    """Test suite for opt-in management system."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        yield db_path

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def opt_in_manager(self, temp_db):
        """Create opt-in manager instance."""
        return OptInManager(db_path=temp_db)

    @pytest.mark.asyncio
    async def test_user_opt_in(self, opt_in_manager):
        """Test user opt-in process."""
        result = await opt_in_manager.opt_in_user(user_id="123", username="testuser", guild_id="guild123")

        assert result.success is True
        assert result.data["action"] in ["created", "updated"]
        assert result.data["user_id"] == "123"

    @pytest.mark.asyncio
    async def test_user_opt_out(self, opt_in_manager):
        """Test user opt-out process."""
        # First opt in
        await opt_in_manager.opt_in_user("123", "testuser", "guild123")

        # Then opt out
        result = await opt_in_manager.opt_out_user("123", "guild123")

        assert result.success is True
        assert result.data["action"] == "opted_out"

    @pytest.mark.asyncio
    async def test_user_status_check(self, opt_in_manager):
        """Test user status checking."""
        # Check non-existent user
        result = await opt_in_manager.get_user_status("nonexistent", "guild123")
        assert result.success is True
        assert result.data["opted_in"] is False

        # Opt in and check status
        await opt_in_manager.opt_in_user("123", "testuser", "guild123")
        result = await opt_in_manager.get_user_status("123", "guild123")

        assert result.success is True
        assert result.data["opted_in"] is True
        assert result.data["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_interaction_recording(self, opt_in_manager):
        """Test interaction recording."""
        await opt_in_manager.opt_in_user("123", "testuser", "guild123")

        result = await opt_in_manager.record_interaction(
            user_id="123",
            guild_id="guild123",
            message_id="msg123",
            interaction_type="ai_response",
            content="Hello bot",
            bot_response="Hi there!",
        )

        assert result.success is True
        assert result.data["action"] == "interaction_recorded"


class TestPersonalityManager:
    """Test suite for personality management system."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        memory_service = AsyncMock()
        learning_engine = MagicMock()

        return memory_service, learning_engine

    @pytest.fixture
    def personality_manager(self, mock_services):
        """Create personality manager instance."""
        memory_service, learning_engine = mock_services
        return PersonalityStateManager(memory_service, learning_engine)

    def test_personality_traits_creation(self):
        """Test personality traits creation and manipulation."""
        traits = PersonalityTraits()

        assert traits.humor == 0.5
        assert traits.formality == 0.5
        assert traits.enthusiasm == 0.7

        # Test vector conversion
        vector = traits.to_vector()
        assert len(vector) == 8

        # Test from vector
        new_traits = PersonalityTraits.from_vector(vector)
        assert new_traits.humor == traits.humor

    def test_personality_traits_from_dict(self):
        """Test personality traits creation from dictionary."""
        data = {
            "humor": 0.8,
            "formality": 0.3,
            "enthusiasm": 0.9,
            "knowledge_confidence": 0.95,
            "debate_tolerance": 0.4,
            "empathy": 0.7,
            "creativity": 0.6,
            "directness": 0.8,
        }

        traits = PersonalityTraits.from_dict(data)

        assert traits.humor == 0.8
        assert traits.formality == 0.3
        assert traits.enthusiasm == 0.9

    @pytest.mark.asyncio
    async def test_personality_loading(self, personality_manager):
        """Test personality loading from memory."""
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
                                "knowledge_confidence": 0.95,
                                "debate_tolerance": 0.4,
                                "empathy": 0.7,
                                "creativity": 0.6,
                                "directness": 0.8,
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

    @pytest.mark.asyncio
    async def test_personality_adaptation(self, personality_manager):
        """Test personality adaptation process."""
        # Mock RL recommendation
        personality_manager._get_rl_recommendation = AsyncMock(
            return_value=AsyncMock(success=True, data={"action": "adjust_humor", "adjustment": 0.1})
        )

        # Mock memory service
        personality_manager.memory_service.store_memory = AsyncMock()

        context = PersonalityContext(
            channel_type="casual",
            time_of_day="afternoon",
            user_history=[],
            message_sentiment=0.5,
            conversation_length=5,
            guild_culture="gaming",
        )

        result = await personality_manager.adapt_personality(
            context=context, reward=0.8, tenant="tenant", workspace="workspace"
        )

        assert result.success is True
        assert isinstance(result.data, PersonalityTraits)


class TestRewardComputer:
    """Test suite for reward computation system."""

    @pytest.fixture
    def reward_computer(self):
        """Create reward computer instance."""
        return RewardComputer()

    @pytest.fixture
    def sample_metrics(self):
        """Sample interaction metrics for testing."""
        return InteractionMetrics(
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

    @pytest.mark.asyncio
    async def test_reward_computation(self, reward_computer, sample_metrics):
        """Test reward signal computation."""
        result = await reward_computer.compute_reward(sample_metrics)

        assert result.success is True
        assert isinstance(result.data, RewardSignal)
        assert 0.0 <= result.data.total_reward <= 1.0
        assert 0.0 <= result.data.confidence <= 1.0

    def test_engagement_reward_calculation(self, reward_computer, sample_metrics):
        """Test engagement reward calculation."""
        reward = reward_computer._compute_engagement_reward(sample_metrics)

        assert 0.0 <= reward <= 1.0
        assert reward > 0  # Should have some reward for the sample metrics

    def test_reaction_reward_calculation(self, reward_computer, sample_metrics):
        """Test reaction reward calculation."""
        reward = reward_computer._compute_reaction_reward(sample_metrics)

        assert 0.0 <= reward <= 1.0
        assert reward > 0  # Should have positive reward for positive reactions

    def test_continuation_reward_calculation(self, reward_computer, sample_metrics):
        """Test continuation reward calculation."""
        reward = reward_computer._compute_continuation_reward(sample_metrics)

        assert 0.0 <= reward <= 1.0
        assert reward > 0  # Should have reward for quick reply and continuation

    def test_confidence_calculation(self, reward_computer, sample_metrics):
        """Test confidence calculation."""
        confidence = reward_computer._compute_confidence(sample_metrics)

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should have decent confidence with good metrics


class TestConversationalPipeline:
    """Test suite for conversational pipeline."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        routing_manager = AsyncMock()
        prompt_engine = AsyncMock()
        memory_service = AsyncMock()
        learning_engine = MagicMock()

        return routing_manager, prompt_engine, memory_service, learning_engine

    @pytest.fixture
    def pipeline(self, mock_services):
        """Create conversational pipeline instance."""
        routing_manager, prompt_engine, memory_service, learning_engine = mock_services
        return ConversationalPipeline(routing_manager, prompt_engine, memory_service, learning_engine)

    @pytest.fixture
    def sample_message_data(self):
        """Sample Discord message data."""
        return {
            "id": "123456789",
            "channel_id": "987654321",
            "guild_id": "111222333",
            "author": {"id": "444555666", "username": "testuser"},
            "content": "Hello bot, can you help me?",
            "timestamp": 1640995200.0,
        }

    @pytest.fixture
    def sample_recent_messages(self):
        """Sample recent messages."""
        return [{"author": {"username": "user1"}, "content": "Previous message"}]

    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.message_evaluator is not None
        assert pipeline.opt_in_manager is not None
        assert pipeline.personality_manager is not None
        assert pipeline.reward_computer is not None

    @pytest.mark.asyncio
    async def test_direct_mention_detection(self, pipeline, sample_message_data):
        """Test direct mention detection."""
        # Test direct mention
        sample_message_data["content"] = "@bot help me"
        is_mention = pipeline._is_direct_mention(sample_message_data)
        assert is_mention is True

        # Test non-mention
        sample_message_data["content"] = "regular message"
        is_mention = pipeline._is_direct_mention(sample_message_data)
        assert is_mention is False

    @pytest.mark.asyncio
    async def test_personality_context_building(self, pipeline, sample_message_data, sample_recent_messages):
        """Test personality context building."""
        context = await pipeline._build_personality_context(sample_message_data, sample_recent_messages)

        assert isinstance(context, PersonalityContext)
        assert context.channel_type == "general"
        assert context.conversation_length == 1

    @pytest.mark.asyncio
    async def test_memory_context_retrieval(self, pipeline):
        """Test memory context retrieval."""
        # Mock memory service
        pipeline.memory_service.search_memories.return_value = AsyncMock(
            success=True, data={"memories": [{"content": "relevant memory"}]}
        )

        pipeline_context = PipelineContext(
            message_data={"content": "test message"},
            guild_id="guild123",
            channel_id="channel123",
            user_id="user123",
            recent_messages=[],
            user_opt_in_status=True,
            personality_context=PersonalityContext(
                channel_type="general",
                time_of_day="afternoon",
                user_history=[],
                message_sentiment=0.0,
                conversation_length=1,
                guild_culture="casual",
            ),
        )

        memory_context = await pipeline._retrieve_memory_context(pipeline_context)

        assert isinstance(memory_context, list)
        assert len(memory_context) == 1
        assert memory_context[0]["content"] == "relevant memory"


class TestMCPIntegration:
    """Test suite for MCP integration layer."""

    @pytest.fixture
    def feature_flags(self):
        """Create feature flags for testing."""
        from performance_optimization.src.ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags

        return FeatureFlags()

    @pytest.fixture
    def mcp_integration(self, feature_flags):
        """Create MCP integration layer instance."""
        return MCPIntegrationLayer(feature_flags)

    @pytest.mark.asyncio
    async def test_initialization(self, mcp_integration):
        """Test MCP integration initialization."""
        # Mock server initialization to avoid actual MCP server dependencies
        with patch.object(mcp_integration, "_init_memory_server"):
            with patch.object(mcp_integration, "_init_kg_server"):
                with patch.object(mcp_integration, "_init_crewai_server"):
                    with patch.object(mcp_integration, "_init_routing_server"):
                        with patch.object(mcp_integration, "_init_creator_intelligence_server"):
                            await mcp_integration.initialize()

        assert mcp_integration._initialized is True

    @pytest.mark.asyncio
    async def test_integration_status(self, mcp_integration):
        """Test integration status reporting."""
        status = await mcp_integration.get_integration_status()

        assert "initialized" in status
        assert "servers" in status
        assert isinstance(status["servers"], dict)


# Integration Tests
class TestDiscordAIIntegration:
    """Integration tests for the complete Discord AI system."""

    @pytest.mark.asyncio
    async def test_end_to_end_message_processing(self):
        """Test complete end-to-end message processing."""
        # This would be a comprehensive integration test
        # that tests the entire flow from message receipt to response generation

    @pytest.mark.asyncio
    async def test_personality_evolution_workflow(self):
        """Test complete personality evolution workflow."""
        # This would test the complete personality adaptation cycle
        # from interaction to reward computation to trait adjustment


# Performance Tests
class TestPerformance:
    """Performance tests for Discord AI components."""

    @pytest.mark.asyncio
    async def test_message_evaluation_performance(self):
        """Test message evaluation performance under load."""
        # This would test performance with multiple concurrent messages

    @pytest.mark.asyncio
    async def test_memory_retrieval_performance(self):
        """Test memory retrieval performance."""
        # This would test vector search performance with large datasets


# Configuration Tests
class TestConfiguration:
    """Test configuration and feature flags."""

    def test_feature_flags_loading(self):
        """Test feature flags loading from environment."""
        from performance_optimization.src.ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags

        flags = FeatureFlags()

        # Test that Discord AI flags are present
        assert hasattr(flags, "ENABLE_DISCORD_AI_RESPONSES")
        assert hasattr(flags, "ENABLE_DISCORD_PERSONALITY_RL")
        assert hasattr(flags, "ENABLE_DISCORD_MESSAGE_EVALUATION")

    def test_mcp_integration_flags(self):
        """Test MCP integration feature flags."""
        from performance_optimization.src.ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags

        flags = FeatureFlags()

        # Test that MCP flags are present
        assert hasattr(flags, "ENABLE_MCP_MEMORY")
        assert hasattr(flags, "ENABLE_MCP_KG")
        assert hasattr(flags, "ENABLE_MCP_CREWAI")
        assert hasattr(flags, "ENABLE_MCP_ROUTER")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
