"""Bandit policy implementations."""

from __future__ import annotations

import math
import random  # noqa: S311 - exploration randomness is non-cryptographic
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EpsilonGreedyBandit:
    """A minimal epsilon-greedy bandit policy.

    Optional ``rng`` allows deterministic testing; when ``None`` the global
    :mod:`random` module is used.
    """

    epsilon: float = 0.1
    q_values: defaultdict[Any, float] = field(default_factory=lambda: defaultdict(float))
    counts: defaultdict[Any, int] = field(default_factory=lambda: defaultdict(int))
    rng: random.Random | None = None

    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any:  # noqa: ARG002
        """Return an arm to pull from candidates.

        When ``rng`` is set, exploration randomness is sourced from it to
        enable deterministic testing. Falls back to :mod:`random` otherwise.
        """
        if not candidates:
            raise ValueError("candidates must not be empty")
        eps = max(0.0, min(1.0, float(self.epsilon)))
        _rng = self.rng or random
        # Non-cryptographic randomness acceptable here: policy exploration.
        if _rng.random() < eps:  # noqa: S311 - epsilon-greedy exploration
            return _rng.choice(list(candidates))  # noqa: S311 - candidate selection not security sensitive
        return max(candidates, key=lambda c: self.q_values[c])

    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None:  # noqa: ARG002
        """Update running mean reward for ``action`` with incremental average."""
        self.counts[action] += 1
        n = self.counts[action]
        q = self.q_values[action]
        self.q_values[action] = q + (reward - q) / n

    # -------------------- optional serialization helpers --------------------
    def state_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable view of the policy state.

        Provided for diagnostics and potential custom persistence. LearningEngine
        does not require this, but will include these fields if present.
        """
        return {
            "policy": self.__class__.__name__,
            "version": 1,
            "epsilon": float(self.epsilon),
            "q_values": dict(self.q_values),
            "counts": dict(self.counts),
        }

    def load_state(self, state: dict[str, Any]) -> None:
        """Load state previously produced by :meth:`state_dict`.

        Backward compatibility:
        - Missing version -> treat as v0 (fields without `version`).
        - Version > known -> ignore (caller should decide to skip).
        """
        ver = state.get("version")
        if ver is not None and ver > 1:
            return  # future version not understood
        qv = state.get("q_values") or {}
        ct = state.get("counts") or {}
        try:
            self.epsilon = float(state.get("epsilon", self.epsilon))
        except Exception:
            pass
        self.q_values.clear()
        self.q_values.update(qv)
        self.counts.clear()
        self.counts.update(ct)


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

    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any:  # noqa: ARG002
        """Return an arm based on UCB1; explore each arm once, then exploit."""
        if not candidates:
            raise ValueError("candidates must not be empty")
        # Explore each arm once before applying the UCB formula.
        for c in candidates:
            if self.counts[c] == 0:
                return c
        self.total_pulls += 1
        return max(
            candidates,
            key=lambda c: self.q_values[c] + math.sqrt(2 * math.log(self.total_pulls) / self.counts[c]),
        )

    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None:  # noqa: ARG002
        """Update running mean reward for ``action`` with incremental average."""
        self.counts[action] += 1
        n = self.counts[action]
        q = self.q_values[action]
        self.q_values[action] = q + (reward - q) / n

    # -------------------- optional serialization helpers --------------------
    def state_dict(self) -> dict[str, Any]:
        return {
            "policy": self.__class__.__name__,
            "version": 1,
            "q_values": dict(self.q_values),
            "counts": dict(self.counts),
            "total_pulls": int(self.total_pulls),
        }

    def load_state(self, state: dict[str, Any]) -> None:
        qv = state.get("q_values") or {}
        ct = state.get("counts") or {}
        ver = state.get("version")
        if ver is not None and ver > 1:
            return
        self.q_values.clear()
        self.q_values.update(qv)
        self.counts.clear()
        self.counts.update(ct)
        try:
            self.total_pulls = int(state.get("total_pulls", self.total_pulls))
        except Exception:
            pass


__all__ = ["EpsilonGreedyBandit", "UCB1Bandit"]


@dataclass
class ThompsonSamplingBandit:
    """Thompson Sampling with Beta priors for rewards in [0,1].

    Keeps Beta(a,b) per arm, samples on recommend, and updates with fractional rewards.
    Also maintains q_values/counts for diagnostics and snapshot compatibility.

    Optional ``rng`` allows deterministic testing; when ``None`` the global
    :mod:`random` module is used.
    """

    a_params: defaultdict[Any, float] = field(default_factory=lambda: defaultdict(lambda: 1.0))
    b_params: defaultdict[Any, float] = field(default_factory=lambda: defaultdict(lambda: 1.0))
    q_values: defaultdict[Any, float] = field(default_factory=lambda: defaultdict(float))
    counts: defaultdict[Any, int] = field(default_factory=lambda: defaultdict(int))
    rng: random.Random | None = None

    def recommend(self, context: dict[str, Any], candidates: Sequence[Any]) -> Any:  # noqa: ARG002
        if not candidates:
            raise ValueError("candidates must not be empty")
        best_arm = None
        best_sample = float("-inf")
        _rng = self.rng or random
        for c in candidates:
            a = self.a_params[c]
            b = self.b_params[c]
            s = _rng.betavariate(a, b)  # noqa: S311 - non-crypto exploration randomness
            if s > best_sample:
                best_sample = s
                best_arm = c
        return best_arm

    def update(self, action: Any, reward: float, context: dict[str, Any]) -> None:  # noqa: ARG002
        r = max(0.0, min(1.0, float(reward)))
        self.a_params[action] += r
        self.b_params[action] += 1.0 - r
        # running mean for diagnostics
        self.counts[action] += 1
        n = self.counts[action]
        q = self.q_values[action]
        self.q_values[action] = q + (r - q) / n

    # -------------------- optional serialization helpers --------------------
    def state_dict(self) -> dict[str, Any]:
        return {
            "policy": self.__class__.__name__,
            "version": 1,
            "q_values": dict(self.q_values),
            "counts": dict(self.counts),
            "a_params": dict(self.a_params),
            "b_params": dict(self.b_params),
        }

    def load_state(self, state: dict[str, Any]) -> None:
        qv = state.get("q_values") or {}
        ct = state.get("counts") or {}
        ap = state.get("a_params") or {}
        bp = state.get("b_params") or {}
        ver = state.get("version")
        if ver is not None and ver > 1:
            return
        self.q_values.clear()
        self.q_values.update(qv)
        self.counts.clear()
        self.counts.update(ct)
        self.a_params.clear()
        self.a_params.update(ap)
        self.b_params.clear()
        self.b_params.update(bp)


__all__.append("ThompsonSamplingBandit")
