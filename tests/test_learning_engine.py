from core.learning_engine import LearningEngine
from core.rl.policies.bandit_base import EpsilonGreedyBandit


def test_bandit_recommend_and_update():
    # Create a deterministic epsilon-greedy bandit with epsilon=0.0
    bandit = EpsilonGreedyBandit(epsilon=0.0)
    eng = LearningEngine()
    eng.register_domain("p", bandit)

    # Test recommendation with candidates
    first = eng.recommend("p", {}, ["a", "b"])
    assert first in {"a", "b"}

    # Record outcomes
    eng.record("p", {}, "a", 1.0)
    eng.record("p", {}, "b", 0.0)

    # After rewards, should favour "a" (deterministic with epsilon=0.0)
    choice = eng.recommend("p", {}, ["a", "b"])
    assert choice == "a"
