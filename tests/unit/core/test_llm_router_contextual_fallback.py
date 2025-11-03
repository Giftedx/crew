from platform.core.llm_client import LLMCallResult, LLMClient
from platform.core.llm_router import LLMRouter


class DummyClient(LLMClient):
    def __init__(self, name: str):
        self._name = name

    def chat(self, messages):
        return LLMCallResult(model=self._name, output="ok", usage_tokens=5, cost=0.001, latency_ms=50)


def test_chat_and_update_fallback_when_contextual_enabled(monkeypatch):
    """If contextual mode is enabled but caller uses legacy chat_and_update without features,
    the router should gracefully fallback to classical bandit instead of raising."""
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")
    monkeypatch.setenv("ENABLE_CONTEXTUAL_BANDIT", "1")
    monkeypatch.setenv("LINUCB_DIMENSION", "4")
    c1 = DummyClient("m1")
    c2 = DummyClient("m2")
    router = LLMRouter({"m1": c1, "m2": c2})
    model, result, reward = router.chat_and_update(
        messages=[{"role": "user", "content": "Hi"}], quality=0.9, latency_ms=120, cost=0.002
    )
    assert model in {"m1", "m2"}
    assert result.output == "ok"
    assert 0.0 <= reward <= 1.0
