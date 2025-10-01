from __future__ import annotations

import pytest

from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant


@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch: pytest.MonkeyPatch):
    # Ensure semantic cache flag can be toggled per test
    monkeypatch.setenv("ENABLE_SEMANTIC_CACHE", "1")
    # Clear any previously set cache-related env to avoid accidental Redis usage in tests
    monkeypatch.delenv("RATE_LIMIT_REDIS_URL", raising=False)
    # Reset settings cache so new env vars are picked up
    from core import settings as settings_mod

    if hasattr(settings_mod.get_settings, "cache_clear"):
        settings_mod.get_settings.cache_clear()  # type: ignore[attr-defined]
    yield
    # Restore default (disabled) after test to avoid impacting other suites
    monkeypatch.delenv("ENABLE_SEMANTIC_CACHE", raising=False)
    if hasattr(settings_mod.get_settings, "cache_clear"):
        settings_mod.get_settings.cache_clear()  # type: ignore[attr-defined]


def test_semantic_cache_hit_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force offline mode and disable traditional cache path
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.delenv("RATE_LIMIT_REDIS_URL", raising=False)

    svc = OpenRouterService(api_key="")  # offline
    prompt = "hello semantic cache"

    r1 = svc.route(prompt)
    assert r1["status"] == "success"
    assert r1.get("cached") is False

    r2 = svc.route(prompt)
    assert r2["status"] == "success"
    assert r2.get("cached") is True
    # Semantic path should mark cache type when hit via semantic layer
    assert r2.get("cache_type") == "semantic"


def test_semantic_cache_isolated_by_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force offline mode and disable traditional cache path
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.delenv("RATE_LIMIT_REDIS_URL", raising=False)

    svc = OpenRouterService(api_key="")
    prompt = "isolation check"

    with with_tenant(TenantContext("t1", "w1")):
        a1 = svc.route(prompt)
        assert a1["status"] == "success"
        assert a1.get("cached") is False

    with with_tenant(TenantContext("t2", "w1")):
        b1 = svc.route(prompt)
        assert b1["status"] == "success"
        # Different tenant should not hit the semantic cache populated by t1
        assert b1.get("cached") is False

    with with_tenant(TenantContext("t1", "w1")):
        a2 = svc.route(prompt)
        assert a2["status"] == "success"
        assert a2.get("cached") is True
        assert a2.get("cache_type") == "semantic"
