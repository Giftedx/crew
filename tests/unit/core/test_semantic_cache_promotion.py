import pytest
from platform.observability import metrics
from src.ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
from platform.cache.semantic_cache import CacheStats

class _FakeSemanticCache:

    def __init__(self):
        self.store = {}
        self.calls = []

    def get(self, prompt: str, model: str, namespace: str | None=None):
        self.calls.append(('get', prompt, model, namespace))
        return self.store.get((namespace, model, prompt))

    def set(self, prompt: str, model: str, value, namespace: str | None=None):
        self.calls.append(('set', prompt, model, namespace))
        self.store[namespace, model, prompt] = value

    def get_stats(self) -> CacheStats:
        return CacheStats()

@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    for k in ['ENABLE_SEMANTIC_CACHE', 'ENABLE_SEMANTIC_CACHE_SHADOW', 'ENABLE_SEMANTIC_CACHE_PROMOTION', 'SEMANTIC_CACHE_PROMOTION_THRESHOLD']:
        monkeypatch.delenv(k, raising=False)
    yield

def test_semantic_cache_shadow_promotion_enabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('ENABLE_SEMANTIC_CACHE', '1')
    monkeypatch.setenv('ENABLE_SEMANTIC_CACHE_SHADOW', '1')
    monkeypatch.setenv('ENABLE_SEMANTIC_CACHE_PROMOTION', '1')
    monkeypatch.setenv('SEMANTIC_CACHE_PROMOTION_THRESHOLD', '0.9')
    metrics.reset()
    fake_sc = _FakeSemanticCache()
    monkeypatch.setattr('src.ultimate_discord_intelligence_bot.services.openrouter_service._semantic_cache_get', lambda: fake_sc, raising=True)
    svc = OpenRouterService(api_key='')
    prompt = 'promotion case'
    model = svc._choose_model_from_map('general', svc.models_map)
    res1 = svc.route(prompt)
    assert res1['cached'] is False
    fake_sc.store['default:main', model, prompt] = {'status': 'success', 'model': res1['model'], 'response': 'CACHED-HIGH-SIM', 'tokens': res1['tokens'], 'provider': res1['provider'], 'similarity': 0.95}
    res2 = svc.route(prompt)
    assert res2['cached'] is True
    assert res2.get('cache_type') == 'semantic'
    assert res2.get('response') == 'CACHED-HIGH-SIM'

def test_semantic_cache_shadow_no_promotion_when_below_threshold(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('ENABLE_SEMANTIC_CACHE', '1')
    monkeypatch.setenv('ENABLE_SEMANTIC_CACHE_SHADOW', '1')
    monkeypatch.setenv('ENABLE_SEMANTIC_CACHE_PROMOTION', '1')
    monkeypatch.setenv('SEMANTIC_CACHE_PROMOTION_THRESHOLD', '0.99')
    metrics.reset()
    fake_sc = _FakeSemanticCache()
    monkeypatch.setattr('src.ultimate_discord_intelligence_bot.services.openrouter_service._semantic_cache_get', lambda: fake_sc, raising=True)
    svc = OpenRouterService(api_key='')
    prompt = 'no promotion case'
    model = svc._choose_model_from_map('general', svc.models_map)
    res1 = svc.route(prompt)
    assert res1['cached'] is False
    fake_sc.store['default:main', model, prompt] = {'status': 'success', 'model': res1['model'], 'response': 'CACHED-LOW-SIM', 'tokens': res1['tokens'], 'provider': res1['provider'], 'similarity': 0.8}
    res2 = svc.route(prompt)
    assert res2['cached'] is False
    assert res2.get('response') != 'CACHED-LOW-SIM'