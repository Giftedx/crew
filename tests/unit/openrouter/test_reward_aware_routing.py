import json


def test_reward_aware_picks_cheaper_and_faster(monkeypatch):
    # Ensure offline execution regardless of runner environment
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    # Configure latency estimates for deterministic selection
    lat_map = {
        "provider/expensive_slow": 1500,
        "provider/cheap_fast": 400,
    }
    monkeypatch.setenv("MODEL_LATENCY_ESTIMATES", json.dumps(lat_map))

    # Import locally to ensure sitecustomize has run
    from ultimate_discord_intelligence_bot.services.openrouter_service.service import OpenRouterService
    from ultimate_discord_intelligence_bot.services.token_meter import TokenMeter

    # Prices: cheaper model is also cheaper per 1k tokens
    tm = TokenMeter(
        model_prices={
            "provider/expensive_slow": 5.0,
            "provider/cheap_fast": 0.1,
        }
    )

    svc = OpenRouterService(
        models_map={"general": ["provider/expensive_slow", "provider/cheap_fast"]},
        api_key=None,  # offline
        token_meter=tm,
    )

    # Route with compression disabled to avoid heavy optional deps
    res = svc.route("hello world", task_type="general", model=None, provider_opts=None, compress=False)

    assert res["status"] == "success"
    assert res["model"] == "provider/cheap_fast"


def test_budget_pushes_to_affordable(monkeypatch):
    # Ensure offline execution regardless of runner environment
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    # Large prompt to drive cost
    prompt = "x" * 8000  # ~2000 tokens via heuristic

    # Latency: expensive is faster to tempt selection, but budget should force cheap
    lat_map = {
        "provider/fast_costly": 600,
        "provider/slow_cheap": 800,
    }
    monkeypatch.setenv("MODEL_LATENCY_ESTIMATES", json.dumps(lat_map))

    from ultimate_discord_intelligence_bot.services.openrouter_service.service import OpenRouterService
    from ultimate_discord_intelligence_bot.services.token_meter import TokenMeter

    # Prices: costly model will exceed default max_cost_per_request (1.0) with large prompt
    # cheap stays within limit
    tm = TokenMeter(
        model_prices={
            "provider/fast_costly": 2.0,  # -> ~4.0 USD for ~2000 tokens
            "provider/slow_cheap": 0.2,  # -> ~0.4 USD for ~2000 tokens
        }
    )

    svc = OpenRouterService(
        models_map={"general": ["provider/fast_costly", "provider/slow_cheap"]},
        api_key=None,
        token_meter=tm,
    )

    res = svc.route(prompt, task_type="general", model=None, provider_opts=None, compress=False)

    assert res["status"] == "success"
    # Expect budget to steer final choice to affordable model
    assert res["model"] == "provider/slow_cheap"
