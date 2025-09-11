"""Experiment harness for RL policy / model routing.

Provides a minimal, flag-gated (``ENABLE_EXPERIMENT_HARNESS``) A/B style
mechanism focused on routing / bandit policy decisions. Keeps state in-memory
and imposes near-zero overhead when disabled.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Callable, Mapping, MutableMapping
from dataclasses import dataclass, field
from typing import Any


def _flag_enabled(name: str) -> bool:
    v = os.getenv(name, "").strip().lower()
    return v in {"1", "true", "yes", "on"}


def _hash_key(s: str) -> int:
    h = hashlib.sha256(s.encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big", signed=False)


@dataclass
class VariantStats:
    pulls: int = 0
    reward_sum: float = 0.0
    last_reward: float = 0.0
    regret_sum: float = 0.0

    @property
    def reward_mean(self) -> float:  # derived metric
        return self.reward_sum / self.pulls if self.pulls else 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "pulls": float(self.pulls),
            "reward_sum": float(self.reward_sum),
            "reward_mean": float(self.reward_mean),
            "last_reward": float(self.last_reward),
            "regret_sum": float(self.regret_sum),
        }


@dataclass
class Experiment:
    experiment_id: str
    control: str
    variants: Mapping[str, float]
    phase: str = "shadow"
    auto_activate_after: int | None = None
    baseline_regret_arm: str | None = None
    description: str | None = None
    stats: MutableMapping[str, VariantStats] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.stats.setdefault(self.control, VariantStats())
        for arm in self.variants:
            self.stats.setdefault(arm, VariantStats())
        if self.baseline_regret_arm is None:
            self.baseline_regret_arm = self.control

    def allocate(self, allocation_key: str) -> str:
        if not self.variants:
            return self.control
        cumulative: list[tuple[str, float]] = []
        running = 0.0
        for arm, frac in self.variants.items():
            running += max(0.0, float(frac))
            cumulative.append((arm, running))
        # Control receives residual probability mass (1 - running) if any.
        r = _hash_key(allocation_key) / float(2**64 - 1)
        chosen = self.control
        for arm, boundary in cumulative:
            threshold = min(1.0, boundary)
            if r <= threshold:
                chosen = arm
                break
        return self.control if self.phase == "shadow" else chosen

    def record(self, arm: str, reward: float) -> None:
        vs = self.stats.setdefault(arm, VariantStats())
        vs.pulls += 1
        vs.reward_sum += reward
        vs.last_reward = reward
        baseline = self.baseline_regret_arm or self.control
        if baseline in self.stats and arm != baseline:
            base_mean = self.stats[baseline].reward_mean
            vs.regret_sum += max(0.0, base_mean - reward)
        if self.phase == "shadow" and self.auto_activate_after is not None:
            if self.stats[self.control].pulls >= self.auto_activate_after:
                self.phase = "active"

    def snapshot(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "control": self.control,
            "variants": dict(self.variants),
            "phase": self.phase,
            "stats": {k: v.as_dict() for k, v in self.stats.items()},
        }


class ExperimentManager:
    FLAG = "ENABLE_EXPERIMENT_HARNESS"

    def __init__(self) -> None:
        self._experiments: dict[str, Experiment] = {}

    def register(self, exp: Experiment) -> None:
        self._experiments[exp.experiment_id] = exp

    def exists(self, experiment_id: str) -> bool:
        return experiment_id in self._experiments

    def recommend(
        self,
        experiment_id: str,
        context: Mapping[str, Any],
        candidates: list[str],
        allocation_key_fn: Callable[[Mapping[str, Any]], str] | None = None,
    ) -> str:
        if not _flag_enabled(self.FLAG) or not candidates:
            return candidates[0] if candidates else ""
        exp = self._experiments.get(experiment_id)
        if not exp:
            return candidates[0]
        if allocation_key_fn:
            key = allocation_key_fn(context)
        else:
            tenant = context.get("tenant", "t")
            workspace = context.get("workspace", "w")
            group = context.get("user_group", "g")
            key = f"{tenant}:{workspace}:{group}:{experiment_id}"
        return exp.allocate(key)

    def record(self, experiment_id: str, arm: str, reward: float) -> None:
        if not _flag_enabled(self.FLAG):
            return
        exp = self._experiments.get(experiment_id)
        if not exp:
            return
        exp.record(arm, reward)

    def snapshot(self) -> dict[str, Any]:
        return {eid: exp.snapshot() for eid, exp in self._experiments.items()}


__all__ = ["Experiment", "ExperimentManager"]
