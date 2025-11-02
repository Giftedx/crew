import random
import unittest
from platform.core.rl.policies.bandit_base import EpsilonGreedyBandit, ThompsonSamplingBandit, UCB1Bandit

class TestBanditPolicies(unittest.TestCase):

    def test_epsilon_greedy_exploit_when_zero(self) -> None:
        bandit = EpsilonGreedyBandit(epsilon=0.0)
        bandit.q_values['a'] = 0.1
        bandit.q_values['b'] = 0.9
        choice = bandit.recommend({}, ['a', 'b'])
        self.assertEqual(choice, 'b')

    def test_epsilon_greedy_explore_with_rng(self) -> None:
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        b1 = EpsilonGreedyBandit(epsilon=1.0, rng=rng1)
        b2 = EpsilonGreedyBandit(epsilon=1.0, rng=rng2)
        c1 = b1.recommend({}, [1, 2, 3])
        c2 = b2.recommend({}, [1, 2, 3])
        self.assertEqual(c1, c2)
        self.assertIn(c1, (1, 2, 3))

    def test_ucb1_explore_each_once(self) -> None:
        bandit = UCB1Bandit()
        first = bandit.recommend({}, ['x', 'y'])
        self.assertIn(first, ('x', 'y'))
        bandit.update(first, 1.0, {})
        second = bandit.recommend({}, ['x', 'y'])
        self.assertNotEqual(first, second)

    def test_thompson_sampling_deterministic_rng(self) -> None:
        rng = random.Random(7)
        bandit = ThompsonSamplingBandit(rng=rng)
        choice1 = bandit.recommend({}, ['a', 'b', 'c'])
        rng2 = random.Random(7)
        bandit2 = ThompsonSamplingBandit(rng=rng2)
        choice2 = bandit2.recommend({}, ['a', 'b', 'c'])
        self.assertEqual(choice1, choice2)

    def test_updates_adjust_means(self) -> None:
        bandit = EpsilonGreedyBandit(epsilon=0.0)
        bandit.update('arm', 1.0, {})
        bandit.update('arm', 0.0, {})
        self.assertAlmostEqual(bandit.q_values['arm'], 0.5, places=6)
if __name__ == '__main__':
    unittest.main()