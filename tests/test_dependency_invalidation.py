"""
Tests for dependency-based cache invalidation system.

This module provides comprehensive tests for the dependency tracking,
invalidation engine, and integration with MultiLevelCache.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from core.cache.dependency_tracker import DependencyNode, DependencyTracker
from core.cache.invalidation_engine import InvalidationEngine, InvalidationResult
from core.cache.multi_level_cache import CacheEntry, MultiLevelCache


class TestDependencyTracker:
    """Test cases for the dependency tracker."""

    @pytest.fixture
    def tracker(self) -> DependencyTracker:
        """Create a fresh dependency tracker for each test."""
        return DependencyTracker(max_graph_size=100)

    @pytest.mark.asyncio
    async def test_register_dependencies(self, tracker: DependencyTracker):
        """Test registering dependencies for a cache key."""
        key = "user:123"
        dependencies = {"user:profile:123", "user:permissions:123"}

        await tracker.register_dependencies(key, dependencies)

        # Check that nodes were created
        assert key in tracker._graph
        assert "user:profile:123" in tracker._graph
        assert "user:permissions:123" in tracker._graph

        # Check relationships
        assert tracker._graph[key].depends_on == dependencies
        assert key in tracker._graph["user:profile:123"].depended_by
        assert key in tracker._graph["user:permissions:123"].depended_by

    @pytest.mark.asyncio
    async def test_get_dependents_simple(self, tracker: DependencyTracker):
        """Test getting direct dependents of a key."""
        key = "user:123"
        dependent1 = "user:profile:123"
        dependent2 = "user:permissions:123"

        await tracker.register_dependencies(dependent1, {key})
        await tracker.register_dependencies(dependent2, {key})

        dependents = await tracker.get_dependents(key)
        assert dependents == {dependent1, dependent2}

    @pytest.mark.asyncio
    async def test_get_dependents_transitive(self, tracker: DependencyTracker):
        """Test getting transitive dependents (dependents of dependents)."""
        # A -> B -> C (A depends on B, B depends on C)
        # When C changes, both A and B should be invalidated
        await tracker.register_dependencies("cache:A", {"cache:B"})
        await tracker.register_dependencies("cache:B", {"cache:C"})

        dependents = await tracker.get_dependents("cache:C")
        assert dependents == {"cache:A", "cache:B"}

    @pytest.mark.asyncio
    async def test_unregister_key(self, tracker: DependencyTracker):
        """Test unregistering a key and cleaning up relationships."""
        key = "user:123"
        dependencies = {"user:profile:123", "user:permissions:123"}

        await tracker.register_dependencies(key, dependencies)
        await tracker.unregister_key(key)

        # Key should be removed
        assert key not in tracker._graph

        # Dependencies should no longer have the key as a dependent
        assert key not in tracker._graph["user:profile:123"].depended_by
        assert key not in tracker._graph["user:permissions:123"].depended_by

    @pytest.mark.asyncio
    async def test_circular_reference_detection(self, tracker: DependencyTracker):
        """Test detection of circular dependencies."""
        # Create a circular dependency: A -> B -> C -> A
        await tracker.register_dependencies("cache:A", {"cache:B"})
        await tracker.register_dependencies("cache:B", {"cache:C"})
        await tracker.register_dependencies("cache:C", {"cache:A"})  # Creates cycle

        # Should detect circular reference
        assert await tracker._detect_circular_reference("cache:A")
        assert await tracker._detect_circular_reference("cache:B")
        assert await tracker._detect_circular_reference("cache:C")

    def test_get_stats(self, tracker: DependencyTracker):
        """Test getting tracker statistics."""
        stats = tracker.get_stats()
        assert "graph_size" in stats
        assert "max_graph_size" in stats
        assert "utilization_ratio" in stats
        assert "nodes_created" in stats
        assert "nodes_removed" in stats


class TestInvalidationEngine:
    """Test cases for the invalidation engine."""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock dependency tracker."""
        tracker = AsyncMock()
        tracker.invalidate_key.return_value = {"dependent:1", "dependent:2"}
        return tracker

    @pytest.fixture
    def engine(self, mock_tracker: AsyncMock) -> InvalidationEngine:
        """Create an invalidation engine with mock tracker."""
        return InvalidationEngine(dependency_tracker=mock_tracker, max_batch_size=10, max_concurrent_invalidations=5)

    @pytest.mark.asyncio
    async def test_invalidate_key_cascade(self, engine: InvalidationEngine, mock_tracker: AsyncMock):
        """Test invalidating a key with cascading."""
        result = await engine.invalidate_key("test:key", cascade=True)

        assert isinstance(result, InvalidationResult)
        assert "test:key" in result.invalidated_keys or "test:key" in result.skipped_keys
        mock_tracker.invalidate_key.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_invalidate_key_no_cascade(self, engine: InvalidationEngine, mock_tracker: AsyncMock):
        """Test invalidating a key without cascading."""
        result = await engine.invalidate_key("test:key", cascade=False)

        assert isinstance(result, InvalidationResult)
        mock_tracker.invalidate_key.assert_not_called()

    @pytest.mark.asyncio
    async def test_circuit_breaker_open(self, engine: InvalidationEngine):
        """Test circuit breaker behavior when open."""
        # Force circuit breaker open
        engine._failure_count = 10
        engine._circuit_open = True

        result = await engine.invalidate_key("test:key")

        assert "Circuit breaker open" in " ".join(result.errors)
        assert "test:key" in result.skipped_keys

    def test_get_stats(self, engine: InvalidationEngine):
        """Test getting engine statistics."""
        stats = engine.get_stats()
        assert "circuit_breaker" in stats
        assert "performance" in stats
        assert "queue" in stats


