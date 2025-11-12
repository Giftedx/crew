from platform.llm.llm_client import LLMCallResult, LLMClient
from platform.llm.llm_router import LLMRouter

from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant


class DummyClient(LLMClient):
    def __init__(self, name: str, latency_ms: float, cost: float, quality: float):
        self._name = name
        self._latency = latency_ms
        self._cost = cost
        self._quality = quality

    def chat(self, messages):
        return LLMCallResult(model=self._name, output="ok", usage_tokens=10, cost=self._cost, latency_ms=self._latency)


def test_tenant_mode_reuses_router(monkeypatch):
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")
    monkeypatch.setenv("ENABLE_BANDIT_TENANT", "1")
    c1 = DummyClient("m1", 100, 0.002, 0.9)
    c2 = DummyClient("m2", 120, 0.0025, 0.8)
    ctx = TenantContext(tenant_id="tenantX", workspace_id="ws1")
    with with_tenant(ctx):
        router_a = LLMRouter({"m1": c1, "m2": c2})
        router_b = LLMRouter({"m1": c1, "m2": c2})
        assert id(router_a._bandit) == id(router_b._bandit)


def test_chat_and_update_reward(monkeypatch):
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")
    monkeypatch.setenv("ENABLE_BANDIT_TENANT", "0")
    c1 = DummyClient("m1", 150, 0.003, 0.7)
    c2 = DummyClient("m2", 80, 0.004, 0.9)
    router = LLMRouter({"m1": c1, "m2": c2})
    model, result, reward = router.chat_and_update(
        messages=[{"role": "user", "content": "Hi"}], quality=0.85, latency_ms=200, cost=0.002
    )
    assert model in {"m1", "m2"}
    assert 0 <= reward <= 1
    assert result.output == "ok"
