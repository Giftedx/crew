import pytest

from ultimate_discord_intelligence_bot.core.cache.semantic_cache import CacheStats
from src.obs import metrics
from src.ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService


class _FakeSemanticCache:
    def __init__(self):
        self.store = {}

    def get(self, prompt: str, model: str, namespace: str | None = None):
        return self.store.get((namespace, model, prompt))

    def set(self, prompt: str, model: str, value, namespace: str | None = None):
        self.store[(namespace, model, prompt)] = value

    def get_stats(self) -> CacheStats:
        return CacheStats()


def test_semantic_cache_promotion_increments_counter(monkeypatch: pytest.MonkeyPatch):
    # Enable semantic cache, shadow mode, and promotion
    monkeypatch.setenv("ENABLE_SEMANTIC_CACHE", "1")
    monkeypatch.setenv("ENABLE_SEMANTIC_CACHE_SHADOW", "1")
    monkeypatch.setenv("ENABLE_SEMANTIC_CACHE_PROMOTION", "1")
    monkeypatch.setenv("SEMANTIC_CACHE_PROMOTION_THRESHOLD", "0.9")

    metrics.reset()

    fake_sc = _FakeSemanticCache()
    monkeypatch.setattr(
        "src.ultimate_discord_intelligence_bot.services.openrouter_service._semantic_cache_get",
        lambda: fake_sc,
        raising=True,
    )

    svc = OpenRouterService(api_key="")
    prompt = "promotion metrics case"
    model = svc._choose_model_from_map("general", svc.models_map)

    # First call to populate cache with offline result
    first = svc.route(prompt)
    assert first["cached"] is False

    # Insert high similarity cached value
    fake_sc.store[("default:main", model, prompt)] = {
        "status": "success",
        "model": first["model"],
        "response": "CACHED-HIGH-SIM",
        "tokens": first["tokens"],
        "provider": first["provider"],
        "similarity": 0.95,
    }

    # Second call should promote and count promotion
    second = svc.route(prompt)
    assert second["cached"] is True
    assert second.get("cache_type") == "semantic"

    # If prometheus client is present, ensure exposition contains promotions metric name
    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    assert "cache_promotions_total" in rendered or not metrics.PROMETHEUS_AVAILABLE
