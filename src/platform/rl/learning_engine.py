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

from contextlib import suppress
from dataclasses import dataclass
from typing import Any


@dataclass
class _ArmState:
    q: float = 0.0
    n: int = 0


class LearningEngine:
    def __init__(self, registry: dict[str, Any] | None = None, **_: Any) -> None:
        # domain -> arm -> _ArmState (internal fallback when no external policy is set)
        self._domains: dict[str, dict[str, _ArmState]] = {}
        # Optional per-domain policy objects (e.g., epsilon-greedy, LinUCB, etc.)
        self._registry: dict[str, Any] = dict(registry) if isinstance(registry, dict) else {}
        # simple policy label for introspection
        self._policy: str = "EpsilonGreedyBandit"

    # Administrative -----------------------------------------------------
    def register_domain(self, name: str, policy: Any | None = None) -> None:
        """Register a logical domain with an optional policy object.

        Accepts an optional policy instance (bandit). If omitted, the domain is
        initialised with internal stats-only storage; callers may still record
        outcomes and get sensible recommendations based on running means.
        """
        self._domains.setdefault(name, {})
        if policy is not None:
            self._registry[name] = policy

    # Decision -----------------------------------------------------------
    def recommend(self, domain: str, _context: dict[str, Any] | None, candidates: list[str]) -> str:
        """Pick the best-known arm from candidates or the first if unseen."""
        if not candidates:
            return "default"
        # Prefer registered policy if present
        policy = self._registry.get(domain)
        if policy is not None and hasattr(policy, "recommend"):
            try:
                choice = policy.recommend(_context or {}, list(candidates))
                return str(choice)
            except Exception:
                # fall back to internal heuristic
                pass
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
        # Update internal running mean stats
        arms = self._domains.setdefault(domain, {})
        st = arms.setdefault(arm, _ArmState())
        st.n += 1
        st.q += (reward - st.q) / max(st.n, 1)
        # Forward to registered policy if it supports updates
        policy = self._registry.get(domain)
        if policy is not None and hasattr(policy, "update"):
            with suppress(Exception):
                policy.update(arm, reward, _context or {})

    # Legacy compatibility ------------------------------------------------
    def select_model(self, domain: str, candidates: list[str]) -> str:
        if not candidates:
            raise ValueError("candidates must not be empty")
        return self.recommend(domain, {}, candidates)

    def update(self, domain: str, action: str, reward: float) -> None:
        self.record(domain, {}, action, reward)

    # Introspection ------------------------------------------------------
    def status(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for d, arms in self._domains.items():
            out[d] = {
                "policy": self._policy,
                "arms": {name: {"q": st.q, "n": st.n} for name, st in arms.items()},
            }
        return out

    # Expose registry for shims that inspect underlying policies
    @property
    def registry(self) -> dict[str, Any]:
        return self._registry


__all__ = ["LearningEngine"]
