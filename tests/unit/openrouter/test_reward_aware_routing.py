import json


def test_reward_aware_picks_cheaper_and_faster(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    lat_map = {"provider/expensive_slow": 1500, "provider/cheap_fast": 400}
    monkeypatch.setenv("MODEL_LATENCY_ESTIMATES", json.dumps(lat_map))
    from platform.llm.providers.openrouter.service import OpenRouterService

    from ultimate_discord_intelligence_bot.services.token_meter import TokenMeter

    tm = TokenMeter(model_prices={"provider/expensive_slow": 5.0, "provider/cheap_fast": 0.1})
    svc = OpenRouterService(
        models_map={"general": ["provider/expensive_slow", "provider/cheap_fast"]}, api_key=None, token_meter=tm
    )
    res = svc.route("hello world", task_type="general", model=None, provider_opts=None, compress=False)
    assert res["status"] == "success"
    assert res["model"] == "provider/cheap_fast"


def test_budget_pushes_to_affordable(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    prompt = "x" * 8000
    lat_map = {"provider/fast_costly": 600, "provider/slow_cheap": 800}
    monkeypatch.setenv("MODEL_LATENCY_ESTIMATES", json.dumps(lat_map))
    from platform.llm.providers.openrouter.service import OpenRouterService

    from ultimate_discord_intelligence_bot.services.token_meter import TokenMeter

    tm = TokenMeter(model_prices={"provider/fast_costly": 2.0, "provider/slow_cheap": 0.2})
    svc = OpenRouterService(
        models_map={"general": ["provider/fast_costly", "provider/slow_cheap"]}, api_key=None, token_meter=tm
    )
    res = svc.route(prompt, task_type="general", model=None, provider_opts=None, compress=False)
    assert res["status"] == "success"
    assert res["model"] == "provider/slow_cheap"
