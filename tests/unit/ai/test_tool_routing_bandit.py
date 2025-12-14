"""Unit tests for ToolRoutingBandit."""

from platform.rl.tool_routing_bandit import ToolCapability, ToolContextualBandit, ToolRoutingBandit, get_tool_router
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def tool_router():
    """Create tool router instance for testing."""
    return ToolRoutingBandit()


@pytest.fixture
def mock_tool_mapping():
    """Create mock tool mapping."""
    return {
        "analysis.sentiment": MagicMock(category="analysis", capabilities=["sentiment", "emotion"], cost_tier="low"),
        "verification.fact_check": MagicMock(
            category="verification", capabilities=["fact_checking", "validation"], cost_tier="medium"
        ),
        "memory.vector_search": MagicMock(category="memory", capabilities=["search", "retrieval"], cost_tier="low"),
    }


class TestToolCapability:
    """Test ToolCapability dataclass."""

    def test_create_capability(self):
        """Test creating tool capability."""
        cap = ToolCapability(
            tool_id="sentiment_tool",
            tool_name="Sentiment Tool",
            category="analysis",
            capabilities=["sentiment", "emotion"],
            cost_score=0.1,
            average_latency_ms=500.0,
        )
        assert cap.tool_id == "sentiment_tool"
        assert cap.category == "analysis"
        assert "sentiment" in cap.capabilities
        assert cap.cost_score == 0.1


class TestToolContextualBandit:
    """Test ToolContextualBandit class."""

    def test_initialization(self):
        """Test bandit initialization."""
        tools = [
            ToolCapability(tool_id="tool1", tool_name="T1", category="cat"),
            ToolCapability(tool_id="tool2", tool_name="T2", category="cat"),
            ToolCapability(tool_id="tool3", tool_name="T3", category="cat"),
        ]
        bandit = ToolContextualBandit(tools, context_dim=15)
        assert len(bandit.tools) == 3
        assert bandit.context_dim == 15
        assert "tool1" in bandit.tool_parameters
        assert bandit.tool_parameters["tool1"].shape == (15,)

    def test_select_tool(self):
        """Test tool selection."""
        tools = [
            ToolCapability(tool_id="tool1", tool_name="T1", category="cat"),
            ToolCapability(tool_id="tool2", tool_name="T2", category="cat"),
            ToolCapability(tool_id="tool3", tool_name="T3", category="cat"),
        ]
        bandit = ToolContextualBandit(tools, context_dim=5)
        context = [0.5, 0.7, 0.3, 0.9, 0.2]
        result = bandit.select_tool(context, task_type="cat")
        assert result.success
        assert result.data.tool_id in ["tool1", "tool2", "tool3"]
        assert 0.0 <= result.data.confidence <= 1.0

    def test_disabled_tools_excluded(self):
        """Test that disabled/unhealthy tools are not selected."""
        tools = [
            ToolCapability(tool_id="tool1", tool_name="T1", category="cat", health_score=0.1),  # Unhealthy
            ToolCapability(tool_id="tool2", tool_name="T2", category="cat", health_score=1.0),
        ]
        bandit = ToolContextualBandit(tools, context_dim=3)
        context = [0.5, 0.5, 0.5]

        # Should always select tool2 as tool1 is unhealthy
        for _ in range(10):
            result = bandit.select_tool(context, task_type="cat")
            assert result.success
            assert result.data.tool_id == "tool2"

    def test_update(self):
        """Test bandit parameter update."""
        tools = [ToolCapability(tool_id="tool1", tool_name="T1", category="cat")]
        bandit = ToolContextualBandit(tools, context_dim=3)
        import numpy as np
        context = np.array([0.5, 0.5, 0.5])
        initial_params = bandit.tool_parameters["tool1"].copy()
        bandit.update("tool1", context, reward=1.0)
        assert not all(bandit.tool_parameters["tool1"] == initial_params)


