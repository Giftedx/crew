from __future__ import annotations

import pytest
from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant


@pytest.fixture(autouse=True)
def _semantic_cache_flag(monkeypatch: pytest.MonkeyPatch):
    """Ensure semantic cache enabled and settings cache cleared per test."""
    monkeypatch.setenv("ENABLE_SEMANTIC_CACHE", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")  # force offline deterministic path
    from core import settings as settings_mod

    if hasattr(settings_mod.get_settings, "cache_clear"):
        settings_mod.get_settings.cache_clear()  # type: ignore[attr-defined]
    yield
    monkeypatch.delenv("ENABLE_SEMANTIC_CACHE", raising=False)
    if hasattr(settings_mod.get_settings, "cache_clear"):
        settings_mod.get_settings.cache_clear()  # type: ignore[attr-defined]


def _namespace_isolation_behavior(svc: OpenRouterService):
    """Common assertions verifying per-tenant isolation for a provided service instance.

    Uses a single prompt and alternates tenants to confirm only same-tenant second call hits cache.
    """
    prompt = "fallback namespace isolation"

    with with_tenant(TenantContext("tenantA", "w1")):
        r_a1 = svc.route(prompt)
        assert r_a1["status"] == "success"
        assert r_a1.get("cached") is False

    with with_tenant(TenantContext("tenantB", "w1")):
        r_b1 = svc.route(prompt)
        assert r_b1["status"] == "success"
        # Must be a miss for second tenant
        assert r_b1.get("cached") is False

    # Second call same tenantA should now be a semantic hit
    with with_tenant(TenantContext("tenantA", "w1")):
        r_a2 = svc.route(prompt)
        assert r_a2["status"] == "success"
        assert r_a2.get("cached") is True
        assert r_a2.get("cache_type") == "semantic"

    # TenantB second call becomes its first hit
    with with_tenant(TenantContext("tenantB", "w1")):
        r_b2 = svc.route(prompt)
        assert r_b2["status"] == "success"
        assert r_b2.get("cached") is True
        assert r_b2.get("cache_type") == "semantic"


def test_fallback_semantic_cache_namespace_isolation(monkeypatch: pytest.MonkeyPatch):
    """Force full fallback (no GPTCache available) and verify tenant isolation.

    We simulate absence of GPTCache by monkeypatching the availability flag. This should instantiate a
    FallbackSemanticCache instance. The isolation behaviour must hold (no cross-tenant hits).
    """
    from core.cache import semantic_cache as sc

    # Force code path where GPTCACHE_AVAILABLE is False
    monkeypatch.setattr(sc, "GPTCACHE_AVAILABLE", False, raising=True)
    # Reset global instance so factory runs with modified flag
    sc._semantic_cache = None  # type: ignore[attr-defined]

    svc = OpenRouterService(api_key="")
    # Sanity: ensure we really got fallback cache (string matching implementation)
    from core.cache.semantic_cache import FallbackSemanticCache

    assert isinstance(svc.semantic_cache, FallbackSemanticCache)
    _namespace_isolation_behavior(svc)


@pytest.mark.skipif(
    not pytest.importorskip("gptcache", reason="GPTCache not installed for degraded mode test") or False,
    reason="GPTCache unavailable",
)
def test_degraded_gptcache_simple_store_namespace_isolation(monkeypatch: pytest.MonkeyPatch):
    """Force GPTCache initialisation failure to trigger internal simple cache downgrade.

    The downgraded GPTCacheSemanticCache sets ``self.cache`` to None and uses an internal ``simple_cache``.
    We monkeypatch ``get_data_manager`` to raise so initialization falls back. Isolation must persist.
    """
    from core.cache import semantic_cache as sc

    # Ensure GPTCache path taken first
    monkeypatch.setattr(sc, "GPTCACHE_AVAILABLE", True, raising=True)

    # Monkeypatch get_data_manager to raise inside _initialize_cache -> triggers _initialize_simple_cache
    def _boom(*_a, **_k):  # pragma: no cover - trivial
        raise RuntimeError("synthetic init failure")

    monkeypatch.setattr(sc, "get_data_manager", _boom, raising=True)

    # Reset global instance
    sc._semantic_cache = None  # type: ignore[attr-defined]

    svc = OpenRouterService(api_key="")
    from core.cache.semantic_cache import GPTCacheSemanticCache

    assert isinstance(svc.semantic_cache, GPTCacheSemanticCache)
    # Degraded mode characteristics
    assert getattr(svc.semantic_cache, "cache", None) is None
    assert hasattr(svc.semantic_cache, "simple_cache")

    _namespace_isolation_behavior(svc)
