"""Tests for unified cache facade (ADR-0001)."""

from __future__ import annotations

from platform.core.step_result import StepResult

import pytest

from ultimate_discord_intelligence_bot.cache import (
    ENABLE_CACHE_V2,
    CacheNamespace,
    UnifiedCache,
    get_cache_namespace,
    get_unified_cache,
)


@pytest.fixture
def cache_namespace():
    """Create test cache namespace."""
    return CacheNamespace(tenant="test_tenant", workspace="test_workspace")


@pytest.fixture
def unified_cache():
    """Create unified cache instance."""
    return UnifiedCache()


class TestCacheNamespace:
    """Test cache namespace utilities."""

    def test_namespace_creation(self):
        """Test namespace creation from tenant/workspace."""
        ns = get_cache_namespace("tenant1", "workspace1")
        assert ns.tenant == "tenant1"
        assert ns.workspace == "workspace1"

    def test_namespace_name_generation(self, cache_namespace):
        """Test namespace name includes tenant, workspace, and suffix."""
        name = cache_namespace.name("llm")
        assert name == "test_tenant:test_workspace:llm"


class TestUnifiedCache:
    """Test unified cache facade."""

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, unified_cache, cache_namespace):
        """Test cache get on miss returns empty result."""
        result = await unified_cache.get(cache_namespace, "test", "nonexistent_key")
        assert isinstance(result, StepResult)
        assert result.success
        assert not result.data["hit"]
        assert result.data["value"] is None

    @pytest.mark.asyncio
    async def test_set_and_get(self, unified_cache, cache_namespace):
        """Test cache set followed by get."""
        test_value = {"data": "test_content"}
        set_result = await unified_cache.set(cache_namespace, "test", "test_key", test_value)
        assert set_result.success
        get_result = await unified_cache.get(cache_namespace, "test", "test_key")
        assert get_result.success
        assert get_result.data["hit"]
        assert get_result.data["value"] == test_value

    @pytest.mark.asyncio
    async def test_cache_isolation(self, unified_cache):
        """Test tenant isolation between namespaces."""
        ns1 = CacheNamespace(tenant="tenant1", workspace="workspace1")
        ns2 = CacheNamespace(tenant="tenant2", workspace="workspace2")
        await unified_cache.set(ns1, "test", "shared_key", "value1")
        result = await unified_cache.get(ns2, "test", "shared_key")
        assert result.success
        assert not result.data["hit"]

    def test_feature_flag_defined(self):
        """Test ENABLE_CACHE_V2 flag is defined."""
        assert isinstance(ENABLE_CACHE_V2, bool)


class TestCacheFacadeIntegration:
    """Integration tests for cache facade."""

    @pytest.mark.asyncio
    async def test_get_unified_cache_singleton(self):
        """Test get_unified_cache returns singleton."""
        cache1 = get_unified_cache()
        cache2 = get_unified_cache()
        assert cache1 is cache2

    @pytest.mark.asyncio
    async def test_multi_level_cache_integration(self, cache_namespace):
        """Test integration with multi-level cache backend."""
        cache = get_unified_cache()
        multi_level = cache.get_cache(cache_namespace, "integration_test")
        assert multi_level is not None
        assert hasattr(multi_level, "get")
        assert hasattr(multi_level, "set")
