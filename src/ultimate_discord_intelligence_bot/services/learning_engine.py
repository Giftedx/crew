"""Deprecated learning engine shim.

Summary:
    Historical epsilon-greedy implementation lived here with ad-hoc SQLite / JSON
        persistence. The canonical engine is :mod:`core.learning_engine` which
        centralizes policy registration and snapshot handling.

Backward Compatibility:
        We retain a thin subclass exposing the minimal legacy surface
        (``select_model`` / ``update`` / ``register_policy``) while delegating core
        logic to :class:`core.learning_engine.LearningEngine`. Persistence path
        parameters are accepted but ignored.

Deprecation Timeline:
        - Unified engine introduced: 2025-Q2
        - Grace period ends: 2025-12-31 (planned)
        - Removal target: first minor release after grace period (see CHANGELOG &
            config/deprecations.yaml). After removal, importing
            ``services.learning_engine`` will raise ``ImportError``.

Migration Instructions:
        - Replace ``from services.learning_engine import LearningEngine`` with
            ``from core.learning_engine import LearningEngine``.
        - Update calls: ``select_model`` -> ``recommend`` with domain naming
            convention ``route.model.select::<task_type>`` if still needed.
        - Use ``record`` instead of ``update`` with explicit domain/action.

New code MUST import the core engine directly.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any
from warnings import warn

from core.learning_engine import LearningEngine as _CoreLearningEngine
from core.rl.policies.bandit_base import EpsilonGreedyBandit


if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


__all__ = ["LearningEngine"]


_REMOVAL_DEADLINE = date.fromisoformat("2025-12-31")
_DEPRECATION_LOG_EMITTED = False


def _check_deadline() -> None:
    today = date.today()
    if today > _REMOVAL_DEADLINE:  # hard stop after grace period
        raise ImportError(
            "services.learning_engine.LearningEngine has passed its removal deadline ("
            f"{_REMOVAL_DEADLINE}); the shim has been disabled. Import core.learning_engine instead."
        )


class LearningEngine(_CoreLearningEngine):  # pragma: no cover - thin wrapper
    """Backward compatible shim for the legacy services learner.

    Args:
        epsilon: Exploration rate applied to newly created epsilon-greedy bandits.
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
        registry: Any | None = None,
    ) -> None:
        _check_deadline()
        warn(
            "services.learning_engine.LearningEngine is deprecated until 2025-12-31; "
            "import core.learning_engine.LearningEngine instead (persistence args are ignored)",
            DeprecationWarning,
            stacklevel=2,
        )
        global _DEPRECATION_LOG_EMITTED
        if not _DEPRECATION_LOG_EMITTED:
            logging.getLogger("deprecations").info(
                "{event}".replace(
                    "{event}",
                    "{",  # simple brace escape for f-string avoidance
                )
            )
            logging.getLogger("deprecations").info(
                json.dumps(
                    {
                        "event": "deprecated_class_used",
                        "symbol": "services.learning_engine.LearningEngine",
                        "replacement": "core.learning_engine.LearningEngine",
                        "removal_date": str(_REMOVAL_DEADLINE),
                    }
                )
            )
            _DEPRECATION_LOG_EMITTED = True
        # The legacy shim only forwards an optional registry; older code may
        # have passed extraneous kwargs which we now ignore explicitly.
        if registry is not None:
            try:
                super().__init__(registry=registry)
            except Exception:
                # Fallback: if the provided object is not a proper registry just delegate default init
                super().__init__()
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
        # Register the domain lazily with an epsilon-greedy bandit if absent.
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
                qv = policy.q_values
                for a in actions:
                    _ = qv[a]
            except Exception as exc:  # pragma: no cover - defensive
                logging.getLogger(__name__).debug("Unable to prime q_values for legacy policy: %s", exc)

    # Legacy methods below mirror the prior minimal surface -----------------
    def recommend_legacy(self, policy_id: str, candidates: Sequence[str] | None = None) -> str:
        policy = self.registry.get(policy_id)
        if candidates is None:
            # Derive candidate set from known q_values/ counts (arms seen so far)
            cand: list[str] = list(getattr(policy, "q_values", {}).keys()) or list(getattr(policy, "counts", {}).keys())
        else:
            cand = list(candidates)
        choice = super().recommend(policy_id, {}, cand)
        return str(choice)

    def record_outcome(self, policy_id: str, action: str, reward: float) -> None:
        super().record(policy_id, {}, action, reward)
