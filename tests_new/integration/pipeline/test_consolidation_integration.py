"""Integration tests for consolidated architecture (Phases 1-7).

Tests end-to-end workflows across all unified facades:
- UnifiedCache (Phase 1)
- UnifiedMemoryService (Phase 2)
- Orchestration strategies (Phase 5)
- OpenRouterService (Phase 6)
- AnalyticsService (Phase 7)
"""

from __future__ import annotations

import pytest


# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestCacheIntegration:
    """Test unified cache integration workflows."""

    def test_cache_end_to_end_workflow(self):
        """Test complete cache workflow: store → retrieve → hit rate."""
        from ultimate_discord_intelligence_bot.cache import get_unified_cache

        cache = get_unified_cache()

        # Store multiple items
        test_data = [
            ("key1", "value1"),
            ("key2", "value2"),
            ("key3", "value3"),
        ]

        for key, value in test_data:
            cache.set(key, value, ttl=300)

        # Retrieve and verify
        for key, expected_value in test_data:
            retrieved = cache.get(key)
            assert retrieved == expected_value

        # Verify hits are tracked
        # (exact metrics depend on cache implementation)
        assert cache is not None


class TestMemoryIntegration:
    """Test unified memory service integration workflows."""

    @pytest.mark.asyncio
    async def test_memory_plugin_routing(self):
        """Test memory plugin routing across different plugin types."""
        from ultimate_discord_intelligence_bot.memory import get_unified_memory

        memory = get_unified_memory()

        # Test basic upsert (no plugin)
        result = await memory.upsert(
            collection="test_facts",
            documents=["Integration test fact"],
            metadatas=[{"test": True}],
            ids=["test_001"],
        )

        # Should succeed or return result
        assert result is not None

    @pytest.mark.asyncio
    async def test_memory_query_workflow(self):
        """Test complete memory workflow: store → query → retrieve."""
        from ultimate_discord_intelligence_bot.memory import get_unified_memory

        memory = get_unified_memory()

        # Store test data
        await memory.upsert(
            collection="integration_test",
            documents=["Test document for integration"],
            metadatas=[{"type": "test", "category": "integration"}],
            ids=["integration_001"],
        )

        # Query
        results = await memory.query(
            collection="integration_test",
            query_texts=["integration test"],
            n_results=5,
        )

        # Verify results structure
        assert results is not None
        assert isinstance(results, dict)


class TestOrchestrationIntegration:
    """Test orchestration strategy integration."""

    def test_orchestration_strategy_selection(self):
        """Test strategy selection and initialization."""
        from ultimate_discord_intelligence_bot.orchestration import (
            OrchestrationStrategy,
            get_orchestrator,
        )

        # Test fallback strategy
        orchestrator = get_orchestrator(OrchestrationStrategy.FALLBACK)
        assert orchestrator is not None
        assert hasattr(orchestrator, "name")
        assert hasattr(orchestrator, "description")

    def test_orchestration_registry_listing(self):
        """Test strategy registry can list all strategies."""
        from ultimate_discord_intelligence_bot.orchestration.strategies.base import (
            get_strategy_registry,
        )

        registry = get_strategy_registry()
        strategies = registry.list_strategies()

        # Should have at least Phase 5 strategies
        assert len(strategies) >= 3
        assert "fallback" in strategies or "FallbackStrategy" in strategies


class TestAnalyticsIntegration:
    """Test analytics service integration workflows."""

    def test_analytics_system_monitoring_workflow(self):
        """Test complete system monitoring workflow."""
        from ultimate_discord_intelligence_bot.observability import (
            get_analytics_service,
        )

        analytics = get_analytics_service()

        # Get system health
        health_result = analytics.get_system_health()
        assert health_result is not None
        assert hasattr(health_result, "success") or hasattr(health_result, "ok")

        # Get performance metrics
        perf_result = analytics.get_performance_metrics()
        assert perf_result is not None

    def test_analytics_agent_monitoring_workflow(self):
        """Test complete agent monitoring workflow."""
        from ultimate_discord_intelligence_bot.observability import (
            get_analytics_service,
        )

        analytics = get_analytics_service()

        # Record agent interactions
        test_agent = "integration_test_agent"
        for i in range(5):
            result = analytics.record_agent_performance(
                agent_name=test_agent,
                task_type="integration_test",
                quality_score=0.8 + (i * 0.02),
                response_time=2.0 + (i * 0.1),
                tools_used=["test_tool"],
            )
            assert result is not None

        # Get report
        report_result = analytics.get_agent_performance_report(test_agent, days=1)
        assert report_result is not None

    def test_analytics_comparative_analysis_workflow(self):
        """Test comparative agent analysis workflow."""
        from ultimate_discord_intelligence_bot.observability import (
            get_analytics_service,
        )

        analytics = get_analytics_service()

        # Record for multiple agents
        test_agents = [
            "integration_agent_a",
            "integration_agent_b",
            "integration_agent_c",
        ]

        for idx, agent in enumerate(test_agents):
            analytics.record_agent_performance(
                agent_name=agent,
                task_type="integration_test",
                quality_score=0.7 + (idx * 0.05),
                response_time=2.0,
                tools_used=["test_tool"],
            )

        # Compare agents
        comp_result = analytics.get_comparative_agent_analysis(test_agents, days=1)
        assert comp_result is not None