class TestMultiLevelCacheIntegration:
    """Test integration of dependency invalidation with MultiLevelCache."""

    @pytest.fixture
    def cache(self):
        """Create a MultiLevelCache with dependency tracking enabled."""
        return MultiLevelCache(name="test_cache", enable_dependency_tracking=True)

    @pytest.mark.asyncio
    async def test_set_with_dependencies(self, cache: MultiLevelCache):
        """Test setting cache entries with dependencies."""
        key = "user:123"
        value = {"name": "John", "email": "john@example.com"}
        dependencies = {"user:profile:123", "user:permissions:123"}

        success = await cache.set(key, value, dependencies)
        assert success

        # Check that dependencies were registered
        if cache._dependency_tracker:
            deps = await cache.get_dependencies(key)
            assert deps == set()  # The key depends on the dependencies

            dependents = await cache.get_dependents("user:profile:123")
            assert key in dependents

    @pytest.mark.asyncio
    async def test_invalidate_dependencies(self, cache: MultiLevelCache):
        """Test invalidating dependencies."""
        # Set up a chain of dependencies
        await cache.set("page:1", "page content", {"template:header", "data:user:123"})
        await cache.set("page:2", "page content 2", {"template:header", "data:user:456"})

        # Invalidate template:header using invalidation engine
        if cache._invalidation_engine:
            result = await cache._invalidation_engine.invalidate_key("template:header", cascade=True)
            invalidated_count = len(result.invalidated_keys)
            assert invalidated_count >= 2  # Both pages should be invalidated
        else:
            pytest.skip("Invalidation engine not available")

    @pytest.mark.asyncio
    async def test_delete_with_cascade(self, cache: MultiLevelCache):
        """Test deleting with cascading invalidation."""
        # Set up dependencies
        await cache.set("user:123", "user data", {"profile:123"})
        await cache.set("profile:123", "profile data")

        # Delete with cascade
        success = await cache.delete("profile:123", cascade=True)
        assert success

        # Check that dependent was also handled
        if cache._dependency_tracker:
            dependents = await cache.get_dependents("profile:123")
            assert len(dependents) == 0  # Should be cleaned up

    def test_get_stats_includes_dependency_info(self, cache: MultiLevelCache):
        """Test that cache stats include dependency information."""
        stats = cache.get_stats()

        if cache.enable_dependency_tracking:
            assert "dependency_tracking" in stats
            assert "invalidation_engine" in stats
        else:
            assert stats["configuration"]["dependency_tracking_enabled"] is False


