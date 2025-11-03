import random
import unittest
from platform.core.learning_engine import LearningEngine
from platform.core.rl.policies.bandit_base import EpsilonGreedyBandit, ThompsonSamplingBandit, UCB1Bandit
from platform.core.rl.policies.linucb import LinUCBDiagBandit
from platform.core.rl.registry import PolicyRegistry
from typing import cast


class TestLearningEngineSnapshotRestore(unittest.TestCase):
    def test_snapshot_and_restore_epsilon_greedy(self) -> None:
        rng = random.Random(123)
        registry = PolicyRegistry()
        engine = LearningEngine(registry)
        engine.register_domain("demo", policy=EpsilonGreedyBandit(epsilon=0.0, rng=rng))
        policy_obj = registry.get("demo")
        policy = cast("EpsilonGreedyBandit", policy_obj)
        policy.q_values["a"] = 0.2
        policy.q_values["b"] = 0.8
        engine.record("demo", {}, "a", 1.0)
        engine.record("demo", {}, "b", 0.0)
        snap = engine.snapshot()
        self.assertIn("demo", snap)
        self.assertEqual(snap["demo"]["policy"], "EpsilonGreedyBandit")
        self.assertAlmostEqual(snap["demo"]["q_values"]["a"], policy.q_values["a"], places=9)
        self.assertAlmostEqual(snap["demo"]["q_values"]["b"], policy.q_values["b"], places=9)
        self.assertEqual(snap["demo"]["counts"]["a"], policy.counts["a"])
        registry2 = PolicyRegistry()
        engine2 = LearningEngine(registry2)
        engine2.register_domain("demo", policy=EpsilonGreedyBandit(epsilon=0.0, rng=random.Random(123)))
        engine2.restore(snap)
        choice = engine2.recommend("demo", {}, ["a", "b"])
        expected = "a" if policy.q_values["a"] >= policy.q_values["b"] else "b"
        self.assertEqual(choice, expected)

    def test_snapshot_and_restore_ucb1(self) -> None:
        registry = PolicyRegistry()
        engine = LearningEngine(registry)
        engine.register_domain("bandit", policy=UCB1Bandit())
        policy_obj = registry.get("bandit")
        policy = cast("UCB1Bandit", policy_obj)
        policy.q_values["a"] = 0.9
        policy.q_values["b"] = 0.1
        policy.counts["a"] = 10
        policy.counts["b"] = 10
        policy.total_pulls = 20
        snap = engine.snapshot()
        registry2 = PolicyRegistry()
        engine2 = LearningEngine(registry2)
        engine2.register_domain("bandit", policy=UCB1Bandit())
        engine2.restore(snap)
        choice = engine2.recommend("bandit", {}, ["a", "b"])
        self.assertEqual(choice, "a")

    def test_snapshot_and_restore_linucb(self) -> None:
        registry = PolicyRegistry()
        engine = LearningEngine(registry)
        engine.register_domain("lin", policy=LinUCBDiagBandit(alpha=0.5, dim=6))
        ctx = {"x": 1.5, "y": "foo"}
        engine.record("lin", ctx, "a", 0.8)
        engine.record("lin", ctx, "b", 0.2)
        snap = engine.snapshot()
        registry2 = PolicyRegistry()
        engine2 = LearningEngine(registry2)
        engine2.register_domain("lin", policy=LinUCBDiagBandit(alpha=0.1, dim=8))
        engine2.restore(snap)
        choice = engine2.recommend("lin", ctx, ["a", "b"])
        self.assertEqual(choice, "a")

    def test_restore_missing_version_backward_compat(self) -> None:
        registry = PolicyRegistry()
        engine = LearningEngine(registry)
        engine.register_domain("demo", policy=EpsilonGreedyBandit(epsilon=0.0, rng=random.Random(1)))
        policy = cast("EpsilonGreedyBandit", registry.get("demo"))
        policy.q_values["x"] = 0.5
        policy.counts["x"] = 2
        snap = engine.snapshot()
        legacy = snap["demo"].copy()
        legacy.pop("version", None)
        registry2 = PolicyRegistry()
        engine2 = LearningEngine(registry2)
        engine2.register_domain("demo", policy=EpsilonGreedyBandit(epsilon=0.0, rng=random.Random(1)))
        engine2.restore({"demo": legacy})
        restored = cast("EpsilonGreedyBandit", registry2.get("demo"))
        self.assertAlmostEqual(restored.q_values["x"], 0.5)
        self.assertEqual(restored.counts["x"], 2)

    def test_restore_future_version_is_skipped(self) -> None:
        registry = PolicyRegistry()
        engine = LearningEngine(registry)
        engine.register_domain("demo", policy=EpsilonGreedyBandit(epsilon=0.0, rng=random.Random(1)))
        snap = engine.snapshot()
        future = snap["demo"].copy()
        future["version"] = 999
        policy = cast("EpsilonGreedyBandit", registry.get("demo"))
        policy.q_values["arm"] = 0.77
        before = dict(policy.q_values)
        engine.restore({"demo": future})
        after = dict(policy.q_values)
        self.assertEqual(before, after)


class TestLearningEngineSnapshotRestoreThompson(unittest.TestCase):
    def test_snapshot_and_restore_thompson_sampling(self) -> None:
        seed = 98765
        rng = random.Random(seed)
        registry = PolicyRegistry()
        engine = LearningEngine(registry)
        engine.register_domain("ts", policy=ThompsonSamplingBandit(rng=rng))
        policy_obj = registry.get("ts")
        policy = cast("ThompsonSamplingBandit", policy_obj)
        policy.a_params["a"] = 5.0
        policy.b_params["a"] = 1.0
        policy.a_params["b"] = 1.0
        policy.b_params["b"] = 5.0
        policy.q_values["a"] = 0.8
        policy.q_values["b"] = 0.2
        policy.counts["a"] = 10
        policy.counts["b"] = 10
        snap = engine.snapshot()
        registry2 = PolicyRegistry()
        engine2 = LearningEngine(registry2)
        engine2.register_domain("ts", policy=ThompsonSamplingBandit(rng=random.Random(seed)))
        engine2.restore(snap)
        mirror = ThompsonSamplingBandit(rng=random.Random(seed))
        mirror.load_state(snap["ts"])
        expected = mirror.recommend({}, ["a", "b"])
        choice = engine2.recommend("ts", {}, ["a", "b"])
        self.assertEqual(choice, expected)


if __name__ == "__main__":
    unittest.main()
