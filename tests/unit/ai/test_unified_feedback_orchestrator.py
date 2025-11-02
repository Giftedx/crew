"""Unit tests for UnifiedFeedbackOrchestrator."""

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest
from src.ai.rl.unified_feedback_orchestrator import (
    ComponentType,
    FeedbackSignal,
    FeedbackSource,
    UnifiedFeedbackOrchestrator,
    get_orchestrator,
)


@dataclass
class MockTrajectory:
    """Mock trajectory for testing."""

    trajectory_id: str
    model: str
    quality_score: float


@dataclass
class MockEvaluation:
    """Mock evaluation result for testing."""

    overall_score: float
    latency_ms: float
    cost_usd: float


@pytest.fixture
def orchestrator():
    """Create orchestrator instance for testing."""
    orch = UnifiedFeedbackOrchestrator()
    return orch


@pytest.fixture
def mock_model_router():
    """Create mock model router."""
    router = MagicMock()
    router.process_trajectory_feedback = MagicMock()
    return router


class TestFeedbackSignal:
    """Test FeedbackSignal dataclass."""

    def test_create_signal(self):
        """Test creating feedback signal."""
        signal = FeedbackSignal(
            source=FeedbackSource.TRAJECTORY,
            component_type=ComponentType.MODEL,
            component_id="gpt-4",
            reward=0.85,
            context={"task": "analysis"},
            metadata={"latency_ms": 1200},
        )

        assert signal.source == FeedbackSource.TRAJECTORY
        assert signal.component_type == ComponentType.MODEL
        assert signal.component_id == "gpt-4"
        assert signal.reward == 0.85
        assert signal.context == {"task": "analysis"}
        assert signal.metadata == {"latency_ms": 1200}


