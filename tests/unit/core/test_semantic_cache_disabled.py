from __future__ import annotations

from platform.llm.providers.openrouter import OpenRouterService

import pytest


@pytest.fixture(autouse=True)
def _ensure_semantic_cache_disabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ENABLE_SEMANTIC_CACHE", raising=False)
    from core import settings as settings_mod

    if hasattr(settings_mod.get_settings, "cache_clear"):
        settings_mod.get_settings.cache_clear()
    yield
    if hasattr(settings_mod.get_settings, "cache_clear"):
        settings_mod.get_settings.cache_clear()


def test_semantic_cache_disabled_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.delenv("RATE_LIMIT_REDIS_URL", raising=False)
    svc = OpenRouterService(api_key="")
    p = "semantic cache disabled"
    r1 = svc.route(p)
    assert r1["status"] == "success"
    assert r1.get("cached") is False
    r2 = svc.route(p)
    assert r2["status"] == "success"
    assert r2.get("cached") is False
