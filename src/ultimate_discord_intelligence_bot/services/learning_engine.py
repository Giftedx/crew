"""Light-weight learning module for model selection.

The :class:`LearningEngine` implements a simple epsilon-greedy multi-armed
bandit strategy.  It records rewards for model choices on disk so future
routing decisions can improve over time.
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class LearningEngine:
    """Persisted epsilon-greedy learner for model routing."""

    store_path: str = "learning_stats.json"
    epsilon: float = 0.1
    stats: Dict[str, Dict[str, Dict[str, float]]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if os.path.exists(self.store_path):  # pragma: no cover - startup
            try:
                with open(self.store_path, "r", encoding="utf-8") as fh:
                    self.stats = json.load(fh)
            except Exception:
                self.stats = {}

    def select_model(self, task: str, candidates: List[str]) -> str:
        """Choose a model for ``task`` from ``candidates``."""
        tstats = self.stats.setdefault(task, {})
        for model in candidates:
            tstats.setdefault(model, {"n": 0, "reward": 0.0})
        if random.random() < self.epsilon:
            return random.choice(candidates)
        return max(
            candidates,
            key=lambda m: (
                tstats[m]["reward"] / tstats[m]["n"] if tstats[m]["n"] else 0.0
            ),
        )

    def update(self, task: str, model: str, reward: float) -> None:
        """Record the observed ``reward`` for ``model`` in ``task``."""
        tstats = self.stats.setdefault(task, {})
        mstats = tstats.setdefault(model, {"n": 0, "reward": 0.0})
        mstats["n"] += 1
        mstats["reward"] += reward
        try:  # pragma: no cover - disk I/O
            with open(self.store_path, "w", encoding="utf-8") as fh:
                json.dump(self.stats, fh)
        except Exception:
            pass
