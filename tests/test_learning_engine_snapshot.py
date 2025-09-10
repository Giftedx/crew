import random
import unittest
from typing import cast

from core.learning_engine import LearningEngine
from core.rl.policies.bandit_base import EpsilonGreedyBandit, ThompsonSamplingBandit, UCB1Bandit
from core.rl.policies.linucb import LinUCBDiagBandit
from core.rl.registry import PolicyRegistry


class TestLearningEngineSnapshotRestore(unittest.TestCase):
    def test_snapshot_and_restore_epsilon_greedy(self) -> None:
        # Set up engine with deterministic RNG on epsilon-greedy
        rng = random.Random(123)
        registry = PolicyRegistry()
        engine = LearningEngine(registry)
        engine.register_domain("demo", policy=EpsilonGreedyBandit(epsilon=0.0, rng=rng))

        # Apply priors and some updates
        policy_obj = registry.get("demo")
        policy = cast(EpsilonGreedyBandit, policy_obj)
        policy.q_values["a"] = 0.2
        policy.q_values["b"] = 0.8
        engine.record("demo", {}, "a", 1.0)  # pulls up mean for 'a'
        engine.record("demo", {}, "b", 0.0)  # pulls down mean for 'b'

        # Snapshot current state
        snap = engine.snapshot()
        self.assertIn("demo", snap)
        self.assertEqual(snap["demo"]["policy"], "EpsilonGreedyBandit")
        self.assertAlmostEqual(snap["demo"]["q_values"]["a"], policy.q_values["a"], places=9)
        self.assertAlmostEqual(snap["demo"]["q_values"]["b"], policy.q_values["b"], places=9)
        self.assertEqual(snap["demo"]["counts"]["a"], policy.counts["a"])  # count incremented

        # Create a fresh engine and restore
        registry2 = PolicyRegistry()
        engine2 = LearningEngine(registry2)
        engine2.register_domain("demo", policy=EpsilonGreedyBandit(epsilon=0.0, rng=random.Random(123)))
        engine2.restore(snap)

        # Verify behavior is equivalent post-restore: with epsilon=0 the best arm wins
        choice = engine2.recommend("demo", {}, ["a", "b"])
        expected = "a" if policy.q_values["a"] >= policy.q_values["b"] else "b"
        self.assertEqual(choice, expected)

    def test_snapshot_and_restore_ucb1(self) -> None:
        # Prepare a UCB1 policy state where both arms were tried
        registry = PolicyRegistry()
        engine = LearningEngine(registry)
        engine.register_domain("bandit", policy=UCB1Bandit())

        # Seed state: both arms tried, different q-values; same counts so higher q wins
        policy_obj = registry.get("bandit")
        policy = cast(UCB1Bandit, policy_obj)
        policy.q_values["a"] = 0.9
        policy.q_values["b"] = 0.1
        policy.counts["a"] = 10
        policy.counts["b"] = 10
        policy.total_pulls = 20

        snap = engine.snapshot()

        # Restore into a fresh engine
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

        # Prepare a simple context and two arms, with some updates
        ctx = {"x": 1.5, "y": "foo"}
        engine.record("lin", ctx, "a", 0.8)
        engine.record("lin", ctx, "b", 0.2)

        snap = engine.snapshot()

        # Restore and ensure recommend is stable with same context and arms
        registry2 = PolicyRegistry()
        engine2 = LearningEngine(registry2)
        engine2.register_domain(
            "lin", policy=LinUCBDiagBandit(alpha=0.1, dim=8)
        )  # different ctor args should be overwritten by snapshot
        engine2.restore(snap)
        choice = engine2.recommend("lin", ctx, ["a", "b"])
        self.assertEqual(choice, "a")

    def test_restore_missing_version_backward_compat(self) -> None:
        # Simulate legacy snapshot without a version field
        registry = PolicyRegistry()
        engine = LearningEngine(registry)
        engine.register_domain("demo", policy=EpsilonGreedyBandit(epsilon=0.0, rng=random.Random(1)))
        policy = cast(EpsilonGreedyBandit, registry.get("demo"))
        policy.q_values["x"] = 0.5
        policy.counts["x"] = 2
        snap = engine.snapshot()
        legacy = snap["demo"].copy()
        legacy.pop("version", None)  # remove version to emulate old snapshot
        # Fresh engine
        registry2 = PolicyRegistry()
        engine2 = LearningEngine(registry2)
        engine2.register_domain("demo", policy=EpsilonGreedyBandit(epsilon=0.0, rng=random.Random(1)))
        engine2.restore({"demo": legacy})
        restored = cast(EpsilonGreedyBandit, registry2.get("demo"))
        self.assertAlmostEqual(restored.q_values["x"], 0.5)
        self.assertEqual(restored.counts["x"], 2)

    def test_restore_future_version_is_skipped(self) -> None:
        registry = PolicyRegistry()
        engine = LearningEngine(registry)
        engine.register_domain("demo", policy=EpsilonGreedyBandit(epsilon=0.0, rng=random.Random(1)))
        # Prepare future version snapshot
        snap = engine.snapshot()
        future = snap["demo"].copy()
        future["version"] = 999  # simulate forward-incompatible snapshot
        # Mutate current policy so we can assert it's unchanged after restore attempt
        policy = cast(EpsilonGreedyBandit, registry.get("demo"))
        policy.q_values["arm"] = 0.77
        before = dict(policy.q_values)
        engine.restore({"demo": future})
        after = dict(policy.q_values)
        self.assertEqual(before, after)  # unchanged because future version skipped


class TestLearningEngineSnapshotRestoreThompson(unittest.TestCase):
    def test_snapshot_and_restore_thompson_sampling(self) -> None:
        # Deterministic RNG for TS
        seed = 98765
        rng = random.Random(seed)

        registry = PolicyRegistry()
        engine = LearningEngine(registry)
        engine.register_domain("ts", policy=ThompsonSamplingBandit(rng=rng))

        # Strong priors to make arms distinct and to test a/b params round-trip
        policy_obj = registry.get("ts")
        policy = cast(ThompsonSamplingBandit, policy_obj)
        policy.a_params["a"] = 5.0
        policy.b_params["a"] = 1.0
        policy.a_params["b"] = 1.0
        policy.b_params["b"] = 5.0
        # Optional diagnostics
        policy.q_values["a"] = 0.8
        policy.q_values["b"] = 0.2
        policy.counts["a"] = 10
        policy.counts["b"] = 10

        snap = engine.snapshot()

        # Restore into a fresh engine with the same seeded RNG
        registry2 = PolicyRegistry()
        engine2 = LearningEngine(registry2)
        engine2.register_domain("ts", policy=ThompsonSamplingBandit(rng=random.Random(seed)))
        engine2.restore(snap)

        # Build a mirror TS with the same seed and state to compute expected choice deterministically
        mirror = ThompsonSamplingBandit(rng=random.Random(seed))
        mirror.load_state(snap["ts"])  # type: ignore[arg-type]

        expected = mirror.recommend({}, ["a", "b"])
        choice = engine2.recommend("ts", {}, ["a", "b"])
        self.assertEqual(choice, expected)


if __name__ == "__main__":
    unittest.main()
