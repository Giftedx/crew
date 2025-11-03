"""Minimal learning engine used by tests and examples.

This lightweight implementation provides a simple epsilon-greedy style
interface with methods:
- register_domain(name)
- recommend(domain, context, candidates)
- record(domain, context, arm, reward)
- status()

It is intentionally simple and dependency-free for fast test import.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class _ArmState:
    q: float = 0.0
    n: int = 0


class LearningEngine:
    def __init__(self) -> None:
        # domain -> arm -> _ArmState
        self._domains: dict[str, dict[str, _ArmState]] = {}
        # simple policy label for introspection
        self._policy: str = "EpsilonGreedyBandit"

    # Administrative -----------------------------------------------------
    def register_domain(self, name: str) -> None:
        self._domains.setdefault(name, {})

    # Decision -----------------------------------------------------------
    def recommend(self, domain: str, _context: dict[str, Any] | None, candidates: list[str]) -> str:
        """Pick the best-known arm from candidates or the first if unseen."""
        if not candidates:
            return "default"
        arms = self._domains.setdefault(domain, {})
        # Choose candidate with highest q if any known, else first
        best = None
        best_q = float("-inf")
        for c in candidates:
            st = arms.get(c)
            if st and st.q > best_q:
                best_q = st.q
                best = c
        return best or candidates[0]

    # Feedback -----------------------------------------------------------
    def record(self, domain: str, _context: dict[str, Any] | None, arm: str, reward: float) -> None:
        arms = self._domains.setdefault(domain, {})
        st = arms.setdefault(arm, _ArmState())
        # Incremental average update
        st.n += 1
        st.q += (reward - st.q) / max(st.n, 1)

    # Introspection ------------------------------------------------------
    def status(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for d, arms in self._domains.items():
            out[d] = {
                "policy": self._policy,
                "arms": {name: {"q": st.q, "n": st.n} for name, st in arms.items()},
            }
        return out


__all__ = ["LearningEngine"]
