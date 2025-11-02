from platform.llm.providers.openrouter.context import prepare_route_state
from platform.llm.providers.openrouter.execution import _compute_reward
from platform.llm.providers.openrouter.service import OpenRouterService


class _FakeTenantRegistry:
    def __init__(self, overrides: dict[str, float] | None = None):
        self._overrides = overrides or {}

    def get_rl_overrides(self, _ctx):
        return dict(self._overrides)

    def get_model_overrides(self, _ctx):
        return {}

    def get_provider_preferences(self, _ctx):
        return None

    def get_pricing_map(self, _ctx):
        return {}


def test_reward_includes_quality_when_weighted(monkeypatch):
    monkeypatch.delenv("REWARD_QUALITY_WEIGHT", raising=False)
    svc = OpenRouterService(api_key="sk-test")
    svc.tenant_registry = _FakeTenantRegistry(
        overrides={
            "reward_cost_weight": 0.0,
            "reward_latency_weight": 0.0,
            "reward_quality_weight": 1.0,
            "reward_latency_ms_window": 2000,
        }
    )
    state = prepare_route_state(
        svc, prompt="hello world", task_type="general", model="openai/gpt-4o-mini", provider_opts=None
    )
    r_high = _compute_reward(svc, state, latency_ms=500.0, quality_score=0.9)
    r_low = _compute_reward(svc, state, latency_ms=500.0, quality_score=0.1)
    assert 0.0 <= r_low < r_high <= 1.0
    assert abs(r_high - 0.9) < 1e-06
    assert abs(r_low - 0.1) < 1e-06


def test_reward_env_quality_weight(monkeypatch):
    monkeypatch.setenv("REWARD_QUALITY_WEIGHT", "1.0")
    svc = OpenRouterService(api_key="sk-test")
    svc.tenant_registry = _FakeTenantRegistry(overrides={})
    state = prepare_route_state(
        svc, prompt="hello world", task_type="general", model="openai/gpt-4o-mini", provider_opts=None
    )
    r1 = _compute_reward(svc, state, latency_ms=1000.0, quality_score=0.9)
    r2 = _compute_reward(svc, state, latency_ms=1000.0, quality_score=0.2)
    assert 0.0 <= r2 <= r1 <= 1.0
    monkeypatch.delenv("REWARD_QUALITY_WEIGHT", raising=False)
