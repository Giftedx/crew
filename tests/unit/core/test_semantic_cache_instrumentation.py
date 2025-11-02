import os
from platform.observability import metrics
from src.ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
from platform.cache.semantic_cache import CacheStats
from platform.core.settings import get_settings

class _FakeSemanticCache:

    def __init__(self):
        self.store = {}
        self.calls = []

    def get(self, prompt: str, model: str, namespace: str | None=None):
        self.calls.append(('get', prompt, model, namespace))
        entry = self.store.get((namespace, model, prompt))
        return entry

    def set(self, prompt: str, model: str, value, namespace: str | None=None):
        self.calls.append(('set', prompt, model, namespace))
        self.store[namespace, model, prompt] = value

    def get_stats(self) -> CacheStats:
        return CacheStats()

def _enable_semantic_cache():
    os.environ['ENABLE_SEMANTIC_CACHE'] = '1'
    get_settings.cache_clear()

def _disable_semantic_cache():
    if 'ENABLE_SEMANTIC_CACHE' in os.environ:
        del os.environ['ENABLE_SEMANTIC_CACHE']
    get_settings.cache_clear()

def test_semantic_cache_miss_then_hit(monkeypatch):
    _enable_semantic_cache()
    metrics.reset()
    fake_sc = _FakeSemanticCache()
    monkeypatch.setattr('src.ultimate_discord_intelligence_bot.services.openrouter_service._semantic_cache_get', lambda: fake_sc, raising=True)
    svc = OpenRouterService(api_key='')
    prompt = 'Hello world'
    res1 = svc.route(prompt)
    assert res1['cached'] is False
    fake_sc.store['default:main', svc._choose_model_from_map('general', svc.models_map), prompt] = {'status': 'success', 'model': res1['model'], 'response': 'CACHED', 'tokens': res1['tokens'], 'provider': res1['provider'], 'similarity': 0.92}
    res2 = svc.route(prompt)
    assert res2['cached'] is True
    assert res2['cache_type'] == 'semantic'
    get_ops = [c for c in fake_sc.calls if c[0] == 'get']
    assert len(get_ops) == 2
    _disable_semantic_cache()

def test_semantic_cache_disabled_no_lookup(monkeypatch):
    _disable_semantic_cache()
    metrics.reset()
    monkeypatch.setattr('src.ultimate_discord_intelligence_bot.services.openrouter_service._semantic_cache_get', lambda: _FakeSemanticCache(), raising=True)
    svc = OpenRouterService(api_key='')
    prompt = 'Another prompt'
    res = svc.route(prompt)
    assert res['cached'] is False
    assert svc.semantic_cache is None