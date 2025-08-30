"""Deprecated learning engine shim.

This module previously contained an independent epsilon‑greedy implementation
with ad‑hoc SQLite + JSON persistence. The canonical reinforcement learning
entry point now lives in :mod:`core.learning_engine` exposing a registry of
policies plus snapshot/restore utilities.

To preserve backward compatibility for existing imports we provide a thin
subclass that delegates to the core engine and re‑implements the small legacy
surface (``select_model`` / ``update``). Persistence‑related constructor
arguments (``db_path`` / ``store_path``) are accepted but ignored. The old API
will be removed after a deprecation period – callers should import and use
``core.learning_engine.LearningEngine`` directly and register domains
explicitly.

# Removal Plan:
#   This shim is slated for deletion after the deprecation window tracked in
#   config/deprecations.yaml (add entry if not present). New code MUST import
#   ``core.learning_engine.LearningEngine`` directly. Retention only exists to
#   avoid breaking older plugin integrations mid‑migration.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Sequence
from pathlib import Path
from warnings import warn

from core.learning_engine import LearningEngine as _CoreLearningEngine
from core.rl.policies.bandit_base import EpsilonGreedyBandit

__all__ = ["LearningEngine"]


class LearningEngine(_CoreLearningEngine):  # pragma: no cover - thin wrapper
    """Backward compatible shim for the legacy services learner.

    Args:
        epsilon: Exploration rate applied to newly created epsilon‑greedy bandits.
        db_path: Ignored (legacy - previously SQLite event log location).
        store_path: Ignored (legacy - previously JSON stats persistence path).

    Notes:
        A ``DeprecationWarning`` is emitted upon instantiation. New code should
        depend on :class:`core.learning_engine.LearningEngine` directly and use
        ``register_domain`` + ``recommend`` / ``record``.
    """

    def __init__(
        self,
        db_path: str | None = None,  # kept for signature compatibility
        epsilon: float = 0.1,
        store_path: str | None = None,  # kept for signature compatibility
        registry: object | None = None,
    ) -> None:  # noqa: D401 - delegated
        warn(
            "services.learning_engine.LearningEngine is deprecated; import "
            "core.learning_engine.LearningEngine instead (persistence args are ignored)",
            DeprecationWarning,
            stacklevel=2,
        )
        # The legacy shim only forwards an optional registry; older code may
        # have passed extraneous kwargs which we now ignore explicitly.
        if registry is not None:
            super().__init__(registry=registry)  # type: ignore[arg-type]
        else:
            super().__init__()
        self._default_epsilon = epsilon
        # Legacy lightweight persistence (stats.json style) -----------------
        self._store_path = Path(store_path) if store_path else None
        self.stats: dict[str, dict[str, dict[str, float]]] = {}
        if self._store_path and self._store_path.exists():
            try:
                raw = json.loads(self._store_path.read_text())
                if isinstance(raw, dict):  # defensive
                    self.stats.update(raw)
            except Exception as exc:  # pragma: no cover - corrupt file ignored
                logging.getLogger(__name__).debug("Ignoring legacy stats load error: %s", exc)

    # ----------------------------- legacy convenience API -----------------
    def select_model(self, task_type: str, candidates: Sequence[str]) -> str:
        domain = f"route.model.select::{task_type}"
        # Register the domain lazily with an epsilon‑greedy bandit if absent.
        if domain not in self.registry:
            self.register_domain(domain, policy=EpsilonGreedyBandit(epsilon=self._default_epsilon))
        # Call into core engine (avoid legacy override)
        choice = super().recommend(domain, {}, candidates)
        return str(choice)

    def update(self, task_type: str, action: str, reward: float) -> None:
        domain = f"route.model.select::{task_type}"
        if domain not in self.registry:
            # Ensure domain exists even if update happens before select_model
            self.register_domain(domain, policy=EpsilonGreedyBandit(epsilon=self._default_epsilon))
        super().record(domain, {}, action, reward)
        # Update legacy stats view for tests expecting reward exposure
        task_stats = self.stats.setdefault(task_type, {}).setdefault(action, {"reward": 0.0})
        # Access underlying bandit to read updated q value
        policy = self.registry.get(domain)
        q_values = getattr(policy, "q_values", {})
        task_stats["reward"] = float(q_values.get(action, task_stats["reward"]))
        if self._store_path:
            try:
                self._store_path.write_text(json.dumps(self.stats))
            except Exception as exc:  # pragma: no cover - best effort
                logging.getLogger(__name__).debug("Ignoring legacy stats write error: %s", exc)

    # Legacy API compatibility (used in tests): expose register_policy with old semantics.
    def register_policy(self, policy_id: str, actions: Iterable[str]) -> None:
        if policy_id not in self.registry:
            self.register_domain(policy_id, policy=EpsilonGreedyBandit(epsilon=self._default_epsilon))
        # Prime priors for provided actions so each arm appears with q=0, n=0
        policy = self.registry.get(policy_id)
        if hasattr(policy, "q_values"):
            try:  # narrow type for mypy via dynamic getattr
                qv = getattr(policy, "q_values")
                for a in actions:
                    _ = qv[a]
            except Exception as exc:  # pragma: no cover - defensive
                logging.getLogger(__name__).debug("Unable to prime q_values for legacy policy: %s", exc)

    # Legacy methods below mirror the prior minimal surface -----------------
    def recommend(self, policy_id: str, candidates: Sequence[str] | None = None) -> str:  # type: ignore[override]
        policy = self.registry.get(policy_id)
        if candidates is None:
            # Derive candidate set from known q_values/ counts (arms seen so far)
            cand: list[str] = list(getattr(policy, "q_values", {}).keys()) or list(
                getattr(policy, "counts", {}).keys()
            )
        else:
            cand = list(candidates)
        choice = super().recommend(policy_id, {}, cand)
        return str(choice)

    def record_outcome(self, policy_id: str, action: str, reward: float) -> None:
        super().record(policy_id, {}, action, reward)
