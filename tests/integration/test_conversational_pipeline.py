"""
Integration tests for the conversational pipeline.
"""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest
from performance_optimization.src.discord.conversational_pipeline import (
    ConversationalPipeline,
    PipelineConfig,
    PipelineContext,
    PipelineResult,
)
from performance_optimization.src.discord.personality.personality_manager import (
    PersonalityContext,
)


class TestConversationalPipelineIntegration:
    """Integration tests for the conversational pipeline."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for integration testing."""
        routing_manager = AsyncMock()
        prompt_engine = AsyncMock()
        memory_service = AsyncMock()
        learning_engine = MagicMock()

        return routing_manager, prompt_engine, memory_service, learning_engine

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
    def pipeline_config(self):
        """Create pipeline configuration."""
        return PipelineConfig(
            confidence_threshold=0.7,
            max_recent_messages=10,
            memory_search_limit=5,
            enable_personality_adaptation=True,
            enable_reward_computation=True,
            tenant="test_tenant",
            workspace="test_workspace",
        )

    @pytest.fixture
    def pipeline(self, mock_services, temp_db, pipeline_config):
        """Create conversational pipeline instance."""
        routing_manager, prompt_engine, memory_service, learning_engine = mock_services

        return ConversationalPipeline(
            routing_manager=routing_manager,
            prompt_engine=prompt_engine,
            memory_service=memory_service,
            learning_engine=learning_engine,
            db_path=temp_db,
            config=pipeline_config,
        )

    @pytest.fixture
    def sample_message_data(self):
        """Sample Discord message data."""
        return {
            "id": "123456789",
            "channel_id": "987654321",
            "guild_id": "111222333",
            "author": {"id": "444555666", "username": "testuser"},
            "content": "@bot can you help me understand this topic?",
            "timestamp": 1640995200.0,
        }

    @pytest.fixture
    def sample_recent_messages(self):
        """Sample recent messages for context."""
        return [
            {"author": {"username": "user1"}, "content": "Previous message about the topic", "timestamp": 1640995100.0},
            {
                "author": {"username": "testuser"},
                "content": "I'm interested in learning more",
                "timestamp": 1640995150.0,
            },
        ]

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization with all components."""
        assert pipeline.message_evaluator is not None
        assert pipeline.opt_in_manager is not None
        assert pipeline.personality_manager is not None
        assert pipeline.reward_computer is not None
        assert pipeline.config is not None

    @pytest.mark.asyncio
    async def test_direct_mention_detection(self, pipeline, sample_message_data):
        """Test direct mention detection in pipeline."""
        # Test direct mention
        is_mention = pipeline._is_direct_mention(sample_message_data)
        assert is_mention is True

        # Test non-mention
        sample_message_data["content"] = "regular message without mention"
        is_mention = pipeline._is_direct_mention(sample_message_data)
        assert is_mention is False

    @pytest.mark.asyncio
    async def test_user_opt_in_workflow(self, pipeline, sample_message_data):
        """Test complete user opt-in workflow."""
        user_id = "444555666"
        guild_id = "111222333"

        # Test initial status (should be opted out)
        status_result = await pipeline.opt_in_manager.get_user_status(user_id, guild_id)
        assert status_result.success is True
        assert status_result.data["opted_in"] is False

        # Test opt-in
        opt_in_result = await pipeline.opt_in_manager.opt_in_user(
            user_id=user_id, username="testuser", guild_id=guild_id
        )
        assert opt_in_result.success is True

        # Test status after opt-in
        status_result = await pipeline.opt_in_manager.get_user_status(user_id, guild_id)
        assert status_result.success is True
        assert status_result.data["opted_in"] is True
        assert status_result.data["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_personality_context_building(self, pipeline, sample_message_data, sample_recent_messages):
        """Test personality context building."""
        context = await pipeline._build_personality_context(sample_message_data, sample_recent_messages)

        assert isinstance(context, PersonalityContext)
        assert context.channel_type == "general"
        assert context.conversation_length == 2  # Based on recent messages
        assert context.guild_culture == "casual"

    @pytest.mark.asyncio
    async def test_memory_context_retrieval(self, pipeline):
        """Test memory context retrieval."""
        # Mock memory service response
        pipeline.memory_service.search_memories.return_value = AsyncMock(
            success=True,
            data={
                "memories": [
                    {
                        "content": "User previously asked about machine learning",
                        "metadata": {"timestamp": 1640990000.0, "relevance": 0.9},
                    },
                    {
                        "content": "Bot explained neural networks",
                        "metadata": {"timestamp": 1640990100.0, "relevance": 0.8},
                    },
                ]
            },
        )

        pipeline_context = PipelineContext(
            message_data={"content": "Can you explain deep learning?"},
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
        assert len(memory_context) == 2
        assert memory_context[0]["content"] == "User previously asked about machine learning"
        assert memory_context[1]["content"] == "Bot explained neural networks"

    @pytest.mark.asyncio
    async def test_complete_message_processing_workflow(self, pipeline, sample_message_data, sample_recent_messages):
        """Test complete message processing workflow."""
        # Mock all service responses for successful processing
        pipeline.routing_manager.suggest_model.return_value = AsyncMock(success=True, data={"model": "gpt-4o-mini"})

        pipeline.prompt_engine.generate_response.return_value = AsyncMock(
            success=True,
            data='{"should_respond": true, "confidence": 0.85, "reasoning": "Direct mention detected", "priority": "high", "suggested_personality_traits": {"humor": 0.6, "formality": 0.3, "enthusiasm": 0.8, "knowledge_confidence": 0.9, "debate_tolerance": 0.5, "empathy": 0.7, "creativity": 0.6, "directness": 0.8}, "context_relevance_score": 0.9}',
        )

        pipeline.memory_service.search_memories.return_value = AsyncMock(success=True, data={"memories": []})

        # First opt in the user
        await pipeline.opt_in_manager.opt_in_user(user_id="444555666", username="testuser", guild_id="111222333")

        # Process the message
        result = await pipeline.process_discord_message(sample_message_data, sample_recent_messages)

        assert result.success is True
        assert isinstance(result.data, PipelineResult)
        assert result.data.should_respond is True
        assert result.data.confidence == 0.85
        assert result.data.response_generated is True

    @pytest.mark.asyncio
    async def test_message_processing_with_low_confidence(self, pipeline, sample_message_data, sample_recent_messages):
        """Test message processing with low confidence evaluation."""
        # Mock low confidence evaluation
        pipeline.routing_manager.suggest_model.return_value = AsyncMock(success=True, data={"model": "gpt-4o-mini"})

        pipeline.prompt_engine.generate_response.return_value = AsyncMock(
            success=True,
            data='{"should_respond": true, "confidence": 0.3, "reasoning": "Uncertain about relevance", "priority": "low", "suggested_personality_traits": {"humor": 0.5, "formality": 0.5, "enthusiasm": 0.5, "knowledge_confidence": 0.5, "debate_tolerance": 0.5, "empathy": 0.5, "creativity": 0.5, "directness": 0.5}, "context_relevance_score": 0.3}',
        )

        pipeline.memory_service.search_memories.return_value = AsyncMock(success=True, data={"memories": []})

        # Opt in the user
        await pipeline.opt_in_manager.opt_in_user(user_id="444555666", username="testuser", guild_id="111222333")

        # Process the message
        result = await pipeline.process_discord_message(sample_message_data, sample_recent_messages)

        assert result.success is True
        assert isinstance(result.data, PipelineResult)
        # Should be filtered out due to low confidence
        assert result.data.should_respond is False
        assert "Confidence too low" in result.data.reasoning

    @pytest.mark.asyncio
    async def test_non_opted_in_user_processing(self, pipeline, sample_message_data, sample_recent_messages):
        """Test message processing for non-opted-in user."""
        # Mock evaluation that would normally respond
        pipeline.routing_manager.suggest_model.return_value = AsyncMock(success=True, data={"model": "gpt-4o-mini"})

        pipeline.prompt_engine.generate_response.return_value = AsyncMock(
            success=True,
            data='{"should_respond": true, "confidence": 0.9, "reasoning": "Direct mention", "priority": "high", "suggested_personality_traits": {"humor": 0.6, "formality": 0.3, "enthusiasm": 0.8, "knowledge_confidence": 0.9, "debate_tolerance": 0.5, "empathy": 0.7, "creativity": 0.6, "directness": 0.8}, "context_relevance_score": 0.95}',
        )

        pipeline.memory_service.search_memories.return_value = AsyncMock(success=True, data={"memories": []})

        # Don't opt in the user - they should be opted out by default

        # Process the message
        result = await pipeline.process_discord_message(sample_message_data, sample_recent_messages)

        assert result.success is True
        assert isinstance(result.data, PipelineResult)
        # Should still respond to direct mentions even if not opted in
        assert result.data.should_respond is True

    @pytest.mark.asyncio
    async def test_personality_adaptation_integration(self, pipeline, sample_message_data, sample_recent_messages):
        """Test personality adaptation integration."""
        # Mock successful evaluation
        pipeline.routing_manager.suggest_model.return_value = AsyncMock(success=True, data={"model": "gpt-4o-mini"})

        pipeline.prompt_engine.generate_response.return_value = AsyncMock(
            success=True,
            data='{"should_respond": true, "confidence": 0.85, "reasoning": "Direct mention", "priority": "high", "suggested_personality_traits": {"humor": 0.6, "formality": 0.3, "enthusiasm": 0.8, "knowledge_confidence": 0.9, "debate_tolerance": 0.5, "empathy": 0.7, "creativity": 0.6, "directness": 0.8}, "context_relevance_score": 0.9}',
        )

        pipeline.memory_service.search_memories.return_value = AsyncMock(success=True, data={"memories": []})

        # Mock personality adaptation
        pipeline.personality_manager.adapt_personality = AsyncMock(
            return_value=AsyncMock(success=True, data={"humor": 0.65, "formality": 0.25, "enthusiasm": 0.85})
        )

        # Mock reward computation
        pipeline.reward_computer.compute_reward = AsyncMock(
            return_value=AsyncMock(success=True, data={"total_reward": 0.8, "confidence": 0.85})
        )

        # Opt in the user
        await pipeline.opt_in_manager.opt_in_user(user_id="444555666", username="testuser", guild_id="111222333")

        # Process the message
        result = await pipeline.process_discord_message(sample_message_data, sample_recent_messages)

        assert result.success is True
        assert isinstance(result.data, PipelineResult)
        assert result.data.should_respond is True
        assert result.data.personality_adapted is True

    @pytest.mark.asyncio
    async def test_error_handling_in_pipeline(self, pipeline, sample_message_data, sample_recent_messages):
        """Test error handling in the pipeline."""
        # Mock service failure
        pipeline.routing_manager.suggest_model.return_value = AsyncMock(
            success=False, error="Routing service unavailable"
        )

        # Opt in the user
        await pipeline.opt_in_manager.opt_in_user(user_id="444555666", username="testuser", guild_id="111222333")

        # Process the message - should handle error gracefully
        result = await pipeline.process_discord_message(sample_message_data, sample_recent_messages)

        assert result.success is False
        assert "Routing service unavailable" in result.error

    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self, pipeline):
        """Test concurrent message processing."""
        # Create multiple message data
        message_data_1 = {
            "id": "msg1",
            "channel_id": "channel1",
            "guild_id": "guild1",
            "author": {"id": "user1", "username": "user1"},
            "content": "@bot help with topic 1",
            "timestamp": 1640995200.0,
        }

        message_data_2 = {
            "id": "msg2",
            "channel_id": "channel2",
            "guild_id": "guild2",
            "author": {"id": "user2", "username": "user2"},
            "content": "@bot help with topic 2",
            "timestamp": 1640995210.0,
        }

        # Mock successful responses for both
        pipeline.routing_manager.suggest_model.return_value = AsyncMock(success=True, data={"model": "gpt-4o-mini"})

        pipeline.prompt_engine.generate_response.return_value = AsyncMock(
            success=True,
            data='{"should_respond": true, "confidence": 0.8, "reasoning": "Direct mention", "priority": "high", "suggested_personality_traits": {"humor": 0.6, "formality": 0.3, "enthusiasm": 0.8, "knowledge_confidence": 0.9, "debate_tolerance": 0.5, "empathy": 0.7, "creativity": 0.6, "directness": 0.8}, "context_relevance_score": 0.9}',
        )

        pipeline.memory_service.search_memories.return_value = AsyncMock(success=True, data={"memories": []})

        # Opt in both users
        await pipeline.opt_in_manager.opt_in_user("user1", "user1", "guild1")
        await pipeline.opt_in_manager.opt_in_user("user2", "user2", "guild2")

        # Process messages concurrently
        results = await asyncio.gather(
            pipeline.process_discord_message(message_data_1, []),
            pipeline.process_discord_message(message_data_2, []),
            return_exceptions=True,
        )

        # Both should succeed
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is True
        assert isinstance(results[0].data, PipelineResult)
        assert isinstance(results[1].data, PipelineResult)

    @pytest.mark.asyncio
    async def test_memory_integration_workflow(self, pipeline, sample_message_data, sample_recent_messages):
        """Test memory integration workflow."""
        # Mock memory service with relevant memories
        pipeline.memory_service.search_memories.return_value = AsyncMock(
            success=True,
            data={
                "memories": [
                    {
                        "content": "User previously asked about machine learning concepts",
                        "metadata": {"timestamp": 1640990000.0, "relevance": 0.9, "user_id": "444555666"},
                    }
                ]
            },
        )

        # Mock successful evaluation
        pipeline.routing_manager.suggest_model.return_value = AsyncMock(success=True, data={"model": "gpt-4o-mini"})

        pipeline.prompt_engine.generate_response.return_value = AsyncMock(
            success=True,
            data='{"should_respond": true, "confidence": 0.9, "reasoning": "Direct mention with relevant context", "priority": "high", "suggested_personality_traits": {"humor": 0.6, "formality": 0.3, "enthusiasm": 0.8, "knowledge_confidence": 0.9, "debate_tolerance": 0.5, "empathy": 0.7, "creativity": 0.6, "directness": 0.8}, "context_relevance_score": 0.95}',
        )

        # Mock interaction recording
        pipeline.opt_in_manager.record_interaction = AsyncMock(
            return_value=AsyncMock(success=True, data={"action": "interaction_recorded"})
        )

        # Opt in the user
        await pipeline.opt_in_manager.opt_in_user(user_id="444555666", username="testuser", guild_id="111222333")

        # Process the message
        result = await pipeline.process_discord_message(sample_message_data, sample_recent_messages)

        assert result.success is True
        assert isinstance(result.data, PipelineResult)
        assert result.data.should_respond is True
        assert result.data.confidence == 0.9

        # Verify memory search was called
        pipeline.memory_service.search_memories.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_metrics_collection(self, pipeline, sample_message_data, sample_recent_messages):
        """Test pipeline metrics collection."""
        # Mock successful processing
        pipeline.routing_manager.suggest_model.return_value = AsyncMock(success=True, data={"model": "gpt-4o-mini"})

        pipeline.prompt_engine.generate_response.return_value = AsyncMock(
            success=True,
            data='{"should_respond": true, "confidence": 0.8, "reasoning": "Direct mention", "priority": "high", "suggested_personality_traits": {"humor": 0.6, "formality": 0.3, "enthusiasm": 0.8, "knowledge_confidence": 0.9, "debate_tolerance": 0.5, "empathy": 0.7, "creativity": 0.6, "directness": 0.8}, "context_relevance_score": 0.9}',
        )

        pipeline.memory_service.search_memories.return_value = AsyncMock(success=True, data={"memories": []})

        # Opt in the user
        await pipeline.opt_in_manager.opt_in_user(user_id="444555666", username="testuser", guild_id="111222333")

        # Process the message
        result = await pipeline.process_discord_message(sample_message_data, sample_recent_messages)

        assert result.success is True
        assert isinstance(result.data, PipelineResult)

        # Check that metrics are collected
        assert result.data.processing_time_ms > 0
        assert result.data.memory_retrieval_count >= 0
        assert result.data.personality_adapted is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
