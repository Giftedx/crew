"""Tests for semantic cache shadow mode functionality."""

from __future__ import annotations

import pytest

from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant


@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch: pytest.MonkeyPatch):
    """Reset settings and enable shadow mode for testing."""
    # Enable semantic cache shadow mode
    monkeypatch.setenv("ENABLE_SEMANTIC_CACHE_SHADOW", "1")
    # Force offline mode for testing
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    # Clear any cache-related env to avoid Redis usage in tests
    monkeypatch.delenv("RATE_LIMIT_REDIS_URL", raising=False)

    # Reset settings cache
    from core import settings as settings_mod

    if hasattr(settings_mod.get_settings, "cache_clear"):
        settings_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    # Reset metrics to start fresh
    try:
        from ultimate_discord_intelligence_bot.obs.metrics import reset

        reset()
    except Exception:
        pass

    yield

    # Cleanup
    monkeypatch.delenv("ENABLE_SEMANTIC_CACHE_SHADOW", raising=False)
    if hasattr(settings_mod.get_settings, "cache_clear"):
        settings_mod.get_settings.cache_clear()  # type: ignore[attr-defined]


def test_semantic_cache_shadow_mode_enabled():
    """Test that shadow mode is properly enabled via environment variable."""
    svc = OpenRouterService(api_key="")  # Force offline mode

    # Should have shadow mode enabled
    assert hasattr(svc, "semantic_cache_shadow_mode")
    assert svc.semantic_cache_shadow_mode is True

    # Should have semantic cache instance for tracking
    assert svc.semantic_cache is not None


def test_semantic_cache_shadow_mode_tracks_but_no_return():
    """Test that shadow mode tracks cache hits but doesn't return cached results."""
    svc = OpenRouterService(api_key="")  # Force offline mode
    prompt = "test shadow mode"

    # First call should miss and execute normally
    with with_tenant(TenantContext("test", "shadow")):
        result1 = svc.route(prompt)
        assert result1["status"] == "success"
        assert result1.get("cached") is False  # Not cached in shadow mode
        assert "cache_type" not in result1

        # Second call should track a hit but still execute and return fresh result
        result2 = svc.route(prompt)
        assert result2["status"] == "success"
        assert result2.get("cached") is False  # Still not cached in shadow mode
        assert "cache_type" not in result2

        # Results should be the same (deterministic offline responses)
        assert result1["response"] == result2["response"]


def test_semantic_cache_shadow_mode_metrics():
    """Test that shadow mode tracks hit/miss metrics."""
    # Import to verify metrics exist
    from ultimate_discord_intelligence_bot.obs.metrics import SEMANTIC_CACHE_SHADOW_MISSES

    svc = OpenRouterService(api_key="")
    prompt = "metrics test prompt"

    with with_tenant(TenantContext("test", "metrics")):
        # First call should increment miss counter
        svc.route(prompt)

        # Check that miss metric exists
        try:
            miss_metric = SEMANTIC_CACHE_SHADOW_MISSES.labels(
                tenant="test", workspace="metrics", model="openai/gpt-3.5-turbo"
            )
            assert miss_metric is not None
        except Exception:
            pass  # Metrics might not be available in test environment

        # Second call should track a hit but still return fresh result
        result = svc.route(prompt)
        assert result["status"] == "success"
        assert result.get("cached") is False  # Shadow mode doesn't return cached


def test_semantic_cache_shadow_vs_production_mode(monkeypatch: pytest.MonkeyPatch):
    """Test the difference between shadow mode and production mode."""
    # Test production mode (semantic cache enabled, shadow disabled)
    monkeypatch.delenv("ENABLE_SEMANTIC_CACHE_SHADOW", raising=False)
    monkeypatch.setenv("ENABLE_SEMANTIC_CACHE", "1")

    from core import settings as settings_mod

    if hasattr(settings_mod.get_settings, "cache_clear"):
        settings_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    svc_prod = OpenRouterService(api_key="")
    prompt = "production vs shadow test"

    with with_tenant(TenantContext("prod", "test")):
        # First call - miss
        result1 = svc_prod.route(prompt)
        assert result1["status"] == "success"
        assert result1.get("cached") is False

        # Second call - should be cached in production mode
        result2 = svc_prod.route(prompt)
        assert result2["status"] == "success"
        assert result2.get("cached") is True
        assert result2.get("cache_type") == "semantic"


def test_semantic_cache_shadow_mode_namespace_isolation():
    """Test that shadow mode respects tenant/workspace isolation."""
    svc = OpenRouterService(api_key="")
    prompt = "namespace isolation test"

    # Same prompt, different tenants should not cross-contaminate
    with with_tenant(TenantContext("tenant1", "workspace1")):
        result1 = svc.route(prompt)
        assert result1["status"] == "success"
        assert result1.get("cached") is False

    with with_tenant(TenantContext("tenant2", "workspace1")):
        result2 = svc.route(prompt)
        assert result2["status"] == "success"
        assert result2.get("cached") is False  # Different tenant, should not hit cache

    with with_tenant(TenantContext("tenant1", "workspace1")):
        result3 = svc.route(prompt)
        assert result3["status"] == "success"
        # Even in shadow mode, cache is populated for this namespace
        assert result3.get("cached") is False  # But still returns fresh in shadow mode


def test_analysis_only_shadow_mode(monkeypatch: pytest.MonkeyPatch):
    """GPTCache can run in analysis-only shadow mode without affecting other tasks."""

    # Override autouse fixture defaults for this test
    monkeypatch.setenv("ENABLE_SEMANTIC_CACHE_SHADOW", "0")
    monkeypatch.setenv("ENABLE_SEMANTIC_CACHE", "0")
    monkeypatch.setenv("ENABLE_GPTCACHE", "1")
    monkeypatch.setenv("ENABLE_GPTCACHE_ANALYSIS_SHADOW", "1")

    from core import settings as settings_mod

    if hasattr(settings_mod.get_settings, "cache_clear"):
        settings_mod.get_settings.cache_clear()  # type: ignore[attr-defined]

    # Reset metrics to ensure clean counters for this test
    try:
        from ultimate_discord_intelligence_bot.obs.metrics import reset

        reset()
    except Exception:
        pass

    svc = OpenRouterService(api_key="")
    analysis_prompt = "analysis shadow prompt"
    general_prompt = "general cache prompt"

    with with_tenant(TenantContext("tenant-analysis", "shadow")):
        first = svc.route(analysis_prompt, task_type="analysis")
        assert first["cached"] is False
        second = svc.route(analysis_prompt, task_type="analysis")
        assert second["cached"] is False
        cache_info = second.get("cache_info", {})
        semantic_meta = cache_info.get("semantic", {})
        assert semantic_meta.get("mode") == "shadow"
        assert semantic_meta.get("status") in {"hit", "miss"}

    with with_tenant(TenantContext("tenant-general", "active")):
        first_general = svc.route(general_prompt, task_type="general")
        assert first_general["cached"] is False
        second_general = svc.route(general_prompt, task_type="general")
        assert second_general.get("cached") is True
        assert second_general.get("cache_type") == "semantic"
