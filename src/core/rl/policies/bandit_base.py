"""Bandit policy implementations."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EpsilonGreedyBandit:
    """A minimal epsilon-greedy bandit policy."""

    epsilon: float = 0.1
    q_values: defaultdict[Any, float] = field(default_factory=lambda: defaultdict(float))
    counts: defaultdict[Any, int] = field(default_factory=lambda: defaultdict(int))

    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any:
        if not candidates:
            raise ValueError("candidates must not be empty")
        if random.random() < self.epsilon:
            return random.choice(list(candidates))
        return max(candidates, key=lambda c: self.q_values[c])

    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None:
        self.counts[action] += 1
        n = self.counts[action]
        q = self.q_values[action]
        self.q_values[action] = q + (reward - q) / n


@dataclass
class UCB1Bandit:
    """Upper Confidence Bound (UCB1) bandit policy.

    Each arm is tried once before exploitation begins. Thereafter the policy
    picks the arm maximising ``q + sqrt(2*ln(total)/n)`` where ``q`` is the mean
    reward and ``n`` the pull count for the arm.
    """

    q_values: defaultdict[Any, float] = field(default_factory=lambda: defaultdict(float))
    counts: defaultdict[Any, int] = field(default_factory=lambda: defaultdict(int))
    total_pulls: int = 0

    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any:
        if not candidates:
            raise ValueError("candidates must not be empty")
        # Explore each arm once before applying the UCB formula.
        for c in candidates:
            if self.counts[c] == 0:
                return c
        self.total_pulls += 1
        return max(
            candidates,
            key=lambda c: self.q_values[c]
            + math.sqrt(2 * math.log(self.total_pulls) / self.counts[c]),
        )

    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None:
        self.counts[action] += 1
        n = self.counts[action]
        q = self.q_values[action]
        self.q_values[action] = q + (reward - q) / n


__all__ = ["EpsilonGreedyBandit", "UCB1Bandit"]
