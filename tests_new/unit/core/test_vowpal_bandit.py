import pytest


pytest.importorskip("vowpalwabbit.pyvw")

from core import settings as settings_module
from core.learning_engine import LearningEngine
from core.rl.policies.vowpal_wabbit import VowpalWabbitBandit


def test_vowpal_bandit_recommend_update():
    bandit = VowpalWabbitBandit()
    candidates = ["model_a", "model_b"]
    action = bandit.recommend({"score": 0.5}, candidates)
    assert action in candidates
    bandit.update(action, reward=0.8, context={"score": 0.5})
    state = bandit.state_dict()
    assert state["q_values"].get(action, 0.0) > 0.0
    bandit.close()


def test_learning_engine_uses_vowpal_when_enabled(monkeypatch):
    settings_module._reset_cache_for_tests()
    monkeypatch.setenv("RL_POLICY_MODEL_SELECTION", "vowpal")
    monkeypatch.setenv("ENABLE_RL_VOWPAL", "1")
    engine = LearningEngine()
    engine.register_domain("vw::test")
    policy = engine.registry.get("vw::test")
    assert isinstance(policy, VowpalWabbitBandit)
    action = policy.recommend({}, ["x", "y"])
    policy.update(action, reward=1.0, context={})
    policy.close()
    settings_module._reset_cache_for_tests()