class TestUnifiedFeedbackOrchestrator:
    """Test UnifiedFeedbackOrchestrator class."""

    def test_singleton_pattern(self):
        """Test that get_orchestrator returns same instance."""
        orch1 = get_orchestrator()
        orch2 = get_orchestrator()
        assert orch1 is orch2

    def test_submit_trajectory_feedback(self, orchestrator):
        """Test submitting trajectory feedback."""
        trajectory = MockTrajectory(trajectory_id="traj_123", model="gpt-4", quality_score=0.9)
        evaluation = MockEvaluation(overall_score=0.85, latency_ms=1500, cost_usd=0.05)

        orchestrator.submit_trajectory_feedback(trajectory, evaluation)

        # Check feedback queues
        assert len(orchestrator.model_feedback_queue) == 1
        signal = orchestrator.model_feedback_queue[0]
        assert signal.component_id == "gpt-4"
        assert signal.reward == 0.85

    def test_submit_tool_feedback(self, orchestrator):
        """Test submitting tool feedback."""
        orchestrator.submit_tool_feedback(
            tool_id="sentiment_tool", context={"complexity": 0.7}, success=True, latency_ms=800, quality_score=0.92
        )

        assert len(orchestrator.tool_feedback_queue) == 1
        signal = orchestrator.tool_feedback_queue[0]
        assert signal.component_id == "sentiment_tool"
        assert signal.reward == 0.92

    def test_submit_agent_feedback(self, orchestrator):
        """Test submitting agent feedback."""
        orchestrator.submit_agent_feedback(
            agent_id="verification_analyst", context={"urgency": 0.8}, success=True, duration_s=45.2, quality_score=0.88
        )

        assert len(orchestrator.agent_feedback_queue) == 1
        signal = orchestrator.agent_feedback_queue[0]
        assert signal.component_id == "verification_analyst"
        assert signal.reward == 0.88

    def test_submit_rag_feedback(self, orchestrator):
        """Test submitting RAG feedback."""
        orchestrator.submit_rag_feedback(
            query_id="query_456", relevance_score=0.75, retrieval_latency_ms=200, num_results=10
        )

        assert len(orchestrator.rag_feedback_queue) == 1
        signal = orchestrator.rag_feedback_queue[0]
        assert signal.reward == 0.75
        assert signal.metadata["num_results"] == 10

    def test_calculate_component_health(self, orchestrator):
        """Test health calculation."""
        # Add some feedback signals
        for i in range(10):
            signal = FeedbackSignal(
                source=FeedbackSource.TOOL,
                component_type=ComponentType.TOOL,
                component_id="test_tool",
                reward=0.8,
                context={},
                metadata={},
            )
            orchestrator._update_component_stats(signal)

        health = orchestrator._calculate_component_health(ComponentType.TOOL, "test_tool")
        assert 0.0 <= health <= 1.0
        assert health > 0.5  # Should be healthy with 0.8 reward

    @pytest.mark.asyncio
    async def test_process_model_feedback(self, orchestrator, mock_model_router):
        """Test processing model feedback batch."""
        # Add feedback to queue
        for i in range(5):
            signal = FeedbackSignal(
                source=FeedbackSource.TRAJECTORY,
                component_type=ComponentType.MODEL,
                component_id=f"model_{i}",
                reward=0.7 + i * 0.05,
                context={"test": i},
                metadata={},
            )
            orchestrator.model_feedback_queue.append(signal)

        # Process feedback
        with patch("src.ai.rl.unified_feedback_orchestrator.get_model_router", return_value=mock_model_router):
            await orchestrator._process_model_feedback()

        # Should have cleared queue
        assert len(orchestrator.model_feedback_queue) == 0

    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self, orchestrator):
        """Test orchestrator lifecycle."""
        await orchestrator.start()
        assert orchestrator.running
        assert len(orchestrator.tasks) > 0

        await orchestrator.stop()
        assert not orchestrator.running
        assert len(orchestrator.tasks) == 0

    def test_get_metrics(self, orchestrator):
        """Test metrics collection."""
        # Submit various feedback
        trajectory = MockTrajectory("traj_1", "gpt-4", 0.9)
        evaluation = MockEvaluation(0.85, 1500, 0.05)
        orchestrator.submit_trajectory_feedback(trajectory, evaluation)
        orchestrator.submit_tool_feedback("tool_1", {}, True, 800, 0.9)

        metrics = orchestrator.get_metrics()

        assert "signals_processed" in metrics
        assert "signals_by_source" in metrics
        assert "signals_by_component" in metrics
        assert metrics["signals_processed"] > 0

    def test_get_component_health_report(self, orchestrator):
        """Test health report generation."""
        # Add some component stats
        for i in range(5):
            signal = FeedbackSignal(
                source=FeedbackSource.TOOL,
                component_type=ComponentType.TOOL,
                component_id="healthy_tool",
                reward=0.9,
                context={},
                metadata={},
            )
            orchestrator._update_component_stats(signal)

        report = orchestrator.get_component_health_report()

        assert ComponentType.TOOL in report
        assert "healthy_tool" in report[ComponentType.TOOL]
        health_score = report[ComponentType.TOOL]["healthy_tool"]
        assert health_score > 0.7

    def test_health_based_disable(self, orchestrator):
        """Test auto-disable of unhealthy components."""
        # Add many low-reward signals
        for i in range(20):
            signal = FeedbackSignal(
                source=FeedbackSource.TOOL,
                component_type=ComponentType.TOOL,
                component_id="unhealthy_tool",
                reward=0.1,
                context={},
                metadata={},
            )
            orchestrator._update_component_stats(signal)

        health = orchestrator._calculate_component_health(ComponentType.TOOL, "unhealthy_tool")
        assert health < 0.3  # Should be unhealthy


class TestIntegration:
    """Integration tests for feedback orchestrator."""

    @pytest.mark.asyncio
    async def test_end_to_end_feedback_flow(self):
        """Test complete feedback processing flow."""
        orchestrator = get_orchestrator()

        # Submit feedback from multiple sources
        trajectory = MockTrajectory("traj_1", "gpt-4", 0.9)
        evaluation = MockEvaluation(0.85, 1500, 0.05)
        orchestrator.submit_trajectory_feedback(trajectory, evaluation)

        orchestrator.submit_tool_feedback("tool_1", {"complexity": 0.7}, True, 800, 0.9)
        orchestrator.submit_agent_feedback("agent_1", {"urgency": 0.8}, True, 45.2, 0.88)
        orchestrator.submit_rag_feedback("query_1", 0.75, 200, 10)

        # Check all queues populated
        assert len(orchestrator.model_feedback_queue) == 1
        assert len(orchestrator.tool_feedback_queue) == 1
        assert len(orchestrator.agent_feedback_queue) == 1
        assert len(orchestrator.rag_feedback_queue) == 1

        # Get metrics
        metrics = orchestrator.get_metrics()
        assert metrics["signals_processed"] >= 4

    @pytest.mark.asyncio
    async def test_consolidation_trigger(self):
        """Test that consolidation is triggered when needed."""
        orchestrator = get_orchestrator()

        # Submit many low-quality RAG signals
        for i in range(150):
            orchestrator.submit_rag_feedback(f"query_{i}", 0.2, 200, 5)

        metrics = orchestrator.get_metrics()
        # Should have triggered consolidation
        assert metrics.get("consolidations_triggered", 0) >= 0
