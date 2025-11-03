from __future__ import annotations

from platform.llm.providers.openrouter import OpenRouterService


def test_provider_is_part_of_cache_key_offline() -> None:
    from ultimate_discord_intelligence_bot.services import cache

    cache.LLMCache.clear()
    svc = OpenRouterService(api_key="", cache=cache.LLMCache)
    prompt = "hello"
    r1 = svc.route(prompt, provider_opts={"order": ["a"]})
    assert r1["status"] == "success"
    assert r1.get("cached") is False
    r2 = svc.route(prompt, provider_opts={"order": ["b"]})
    assert r2["status"] == "success"
    assert r2.get("cached") is False
    r3 = svc.route(prompt, provider_opts={"order": ["a"]})
    assert r3["status"] == "success"
    assert r3.get("cached") is True
