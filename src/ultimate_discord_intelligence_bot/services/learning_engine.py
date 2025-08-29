"""Lightweight reinforcement learning helpers.

This module provides a very small epsilon-greedy bandit implementation that
can be used to improve decision making across the stack.  It intentionally
keeps the interface tiny so it can be swapped out for a more sophisticated
learner later without touching callers.
"""

from __future__ import annotations

import json
import random
import sqlite3
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass
class _ArmState:
    action: str
    count: int = 0
    value: float = 0.0


class LearningEngine:
    """Very small epsilon-greedy bandit learner.

    The learner stores outcomes in an SQLite database so multiple processes can
    inspect the collected rewards.  For in-memory usage pass ``":memory:"`` as
    ``db_path`` which is also the default.
    """

    def __init__(
        self,
        db_path: str | None = None,
        epsilon: float = 0.1,
        store_path: str | None = None,
    ) -> None:
        self.conn = sqlite3.connect(db_path or ":memory:")
        self.epsilon = epsilon
        self._init_db()
        self.policies: dict[str, dict[str, _ArmState]] = {}
        self.store_path = Path(store_path) if store_path else None
        if self.store_path and self.store_path.exists():
            self.stats = json.loads(self.store_path.read_text())
        else:
            self.stats: dict[str, dict[str, dict[str, float]]] = {}

    # ------------------------------------------------------------------ utils
    def _init_db(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rl_events (
                policy_id TEXT,
                action TEXT,
                reward REAL,
                ts REAL
            )
            """
        )
        self.conn.commit()

    # ---------------------------------------------------------------- policy
    def register_policy(self, policy_id: str, actions: Iterable[str]) -> None:
        """Register ``policy_id`` with the given action set."""
        self.policies[policy_id] = {a: _ArmState(a) for a in actions}

    # -------------------------------------------------------------- bandit api
    def recommend(self, policy_id: str, candidates: Sequence[str] | None = None) -> str:
        """Return the action to take for ``policy_id``.

        Args:
            policy_id: Registered policy identifier.
            candidates: Optional subset of actions that are currently valid.
        """
        arms = self.policies.get(policy_id)
        if not arms:
            raise KeyError(f"policy '{policy_id}' is not registered")

        available: list[str] = [a for a in arms if not candidates or a in candidates]
        if not available:
            available = list(arms)

        if random.random() < self.epsilon:
            return random.choice(available)
        return max(available, key=lambda a: arms[a].value)

    def record_outcome(self, policy_id: str, action: str, reward: float) -> None:
        """Record the ``reward`` observed for ``action`` under ``policy_id``."""
        arms = self.policies.get(policy_id)
        if not arms or action not in arms:
            return
        arm = arms[action]
        arm.count += 1
        arm.value += (reward - arm.value) / arm.count
        self.conn.execute(
            "INSERT INTO rl_events(policy_id, action, reward, ts) VALUES (?,?,?,?)",
            (policy_id, action, reward, time.time()),
        )
        self.conn.commit()
        task = policy_id.split("::", 1)[-1]
        self.stats.setdefault(task, {}).setdefault(action, {"reward": 0.0})
        self.stats[task][action]["reward"] = arm.value
        if self.store_path:
            self.store_path.write_text(json.dumps(self.stats))

    # ---------------------------------------------------------- convenience
    def select_model(self, task_type: str, candidates: Sequence[str]) -> str:
        """Wrapper for the ``route.model.select`` policy.

        Each ``task_type`` maintains its own bandit.  ``candidates`` must not be
        empty; the first candidate is used as a safe default.
        """
        policy_id = f"route.model.select::{task_type}"
        if policy_id not in self.policies:
            self.register_policy(policy_id, candidates)
        return self.recommend(policy_id, candidates)

    def update(self, task_type: str, action: str, reward: float) -> None:
        """Update the model selection policy for ``task_type`` with ``reward``."""
        policy_id = f"route.model.select::{task_type}"
        self.record_outcome(policy_id, action, reward)
