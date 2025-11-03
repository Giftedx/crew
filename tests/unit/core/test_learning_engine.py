from platform.core.learning_engine import LearningEngine
from platform.core.rl.policies.bandit_base import EpsilonGreedyBandit


def test_bandit_recommend_and_update():
    bandit = EpsilonGreedyBandit(epsilon=0.0)
    eng = LearningEngine()
    eng.register_domain("p", bandit)
    first = eng.recommend("p", {}, ["a", "b"])
    assert first in {"a", "b"}
    eng.record("p", {}, "a", 1.0)
    eng.record("p", {}, "b", 0.0)
    choice = eng.recommend("p", {}, ["a", "b"])
    assert choice == "a"
