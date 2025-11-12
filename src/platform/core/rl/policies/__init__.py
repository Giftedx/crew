"""Compatibility shims for RL policies under `platform.core.rl.policies`.

Re-exports policy classes from `platform.rl.core.policies`.
"""

from platform.rl.core.policies import (
    EpsilonGreedyBandit,
    LinTSDiagBandit,
    ThompsonSamplingBandit,
    UCB1Bandit,
    VowpalWabbitBandit,
)


__all__ = [
    "EpsilonGreedyBandit",
    "LinTSDiagBandit",
    "ThompsonSamplingBandit",
    "UCB1Bandit",
    "VowpalWabbitBandit",
]
