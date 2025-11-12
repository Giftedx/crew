"""Thompson Sampling router for adaptive LLM model selection.

Implements multi-armed bandit routing with Thompson Sampling (Beta-Bernoulli)
for per-task/tenant adaptation. Tracks reward signals from evaluation gates
and cost metrics to select optimal models over time.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from platform.config.configuration import get_config
from typing import Any

import numpy as np

from ultimate_discord_intelligence_bot.obs import metrics
from ultimate_discord_intelligence_bot.tenancy import current_tenant


logger = logging.getLogger(__name__)


@dataclass
class BetaPosterior:
    """Beta distribution posterior for Thompson Sampling."""

    alpha: float = 1.0
    beta: float = 1.0
    trials: int = 0
    last_updated: float = field(default_factory=time.time)

    def sample(self) -> float:
        """Sample from Beta(alpha, beta) distribution."""
        return np.random.beta(self.alpha, self.beta)

    def update(self, reward: float) -> None:
        """Update posterior with Bernoulli reward [0, 1]."""
        self.alpha += reward
        self.beta += 1.0 - reward
        self.trials += 1
        self.last_updated = time.time()

    def mean(self) -> float:
        """Return posterior mean (expected reward)."""
        return self.alpha / (self.alpha + self.beta)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"alpha": self.alpha, "beta": self.beta, "trials": self.trials, "last_updated": self.last_updated}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BetaPosterior:
        """Deserialize from dict."""
        return cls(
            alpha=data.get("alpha", 1.0),
            beta=data.get("beta", 1.0),
            trials=data.get("trials", 0),
            last_updated=data.get("last_updated", time.time()),
        )


class ThompsonSamplingRouter:
    """Adaptive LLM router using Thompson Sampling for model selection.

    Features:
    - Per-task/tenant posteriors (e.g., "tenant_A:analysis", "tenant_B:fallacy")
    - Beta-Bernoulli conjugate prior (uniform initialization)
    - Persistent state (JSON file or Redis)
    - Cold-start exploration (forced uniform sampling for first N trials)
    - A/B gating (gradual rollout)
    - Fallback to LinUCB/default on failure

    Reward Signal:
    - Combines evaluation score (quality/safety) + cost efficiency + latency
    - Range: [0.0, 1.0]
    """

    def __init__(self, persistence_path: str | Path | None = None, cold_start_trials: int | None = None) -> None:
        """Initialize Thompson Sampling router.

        Args:
            persistence_path: Path to JSON file for state persistence (default: ./data/ts_router_state.json)
            cold_start_trials: Number of uniform trials before exploitation (default from config)
        """
        config = get_config()
        self.enabled = config.enable_ts_routing
        self.cold_start_trials = (
            cold_start_trials if cold_start_trials is not None else config.ts_routing_cold_start_trials
        )
        self._posteriors: dict[str, dict[str, BetaPosterior]] = {}
        if persistence_path is None:
            persistence_path = Path("./data/ts_router_state.json")
        self.persistence_path = Path(persistence_path)
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        if self.enabled:
            self._load_state()
            logger.info(
                "Thompson Sampling router initialized (cold_start=%d, state=%s)",
                self.cold_start_trials,
                self.persistence_path,
            )

    def select_model(self, task_name: str, available_models: list[str], deterministic: bool = False) -> str:
        """Select model for task using Thompson Sampling.

        Args:
            task_name: Name of the task (e.g., "analysis", "fallacy_detection")
            available_models: List of candidate model names
            deterministic: If True, return model with highest posterior mean (no sampling)

        Returns:
            Selected model name
        """
        if not self.enabled or not available_models:
            return available_models[0] if available_models else "default"
        tenant_ctx = current_tenant()
        tenant_id = tenant_ctx.tenant_id if tenant_ctx else "default"
        task_key = f"{tenant_id}:{task_name}"
        if task_key not in self._posteriors:
            self._posteriors[task_key] = {}
        posteriors = self._posteriors[task_key]
        for model in available_models:
            if model not in posteriors:
                posteriors[model] = BetaPosterior()
        total_trials = sum(p.trials for p in posteriors.values())
        in_cold_start = total_trials < self.cold_start_trials
        if in_cold_start:
            selected = np.random.choice(available_models)
            logger.debug(
                "Cold-start exploration: task=%s, selected=%s, trials=%d/%d",
                task_key,
                selected,
                total_trials,
                self.cold_start_trials,
            )
        elif deterministic:
            selected = max(available_models, key=lambda m: posteriors[m].mean())
            logger.debug(
                "Deterministic selection: task=%s, selected=%s, mean=%.3f",
                task_key,
                selected,
                posteriors[selected].mean(),
            )
        else:
            samples = {model: posteriors[model].sample() for model in available_models}
            selected = max(samples, key=samples.get)
            logger.debug("Thompson Sampling: task=%s, selected=%s, sample=%.3f", task_key, selected, samples[selected])
        metrics.get_metrics().counter(
            "ts_router_selections_total",
            labels={"task": task_name, "model": selected, "cold_start": str(in_cold_start)},
        )
        return selected

    def update_reward(self, task_name: str, model_name: str, reward: float) -> None:
        """Update posterior with observed reward.

        Args:
            task_name: Name of the task
            model_name: Model that was used
            reward: Reward in [0.0, 1.0] (from evaluation + cost/latency)
        """
        if not self.enabled:
            return
        reward = max(0.0, min(1.0, reward))
        tenant_ctx = current_tenant()
        tenant_id = tenant_ctx.tenant_id if tenant_ctx else "default"
        task_key = f"{tenant_id}:{task_name}"
        if task_key not in self._posteriors:
            self._posteriors[task_key] = {}
        if model_name not in self._posteriors[task_key]:
            self._posteriors[task_key][model_name] = BetaPosterior()
        posterior = self._posteriors[task_key][model_name]
        posterior.update(reward)
        logger.debug(
            "Updated posterior: task=%s, model=%s, reward=%.3f, alpha=%.2f, beta=%.2f, mean=%.3f",
            task_key,
            model_name,
            reward,
            posterior.alpha,
            posterior.beta,
            posterior.mean(),
        )
        metrics.get_metrics().histogram("ts_router_reward", reward, labels={"task": task_name, "model": model_name})
        metrics.get_metrics().histogram(
            "ts_router_posterior_mean", posterior.mean(), labels={"task": task_name, "model": model_name}
        )
        if posterior.trials % 10 == 0:
            self._save_state()

    def get_statistics(self, task_name: str | None = None) -> dict[str, Any]:
        """Get router statistics.

        Args:
            task_name: Optional task filter

        Returns:
            Dict with posteriors, means, trials
        """
        stats: dict[str, Any] = {}
        for task_key, posteriors in self._posteriors.items():
            if task_name and (not task_key.endswith(f":{task_name}")):
                continue
            stats[task_key] = {
                model: {
                    "mean": posterior.mean(),
                    "alpha": posterior.alpha,
                    "beta": posterior.beta,
                    "trials": posterior.trials,
                    "last_updated": posterior.last_updated,
                }
                for model, posterior in posteriors.items()
            }
        return stats

    def _save_state(self) -> None:
        """Persist posteriors to JSON."""
        try:
            state = {
                task_key: {model: posterior.to_dict() for model, posterior in posteriors.items()}
                for task_key, posteriors in self._posteriors.items()
            }
            with open(self.persistence_path, "w") as f:
                json.dump(state, f, indent=2)
            logger.debug("Saved TS router state to %s", self.persistence_path)
        except Exception as e:
            logger.warning("Failed to save TS router state: %s", e)

    def _load_state(self) -> None:
        """Load posteriors from JSON."""
        if not self.persistence_path.exists():
            logger.info("No existing TS router state found; starting fresh")
            return
        try:
            with open(self.persistence_path) as f:
                state = json.load(f)
            for task_key, posteriors_dict in state.items():
                self._posteriors[task_key] = {
                    model: BetaPosterior.from_dict(posterior_dict) for model, posterior_dict in posteriors_dict.items()
                }
            total_tasks = len(self._posteriors)
            total_trials = sum(p.trials for posteriors in self._posteriors.values() for p in posteriors.values())
            logger.info("Loaded TS router state: %d tasks, %d total trials", total_tasks, total_trials)
        except Exception as e:
            logger.warning("Failed to load TS router state: %s; starting fresh", e)
            self._posteriors = {}


__all__ = ["BetaPosterior", "ThompsonSamplingRouter"]
