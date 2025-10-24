"""
Comprehensive test suite for Discord AI observability system.

This module tests all observability components including metrics collection,
conversation tracing, personality dashboard, and integration.
"""

import pytest

from src.discord.observability import (
    create_conversation_tracer,
    create_discord_metrics_collector,
    create_personality_dashboard,
)
from src.discord.observability_integration import create_discord_observability_integration


class TestDiscordMetricsCollector:
    """Test suite for DiscordMetricsCollector."""

    @pytest.fixture
    def metrics_collector(self):
        """Create a metrics collector for testing."""
        return create_discord_metrics_collector(max_history_size=100)

    @pytest.mark.asyncio
    async def test_start_conversation(self, metrics_collector):
        """Test starting conversation tracking."""
        result = await metrics_collector.start_conversation(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        assert result.success
        assert result.data["conversation_id"] == "test_conv_1"
        assert result.data["action"] == "conversation_started"

    @pytest.mark.asyncio
    async def test_record_message(self, metrics_collector):
        """Test recording messages in conversations."""
        # Start conversation first
        await metrics_collector.start_conversation(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        # Record user message
        result = await metrics_collector.record_message(
            conversation_id="test_conv_1", user_id="user_123", message_type="user", response_time_ms=None
        )

        assert result.success
        assert result.data["message_recorded"] is True
        assert result.data["message_type"] == "user"

    @pytest.mark.asyncio
    async def test_end_conversation(self, metrics_collector):
        """Test ending conversation tracking."""
        # Start conversation first
        await metrics_collector.start_conversation(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        # Record some messages
        await metrics_collector.record_message(conversation_id="test_conv_1", user_id="user_123", message_type="user")

        await metrics_collector.record_message(
            conversation_id="test_conv_1", user_id="user_123", message_type="bot", response_time_ms=1500.0
        )

        # End conversation
        result = await metrics_collector.end_conversation(
            conversation_id="test_conv_1", satisfaction_score=0.8, topics_discussed=["AI", "technology"]
        )

        assert result.success
        assert result.data["conversation_id"] == "test_conv_1"
        assert result.data["action"] == "conversation_ended"

    @pytest.mark.asyncio
    async def test_get_conversation_metrics(self, metrics_collector):
        """Test retrieving conversation metrics."""
        # Start and end a conversation
        await metrics_collector.start_conversation(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        await metrics_collector.end_conversation(conversation_id="test_conv_1", satisfaction_score=0.8)

        # Get metrics
        result = await metrics_collector.get_conversation_metrics("test_conv_1")

        assert result.success
        assert result.data["status"] == "completed"
        assert result.data["conversation"].conversation_id == "test_conv_1"

    @pytest.mark.asyncio
    async def test_get_comprehensive_stats(self, metrics_collector):
        """Test getting comprehensive statistics."""
        # Create some test data
        await metrics_collector.start_conversation(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        await metrics_collector.end_conversation(conversation_id="test_conv_1", satisfaction_score=0.8)

        # Get stats
        result = await metrics_collector.get_comprehensive_stats()

        assert result.success
        assert "system_stats" in result.data
        assert result.data["system_stats"]["total_conversations"] >= 1


class TestConversationTracer:
    """Test suite for ConversationTracer."""

    @pytest.fixture
    def conversation_tracer(self):
        """Create a conversation tracer for testing."""
        return create_conversation_tracer(max_traces=50, max_steps_per_trace=20)

    @pytest.mark.asyncio
    async def test_start_trace(self, conversation_tracer):
        """Test starting a conversation trace."""
        result = await conversation_tracer.start_trace(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        assert result.success
        assert "trace_id" in result.data
        assert result.data["action"] == "trace_started"

    @pytest.mark.asyncio
    async def test_add_step(self, conversation_tracer):
        """Test adding steps to a trace."""
        # Start trace first
        trace_result = await conversation_tracer.start_trace(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        trace_id = trace_result.data["trace_id"]

        # Add step
        result = await conversation_tracer.add_step(
            trace_id=trace_id, step_type="user_message", content="Hello, bot!", metadata={"message_id": "msg_123"}
        )

        assert result.success
        assert "step_id" in result.data
        assert result.data["step_added"] is True

    @pytest.mark.asyncio
    async def test_end_trace(self, conversation_tracer):
        """Test ending a conversation trace."""
        # Start trace and add steps
        trace_result = await conversation_tracer.start_trace(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        trace_id = trace_result.data["trace_id"]

        await conversation_tracer.add_step(trace_id=trace_id, step_type="user_message", content="Hello, bot!")

        # End trace
        result = await conversation_tracer.end_trace(trace_id=trace_id, summary="Test conversation completed")

        assert result.success
        assert result.data["trace_id"] == trace_id
        assert result.data["action"] == "trace_ended"
        assert result.data["total_steps"] >= 1

    @pytest.mark.asyncio
    async def test_analyze_conversation_flow(self, conversation_tracer):
        """Test analyzing conversation flow."""
        # Create a trace with multiple steps
        trace_result = await conversation_tracer.start_trace(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        trace_id = trace_result.data["trace_id"]

        # Add multiple steps
        await conversation_tracer.add_step(trace_id=trace_id, step_type="user_message", content="Hello, bot!")

        await conversation_tracer.add_step(
            trace_id=trace_id, step_type="bot_decision", content="Deciding how to respond"
        )

        await conversation_tracer.add_step(
            trace_id=trace_id, step_type="bot_response", content="Hello! How can I help you?"
        )

        # End trace
        await conversation_tracer.end_trace(trace_id, "Test conversation")

        # Analyze flow
        result = await conversation_tracer.analyze_conversation_flow(trace_id)

        assert result.success
        assert "flow_analysis" in result.data
        flow_analysis = result.data["flow_analysis"]
        assert flow_analysis["total_steps"] >= 3
        assert "step_types" in flow_analysis
        assert "conversation_pattern" in flow_analysis


class TestPersonalityDashboard:
    """Test suite for PersonalityDashboard."""

    @pytest.fixture
    def personality_dashboard(self):
        """Create a personality dashboard for testing."""
        return create_personality_dashboard(max_history_size=100)

    @pytest.mark.asyncio
    async def test_record_trait_snapshot(self, personality_dashboard):
        """Test recording personality trait snapshots."""
        result = await personality_dashboard.record_trait_snapshot(
            trait_name="friendliness",
            value=0.8,
            confidence=0.9,
            user_feedback={"count": 5, "positive": 4, "negative": 1},
        )

        assert result.success
        assert result.data["trait_name"] == "friendliness"
        assert result.data["current_value"] == 0.8

    @pytest.mark.asyncio
    async def test_record_user_feedback(self, personality_dashboard):
        """Test recording user feedback."""
        result = await personality_dashboard.record_user_feedback(
            user_id="user_123", trait_name="friendliness", feedback_value=0.7, context={"conversation_id": "conv_456"}
        )

        assert result.success
        assert result.data["user_id"] == "user_123"
        assert result.data["trait_name"] == "friendliness"
        assert result.data["feedback_recorded"] is True

    @pytest.mark.asyncio
    async def test_get_trait_evolution(self, personality_dashboard):
        """Test getting trait evolution data."""
        # Record multiple snapshots
        await personality_dashboard.record_trait_snapshot(trait_name="friendliness", value=0.6, confidence=0.8)

        await personality_dashboard.record_trait_snapshot(trait_name="friendliness", value=0.7, confidence=0.9)

        await personality_dashboard.record_trait_snapshot(trait_name="friendliness", value=0.8, confidence=0.95)

        # Get evolution
        result = await personality_dashboard.get_trait_evolution("friendliness")

        assert result.success
        assert result.data["trait_name"] == "friendliness"
        evolution = result.data["evolution"]
        assert len(evolution.evolution_points) >= 3
        assert evolution.trend_direction in ["increasing", "decreasing", "stable"]

    @pytest.mark.asyncio
    async def test_get_personality_analytics(self, personality_dashboard):
        """Test getting personality analytics."""
        # Create some test data
        await personality_dashboard.record_trait_snapshot(trait_name="friendliness", value=0.8, confidence=0.9)

        await personality_dashboard.record_user_feedback(
            user_id="user_123", trait_name="friendliness", feedback_value=0.7
        )

        # Get analytics
        result = await personality_dashboard.get_personality_analytics()

        assert result.success
        assert "analytics" in result.data
        analytics = result.data["analytics"]
        assert "trait_distributions" in analytics
        assert "recommendations" in analytics


class TestDiscordObservabilityIntegration:
    """Test suite for DiscordObservabilityIntegration."""

    @pytest.fixture
    def observability_integration(self):
        """Create an observability integration for testing."""
        return create_discord_observability_integration()

    @pytest.mark.asyncio
    async def test_initialize(self, observability_integration):
        """Test initializing the observability integration."""
        result = await observability_integration.initialize()

        assert result.success
        assert observability_integration._initialized is True

    @pytest.mark.asyncio
    async def test_conversation_monitoring_workflow(self, observability_integration):
        """Test complete conversation monitoring workflow."""
        # Initialize
        await observability_integration.initialize()

        # Start monitoring
        start_result = await observability_integration.start_conversation_monitoring(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        assert start_result.success

        # Track message evaluation
        eval_result = await observability_integration.track_message_evaluation(
            conversation_id="test_conv_1",
            message_content="Hello, bot!",
            evaluation_result={"should_respond": True, "confidence": 0.9},
            processing_time_ms=150.0,
        )

        assert eval_result.success

        # Track personality adaptation
        personality_result = await observability_integration.track_personality_adaptation(
            conversation_id="test_conv_1",
            trait_name="friendliness",
            old_value=0.6,
            new_value=0.7,
            adaptation_reason="positive_user_interaction",
        )

        assert personality_result.success

        # Track reward computation
        reward_result = await observability_integration.track_reward_computation(
            conversation_id="test_conv_1",
            user_id="user_123",
            reward_signals={"friendliness": 0.8, "helpfulness": 0.9},
            final_reward=0.85,
        )

        assert reward_result.success

        # End monitoring
        end_result = await observability_integration.end_conversation_monitoring(
            conversation_id="test_conv_1",
            satisfaction_score=0.8,
            topics_discussed=["AI", "conversation"],
            summary="Test conversation completed successfully",
        )

        assert end_result.success

    @pytest.mark.asyncio
    async def test_get_conversation_analytics(self, observability_integration):
        """Test getting conversation analytics."""
        # Initialize and create test data
        await observability_integration.initialize()

        await observability_integration.start_conversation_monitoring(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        await observability_integration.end_conversation_monitoring(
            conversation_id="test_conv_1", satisfaction_score=0.8
        )

        # Get analytics
        result = await observability_integration.get_conversation_analytics("test_conv_1")

        assert result.success
        assert "conversation_insights" in result.data

    @pytest.mark.asyncio
    async def test_error_tracking(self, observability_integration):
        """Test error tracking functionality."""
        # Initialize
        await observability_integration.initialize()

        # Start monitoring
        await observability_integration.start_conversation_monitoring(
            conversation_id="test_conv_1", user_id="user_123", guild_id="guild_456", channel_id="channel_789"
        )

        # Track error
        error_result = await observability_integration.track_error(
            conversation_id="test_conv_1",
            error_type="processing_error",
            error_message="Failed to process message",
            error_context={"error_code": "PROC_001"},
        )

        assert error_result.success

        # End monitoring
        await observability_integration.end_conversation_monitoring(conversation_id="test_conv_1")

    @pytest.mark.asyncio
    async def test_system_analytics(self, observability_integration):
        """Test getting system analytics."""
        # Initialize
        await observability_integration.initialize()

        # Get system analytics
        result = await observability_integration.get_system_analytics()

        assert result.success
        assert "system_insights" in result.data

    @pytest.mark.asyncio
    async def test_export_analytics_data(self, observability_integration):
        """Test exporting analytics data."""
        # Initialize
        await observability_integration.initialize()

        # Export data
        result = await observability_integration.export_analytics_data("json")

        assert result.success
        assert "export_data" in result.data
        assert result.data["export_data"]["format"] == "json"


@pytest.mark.asyncio
async def test_observability_system_integration():
    """Integration test for the complete observability system."""
    # Create all components
    metrics_collector = create_discord_metrics_collector()
    conversation_tracer = create_conversation_tracer()
    personality_dashboard = create_personality_dashboard()
    observability_integration = create_discord_observability_integration()

    # Initialize integration
    await observability_integration.initialize()

    # Test complete workflow
    conversation_id = "integration_test_conv"
    user_id = "integration_user"
    guild_id = "integration_guild"
    channel_id = "integration_channel"

    # Start monitoring
    start_result = await observability_integration.start_conversation_monitoring(
        conversation_id=conversation_id,
        user_id=user_id,
        guild_id=guild_id,
        channel_id=channel_id,
        initial_context={"test": "integration"},
    )

    assert start_result.success

    # Track various operations
    await observability_integration.track_message_evaluation(
        conversation_id=conversation_id,
        message_content="Integration test message",
        evaluation_result={"should_respond": True},
        processing_time_ms=100.0,
    )

    await observability_integration.track_personality_adaptation(
        conversation_id=conversation_id,
        trait_name="helpfulness",
        old_value=0.5,
        new_value=0.7,
        adaptation_reason="integration_test",
    )

    await observability_integration.track_reward_computation(
        conversation_id=conversation_id, user_id=user_id, reward_signals={"helpfulness": 0.8}, final_reward=0.8
    )

    # End monitoring
    end_result = await observability_integration.end_conversation_monitoring(
        conversation_id=conversation_id,
        satisfaction_score=0.9,
        topics_discussed=["integration", "testing"],
        summary="Integration test completed successfully",
    )

    assert end_result.success

    # Verify data was recorded
    analytics_result = await observability_integration.get_conversation_analytics(conversation_id)
    assert analytics_result.success

    user_analytics_result = await observability_integration.get_user_analytics(user_id)
    assert user_analytics_result.success

    system_analytics_result = await observability_integration.get_system_analytics()
    assert system_analytics_result.success


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
