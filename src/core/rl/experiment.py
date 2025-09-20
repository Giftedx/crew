"""Experiment harness for RL policy / model routing.

Provides a minimal, flag-gated (``ENABLE_EXPERIMENT_HARNESS``) A/B style
mechanism focused on routing / bandit policy decisions. Keeps state in-memory
and imposes near-zero overhead when disabled.
"""

from __future__ import annotations

import hashlib
import logging
import os
from collections.abc import Callable, Mapping, MutableMapping
from dataclasses import dataclass, field
from typing import Any

try:  # Provide a patchable placeholder metrics namespace for tests
    METRICS_AVAILABLE = True

    class _MetricsShim:  # minimal attribute container; tests will patch attributes on this
        pass

    metrics = _MetricsShim()  # type: ignore
except ImportError:  # pragma: no cover
    METRICS_AVAILABLE = False
    metrics = None  # type: ignore


# Provide a patchable placeholder for tenancy accessor used in tests when metrics patched
def current_tenant():  # type: ignore
    return None


logger = logging.getLogger(__name__)


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

        # Log allocation decision with full context
        logger.debug(
            "Experiment allocation: experiment_id=%s, allocation_key=%s, phase=%s, chosen=%s, r=%f, variants=%s",
            self.experiment_id,
            allocation_key,
            self.phase,
            chosen,
            r,
            self.variants,
        )

        # Record metrics if available
        if METRICS_AVAILABLE:
            try:
                from obs import metrics
                from ultimate_discord_intelligence_bot.tenancy import current_tenant

                ctx = current_tenant()
                if ctx:
                    labels = {
                        "tenant": ctx.tenant_id,
                        "workspace": ctx.workspace_id,
                        "experiment_id": self.experiment_id,
                        "variant": chosen,
                        "phase": self.phase,
                    }
                    metrics.EXPERIMENT_VARIANT_ALLOCATIONS.labels(**labels).inc()

                    # Update phase status gauge
                    phase_labels = {
                        "tenant": ctx.tenant_id,
                        "workspace": ctx.workspace_id,
                        "experiment_id": self.experiment_id,
                    }
                    phase_value = 1.0 if self.phase == "active" else 0.0
                    metrics.EXPERIMENT_PHASE_STATUS.labels(**phase_labels).set(phase_value)
            except Exception as e:
                logger.debug("Failed to record experiment allocation metrics: %s", e)

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

        # Log reward recording with context
        logger.debug(
            "Experiment reward recorded: experiment_id=%s, arm=%s, reward=%f, "
            "pulls=%d, reward_sum=%f, reward_mean=%f, regret_sum=%f",
            self.experiment_id,
            arm,
            reward,
            vs.pulls,
            vs.reward_sum,
            vs.reward_mean,
            vs.regret_sum,
        )

        # Record metrics if available
        if METRICS_AVAILABLE:
            try:
                from obs import metrics
                from ultimate_discord_intelligence_bot.tenancy import current_tenant

                ctx = current_tenant()
                if ctx:
                    reward_labels = {
                        "tenant": ctx.tenant_id,
                        "workspace": ctx.workspace_id,
                        "experiment_id": self.experiment_id,
                        "variant": arm,
                    }
                    metrics.EXPERIMENT_REWARDS.labels(**reward_labels).inc()
                    metrics.EXPERIMENT_REWARD_VALUE.labels(**reward_labels).observe(reward)

                    # Update regret gauge
                    metrics.EXPERIMENT_REGRET.labels(**reward_labels).set(vs.regret_sum)
            except Exception as e:
                logger.debug("Failed to record experiment reward metrics: %s", e)

        if self.phase == "shadow" and self.auto_activate_after is not None:
            if self.stats[self.control].pulls >= self.auto_activate_after:
                old_phase = self.phase
                self.phase = "active"
                logger.info(
                    "Experiment auto-activated: experiment_id=%s, phase=%s->%s, control_pulls=%d, threshold=%d",
                    self.experiment_id,
                    old_phase,
                    self.phase,
                    self.stats[self.control].pulls,
                    self.auto_activate_after,
                )

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
        logger.info(
            "Experiment registered: experiment_id=%s, control=%s, variants=%s, phase=%s, auto_activate_after=%s",
            exp.experiment_id,
            exp.control,
            exp.variants,
            exp.phase,
            exp.auto_activate_after,
        )

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
            logger.debug("Experiment not found: experiment_id=%s", experiment_id)
            return candidates[0]
        if allocation_key_fn:
            key = allocation_key_fn(context)
        else:
            tenant = context.get("tenant", "t")
            workspace = context.get("workspace", "w")
            group = context.get("user_group", "g")
            key = f"{tenant}:{workspace}:{group}:{experiment_id}"

        chosen = exp.allocate(key)
        logger.debug(
            "Experiment recommendation: experiment_id=%s, key=%s, chosen=%s, candidates=%s, context_keys=%s",
            experiment_id,
            key,
            chosen,
            candidates,
            list(context.keys()),
        )
        return chosen

    def record(self, experiment_id: str, arm: str, reward: float) -> None:
        if not _flag_enabled(self.FLAG):
            return
        exp = self._experiments.get(experiment_id)
        if not exp:
            logger.debug("Cannot record reward - experiment not found: experiment_id=%s", experiment_id)
            return
        logger.debug("Recording experiment reward: experiment_id=%s, arm=%s, reward=%f", experiment_id, arm, reward)
        exp.record(arm, reward)

    def snapshot(self) -> dict[str, Any]:
        snapshot_data = {eid: exp.snapshot() for eid, exp in self._experiments.items()}

        # Add dashboard metadata
        dashboard_summary = {
            "total_experiments": len(self._experiments),
            "active_experiments": sum(1 for exp in self._experiments.values() if exp.phase == "active"),
            "shadow_experiments": sum(1 for exp in self._experiments.values() if exp.phase == "shadow"),
            "experiments": snapshot_data,
            "timestamp": __import__("time").time(),
        }

        logger.debug(
            "Experiment snapshot generated: total=%d, active=%d, shadow=%d",
            dashboard_summary["total_experiments"],
            dashboard_summary["active_experiments"],
            dashboard_summary["shadow_experiments"],
        )

        return dashboard_summary


__all__ = ["Experiment", "ExperimentManager"]
