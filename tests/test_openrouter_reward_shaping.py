from __future__ import annotations

from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
from ultimate_discord_intelligence_bot.services.token_meter import TokenMeter


class StubEngine:
    def __init__(self) -> None:
        self.updated: list[tuple[str, str, float]] = []

    def select_model(self, task_type: str, candidates: list[str]) -> str:
        return candidates[0]

    def update(self, task_type: str, action: str, reward: float) -> None:
        self.updated.append((task_type, action, reward))


def test_reward_shaping_offline_monkeypatched_latency(monkeypatch):
    # Patch perf_counter to simulate ~1000ms latency
    import ultimate_discord_intelligence_bot.services.openrouter_service as mod

    start = 1000.0
    calls = {"n": 0}

    def fake_perf_counter():
        calls["n"] += 1
        return start if calls["n"] == 1 else start + 1.0

    monkeypatch.setattr(mod.time, "perf_counter", fake_perf_counter)

    # Make cost high: 2500 tokens at 0.1 USD/1k = 0.25 USD
    meter = TokenMeter(model_prices={"openai/gpt-4": 0.1}, max_cost_per_request=float("inf"))
    engine = StubEngine()
    svc = OpenRouterService(
        models_map={"general": ["openai/gpt-4"]},
        learning_engine=engine,
        api_key="",  # offline path
        token_meter=meter,
    )
    # Prompt with 2500 whitespace tokens
    prompt = "x " * 2500
    res = svc.route(prompt)
    assert res["status"] == "success"
    assert engine.updated, "learning engine did not receive update"
    # With cost_norm=1, lat_norm=~0.5, weights 0.5/0.5 reward≈0.25
    _, _, reward = engine.updated[-1]
    assert 0.2 <= reward <= 0.3
