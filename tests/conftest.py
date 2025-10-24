"""
Test configuration and fixtures for Discord AI integration tests.
"""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_routing_manager():
    """Create mock routing manager."""
    routing_manager = AsyncMock()
    routing_manager.suggest_model.return_value = AsyncMock(
        success=True, data={"model": "gpt-4o-mini", "reasoning": "Fast and cost-effective"}
    )
    return routing_manager


@pytest.fixture
def mock_prompt_engine():
    """Create mock prompt engine."""
    prompt_engine = AsyncMock()
    prompt_engine.generate_response.return_value = AsyncMock(
        success=True,
        data='{"should_respond": true, "confidence": 0.8, "reasoning": "Direct mention detected", "priority": "high", "suggested_personality_traits": {"humor": 0.6, "formality": 0.3, "enthusiasm": 0.8, "knowledge_confidence": 0.9, "debate_tolerance": 0.5, "empathy": 0.7, "creativity": 0.6, "directness": 0.8}, "context_relevance_score": 0.9}',
    )
    return prompt_engine


@pytest.fixture
def mock_memory_service():
    """Create mock memory service."""
    memory_service = AsyncMock()
    memory_service.search_memories.return_value = AsyncMock(success=True, data={"memories": []})
    memory_service.store_memory.return_value = AsyncMock(success=True, data={"memory_id": "mem123"})
    return memory_service


@pytest.fixture
def mock_learning_engine():
    """Create mock learning engine."""
    learning_engine = MagicMock()
    learning_engine.get_recommendation.return_value = {"action": "adjust_humor", "adjustment": 0.1}
    return learning_engine


@pytest.fixture
def sample_discord_message():
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
def sample_recent_messages():
    """Sample recent messages for context."""
    return [
        {"author": {"username": "user1"}, "content": "Previous message 1", "timestamp": 1640995100.0},
        {"author": {"username": "user2"}, "content": "Previous message 2", "timestamp": 1640995150.0},
    ]


@pytest.fixture
def sample_personality_traits():
    """Sample personality traits for testing."""
    from performance_optimization.src.discord.personality.personality_manager import PersonalityTraits

    return PersonalityTraits(
        humor=0.8,
        formality=0.3,
        enthusiasm=0.9,
        knowledge_confidence=0.85,
        debate_tolerance=0.4,
        empathy=0.7,
        creativity=0.8,
        directness=0.6,
    )


@pytest.fixture
def sample_interaction_metrics():
    """Sample interaction metrics for testing."""
    from performance_optimization.src.discord.personality.reward_computer import InteractionMetrics

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


@pytest.fixture
def sample_personality_context():
    """Sample personality context for testing."""
    from performance_optimization.src.discord.personality.personality_manager import PersonalityContext

    return PersonalityContext(
        channel_type="casual",
        time_of_day="afternoon",
        user_history=[],
        message_sentiment=0.5,
        conversation_length=5,
        guild_culture="gaming",
    )


@pytest.fixture
def mock_feature_flags():
    """Mock feature flags for testing."""
    from unittest.mock import MagicMock

    flags = MagicMock()
    flags.ENABLE_DISCORD_AI_RESPONSES = True
    flags.ENABLE_DISCORD_PERSONALITY_RL = True
    flags.ENABLE_DISCORD_MESSAGE_EVALUATION = True
    flags.ENABLE_DISCORD_OPT_IN_SYSTEM = True
    flags.ENABLE_DISCORD_CONVERSATIONAL_PIPELINE = True
    flags.ENABLE_PERSONALITY_ADAPTATION = True
    flags.ENABLE_REWARD_COMPUTATION = True
    flags.ENABLE_PERSONALITY_MEMORY = True
    flags.ENABLE_MCP_MEMORY = True
    flags.ENABLE_MCP_KG = True
    flags.ENABLE_MCP_CREWAI = True
    flags.ENABLE_MCP_ROUTER = True
    flags.ENABLE_MCP_CREATOR_INTELLIGENCE = True
    flags.ENABLE_MCP_OBS = True
    flags.ENABLE_MCP_INGEST = True
    flags.ENABLE_MCP_HTTP = True
    flags.ENABLE_MCP_A2A = True
    return flags


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "performance: mark test as performance test")


# Async test configuration
@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for anyio tests."""
    return "asyncio"


# Mock utilities
class MockStepResult:
    """Mock StepResult for testing."""

    @staticmethod
    def success(data=None, metadata=None):
        """Create successful StepResult."""
        return StepResult(success=True, data=data, metadata=metadata)

    @staticmethod
    def fail(error, status="error"):
        """Create failed StepResult."""
        return StepResult(success=False, error=error, status=status)


@pytest.fixture
def mock_step_result():
    """Mock StepResult utility."""
    return MockStepResult()


# Test data utilities
class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_discord_message(
        message_id="test123", user_id="user123", guild_id="guild123", content="@bot help", timestamp=1640995200.0
    ):
        """Create Discord message data."""
        return {
            "id": message_id,
            "channel_id": f"channel_{message_id}",
            "guild_id": guild_id,
            "author": {"id": user_id, "username": f"user_{user_id}"},
            "content": content,
            "timestamp": timestamp,
        }

    @staticmethod
    def create_interaction_metrics(message_id="msg123", user_id="user123", engagement_level="high"):
        """Create interaction metrics."""
        from performance_optimization.src.discord.personality.reward_computer import InteractionMetrics

        if engagement_level == "high":
            return InteractionMetrics(
                message_id=message_id,
                user_id=user_id,
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
        elif engagement_level == "medium":
            return InteractionMetrics(
                message_id=message_id,
                user_id=user_id,
                guild_id="guild123",
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
        else:  # low
            return InteractionMetrics(
                message_id=message_id,
                user_id=user_id,
                guild_id="guild123",
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
def test_data_factory():
    """Test data factory fixture."""
    return TestDataFactory()


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Performance timer for tests."""
    import time

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()
            return self.elapsed

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

    return PerformanceTimer()


# Error simulation utilities
@pytest.fixture
def error_simulator():
    """Error simulator for testing error handling."""

    class ErrorSimulator:
        @staticmethod
        def simulate_service_failure(service_name):
            """Simulate service failure."""
            return AsyncMock(success=False, error=f"{service_name} service unavailable")

        @staticmethod
        def simulate_timeout():
            """Simulate timeout error."""
            import asyncio

            raise asyncio.TimeoutError("Operation timed out")

        @staticmethod
        def simulate_network_error():
            """Simulate network error."""
            import aiohttp

            raise aiohttp.ClientError("Network error")

    return ErrorSimulator()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
