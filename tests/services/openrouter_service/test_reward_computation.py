from ultimate_discord_intelligence_bot.services.openrouter_service.context import (
    prepare_route_state,
)
from ultimate_discord_intelligence_bot.services.openrouter_service.execution import (
    _compute_reward,
)
from ultimate_discord_intelligence_bot.services.openrouter_service.service import OpenRouterService


class _FakeTenantRegistry:
    def __init__(self, overrides: dict[str, float] | None = None):
        self._overrides = overrides or {}

    def get_rl_overrides(self, _ctx):
        return dict(self._overrides)

    # Stubs required by prepare_route_state
    def get_model_overrides(self, _ctx):
        return {}

    def get_provider_preferences(self, _ctx):
        return None

    def get_pricing_map(self, _ctx):
        return {}


def test_reward_includes_quality_when_weighted(monkeypatch):
    # Ensure env fallback doesn't interfere
    monkeypatch.delenv("REWARD_QUALITY_WEIGHT", raising=False)

    svc = OpenRouterService(api_key="sk-test")

    # Inject tenant overrides to control weights deterministically
    svc.tenant_registry = _FakeTenantRegistry(
        overrides={
            "reward_cost_weight": 0.0,
            "reward_latency_weight": 0.0,
            "reward_quality_weight": 1.0,
            "reward_latency_ms_window": 2000,
        }
    )

    state = prepare_route_state(
        svc,
        prompt="hello world",
        task_type="general",
        model="openai/gpt-4o-mini",
        provider_opts=None,
    )
    # With weights set to quality only, reward should equal quality_score (clamped)
    r_high = _compute_reward(svc, state, latency_ms=500.0, quality_score=0.9)
    r_low = _compute_reward(svc, state, latency_ms=500.0, quality_score=0.1)
    assert 0.0 <= r_low < r_high <= 1.0
    assert abs(r_high - 0.9) < 1e-6
    assert abs(r_low - 0.1) < 1e-6


def test_reward_env_quality_weight(monkeypatch):
    # Use env var when no tenant override is present
    monkeypatch.setenv("REWARD_QUALITY_WEIGHT", "1.0")

    svc = OpenRouterService(api_key="sk-test")
    svc.tenant_registry = _FakeTenantRegistry(overrides={})

    state = prepare_route_state(
        svc,
        prompt="hello world",
        task_type="general",
        model="openai/gpt-4o-mini",
        provider_opts=None,
    )

    # If cost and latency weights default to 0.5 each and quality to 1.0, normalization occurs
    # Reward should still be monotonic in quality and within [0,1]
    r1 = _compute_reward(svc, state, latency_ms=1000.0, quality_score=0.9)
    r2 = _compute_reward(svc, state, latency_ms=1000.0, quality_score=0.2)
    assert 0.0 <= r2 <= r1 <= 1.0

    # Clean up
    monkeypatch.delenv("REWARD_QUALITY_WEIGHT", raising=False)
