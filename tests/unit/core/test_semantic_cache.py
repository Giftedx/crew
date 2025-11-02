from __future__ import annotations
import pytest
from platform.llm.providers.openrouter import OpenRouterService
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant

@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('ENABLE_SEMANTIC_CACHE', '1')
    monkeypatch.delenv('RATE_LIMIT_REDIS_URL', raising=False)
    from core import settings as settings_mod
    if hasattr(settings_mod.get_settings, 'cache_clear'):
        settings_mod.get_settings.cache_clear()
    yield
    monkeypatch.delenv('ENABLE_SEMANTIC_CACHE', raising=False)
    if hasattr(settings_mod.get_settings, 'cache_clear'):
        settings_mod.get_settings.cache_clear()

def test_semantic_cache_hit_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('OPENROUTER_API_KEY', '')
    monkeypatch.delenv('RATE_LIMIT_REDIS_URL', raising=False)
    svc = OpenRouterService(api_key='')
    prompt = 'hello semantic cache'
    r1 = svc.route(prompt)
    assert r1['status'] == 'success'
    assert r1.get('cached') is False
    r2 = svc.route(prompt)
    assert r2['status'] == 'success'
    assert r2.get('cached') is True
    assert r2.get('cache_type') == 'semantic'

def test_semantic_cache_isolated_by_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('OPENROUTER_API_KEY', '')
    monkeypatch.delenv('RATE_LIMIT_REDIS_URL', raising=False)
    svc = OpenRouterService(api_key='')
    prompt = 'isolation check'
    with with_tenant(TenantContext('t1', 'w1')):
        a1 = svc.route(prompt)
        assert a1['status'] == 'success'
        assert a1.get('cached') is False
    with with_tenant(TenantContext('t2', 'w1')):
        b1 = svc.route(prompt)
        assert b1['status'] == 'success'
        assert b1.get('cached') is False
    with with_tenant(TenantContext('t1', 'w1')):
        a2 = svc.route(prompt)
        assert a2['status'] == 'success'
        assert a2.get('cached') is True
        assert a2.get('cache_type') == 'semantic'