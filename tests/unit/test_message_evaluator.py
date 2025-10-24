"""
Unit tests for the message evaluation system.
"""

from unittest.mock import AsyncMock

import pytest

from discord.message_evaluator import (
    EvaluationResult,
    MessageContext,
    MessageEvaluator,
    ResponseDecisionAgent,
)


class TestMessageContext:
    """Test MessageContext class."""

    def test_message_context_creation(self):
        """Test MessageContext object creation."""
        context = MessageContext(
            message_id="123",
            user_id="user123",
            guild_id="guild123",
            channel_id="channel123",
            content="Hello bot",
            user_opt_in_status=True,
            recent_messages=[],
            relevant_memories=[],
            direct_mention=True,
            timestamp=1640995200.0,
        )

        assert context.message_id == "123"
        assert context.user_id == "user123"
        assert context.guild_id == "guild123"
        assert context.channel_id == "channel123"
        assert context.content == "Hello bot"
        assert context.user_opt_in_status is True
        assert context.direct_mention is True
        assert context.timestamp == 1640995200.0

    def test_message_context_to_dict(self):
        """Test MessageContext serialization to dictionary."""
        context = MessageContext(
            message_id="123",
            user_id="user123",
            guild_id="guild123",
            channel_id="channel123",
            content="Hello bot",
            user_opt_in_status=True,
            recent_messages=[{"author": "user", "content": "hi"}],
            relevant_memories=[{"content": "memory"}],
            direct_mention=True,
            timestamp=1640995200.0,
        )

        context_dict = context.to_dict()

        assert isinstance(context_dict, dict)
        assert context_dict["message_id"] == "123"
        assert context_dict["user_id"] == "user123"
        assert context_dict["guild_id"] == "guild123"
        assert context_dict["channel_id"] == "channel123"
        assert context_dict["content"] == "Hello bot"
        assert context_dict["user_opt_in_status"] is True
        assert context_dict["direct_mention"] is True
        assert context_dict["timestamp"] == 1640995200.0


class TestEvaluationResult:
    """Test EvaluationResult class."""

    def test_evaluation_result_creation(self):
        """Test EvaluationResult object creation."""
        result = EvaluationResult(
            should_respond=True,
            confidence=0.85,
            reasoning="Direct mention detected",
            priority="high",
            suggested_personality_traits={"humor": 0.6, "formality": 0.3, "enthusiasm": 0.8},
            context_relevance_score=0.9,
        )

        assert result.should_respond is True
        assert result.confidence == 0.85
        assert result.reasoning == "Direct mention detected"
        assert result.priority == "high"
        assert result.suggested_personality_traits["humor"] == 0.6
        assert result.context_relevance_score == 0.9

    def test_evaluation_result_from_dict(self):
        """Test EvaluationResult creation from dictionary."""
        data = {
            "should_respond": False,
            "confidence": 0.3,
            "reasoning": "Not relevant",
            "priority": "low",
            "suggested_personality_traits": {"humor": 0.4, "formality": 0.7},
            "context_relevance_score": 0.2,
        }

        result = EvaluationResult.from_dict(data)

        assert result.should_respond is False
        assert result.confidence == 0.3
        assert result.reasoning == "Not relevant"
        assert result.priority == "low"
        assert result.suggested_personality_traits["humor"] == 0.4
        assert result.context_relevance_score == 0.2


