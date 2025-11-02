"""Tests for Cache Shadow Harness."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from ultimate_discord_intelligence_bot.services.cache_shadow_harness import (
    CacheShadowHarness,
    get_cache_shadow_harness,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestCacheShadowHarness:
    """Test suite for CacheShadowHarness."""

    def setup_method(self):
        """Set up test fixtures."""
        self.harness = CacheShadowHarness()

    @pytest.mark.asyncio
    @patch(
        "ultimate_discord_intelligence_bot.services.cache_shadow_harness.ENABLE_CACHE_V2",
        True,
    )
    @patch("ultimate_discord_intelligence_bot.services.cache_shadow_harness.get_unified_cache")
    @patch("ultimate_discord_intelligence_bot.services.cache_shadow_harness.get_cache_namespace")
    async def test_shadow_get_unified_hit_legacy_miss(self, mock_namespace, mock_cache_factory):
        """Test shadow get with unified hit and legacy miss."""
        # Setup mocks
        mock_cache = AsyncMock()
        mock_cache.get.return_value = StepResult.ok(value="unified_value", hit=True)
        mock_cache_factory.return_value = mock_cache
        mock_namespace.return_value = Mock()

        # Mock legacy cache
        self.harness.legacy_cache = Mock()
        self.harness.legacy_cache.get.return_value = None

        value, metrics = await self.harness.shadow_get(
            cache_name="test",
            key="test_key",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert value == "unified_value"
        assert metrics["unified_hit"] is True
        assert metrics["legacy_hit"] is False
        assert self.harness._shadow_metrics["unified_hits"] == 1
        assert self.harness._shadow_metrics["legacy_misses"] == 1

    @pytest.mark.asyncio
    @patch(
        "ultimate_discord_intelligence_bot.services.cache_shadow_harness.ENABLE_CACHE_V2",
        True,
    )
    @patch("ultimate_discord_intelligence_bot.services.cache_shadow_harness.get_unified_cache")
    @patch("ultimate_discord_intelligence_bot.services.cache_shadow_harness.get_cache_namespace")
    async def test_shadow_get_unified_miss_legacy_hit(self, mock_namespace, mock_cache_factory):
        """Test shadow get with unified miss and legacy hit."""
        # Setup mocks
        mock_cache = AsyncMock()
        mock_cache.get.return_value = StepResult.ok(value=None, hit=False)
        mock_cache_factory.return_value = mock_cache
        mock_namespace.return_value = Mock()

        # Mock legacy cache
        self.harness.legacy_cache = Mock()
        self.harness.legacy_cache.get.return_value = "legacy_value"

        value, metrics = await self.harness.shadow_get(
            cache_name="test",
            key="test_key",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert value is None  # Unified cache value takes precedence
        assert metrics["unified_hit"] is False
        assert metrics["legacy_hit"] is True
        assert self.harness._shadow_metrics["unified_misses"] == 1
        assert self.harness._shadow_metrics["legacy_hits"] == 1

    @pytest.mark.asyncio
    @patch(
        "ultimate_discord_intelligence_bot.services.cache_shadow_harness.ENABLE_CACHE_V2",
        False,
    )
    async def test_shadow_get_disabled_feature_flag(self):
        """Test shadow get when ENABLE_CACHE_V2 is disabled."""
        # Mock legacy cache
        self.harness.legacy_cache = Mock()
        self.harness.legacy_cache.get.return_value = "legacy_value"

        value, metrics = await self.harness.shadow_get(
            cache_name="test",
            key="test_key",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert value is None  # No unified cache when disabled
        assert metrics["unified_hit"] is False
        assert metrics["legacy_hit"] is True

    @pytest.mark.asyncio
    @patch(
        "ultimate_discord_intelligence_bot.services.cache_shadow_harness.ENABLE_CACHE_V2",
        True,
    )
    @patch("ultimate_discord_intelligence_bot.services.cache_shadow_harness.get_unified_cache")
    @patch("ultimate_discord_intelligence_bot.services.cache_shadow_harness.get_cache_namespace")
    async def test_shadow_set_dual_write(self, mock_namespace, mock_cache_factory):
        """Test shadow set with dual-write to both caches."""
        # Setup mocks
        mock_cache = AsyncMock()
        mock_cache.set.return_value = StepResult.ok()
        mock_cache_factory.return_value = mock_cache
        mock_namespace.return_value = Mock()

        # Mock legacy cache
        self.harness.legacy_cache = Mock()

        result = await self.harness.shadow_set(
            cache_name="test",
            key="test_key",
            value="test_value",
            tenant="test_tenant",
            workspace="test_workspace",
            dependencies={"dep1", "dep2"},
        )

        assert result.success
        mock_cache.set.assert_called_once()
        self.harness.legacy_cache.set.assert_called_once_with("test:test_key", "test_value")

    @pytest.mark.asyncio
    @patch(
        "ultimate_discord_intelligence_bot.services.cache_shadow_harness.ENABLE_CACHE_V2",
        True,
    )
    @patch("ultimate_discord_intelligence_bot.services.cache_shadow_harness.get_unified_cache")
    async def test_shadow_set_unified_cache_error(self, mock_cache_factory):
        """Test shadow set with unified cache error."""
        # Setup mocks to raise exception
        mock_cache_factory.side_effect = Exception("Unified cache error")

        # Mock legacy cache
        self.harness.legacy_cache = Mock()

        result = await self.harness.shadow_set(
            cache_name="test",
            key="test_key",
            value="test_value",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        # Should still succeed if legacy cache works
        assert result.success
        self.harness.legacy_cache.set.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "ultimate_discord_intelligence_bot.services.cache_shadow_harness.ENABLE_CACHE_V2",
        True,
    )
    @patch("ultimate_discord_intelligence_bot.services.cache_shadow_harness.get_unified_cache")
    @patch("ultimate_discord_intelligence_bot.services.cache_shadow_harness.get_cache_namespace")
    async def test_shadow_set_legacy_cache_error(self, mock_namespace, mock_cache_factory):
        """Test shadow set with legacy cache error."""
        # Setup mocks
        mock_cache = AsyncMock()
        mock_cache.set.return_value = StepResult.ok()
        mock_cache_factory.return_value = mock_cache
        mock_namespace.return_value = Mock()

        # Mock legacy cache to raise exception
        self.harness.legacy_cache = Mock()
        self.harness.legacy_cache.set.side_effect = Exception("Legacy cache error")

        result = await self.harness.shadow_set(
            cache_name="test",
            key="test_key",
            value="test_value",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        # Should still succeed if unified cache works
        assert result.success
        mock_cache.set.assert_called_once()

    def test_get_shadow_metrics(self):
        """Test shadow metrics calculation."""
        # Set up some test data
        self.harness._shadow_metrics = {
            "unified_hits": 80,
            "unified_misses": 20,
            "legacy_hits": 70,
            "legacy_misses": 30,
        }

        metrics = self.harness.get_shadow_metrics()

        assert metrics["unified_hit_rate"] == 0.8  # 80/100
        assert metrics["legacy_hit_rate"] == 0.7  # 70/100
        assert metrics["hit_rate_delta"] == 0.1  # 0.8 - 0.7
        assert metrics["unified_hits"] == 80
        assert metrics["unified_misses"] == 20
        assert metrics["legacy_hits"] == 70
        assert metrics["legacy_misses"] == 30
        assert metrics["total_requests"] == 200

    def test_get_shadow_metrics_zero_requests(self):
        """Test shadow metrics with zero requests."""
        # Reset metrics
        self.harness.reset_metrics()

        metrics = self.harness.get_shadow_metrics()

        assert metrics["unified_hit_rate"] == 0.0
        assert metrics["legacy_hit_rate"] == 0.0
        assert metrics["hit_rate_delta"] == 0.0
        assert metrics["total_requests"] == 0

    def test_reset_metrics(self):
        """Test metrics reset functionality."""
        # Set up some test data
        self.harness._shadow_metrics = {
            "unified_hits": 100,
            "unified_misses": 50,
            "legacy_hits": 90,
            "legacy_misses": 60,
        }

        self.harness.reset_metrics()

        expected = {
            "unified_hits": 0,
            "unified_misses": 0,
            "legacy_hits": 0,
            "legacy_misses": 0,
        }
        assert self.harness._shadow_metrics == expected

    def test_get_cache_shadow_harness_singleton(self):
        """Test that get_cache_shadow_harness returns singleton."""
        harness1 = get_cache_shadow_harness()
        harness2 = get_cache_shadow_harness()

        assert harness1 is harness2
        assert isinstance(harness1, CacheShadowHarness)
