"""High-level API for registering and using bandit policies."""
from __future__ import annotations

from typing import Any, Dict, Sequence

from .rl.registry import PolicyRegistry
from .rl.policies.bandit_base import EpsilonGreedyBandit


class LearningEngine:
    """Wrapper around the RL policy registry."""

    def __init__(self, registry: PolicyRegistry | None = None) -> None:
        self.registry = registry or PolicyRegistry()

    def register_domain(self, name: str, policy: object | None = None, priors: Dict[Any, float] | None = None) -> None:
        """Register ``policy`` under ``name`` and apply optional ``priors``."""

        bandit = policy or EpsilonGreedyBandit()
        if priors:
            for arm, q in priors.items():
                bandit.q_values[arm] = q
        self.registry.register(name, bandit)

    def recommend(
        self, domain: str, context: Dict[str, Any], candidates: Sequence[Any]
    ) -> Any:
        policy = self.registry.get(domain)
        return policy.recommend(context, candidates)

    def record(self, domain: str, context: Dict[str, Any], action: Any, reward: float) -> None:
        policy = self.registry.get(domain)
        policy.update(action, reward, context)


__all__ = ["LearningEngine"]
