"""Compatibility shim for bandit_base under `platform.core.rl.policies`.

Re-exports classes from `platform.rl.core.policies.bandit_base`.
"""

from platform.rl.core.policies.bandit_base import (
    EpsilonGreedyBandit,
    ThompsonSamplingBandit,
    UCB1Bandit,
)


__all__ = [
    "EpsilonGreedyBandit",
    "ThompsonSamplingBandit",
    "UCB1Bandit",
]
