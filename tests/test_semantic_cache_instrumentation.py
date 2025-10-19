import os

from ultimate_discord_intelligence_bot.core.cache.semantic_cache import CacheStats
from ultimate_discord_intelligence_bot.core.settings import get_settings
from src.obs import metrics
from src.ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService


class _FakeSemanticCache:
    def __init__(self):
        self.store = {}
        self.calls = []

    def get(self, prompt: str, model: str, namespace: str | None = None):  # noqa: D401
        self.calls.append(("get", prompt, model, namespace))
        entry = self.store.get((namespace, model, prompt))
        return entry

    def set(self, prompt: str, model: str, value, namespace: str | None = None):  # noqa: D401
        self.calls.append(("set", prompt, model, namespace))
        self.store[(namespace, model, prompt)] = value

    def get_stats(self) -> CacheStats:  # noqa: D401
        return CacheStats()


def _enable_semantic_cache():
    os.environ["ENABLE_SEMANTIC_CACHE"] = "1"
    get_settings.cache_clear()  # type: ignore[attr-defined]


def _disable_semantic_cache():
    if "ENABLE_SEMANTIC_CACHE" in os.environ:
        del os.environ["ENABLE_SEMANTIC_CACHE"]
    get_settings.cache_clear()  # type: ignore[attr-defined]


def test_semantic_cache_miss_then_hit(monkeypatch):
    _enable_semantic_cache()
    metrics.reset()

    fake_sc = _FakeSemanticCache()

    # Monkeypatch constructor to inject fake semantic cache instance
    monkeypatch.setattr(
        "src.ultimate_discord_intelligence_bot.services.openrouter_service._semantic_cache_get",
        lambda: fake_sc,
        raising=True,
    )

    svc = OpenRouterService(api_key="")  # force offline mode
    prompt = "Hello world"

    # First call -> miss (no entry yet) should increment issued counter
    res1 = svc.route(prompt)
    assert res1["cached"] is False

    # Simulate persistence by storing semantic cache entry manually with similarity
    fake_sc.store[("default:main", svc._choose_model_from_map("general", svc.models_map), prompt)] = {
        "status": "success",
        "model": res1["model"],
        "response": "CACHED",
        "tokens": res1["tokens"],
        "provider": res1["provider"],
        "similarity": 0.92,
    }

    # Second call -> hit should increment used counter and record similarity bucket
    res2 = svc.route(prompt)
    assert res2["cached"] is True
    assert res2["cache_type"] == "semantic"

    # We cannot directly read counter values without prometheus client registry, but ensure logic executed via fake cache call order
    get_ops = [c for c in fake_sc.calls if c[0] == "get"]
    assert len(get_ops) == 2

    _disable_semantic_cache()


def test_semantic_cache_disabled_no_lookup(monkeypatch):
    _disable_semantic_cache()
    metrics.reset()

    # Ensure factory returns something if invoked (to prove gate works)
    monkeypatch.setattr(
        "src.ultimate_discord_intelligence_bot.services.openrouter_service._semantic_cache_get",
        lambda: _FakeSemanticCache(),
        raising=True,
    )

    svc = OpenRouterService(api_key="")
    prompt = "Another prompt"
    res = svc.route(prompt)
    assert res["cached"] is False
    # semantic_cache attribute should be None when disabled
    assert svc.semantic_cache is None
