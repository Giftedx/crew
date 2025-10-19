#!/usr/bin/env python3
"""Quick validation script for Phase 5 orchestration strategies.

Tests registry operations, strategy loading, and facade integration.
"""

import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / "src"))

from ultimate_discord_intelligence_bot.orchestration.strategies import (
    FallbackStrategy,
    HierarchicalStrategy,
    MonitoringStrategy,
    get_strategy_registry,
)


def test_strategy_attributes():
    """Verify strategies have required protocol attributes."""
    print("Testing strategy attributes...")

    strategies = [FallbackStrategy, HierarchicalStrategy, MonitoringStrategy]
    for strategy_class in strategies:
        assert hasattr(strategy_class, "name"), (
            f"{strategy_class.__name__} missing 'name'"
        )
        assert hasattr(strategy_class, "description"), (
            f"{strategy_class.__name__} missing 'description'"
        )
        assert hasattr(strategy_class, "execute_workflow"), (
            f"{strategy_class.__name__} missing 'execute_workflow'"
        )
        print(f"  ✅ {strategy_class.__name__} has required attributes")


def test_registry_operations():
    """Test strategy registry registration and lookup."""
    print("\nTesting registry operations...")

    registry = get_strategy_registry()

    # Register strategies
    registry.register(FallbackStrategy)
    registry.register(HierarchicalStrategy)
    registry.register(MonitoringStrategy)
    print("  ✅ Registered 3 strategies")

    # List strategies
    strategies = registry.list_strategies()
    assert "fallback" in strategies, "FallbackStrategy not in registry"
    assert "hierarchical" in strategies, "HierarchicalStrategy not in registry"
    assert "monitoring" in strategies, "MonitoringStrategy not in registry"
    print(f"  ✅ Registry contains {len(strategies)} strategies")

    # Get specific strategy
    fallback = registry.get("fallback")
    assert fallback is FallbackStrategy, "Registry returned wrong strategy"
    print("  ✅ Strategy lookup works")


def test_facade_integration():
    """Test facade can load strategies from registry."""
    print("\nTesting facade integration...")

    from ultimate_discord_intelligence_bot.orchestration import (
        OrchestrationFacade,
        OrchestrationStrategy,
    )

    # Test fallback strategy
    facade = OrchestrationFacade(strategy=OrchestrationStrategy.FALLBACK)
    orchestrator = facade._get_orchestrator()
    assert isinstance(orchestrator, FallbackStrategy), "Facade loaded wrong strategy"
    print("  ✅ Facade loaded FallbackStrategy from registry")

    # Test hierarchical strategy
    facade = OrchestrationFacade(strategy=OrchestrationStrategy.HIERARCHICAL)
    orchestrator = facade._get_orchestrator()
    assert isinstance(orchestrator, HierarchicalStrategy), (
        "Facade loaded wrong strategy"
    )
    print("  ✅ Facade loaded HierarchicalStrategy from registry")

    # Test monitoring strategy
    facade = OrchestrationFacade(strategy=OrchestrationStrategy.MONITORING)
    orchestrator = facade._get_orchestrator()
    assert isinstance(orchestrator, MonitoringStrategy), "Facade loaded wrong strategy"
    print("  ✅ Facade loaded MonitoringStrategy from registry")


def test_strategy_instantiation():
    """Test strategies can be instantiated."""
    print("\nTesting strategy instantiation...")

    strategies = [
        ("FallbackStrategy", FallbackStrategy),
        ("HierarchicalStrategy", HierarchicalStrategy),
        ("MonitoringStrategy", MonitoringStrategy),
    ]

    for name, strategy_class in strategies:
        instance = strategy_class()
        assert hasattr(instance, "execute_workflow"), (
            f"{name} instance missing execute_workflow"
        )
        print(f"  ✅ {name} instantiates successfully")


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Phase 5 Orchestration Strategies - Validation")
    print("=" * 60)

    tests = [
        test_strategy_attributes,
        test_registry_operations,
        test_facade_integration,
        test_strategy_instantiation,
    ]

    for test_func in tests:
        try:
            test_func()
        except Exception as exc:
            print(f"\n❌ {test_func.__name__} FAILED: {exc}")
            return 1

    print("\n" + "=" * 60)
    print("✅ All Phase 5 validation tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
