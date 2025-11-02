"""Tests for the unified routing system."""

import time
from unittest.mock import patch

from ultimate_discord_intelligence_bot.core.routing.base_router import (
    BanditRouter,
    CostAwareRouter,
    FallbackRouter,
    LatencyOptimizedRouter,
    RoutingDecision,
    RoutingRequest,
    UnifiedRouter,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestRoutingRequest:
    """Test RoutingRequest dataclass."""

    def test_routing_request_creation(self) -> None:
        """Test basic routing request creation."""
        request = RoutingRequest(
            prompt="Test prompt",
            context={"key": "value"},
            constraints={"minimize_cost": True},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert request.prompt == "Test prompt"
        assert request.context == {"key": "value"}
        assert request.constraints == {"minimize_cost": True}
        assert request.tenant == "test_tenant"
        assert request.workspace == "test_workspace"
        assert request.request_id is not None
        assert len(request.request_id) == 16

    def test_routing_request_id_generation(self) -> None:
        """Test that request IDs are generated automatically."""
        request1 = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        request2 = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        # Should have different IDs due to timestamp
        assert request1.request_id != request2.request_id


class TestRoutingDecision:
    """Test RoutingDecision dataclass."""

    def test_routing_decision_creation(self) -> None:
        """Test basic routing decision creation."""
        decision = RoutingDecision(
            model_id="gpt-4o-mini",
            provider="openai",
            estimated_cost=0.001,
            estimated_latency=1.5,
            confidence=0.8,
            reasoning="Test reasoning",
            request_id="test_request_123",
            strategy_used="bandit",
            timestamp=time.time(),
        )

        assert decision.model_id == "gpt-4o-mini"
        assert decision.provider == "openai"
        assert decision.estimated_cost == 0.001
        assert decision.estimated_latency == 1.5
        assert decision.confidence == 0.8
        assert decision.reasoning == "Test reasoning"
        assert decision.request_id == "test_request_123"
        assert decision.strategy_used == "bandit"


class TestBanditRouter:
    """Test BanditRouter implementation."""

    def test_bandit_router_creation(self) -> None:
        """Test bandit router initialization."""
        router = BanditRouter()
        assert router.get_strategy_name() == "bandit"

    def test_bandit_router_route(self) -> None:
        """Test bandit router routing."""
        router = BanditRouter()
        request = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result = router.route(request)
        assert result.success
        assert isinstance(result.data, dict)
        assert "data" in result.data
        assert isinstance(result.data["data"], RoutingDecision)
        decision = result.data["data"]
        assert decision.strategy_used == "bandit"


class TestCostAwareRouter:
    """Test CostAwareRouter implementation."""

    def test_cost_aware_router_creation(self) -> None:
        """Test cost-aware router initialization."""
        router = CostAwareRouter()
        assert router.get_strategy_name() == "cost_aware"

    def test_cost_aware_router_route(self) -> None:
        """Test cost-aware router routing."""
        router = CostAwareRouter()
        request = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={"minimize_cost": True},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result = router.route(request)
        assert result.success
        assert isinstance(result.data, dict)
        assert "data" in result.data
        assert isinstance(result.data["data"], RoutingDecision)
        decision = result.data["data"]
        assert decision.strategy_used == "cost_aware"


class TestLatencyOptimizedRouter:
    """Test LatencyOptimizedRouter implementation."""

    def test_latency_optimized_router_creation(self) -> None:
        """Test latency-optimized router initialization."""
        router = LatencyOptimizedRouter()
        assert router.get_strategy_name() == "latency_optimized"

    def test_latency_optimized_router_route(self) -> None:
        """Test latency-optimized router routing."""
        router = LatencyOptimizedRouter()
        request = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={"minimize_latency": True},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result = router.route(request)
        assert result.success
        assert isinstance(result.data, dict)
        assert "data" in result.data
        assert isinstance(result.data["data"], RoutingDecision)
        decision = result.data["data"]
        assert decision.strategy_used == "latency_optimized"


class TestFallbackRouter:
    """Test FallbackRouter implementation."""

    def test_fallback_router_creation(self) -> None:
        """Test fallback router initialization."""
        router = FallbackRouter()
        assert router.get_strategy_name() == "fallback"
        assert len(router.fallback_chain) > 0

    def test_fallback_router_route(self) -> None:
        """Test fallback router routing."""
        router = FallbackRouter()
        request = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result = router.route(request)
        assert result.success
        assert isinstance(result.data, dict)
        assert "data" in result.data
        assert isinstance(result.data["data"], RoutingDecision)
        decision = result.data["data"]
        assert decision.strategy_used == "fallback"


class TestUnifiedRouter:
    """Test UnifiedRouter implementation."""

    def test_unified_router_creation(self) -> None:
        """Test unified router initialization."""
        router = UnifiedRouter()
        assert len(router.strategies) == 4
        assert "bandit" in router.strategies
        assert "cost_aware" in router.strategies
        assert "latency_optimized" in router.strategies
        assert "fallback" in router.strategies
        assert router.default_strategy == "bandit"

    def test_strategy_selection_cost_minimization(self) -> None:
        """Test strategy selection for cost minimization."""
        router = UnifiedRouter()
        request = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={"minimize_cost": True},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result = router.route(request)
        assert result.success
        assert isinstance(result.data, dict)
        assert "data" in result.data
        assert isinstance(result.data["data"], RoutingDecision)
        decision = result.data["data"]
        assert decision.strategy_used == "cost_aware"

    def test_strategy_selection_latency_minimization(self) -> None:
        """Test strategy selection for latency minimization."""
        router = UnifiedRouter()
        request = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={"minimize_latency": True},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result = router.route(request)
        assert result.success
        assert isinstance(result.data, dict)
        assert "data" in result.data
        assert isinstance(result.data["data"], RoutingDecision)
        decision = result.data["data"]
        assert decision.strategy_used == "latency_optimized"

    def test_strategy_selection_default_bandit(self) -> None:
        """Test default strategy selection (bandit)."""
        router = UnifiedRouter()
        request = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result = router.route(request)
        assert result.success
        assert isinstance(result.data, dict)
        assert "data" in result.data
        assert isinstance(result.data["data"], RoutingDecision)
        decision = result.data["data"]
        assert decision.strategy_used == "bandit"

    def test_caching_behavior(self) -> None:
        """Test that routing decisions are cached."""
        router = UnifiedRouter()
        request = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        # First request should not be cached
        result1 = router.route(request)
        assert result1.success

        # Second request should be cached
        result2 = router.route(request)
        assert result2.success

        # Should be the same decision (cached)
        decision1 = result1.data["data"]
        decision2 = result2.data["data"]
        assert decision1.request_id == decision2.request_id

    def test_cache_key_generation(self) -> None:
        """Test cache key generation."""
        router = UnifiedRouter()

        # Same prompt and constraints should generate same cache key
        request1 = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={"minimize_cost": True},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        request2 = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={"minimize_cost": True},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        key1 = router._generate_cache_key(request1)
        key2 = router._generate_cache_key(request2)

        assert key1 == key2
        assert len(key1) == 16

    def test_strategy_stats(self) -> None:
        """Test strategy statistics."""
        router = UnifiedRouter()
        stats = router.get_strategy_stats()

        assert "cache_size" in stats
        assert "available_strategies" in stats
        assert "default_strategy" in stats
        assert stats["cache_size"] == 0
        assert len(stats["available_strategies"]) == 4
        assert stats["default_strategy"] == "bandit"

    def test_cache_clearing(self) -> None:
        """Test cache clearing functionality."""
        router = UnifiedRouter()
        request = RoutingRequest(
            prompt="Test prompt",
            context={},
            constraints={},
            tenant="test_tenant",
            workspace="test_workspace",
            request_id="test_request_123",  # Fixed ID for deterministic caching
        )

        # Make a request to populate cache
        router.route(request)
        # Make the same request again to ensure it's cached
        router.route(request)
        assert len(router.cache) > 0

        # Clear cache
        router.clear_cache()
        assert len(router.cache) == 0

    def test_fallback_on_strategy_failure(self) -> None:
        """Test fallback behavior when primary strategy fails."""
        router = UnifiedRouter()

        # Mock bandit router to fail
        with patch.object(router.strategies["bandit"], "route") as mock_route:
            mock_route.return_value = StepResult.fail("Bandit routing failed")

            request = RoutingRequest(
                prompt="Test prompt",
                context={},
                constraints={},
                tenant="test_tenant",
                workspace="test_workspace",
            )

            result = router.route(request)
            assert result.success
            assert isinstance(result.data, dict)
            assert "data" in result.data
            assert isinstance(result.data["data"], RoutingDecision)
            decision = result.data["data"]
            assert decision.strategy_used == "fallback"
