import importlib
import os

from ultimate_discord_intelligence_bot.core.llm_router import LLMRouter


class DummyClient:
    def __init__(self, name: str):
        self.name = name
        self.calls = 0

    def chat(self, messages):
        self.calls += 1
        return {"content": f"resp-{self.name}", "messages": messages}


def setup_module(module):
    os.environ["ENABLE_CONTEXTUAL_BANDIT"] = "1"
    os.environ["LINUCB_DIMENSION"] = "3"
    os.environ["ENABLE_CONTEXTUAL_HYBRID"] = "1"
    # ensure fresh import state for LinUCB router env usage
    importlib.reload(__import__("ai.routing.linucb_router", fromlist=["LinUCBRouter"]))


def test_hybrid_fallback_on_dimension_mismatch(monkeypatch):
    clients = {"m1": DummyClient("m1"), "m2": DummyClient("m2")}
    router = LLMRouter(clients)
    # Provide wrong dimension -> should fallback to Thompson (no exception)
    selected, result = router.chat_with_features([{"role": "user", "content": "hi"}], features=[0.1, 0.2])
    assert selected in clients
    assert "resp-" in result["content"]
    # update with wrong dimension should also fallback silently
    router.update_with_features(selected, reward=0.8, features=[0.2, 0.3])


def test_contextual_path_with_correct_dimension():
    clients = {"m1": DummyClient("m1"), "m2": DummyClient("m2")}
    router = LLMRouter(clients)
    features = [0.1, 0.2, 0.3]
    selected, _ = router.chat_with_features([{"role": "user", "content": "hi"}], features=features)
    assert selected in clients
    # update path
    router.update_with_features(selected, 0.5, features)
