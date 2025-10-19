import importlib
import os

from ultimate_discord_intelligence_bot.core.llm_router import LLMRouter


class DummyClient:
    def __init__(self, name: str):
        self.name = name

    def chat(self, messages):  # noqa: D401
        return {"content": f"resp-{self.name}"}


def setup_module(module):  # noqa: D401
    os.environ["ENABLE_CONTEXTUAL_BANDIT"] = "1"
    os.environ["LINUCB_DIMENSION"] = "3"
    os.environ["ENABLE_CONTEXTUAL_HYBRID"] = "1"
    os.environ["FEATURE_QUALITY_MIN"] = "0.8"
    os.environ["FEATURE_MIN_NORM"] = "0.1"
    os.environ["FEATURE_MAX_NORM"] = "1.0"
    importlib.reload(__import__("ai.routing.linucb_router", fromlist=["LinUCBRouter"]))


def test_low_quality_fallback_due_to_norm():
    clients = {"a": DummyClient("a"), "b": DummyClient("b")}
    router = LLMRouter(clients)
    # Very large norm -> expect quality penalty and fallback to Thompson (no exception)
    bad_feats = [10.0, 0.0, 0.0]  # norm 10 > max_norm (1.0)
    model, _ = router.chat_with_features([], bad_feats)
    assert model in clients


def test_high_quality_contextual_path():
    clients = {"a": DummyClient("a"), "b": DummyClient("b")}
    router = LLMRouter(clients)
    good_feats = [0.2, 0.1, 0.05]  # norm within range
    model, _ = router.chat_with_features([], good_feats)
    assert model in clients
    # Update path remains contextual
    router.update_with_features(model, reward=0.6, features=good_feats)
