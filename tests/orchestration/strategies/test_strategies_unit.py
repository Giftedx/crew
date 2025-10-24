"""Unit tests for Phase 5 orchestration strategies.

Tests strategy protocol compliance, registry operations, and basic functionality.
"""

import pytest

from ultimate_discord_intelligence_bot.orchestration.strategies import (
    FallbackStrategy,
    HierarchicalStrategy,
    MonitoringStrategy,
    StrategyRegistry,
    get_strategy_registry,
)


class TestStrategyProtocolCompliance:
    """Test that all strategies implement the protocol correctly."""

    @pytest.mark.parametrize(
        "strategy_class",
        [FallbackStrategy, HierarchicalStrategy, MonitoringStrategy],
        ids=["fallback", "hierarchical", "monitoring"],
    )
    def test_strategy_has_required_attributes(self, strategy_class):
        """Verify strategy has required protocol attributes."""
        assert hasattr(strategy_class, "name"), f"{strategy_class.__name__} missing 'name'"
        assert hasattr(strategy_class, "description"), f"{strategy_class.__name__} missing 'description'"
        assert hasattr(strategy_class, "execute_workflow"), f"{strategy_class.__name__} missing 'execute_workflow'"

    @pytest.mark.parametrize(
        "strategy_class,expected_name",
        [
            (FallbackStrategy, "fallback"),
            (HierarchicalStrategy, "hierarchical"),
            (MonitoringStrategy, "monitoring"),
        ],
    )
    def test_strategy_name_attribute(self, strategy_class, expected_name):
        """Verify strategy name attribute is correct."""
        assert strategy_class.name == expected_name

    @pytest.mark.parametrize(
        "strategy_class",
        [FallbackStrategy, HierarchicalStrategy, MonitoringStrategy],
    )
    def test_strategy_description_attribute(self, strategy_class):
        """Verify strategy has non-empty description."""
        assert isinstance(strategy_class.description, str)
        assert len(strategy_class.description) > 0

    @pytest.mark.parametrize(
        "strategy_class",
        [FallbackStrategy, HierarchicalStrategy, MonitoringStrategy],
    )
    def test_strategy_can_instantiate(self, strategy_class):
        """Verify strategy can be instantiated."""
        instance = strategy_class()
        assert instance is not None
        assert hasattr(instance, "execute_workflow")


class TestStrategyRegistry:
    """Test strategy registry operations."""

    def test_registry_initialization(self):
        """Test registry can be initialized."""
        registry = StrategyRegistry()
        assert registry is not None
        assert len(registry.list_strategies()) == 0

    def test_register_strategy_class(self):
        """Test registering a strategy class."""
        registry = StrategyRegistry()
        registry.register(FallbackStrategy)

        assert "fallback" in registry.list_strategies()
        strategy = registry.get("fallback")
        assert isinstance(strategy, FallbackStrategy)

    def test_register_strategy_with_explicit_name(self):
        """Test registering a strategy with explicit name."""
        registry = StrategyRegistry()
        registry.register(FallbackStrategy, name="custom_fallback")

        assert "custom_fallback" in registry.list_strategies()
        strategy = registry.get("custom_fallback")
        assert isinstance(strategy, FallbackStrategy)

    def test_register_multiple_strategies(self):
        """Test registering multiple strategies."""
        registry = StrategyRegistry()
        registry.register(FallbackStrategy)
        registry.register(HierarchicalStrategy)
        registry.register(MonitoringStrategy)

        strategies = registry.list_strategies()
        assert len(strategies) == 3
        assert "fallback" in strategies
        assert "hierarchical" in strategies
        assert "monitoring" in strategies

    def test_get_nonexistent_strategy(self):
        """Test getting a strategy that doesn't exist."""
        registry = StrategyRegistry()
        strategy = registry.get("nonexistent")
        assert strategy is None

    def test_unregister_strategy(self):
        """Test unregistering a strategy."""
        registry = StrategyRegistry()
        registry.register(FallbackStrategy)

        assert "fallback" in registry.list_strategies()

        result = registry.unregister("fallback")
        assert result is True
        assert "fallback" not in registry.list_strategies()

    def test_unregister_nonexistent_strategy(self):
        """Test unregistering a strategy that doesn't exist."""
        registry = StrategyRegistry()
        result = registry.unregister("nonexistent")
        assert result is False

    def test_list_strategies_includes_descriptions(self):
        """Test list_strategies returns descriptions."""
        registry = StrategyRegistry()
        registry.register(FallbackStrategy)
        registry.register(HierarchicalStrategy)

        strategies = registry.list_strategies()
        assert strategies["fallback"] == FallbackStrategy.description
        assert strategies["hierarchical"] == HierarchicalStrategy.description


class TestGlobalRegistry:
    """Test global registry singleton."""

    def test_get_strategy_registry_returns_singleton(self):
        """Test get_strategy_registry returns same instance."""
        registry1 = get_strategy_registry()
        registry2 = get_strategy_registry()
        assert registry1 is registry2

    def test_global_registry_has_registered_strategies(self):
        """Test global registry has Phase 5 strategies registered."""
        # Note: This test depends on facade module import
        # which auto-registers strategies
        from ultimate_discord_intelligence_bot.orchestration import facade  # noqa: F401

        registry = get_strategy_registry()
        strategies = registry.list_strategies()

        # Phase 5 strategies should be registered
        assert "fallback" in strategies
        assert "hierarchical" in strategies
        assert "monitoring" in strategies


class TestStrategyInstantiation:
    """Test strategy instances."""

    def test_fallback_strategy_instantiation(self):
        """Test FallbackStrategy can be instantiated."""
        strategy = FallbackStrategy()
        assert strategy.name == "fallback"
        assert hasattr(strategy, "_orchestrator")

    def test_hierarchical_strategy_instantiation(self):
        """Test HierarchicalStrategy can be instantiated."""
        strategy = HierarchicalStrategy()
        assert strategy.name == "hierarchical"
        assert hasattr(strategy, "_orchestrator")

    def test_monitoring_strategy_instantiation(self):
        """Test MonitoringStrategy can be instantiated."""
        strategy = MonitoringStrategy()
        assert strategy.name == "monitoring"
        assert hasattr(strategy, "_orchestrator")


@pytest.mark.asyncio
class TestStrategyLifecycle:
    """Test strategy lifecycle methods."""

    async def test_strategy_initialize(self):
        """Test strategy initialize() method."""
        strategy = FallbackStrategy()
        # Should not raise
        await strategy.initialize()

    async def test_strategy_cleanup(self):
        """Test strategy cleanup() method."""
        strategy = FallbackStrategy()
        # Should not raise
        await strategy.cleanup()

    async def test_strategy_full_lifecycle(self):
        """Test full strategy lifecycle."""
        strategy = FallbackStrategy()

        await strategy.initialize()
        # Strategy should be ready to use
        assert strategy is not None

        await strategy.cleanup()
        # Strategy should clean up without error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