class TestCacheEntry:
    """Test cases for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(key="test:key", data="test value", dependencies={"dep:1", "dep:2"})

        assert entry.key == "test:key"
        assert entry.data == "test value"
        assert entry.dependencies == {"dep:1", "dep:2"}
        assert entry.access_count == 0

    def test_update_access(self):
        """Test updating access metadata."""
        entry = CacheEntry(key="test:key", data="value")

        entry.update_access()

        assert entry.access_count == 1
        assert entry.last_accessed > 0

    def test_should_promote(self):
        """Test promotion logic."""
        entry = CacheEntry(key="test:key", data="value")

        # Should not promote initially
        assert not entry.should_promote()

        # Should promote after many accesses
        entry.access_count = 15
        assert entry.should_promote()

    def test_should_demote(self):
        """Test demotion logic."""
        entry = CacheEntry(key="test:key", data="value")

        # Should not demote initially
        assert not entry.should_demote()

        # Should demote after long idle time
        entry.last_accessed = 0  # Very old
        assert entry.should_demote()


class TestDependencyNode:
    """Test cases for DependencyNode dataclass."""

    def test_dependency_node_creation(self):
        """Test creating a dependency node."""
        node = DependencyNode(key="test:key")

        assert node.key == "test:key"
        assert node.depends_on == set()
        assert node.depended_by == set()

    def test_add_remove_dependency(self):
        """Test adding and removing dependencies."""
        node = DependencyNode(key="test:key")

        node.add_dependency("dep:1")
        assert "dep:1" in node.depends_on

        node.remove_dependency("dep:1")
        assert "dep:1" not in node.depends_on

    def test_add_remove_dependent(self):
        """Test adding and removing dependents."""
        node = DependencyNode(key="test:key")

        node.add_dependent("dep:1")
        assert "dep:1" in node.depended_by

        node.remove_dependent("dep:1")
        assert "dep:1" not in node.depended_by


# Integration test for the complete system
@pytest.mark.asyncio
async def test_complete_invalidation_workflow():
    """Test a complete invalidation workflow from setup to cleanup."""
    # Create components
    tracker = DependencyTracker()
    engine = InvalidationEngine(dependency_tracker=tracker)
    cache = MultiLevelCache(name="integration_test", enable_dependency_tracking=True)

    # Override with our test instances
    cache._dependency_tracker = tracker
    cache._invalidation_engine = engine

    try:
        # Set up a complex dependency chain
        # user:123 depends on profile:123 and permissions:123
        # page:1 depends on user:123 and template:main
        # page:2 depends on user:456 and template:main

        await cache.set("user:123", "user data", {"profile:123", "permissions:123"})
        await cache.set("user:456", "user data 2", {"profile:456", "permissions:456"})
        await cache.set("page:1", "page 1 content", {"user:123", "template:main"})
        await cache.set("page:2", "page 2 content", {"user:456", "template:main"})

        # Verify initial state
        user_deps = await cache.get_dependencies("page:1")
        assert "user:123" in user_deps
        assert "template:main" in user_deps

        # Invalidate template:main using invalidation engine
        if cache._invalidation_engine:
            result = await cache._invalidation_engine.invalidate_key("template:main", cascade=True)
            invalidated = len(result.invalidated_keys)
            assert invalidated >= 2  # Both pages should be invalidated
        else:
            pytest.skip("Invalidation engine not available")

        # Verify dependents were cleaned up
        template_dependents = await cache.get_dependents("template:main")
        assert len(template_dependents) == 0  # Should be empty after invalidation

        # Test cascade deletion
        await cache.delete("profile:123", cascade=True)

        # Verify cascading worked
        profile_dependents = await cache.get_dependents("profile:123")
        assert len(profile_dependents) == 0

    finally:
        # Cleanup
        await engine.stop()


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(test_complete_invalidation_workflow())
