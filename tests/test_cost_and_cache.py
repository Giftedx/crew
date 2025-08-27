from ultimate_discord_intelligence_bot.services import (
    OpenRouterService,
    TokenMeter,
    LLMCache,
)


def test_cost_guard_downshift():
    models = {"general": ["expensive", "cheap"]}
    tm = TokenMeter(
        model_prices={"expensive": 1000.0, "cheap": 0.5},
        max_cost_per_request=0.01,
    )
    router = OpenRouterService(models_map=models, token_meter=tm, cache=LLMCache())
    res = router.route("hello world")
    assert res["model"] == "cheap"
    assert res["status"] == "success"


def test_llm_cache_hit():
    tm = TokenMeter(model_prices={"openai/gpt-3.5-turbo": 0.5}, max_cost_per_request=1)
    cache = LLMCache(ttl=60)
    router = OpenRouterService(token_meter=tm, cache=cache)
    first = router.route("cached prompt")
    assert first["cached"] is False
    second = router.route("cached prompt")
    assert second["cached"] is True
    assert second["response"] == first["response"]
