from __future__ import annotations

from ultimate_discord_intelligence_bot.services.openrouter_service import (
    OpenRouterService,
)


def test_provider_is_part_of_cache_key_offline() -> None:
    # Using offline path (no API key) ensures deterministic uppercase response
    from ultimate_discord_intelligence_bot.services import cache
    cache.LLMCache.clear()
    svc = OpenRouterService(api_key="", cache=cache.LLMCache)
    prompt = "hello"

    # First call with provider A
    r1 = svc.route(prompt, provider_opts={"order": ["a"]})
    assert r1["status"] == "success"
    assert r1.get("cached") is False

    # Second call with same prompt but different provider must not hit cache
    r2 = svc.route(prompt, provider_opts={"order": ["b"]})
    assert r2["status"] == "success"
    assert r2.get("cached") is False

    # Third call with provider A again should be cached
    r3 = svc.route(prompt, provider_opts={"order": ["a"]})
    assert r3["status"] == "success"
    assert r3.get("cached") is True