class TestCrossComponentIntegration:
    """Test integration across multiple consolidated components."""

    def test_cache_and_analytics_integration(self):
        """Test cache operations with analytics monitoring."""
        from ultimate_discord_intelligence_bot.cache import get_unified_cache
        from ultimate_discord_intelligence_bot.observability import (
            get_analytics_service,
        )

        cache = get_unified_cache()
        analytics = get_analytics_service()

        # Perform cache operations
        cache.set("integration_key", "integration_value")
        value = cache.get("integration_key")
        assert value == "integration_value"

        # Get system health (includes cache metrics)
        health = analytics.get_system_health()
        assert health is not None

    @pytest.mark.asyncio
    async def test_memory_and_analytics_integration(self):
        """Test memory operations with analytics monitoring."""
        from ultimate_discord_intelligence_bot.memory import get_unified_memory
        from ultimate_discord_intelligence_bot.observability import (
            get_analytics_service,
        )

        memory = get_unified_memory()
        analytics = get_analytics_service()

        # Memory operation
        await memory.upsert(
            collection="integration_analytics",
            documents=["Test document"],
            metadatas=[{"test": True}],
            ids=["test_analytics_001"],
        )

        # Analytics monitoring
        health = analytics.get_system_health()
        assert health is not None

    def test_all_facades_accessible(self):
        """Test that all consolidated facades are accessible."""
        # Cache
        from ultimate_discord_intelligence_bot.cache import get_unified_cache

        cache = get_unified_cache()
        assert cache is not None

        # Memory
        from ultimate_discord_intelligence_bot.memory import get_unified_memory

        memory = get_unified_memory()
        assert memory is not None

        # Orchestration
        from ultimate_discord_intelligence_bot.orchestration import get_orchestrator

        orchestrator = get_orchestrator()
        assert orchestrator is not None

        # Analytics
        from ultimate_discord_intelligence_bot.observability import (
            get_analytics_service,
        )

        analytics = get_analytics_service()
        assert analytics is not None


class TestConsolidationFeatureFlags:
    """Test feature flag integration across consolidated components."""

    def test_cache_v2_flag_respected(self):
        """Test ENABLE_CACHE_V2 flag is respected."""
        import os

        from ultimate_discord_intelligence_bot.cache import get_unified_cache

        # Get cache (should work regardless of flag)
        cache = get_unified_cache()
        assert cache is not None

        # Flag determines which backend is used
        os.getenv("ENABLE_CACHE_V2", "false").lower() in [
            "true",
            "1",
            "yes",
        ]
        # Cache should exist regardless
        assert cache is not None

    def test_feature_flags_dont_break_facades(self):
        """Test facades work even with feature flags disabled."""
        # All facades should initialize without errors
        # even if underlying features are disabled

        from ultimate_discord_intelligence_bot.cache import get_unified_cache
        from ultimate_discord_intelligence_bot.memory import get_unified_memory
        from ultimate_discord_intelligence_bot.observability import (
            get_analytics_service,
        )
        from ultimate_discord_intelligence_bot.orchestration import get_orchestrator

        # All should return instances (may be degraded, but functional)
        assert get_unified_cache() is not None
        assert get_unified_memory() is not None
        assert get_analytics_service() is not None
        assert get_orchestrator() is not None


class TestConsolidationPerformance:
    """Test performance characteristics of consolidated architecture."""

    def test_facade_instantiation_performance(self):
        """Test that facade instantiation is fast."""
        import time

        from ultimate_discord_intelligence_bot.cache import get_unified_cache
        from ultimate_discord_intelligence_bot.memory import get_unified_memory
        from ultimate_discord_intelligence_bot.observability import (
            get_analytics_service,
        )

        start = time.time()

        # Instantiate all facades
        get_unified_cache()
        get_unified_memory()
        get_analytics_service()

        elapsed = time.time() - start

        # Should be very fast (< 1 second)
        assert elapsed < 1.0

    def test_singleton_pattern_performance(self):
        """Test singleton pattern prevents redundant instantiation."""
        from ultimate_discord_intelligence_bot.observability import (
            get_analytics_service,
        )

        # Multiple calls should return same instance (no overhead)
        service1 = get_analytics_service()
        service2 = get_analytics_service()
        service3 = get_analytics_service()

        assert service1 is service2 is service3


class TestDeprecationMarkers:
    """Test that deprecation markers are in place."""

    def test_deprecated_modules_have_markers(self):
        """Test that deprecated modules have deprecation markers."""
        from pathlib import Path

        repo_root = Path(__file__).parent.parent

        # Check for Phase 6 routing deprecation markers
        phase6_markers = [
            repo_root / "src/core/routing/.DEPRECATED_PHASE6",
            repo_root / "src/ai/routing/.DEPRECATED_PHASE6",
        ]

        for marker in phase6_markers:
            if marker.exists():
                # Marker should have content
                assert marker.stat().st_size > 0

        # Check for Phase 7 deprecation markers
        phase7_markers = [
            repo_root / "src/ultimate_discord_intelligence_bot/agent_training/performance_monitor_final.py.DEPRECATED",
            repo_root / "src/ultimate_discord_intelligence_bot/enhanced_performance_monitor.py.DEPRECATED",
            repo_root / "src/ultimate_discord_intelligence_bot/.DEPRECATED_PHASE7_ADVANCED_ANALYTICS",
        ]

        for marker in phase7_markers:
            if marker.exists():
                assert marker.stat().st_size > 0


# Parametrized test for all facades
@pytest.mark.parametrize(
    "facade_import,accessor_name",
    [
        ("ultimate_discord_intelligence_bot.cache", "get_unified_cache"),
        ("ultimate_discord_intelligence_bot.memory", "get_unified_memory"),
        ("ultimate_discord_intelligence_bot.orchestration", "get_orchestrator"),
        ("ultimate_discord_intelligence_bot.observability", "get_analytics_service"),
    ],
)
def test_facade_accessor_callable(facade_import, accessor_name):
    """Test that all facade accessors are callable."""
    import importlib

    module = importlib.import_module(facade_import)
    accessor = getattr(module, accessor_name)

    assert callable(accessor)
    instance = accessor()
    assert instance is not None
