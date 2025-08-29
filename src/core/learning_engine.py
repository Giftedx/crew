"""High-level API for registering and using bandit policies."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .rl.policies.bandit_base import EpsilonGreedyBandit
from .rl.registry import PolicyRegistry


class LearningEngine:
    """Wrapper around the RL policy registry."""

    def __init__(self, registry: PolicyRegistry | None = None) -> None:
        self.registry = registry or PolicyRegistry()

    def register_domain(
        self, name: str, policy: object | None = None, priors: dict[Any, float] | None = None
    ) -> None:
        """Register ``policy`` under ``name`` and apply optional ``priors``."""

        bandit = policy or EpsilonGreedyBandit()
        if priors:
            for arm, q in priors.items():
                bandit.q_values[arm] = q
        self.registry.register(name, bandit)

    def recommend(self, domain: str, context: dict[str, Any], candidates: Sequence[Any]) -> Any:
        policy = self.registry.get(domain)
        return policy.recommend(context, candidates)

    def record(self, domain: str, context: dict[str, Any], action: Any, reward: float) -> None:
        policy = self.registry.get(domain)
        policy.update(action, reward, context)

    # ------------------------------------------------------------------ cold-start
    def shadow_bakeoff(
        self,
        domain: str,
        candidates: Sequence[Any],
        trial_fn,
    ) -> None:
        """Run a shadow bakeoff evaluating ``candidates`` without affecting live calls.

        ``trial_fn`` should be a callable accepting an arm and returning a
        reward.  Each candidate is evaluated once and the resulting reward is
        recorded in the policy.  This provides a cheap cold-start prior before
        the domain is used in production.
        """

        for arm in candidates:
            reward = trial_fn(arm)
            self.record(domain, {}, arm, reward)

    # ------------------------------------------------------------------ ops
    def snapshot(self) -> dict[str, dict[str, dict[Any, float]]]:
        """Return a snapshot of all registered policy state.

        The snapshot is a serialisable dictionary mapping ``domain`` to the
        policy class name together with its ``q_values`` and ``counts``.  It can
        be persisted externally and later passed to :meth:`restore` to roll back
        to an earlier state.
        """

        data: dict[str, dict[str, dict[Any, float]]] = {}
        for name, policy in self.registry.items():
            state = {
                "policy": policy.__class__.__name__,
                "q_values": dict(getattr(policy, "q_values", {})),
                "counts": dict(getattr(policy, "counts", {})),
            }
            data[name] = state
        return data

    def restore(self, snapshot: dict[str, dict[str, dict[Any, float]]]) -> None:
        """Restore policy state from ``snapshot`` produced by :meth:`snapshot`."""

        for name, state in snapshot.items():
            policy = self.registry.get(name)
            if hasattr(policy, "q_values"):
                policy.q_values.clear()
                policy.q_values.update(state.get("q_values", {}))
            if hasattr(policy, "counts"):
                policy.counts.clear()
                policy.counts.update(state.get("counts", {}))

    def status(self) -> dict[str, dict[str, Any]]:
        """Return a diagnostic view of all policies and their arms."""

        summary: dict[str, dict[str, Any]] = {}
        for name, policy in self.registry.items():
            arms = {}
            q_vals = getattr(policy, "q_values", {})
            counts = getattr(policy, "counts", {})
            for arm, q in q_vals.items():
                arms[arm] = {"q": q, "n": counts.get(arm, 0)}
            summary[name] = {"policy": policy.__class__.__name__, "arms": arms}
        return summary


__all__ = ["LearningEngine"]
