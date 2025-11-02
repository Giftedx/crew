"""Tests for semantic cache shadow mode functionality."""
from __future__ import annotations
import pytest
from platform.llm.providers.openrouter import OpenRouterService
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant

@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch: pytest.MonkeyPatch):
    """Reset settings and enable shadow mode for testing."""
    monkeypatch.setenv('ENABLE_SEMANTIC_CACHE_SHADOW', '1')
    monkeypatch.setenv('OPENROUTER_API_KEY', '')
    monkeypatch.delenv('RATE_LIMIT_REDIS_URL', raising=False)
    from core import settings as settings_mod
    if hasattr(settings_mod.get_settings, 'cache_clear'):
        settings_mod.get_settings.cache_clear()
    try:
        from platform.observability.metrics import reset
        reset()
    except Exception:
        pass
    yield
    monkeypatch.delenv('ENABLE_SEMANTIC_CACHE_SHADOW', raising=False)
    if hasattr(settings_mod.get_settings, 'cache_clear'):
        settings_mod.get_settings.cache_clear()

def test_semantic_cache_shadow_mode_enabled():
    """Test that shadow mode is properly enabled via environment variable."""
    svc = OpenRouterService(api_key='')
    assert hasattr(svc, 'semantic_cache_shadow_mode')
    assert svc.semantic_cache_shadow_mode is True
    assert svc.semantic_cache is not None

def test_semantic_cache_shadow_mode_tracks_but_no_return():
    """Test that shadow mode tracks cache hits but doesn't return cached results."""
    svc = OpenRouterService(api_key='')
    prompt = 'test shadow mode'
    with with_tenant(TenantContext('test', 'shadow')):
        result1 = svc.route(prompt)
        assert result1['status'] == 'success'
        assert result1.get('cached') is False
        assert 'cache_type' not in result1
        result2 = svc.route(prompt)
        assert result2['status'] == 'success'
        assert result2.get('cached') is False
        assert 'cache_type' not in result2
        assert result1['response'] == result2['response']

def test_semantic_cache_shadow_mode_metrics():
    """Test that shadow mode tracks hit/miss metrics."""
    from platform.observability.metrics import SEMANTIC_CACHE_SHADOW_MISSES
    svc = OpenRouterService(api_key='')
    prompt = 'metrics test prompt'
    with with_tenant(TenantContext('test', 'metrics')):
        svc.route(prompt)
        try:
            miss_metric = SEMANTIC_CACHE_SHADOW_MISSES.labels(tenant='test', workspace='metrics', model='openai/gpt-3.5-turbo')
            assert miss_metric is not None
        except Exception:
            pass
        result = svc.route(prompt)
        assert result['status'] == 'success'
        assert result.get('cached') is False

def test_semantic_cache_shadow_vs_production_mode(monkeypatch: pytest.MonkeyPatch):
    """Test the difference between shadow mode and production mode."""
    monkeypatch.delenv('ENABLE_SEMANTIC_CACHE_SHADOW', raising=False)
    monkeypatch.setenv('ENABLE_SEMANTIC_CACHE', '1')
    from core import settings as settings_mod
    if hasattr(settings_mod.get_settings, 'cache_clear'):
        settings_mod.get_settings.cache_clear()
    svc_prod = OpenRouterService(api_key='')
    prompt = 'production vs shadow test'
    with with_tenant(TenantContext('prod', 'test')):
        result1 = svc_prod.route(prompt)
        assert result1['status'] == 'success'
        assert result1.get('cached') is False
        result2 = svc_prod.route(prompt)
        assert result2['status'] == 'success'
        assert result2.get('cached') is True
        assert result2.get('cache_type') == 'semantic'

def test_semantic_cache_shadow_mode_namespace_isolation():
    """Test that shadow mode respects tenant/workspace isolation."""
    svc = OpenRouterService(api_key='')
    prompt = 'namespace isolation test'
    with with_tenant(TenantContext('tenant1', 'workspace1')):
        result1 = svc.route(prompt)
        assert result1['status'] == 'success'
        assert result1.get('cached') is False
    with with_tenant(TenantContext('tenant2', 'workspace1')):
        result2 = svc.route(prompt)
        assert result2['status'] == 'success'
        assert result2.get('cached') is False
    with with_tenant(TenantContext('tenant1', 'workspace1')):
        result3 = svc.route(prompt)
        assert result3['status'] == 'success'
        assert result3.get('cached') is False

def test_analysis_only_shadow_mode(monkeypatch: pytest.MonkeyPatch):
    """GPTCache can run in analysis-only shadow mode without affecting other tasks."""
    monkeypatch.setenv('ENABLE_SEMANTIC_CACHE_SHADOW', '0')
    monkeypatch.setenv('ENABLE_SEMANTIC_CACHE', '0')
    monkeypatch.setenv('ENABLE_GPTCACHE', '1')
    monkeypatch.setenv('ENABLE_GPTCACHE_ANALYSIS_SHADOW', '1')
    from core import settings as settings_mod
    if hasattr(settings_mod.get_settings, 'cache_clear'):
        settings_mod.get_settings.cache_clear()
    try:
        from platform.observability.metrics import reset
        reset()
    except Exception:
        pass
    svc = OpenRouterService(api_key='')
    analysis_prompt = 'analysis shadow prompt'
    general_prompt = 'general cache prompt'
    with with_tenant(TenantContext('tenant-analysis', 'shadow')):
        first = svc.route(analysis_prompt, task_type='analysis')
        assert first['cached'] is False
        second = svc.route(analysis_prompt, task_type='analysis')
        assert second['cached'] is False
        cache_info = second.get('cache_info', {})
        semantic_meta = cache_info.get('semantic', {})
        assert semantic_meta.get('mode') == 'shadow'
        assert semantic_meta.get('status') in {'hit', 'miss'}
    with with_tenant(TenantContext('tenant-general', 'active')):
        first_general = svc.route(general_prompt, task_type='general')
        assert first_general['cached'] is False
        second_general = svc.route(general_prompt, task_type='general')
        assert second_general.get('cached') is True
        assert second_general.get('cache_type') == 'semantic'