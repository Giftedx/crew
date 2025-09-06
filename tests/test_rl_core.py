from __future__ import annotations

import random

from core import learn, reward_pipe, rl
from core.learning_engine import LearningEngine
from core.rl.policies.bandit_base import EpsilonGreedyBandit, UCB1Bandit


def test_feature_store_stats_and_featurize() -> None:
    rl.feature_store.update_stats({"cost_usd": 1.0, "latency_ms": 50})
    features = rl.feature_store.featurize({"input_tokens": 10, "output_tokens": 5})
    assert features["avg_cost_usd"] == 1.0
    assert features["avg_latency_ms"] == 50


def test_reward_engine_compute_and_attribute() -> None:
    outcome = {"cost_usd": 0.2, "latency_ms": 100}
    signals = {"quality": 1.0, "groundedness": 0.5}
    breakdown = rl.reward_engine.compute_reward(outcome, signals)
    assert breakdown.total == 1.0 + 0.5 - 0.2 - 100
    rewards = rl.reward_engine.attribute_reward({"a": None, "b": None}, breakdown)
    assert set(rewards.keys()) == {"a", "b"}
    assert rewards["a"] == rewards["b"]


def test_reward_engine_weight_overrides() -> None:
    outcome = {"cost_usd": 1.0, "latency_ms": 10}
    signals = {"quality": 1.0, "groundedness": 1.0}
    breakdown = rl.reward_engine.compute_reward(outcome, signals, weights={"quality": 2.0, "cost": 0.5})
    assert breakdown.total == 2.0 * 1.0 + 1.0 * 1.0 - 0.5 * 1.0 - 1.0 * 10


def test_reward_pipe_compute() -> None:
    outcome = {"cost_usd": 0.1, "latency_ms": 50}
    signals = {"quality": 0.8, "groundedness": 0.7}
    result = reward_pipe.compute("routing", {"foo": "bar"}, outcome, signals)
    assert result.domain == "routing"
    assert result.context == {"foo": "bar"}
    assert result.reward == result.breakdown.total
    assert result.signals["quality"] == 0.8


def test_epsilon_greedy_bandit() -> None:
    random.seed(0)
    policy = EpsilonGreedyBandit(epsilon=0.0)
    context: dict[str, object] = {}
    candidates = ["x", "y"]
    policy.update("x", 1.0, context)
    policy.update("y", 0.0, context)
    choice = policy.recommend(context, candidates)
    assert choice == "x"


def test_ucb1_bandit() -> None:
    policy = UCB1Bandit()
    context: dict[str, object] = {}
    candidates = ["x", "y"]
    # First call explores arm x
    choice1 = policy.recommend(context, candidates)
    policy.update(choice1, 1.0 if choice1 == "x" else 0.0, context)
    # Second call explores remaining arm
    choice2 = policy.recommend(context, candidates)
    assert {choice1, choice2} == {"x", "y"}
    policy.update(choice2, 0.0 if choice2 == "y" else 1.0, context)
    # Subsequent recommendation should favour arm x with higher reward
    choice3 = policy.recommend(context, candidates)
    assert choice3 == "x"


def test_policy_registry_and_shields() -> None:
    reg = rl.registry.PolicyRegistry()
    bandit = EpsilonGreedyBandit()
    reg.register("test", bandit)
    assert reg.get("test") is bandit
    result = rl.shields.check({"cost_usd": 2.0}, {"budget": 1.0})
    assert not result.allowed and result.reason == "budget_exceeded"


def test_learning_engine_snapshot_and_status() -> None:
    eng = LearningEngine()
    eng.register_domain("demo", EpsilonGreedyBandit(epsilon=0.0))
    eng.record("demo", {}, "a", 1.0)
    snap = eng.snapshot()
    eng.record("demo", {}, "a", 0.0)
    eng.restore(snap)
    status = eng.status()
    assert status["demo"]["arms"]["a"]["q"] == snap["demo"]["q_values"]["a"]


def test_learning_engine_shadow_bakeoff() -> None:
    eng = LearningEngine()
    eng.register_domain("demo", EpsilonGreedyBandit(epsilon=0.0))

    def trial(arm: str) -> float:
        return 1.0 if arm == "b" else 0.0

    eng.shadow_bakeoff("demo", ["a", "b"], trial)
    status = eng.status()["demo"]["arms"]
    assert status["b"]["q"] > status["a"]["q"]


def test_learn_helper_executes_cycle(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_RL_GLOBAL", "1")
    monkeypatch.setenv("ENABLE_RL_ROUTING", "1")
    reg = rl.registry.PolicyRegistry()
    policy = EpsilonGreedyBandit(epsilon=0.0)
    reg.register("routing", policy)

    def act(arm: str):
        outcome = {"cost_usd": 0.1, "latency_ms": 10}
        signals = {"quality": 1.0, "groundedness": 0.9}
        return outcome, signals

    result = learn.learn("routing", {}, ["a", "b"], act, policy_registry=reg)
    assert result.domain == "routing"
    assert policy.counts["a"] == 1


def test_learn_helper_respects_flags(monkeypatch) -> None:
    reg = rl.registry.PolicyRegistry()
    policy = EpsilonGreedyBandit(epsilon=0.0)
    reg.register("routing", policy)

    def act(arm: str):
        outcome = {"cost_usd": 0.1, "latency_ms": 10}
        signals = {"quality": 1.0, "groundedness": 0.9}
        return outcome, signals

    # Flags disabled -> no learning, first candidate used
    result = learn.learn("routing", {}, ["a", "b"], act, policy_registry=reg)
    assert result.domain == "routing"
    assert policy.counts["a"] == 0

    # Enable global and domain flags -> policy updates
    monkeypatch.setenv("ENABLE_RL_GLOBAL", "1")
    monkeypatch.setenv("ENABLE_RL_ROUTING", "1")
    result = learn.learn("routing", {}, ["a", "b"], act, policy_registry=reg)
    assert policy.counts["a"] == 1