class TestResponseDecisionAgent:
    """Test ResponseDecisionAgent class."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        routing_manager = AsyncMock()
        prompt_engine = AsyncMock()
        memory_service = AsyncMock()

        return routing_manager, prompt_engine, memory_service

    @pytest.fixture
    def decision_agent(self, mock_services):
        """Create ResponseDecisionAgent instance."""
        routing_manager, prompt_engine, memory_service = mock_services
        return ResponseDecisionAgent(routing_manager, prompt_engine, memory_service)

    @pytest.fixture
    def sample_context(self):
        """Create sample message context."""
        return MessageContext(
            message_id="123",
            user_id="user123",
            guild_id="guild123",
            channel_id="channel123",
            content="@bot help me",
            user_opt_in_status=True,
            recent_messages=[],
            relevant_memories=[],
            direct_mention=True,
            timestamp=1640995200.0,
        )

    @pytest.mark.asyncio
    async def test_model_selection(self, decision_agent, sample_context):
        """Test model selection for evaluation."""
        # Mock routing manager response
        decision_agent.routing_manager.suggest_model.return_value = AsyncMock(
            success=True, data={"model": "gpt-4o-mini", "reasoning": "Fast and cost-effective"}
        )

        model_result = await decision_agent._select_model(sample_context)

        assert model_result.success is True
        assert model_result.data["model"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_prompt_generation(self, decision_agent, sample_context):
        """Test prompt generation for evaluation."""
        prompt = await decision_agent._generate_evaluation_prompt(sample_context)

        assert isinstance(prompt, str)
        assert "message evaluation" in prompt.lower()
        assert "@bot help me" in prompt
        assert "direct_mention" in prompt

    @pytest.mark.asyncio
    async def test_llm_evaluation(self, decision_agent, sample_context):
        """Test LLM-based evaluation."""
        # Mock prompt engine response
        decision_agent.prompt_engine.generate_response.return_value = AsyncMock(
            success=True,
            data='{"should_respond": true, "confidence": 0.9, "reasoning": "Direct mention", "priority": "high", "suggested_personality_traits": {"humor": 0.6, "formality": 0.3, "enthusiasm": 0.8, "knowledge_confidence": 0.9, "debate_tolerance": 0.5, "empathy": 0.7, "creativity": 0.6, "directness": 0.8}, "context_relevance_score": 0.95}',
        )

        evaluation_result = await decision_agent._evaluate_with_llm(sample_context, "test prompt")

        assert evaluation_result.success is True
        assert isinstance(evaluation_result.data, EvaluationResult)
        assert evaluation_result.data.should_respond is True
        assert evaluation_result.data.confidence == 0.9

    @pytest.mark.asyncio
    async def test_llm_evaluation_json_error(self, decision_agent, sample_context):
        """Test LLM evaluation with invalid JSON response."""
        # Mock prompt engine response with invalid JSON
        decision_agent.prompt_engine.generate_response.return_value = AsyncMock(
            success=True, data="Invalid JSON response"
        )

        evaluation_result = await decision_agent._evaluate_with_llm(sample_context, "test prompt")

        assert evaluation_result.success is False
        assert "JSON parsing failed" in evaluation_result.error

    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self, decision_agent):
        """Test confidence threshold filtering."""
        # Test high confidence result
        high_conf_result = EvaluationResult(
            should_respond=True,
            confidence=0.9,
            reasoning="High confidence",
            priority="high",
            suggested_personality_traits={},
            context_relevance_score=0.9,
        )

        filtered = decision_agent._apply_confidence_threshold(high_conf_result, 0.8)
        assert filtered.should_respond is True

        # Test low confidence result
        low_conf_result = EvaluationResult(
            should_respond=True,
            confidence=0.3,
            reasoning="Low confidence",
            priority="low",
            suggested_personality_traits={},
            context_relevance_score=0.3,
        )

        filtered = decision_agent._apply_confidence_threshold(low_conf_result, 0.8)
        assert filtered.should_respond is False
        assert filtered.reasoning == "Confidence too low (0.3 < 0.8)"


class TestMessageEvaluator:
    """Test MessageEvaluator class."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        routing_manager = AsyncMock()
        prompt_engine = AsyncMock()
        memory_service = AsyncMock()

        return routing_manager, prompt_engine, memory_service

    @pytest.fixture
    def message_evaluator(self, mock_services):
        """Create MessageEvaluator instance."""
        routing_manager, prompt_engine, memory_service = mock_services
        return MessageEvaluator(routing_manager, prompt_engine, memory_service)

    @pytest.fixture
    def sample_message_data(self):
        """Sample Discord message data."""
        return {
            "id": "123456789",
            "channel_id": "987654321",
            "guild_id": "111222333",
            "author": {"id": "444555666", "username": "testuser"},
            "content": "@bot help me with something",
            "timestamp": 1640995200.0,
        }

    @pytest.fixture
    def sample_recent_messages(self):
        """Sample recent messages."""
        return [
            {"author": {"username": "user1"}, "content": "Previous message 1", "timestamp": 1640995100.0},
            {"author": {"username": "user2"}, "content": "Previous message 2", "timestamp": 1640995150.0},
        ]

    @pytest.mark.asyncio
    async def test_message_evaluation_success(self, message_evaluator, sample_message_data, sample_recent_messages):
        """Test successful message evaluation."""
        # Mock all service responses
        message_evaluator.routing_manager.suggest_model.return_value = AsyncMock(
            success=True, data={"model": "gpt-4o-mini"}
        )

        message_evaluator.prompt_engine.generate_response.return_value = AsyncMock(
            success=True,
            data='{"should_respond": true, "confidence": 0.85, "reasoning": "Direct mention detected", "priority": "high", "suggested_personality_traits": {"humor": 0.6, "formality": 0.3, "enthusiasm": 0.8, "knowledge_confidence": 0.9, "debate_tolerance": 0.5, "empathy": 0.7, "creativity": 0.6, "directness": 0.8}, "context_relevance_score": 0.9}',
        )

        message_evaluator.memory_service.search_memories.return_value = AsyncMock(success=True, data={"memories": []})

        result = await message_evaluator.evaluate_discord_message(sample_message_data, sample_recent_messages, True)

        assert result.success is True
        assert isinstance(result.data, EvaluationResult)
        assert result.data.should_respond is True
        assert result.data.confidence == 0.85

    @pytest.mark.asyncio
    async def test_message_evaluation_failure(self, message_evaluator, sample_message_data, sample_recent_messages):
        """Test message evaluation failure."""
        # Mock service failure
        message_evaluator.routing_manager.suggest_model.return_value = AsyncMock(
            success=False, error="Routing service unavailable"
        )

        result = await message_evaluator.evaluate_discord_message(sample_message_data, sample_recent_messages, True)

        assert result.success is False
        assert "Routing service unavailable" in result.error

    @pytest.mark.asyncio
    async def test_context_building_with_memories(self, message_evaluator, sample_message_data, sample_recent_messages):
        """Test context building with memory retrieval."""
        # Mock memory service with memories
        message_evaluator.memory_service.search_memories.return_value = AsyncMock(
            success=True,
            data={
                "memories": [{"content": "User previously asked about Python", "metadata": {"timestamp": 1640990000.0}}]
            },
        )

        context = await message_evaluator.context_builder.build_context(
            sample_message_data, sample_recent_messages, True
        )

        assert isinstance(context, MessageContext)
        assert len(context.relevant_memories) == 1
        assert context.relevant_memories[0]["content"] == "User previously asked about Python"

    @pytest.mark.asyncio
    async def test_direct_mention_detection(self, message_evaluator):
        """Test direct mention detection."""
        context_builder = message_evaluator.context_builder

        # Test various mention patterns
        test_cases = [
            ("@bot help me", True),
            ("Hey @bot", True),
            ("@bot: what's up?", True),
            ("regular message", False),
            ("mention @someone else", False),
            ("@botbot help", False),  # Different bot name
        ]

        for message_content, expected in test_cases:
            message_data = {"content": message_content, "mentions": [{"id": "bot123", "username": "bot"}]}

            is_mention = context_builder._check_direct_mention(message_content, message_data)
            assert is_mention == expected, f"Failed for message: '{message_content}'"

    @pytest.mark.asyncio
    async def test_message_priority_assessment(self, message_evaluator):
        """Test message priority assessment."""
        decision_agent = message_evaluator.decision_agent

        # Test high priority (direct mention)
        context = MessageContext(
            message_id="123",
            user_id="user123",
            guild_id="guild123",
            channel_id="channel123",
            content="@bot urgent help",
            user_opt_in_status=True,
            recent_messages=[],
            relevant_memories=[],
            direct_mention=True,
            timestamp=1640995200.0,
        )

        priority = decision_agent._assess_message_priority(context)
        assert priority == "high"

        # Test medium priority (opt-in user)
        context.direct_mention = False
        priority = decision_agent._assess_message_priority(context)
        assert priority == "medium"

        # Test low priority (non-opt-in user)
        context.user_opt_in_status = False
        priority = decision_agent._assess_message_priority(context)
        assert priority == "low"

    @pytest.mark.asyncio
    async def test_message_evaluation_with_confidence_threshold(
        self, message_evaluator, sample_message_data, sample_recent_messages
    ):
        """Test message evaluation with confidence threshold filtering."""
        # Mock service responses
        message_evaluator.routing_manager.suggest_model.return_value = AsyncMock(
            success=True, data={"model": "gpt-4o-mini"}
        )

        # Mock low confidence response
        message_evaluator.prompt_engine.generate_response.return_value = AsyncMock(
            success=True,
            data='{"should_respond": true, "confidence": 0.3, "reasoning": "Uncertain", "priority": "low", "suggested_personality_traits": {"humor": 0.5, "formality": 0.5, "enthusiasm": 0.5, "knowledge_confidence": 0.5, "debate_tolerance": 0.5, "empathy": 0.5, "creativity": 0.5, "directness": 0.5}, "context_relevance_score": 0.3}',
        )

        message_evaluator.memory_service.search_memories.return_value = AsyncMock(success=True, data={"memories": []})

        result = await message_evaluator.evaluate_discord_message(sample_message_data, sample_recent_messages, True)

        assert result.success is True
        # Should be filtered out due to low confidence
        assert result.data.should_respond is False
        assert "Confidence too low" in result.data.reasoning


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