class TestToolRoutingBandit:
    """Test ToolRoutingBandit class."""

    def test_singleton_pattern(self):
        """Test that get_tool_router returns same instance."""
        router1 = get_tool_router()
        router2 = get_tool_router()
        assert router1 is router2

    @patch("src.platform.rl.tool_routing_bandit.TOOL_MAPPING")
    def test_discover_tools(self, mock_mapping, tool_router, mock_tool_mapping):
        """Test tool discovery from registry."""
        mock_mapping.items = MagicMock(return_value=mock_tool_mapping.items())
        # Force re-discovery since tool_router might be initialized already
        tool_router.tools = tool_router._discover_tools()
        assert len(tool_router.tools) > 0

    @pytest.mark.asyncio
    @patch("src.platform.rl.tool_routing_bandit.TOOL_MAPPING")
    async def test_route_tool_request(self, mock_mapping, tool_router, mock_tool_mapping):
        """Test routing a tool request."""
        mock_mapping.items = MagicMock(return_value=mock_tool_mapping.items())
        tool_router.tools = tool_router._discover_tools()
        # Re-init bandit with discovered tools
        tool_router.bandit = ToolContextualBandit(tool_router.tools)

        result = await tool_router.route_tool_request(
            task_description="Analyze sentiment of text",
            context={"complexity": 0.7, "data_size": 5000},
            task_type="analysis",
        )
        assert result.success
        selection = result.data
        # With mocked tools, one of them should be selected
        # Note: In _discover_tools implementation, it uses tool_name as tool_id
        # Our mock_tool_mapping keys are like "analysis.sentiment"
        # The _discover_tools loop: for tool_name, module_path in TOOL_MAPPING.items()
        #   tool_id=tool_name
        # So tool_ids will be "analysis.sentiment" etc.
        assert selection.tool_id in [t.tool_id for t in tool_router.tools]
        assert 0.0 <= selection.confidence <= 1.0

    @patch("src.platform.rl.tool_routing_bandit.TOOL_MAPPING")
    def test_submit_tool_feedback(self, mock_mapping, tool_router, mock_tool_mapping):
        """Test submitting tool feedback."""
        mock_mapping.items = MagicMock(return_value=mock_tool_mapping.items())
        tool_router.tools = tool_router._discover_tools()
        tool_id = tool_router.tools[0].tool_id

        tool_router.submit_tool_feedback(
            tool_id=tool_id, context={"complexity": 0.7}, success=True, latency_ms=800, quality_score=0.9
        )
        assert len(tool_router.feedback_queue) == 1

    @patch("src.platform.rl.tool_routing_bandit.TOOL_MAPPING")
    def test_process_feedback_batch(self, mock_mapping, tool_router, mock_tool_mapping):
        """Test batch feedback processing."""
        mock_mapping.items = MagicMock(return_value=mock_tool_mapping.items())
        tool_router.tools = tool_router._discover_tools()
        tool_router.bandit = ToolContextualBandit(tool_router.tools)

        tool_id = tool_router.tools[0].tool_id
        for i in range(5):
            tool_router.submit_tool_feedback(
                tool_id=tool_id,
                context={"complexity": 0.5 + i * 0.1},
                success=True,
                latency_ms=800 + i * 100,
                quality_score=0.8 + i * 0.02,
            )
        tool_router.process_feedback_batch()
        assert len(tool_router.feedback_queue) == 0
        stats = tool_router.bandit.get_tool_statistics()[tool_id]
        assert stats["usage_count"] == 5

    @patch("src.platform.rl.tool_routing_bandit.TOOL_MAPPING")
    def test_health_monitoring(self, mock_mapping, tool_router, mock_tool_mapping):
        """Test tool health monitoring."""
        mock_mapping.items = MagicMock(return_value=mock_tool_mapping.items())
        tool_router.tools = tool_router._discover_tools()
        tool_router.bandit = ToolContextualBandit(tool_router.tools)

        tool_id = tool_router.tools[0].tool_id
        for i in range(20):
            tool_router.submit_tool_feedback(
                tool_id=tool_id, context={}, success=False, latency_ms=5000, quality_score=0.1
            )
        tool_router.process_feedback_batch()
        stats = tool_router.bandit.get_tool_statistics()[tool_id]
        health_score = stats.get("health_score", 1.0)
        # Success rate update logic: 0.9 * rate + 0.1 * 0.0
        # After 20 fails, it should be very low
        assert health_score < 1.0

    @patch("src.platform.rl.tool_routing_bandit.TOOL_MAPPING")
    def test_get_metrics(self, mock_mapping, tool_router, mock_tool_mapping):
        """Test metrics collection."""
        mock_mapping.items = MagicMock(return_value=mock_tool_mapping.items())
        tool_router.tools = tool_router._discover_tools()
        tool_router.bandit = ToolContextualBandit(tool_router.tools)

        metrics = tool_router.get_statistics()
        assert "total_tools" in metrics
        assert "tool_statistics" in metrics
        assert "feedback_queue_size" in metrics
        assert metrics["total_tools"] > 0


class TestContextExtraction:
    """Test context feature extraction."""

    @patch("src.platform.rl.tool_routing_bandit.TOOL_MAPPING")
    def test_extract_context_vector(self, mock_mapping, tool_router, mock_tool_mapping):
        """Test context vector extraction."""
        mock_mapping.items = MagicMock(return_value=mock_tool_mapping.items())

        context = {
            "complexity": 0.7,
            "data_size": 5000,
            "urgency": 0.8,
            "required_accuracy": 0.95,
            "budget_limit": 100,
            "content_type": "text",
            "is_realtime": True,
        }
        vector = tool_router._extract_context_vector(context)
        assert len(vector) == 15
        assert all(isinstance(v, (int, float)) for v in vector)

    @patch("src.platform.rl.tool_routing_bandit.TOOL_MAPPING")
    def test_context_defaults(self, mock_mapping, tool_router, mock_tool_mapping):
        """Test that context extraction handles missing values."""
        mock_mapping.items = MagicMock(return_value=mock_tool_mapping.items())

        vector = tool_router._extract_context_vector({})
        assert len(vector) == 15
        assert all(0.0 <= v <= 1.0 or v == 0 for v in vector)
