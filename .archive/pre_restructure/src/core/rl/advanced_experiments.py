"""Enhanced shadow evaluation integration for advanced bandit algorithms.

This module provides specialized experiment configurations and evaluation
metrics for DoublyRobust and OffsetTree bandit algorithms, enabling
comprehensive A/B testing against existing policy algorithms.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from obs import metrics
from ultimate_discord_intelligence_bot.tenancy import current_tenant

from .experiment import Experiment, ExperimentManager, VariantStats
from .policies.advanced_bandits import DoublyRobustBandit, OffsetTreeBandit


logger = logging.getLogger(__name__)


@dataclass
class AdvancedBanditStats(VariantStats):
    """Extended stats for advanced bandit evaluation."""

    # Additional metrics specific to advanced bandits
    reward_model_mse: float = 0.0  # Mean squared error for DoublyRobust
    tree_depth_sum: int = 0  # Total tree depth for OffsetTree
    importance_weight_sum: float = 0.0  # Sum of importance weights
    confidence_interval_width: float = 0.0  # Average confidence interval width

    def as_dict(self) -> dict[str, float]:
        """Return extended stats as dictionary."""
        base_dict = super().as_dict()
        base_dict.update(
            {
                "reward_model_mse": float(self.reward_model_mse),
                "tree_depth_avg": float(self.tree_depth_sum / self.pulls) if self.pulls else 0.0,
                "importance_weight_avg": float(self.importance_weight_sum / self.pulls) if self.pulls else 0.0,
                "confidence_interval_avg": float(self.confidence_interval_width / self.pulls) if self.pulls else 0.0,
            }
        )
        return base_dict


class AdvancedBanditExperimentManager(ExperimentManager):
    """Enhanced experiment manager for advanced bandit evaluation."""

    def __init__(self) -> None:
        super().__init__()
        self._advanced_experiments: dict[str, str] = {}  # experiment_id -> bandit_type

    def register_advanced_bandit_experiment(
        self,
        domain: str,
        baseline_policy: str = "epsilon_greedy",
        advanced_policies: dict[str, float] | None = None,
        shadow_samples: int = 1000,
        description: str | None = None,
    ) -> None:
        """Register an experiment comparing advanced bandits against baseline.

        Args:
            domain: The domain to run experiments on
            baseline_policy: Baseline policy name (epsilon_greedy, thompson, linucb)
            advanced_policies: Dict mapping advanced policy names to allocation weights
            shadow_samples: Number of shadow samples before auto-activation
            description: Optional experiment description
        """
        if advanced_policies is None:
            advanced_policies = {
                "doubly_robust": 0.3,
                "offset_tree": 0.3,
            }

        experiment_id = f"advanced_bandits::{domain}"

        # Create experiment with baseline as control
        exp = Experiment(
            experiment_id=experiment_id,
            control=baseline_policy,
            variants=advanced_policies,
            phase="shadow",
            auto_activate_after=shadow_samples,
            baseline_regret_arm=baseline_policy,
            description=description or f"Advanced bandit evaluation for {domain}",
        )

        # Override stats with advanced stats
        exp.stats = {
            baseline_policy: AdvancedBanditStats(),
            **{policy: AdvancedBanditStats() for policy in advanced_policies},
        }

        self.register(exp)
        self._advanced_experiments[experiment_id] = domain

        logger.info(
            "Advanced bandit experiment registered: domain=%s, baseline=%s, advanced_policies=%s, shadow_samples=%d",
            domain,
            baseline_policy,
            list(advanced_policies.keys()),
            shadow_samples,
        )

    def record(self, experiment_id: str, arm: str, reward: float) -> None:
        """Override to use AdvancedBanditStats for advanced experiments."""
        if experiment_id in self._advanced_experiments:
            # Handle advanced experiments with proper stats
            if not self._flag_enabled("ENABLE_EXPERIMENT_HARNESS"):
                return

            exp = self._experiments.get(experiment_id)
            if not exp:
                logger.debug(
                    "Cannot record reward - experiment not found: experiment_id=%s",
                    experiment_id,
                )
                return

            # Use AdvancedBanditStats instead of regular VariantStats
            vs = exp.stats.setdefault(arm, AdvancedBanditStats())
            vs.pulls += 1
            vs.reward_sum += reward
            vs.last_reward = reward

            baseline = exp.baseline_regret_arm or exp.control
            if baseline in exp.stats and arm != baseline:
                base_mean = exp.stats[baseline].reward_mean
                vs.regret_sum += max(0.0, base_mean - reward)

            # Handle auto-activation
            if (
                exp.phase == "shadow"
                and exp.auto_activate_after is not None
                and exp.stats[exp.control].pulls >= exp.auto_activate_after
            ):
                old_phase = exp.phase
                exp.phase = "active"
                logger.info(
                    "Advanced experiment auto-activated: experiment_id=%s, phase=%s->%s, "
                    "control_pulls=%d, threshold=%d",
                    experiment_id,
                    old_phase,
                    exp.phase,
                    exp.stats[exp.control].pulls,
                    exp.auto_activate_after,
                )
        else:
            # Use parent implementation for regular experiments
            super().record(experiment_id, arm, reward)

    def _flag_enabled(self, name: str) -> bool:
        """Check if a feature flag is enabled."""
        import os

        v = os.getenv(name, "").strip().lower()
        return v in {"1", "true", "yes", "on"}

    def record_advanced_metrics(
        self,
        experiment_id: str,
        arm: str,
        reward: float,
        context: dict[str, Any] | None = None,
        bandit_instance: Any = None,
    ) -> None:
        """Record reward and advanced bandit-specific metrics."""
        # Record standard reward
        self.record(experiment_id, arm, reward)

        if experiment_id not in self._experiments:
            return

        exp = self._experiments[experiment_id]
        if arm not in exp.stats or not isinstance(exp.stats[arm], AdvancedBanditStats):
            return

        advanced_stats = exp.stats[arm]

        # Record bandit-specific metrics
        if bandit_instance and context:
            self._record_bandit_specific_metrics(advanced_stats, arm, bandit_instance, context)

        # Update Prometheus metrics
        self._update_advanced_metrics(experiment_id, arm, advanced_stats)

    def _record_bandit_specific_metrics(
        self,
        stats: AdvancedBanditStats,
        arm: str,
        bandit: Any,
        context: dict[str, Any],
    ) -> None:
        """Record metrics specific to bandit type."""
        try:
            if isinstance(bandit, DoublyRobustBandit):
                # Calculate reward model prediction error
                predicted = bandit._predict_reward(arm, context)
                actual = stats.last_reward
                mse = (predicted - actual) ** 2
                stats.reward_model_mse = (stats.reward_model_mse * (stats.pulls - 1) + mse) / stats.pulls

                # Record importance weights
                if bandit.importance_weights.get(arm):
                    recent_weight = bandit.importance_weights[arm][-1]
                    stats.importance_weight_sum += recent_weight

                # Calculate confidence interval width
                model = bandit.reward_models[arm]
                confidence = bandit.alpha * (model["variance"] ** 0.5)
                stats.confidence_interval_width += confidence * 2  # +/- confidence

            elif isinstance(bandit, OffsetTreeBandit):
                # Calculate current tree depth for this context
                node_id = bandit._get_node_id(context)
                depth = bandit.tree_nodes[node_id]["depth"] if node_id in bandit.tree_nodes else 0
                stats.tree_depth_sum += depth

        except Exception as e:
            logger.debug("Failed to record advanced bandit metrics: %s", e)

    def _update_advanced_metrics(
        self,
        experiment_id: str,
        arm: str,
        stats: AdvancedBanditStats,
    ) -> None:
        """Update Prometheus metrics for advanced bandits."""
        try:
            ctx = current_tenant()
            if not ctx:
                return

            labels = {
                "tenant": ctx.tenant_id,
                "workspace": ctx.workspace_id,
                "experiment_id": experiment_id,
                "variant": arm,
            }

            # Update advanced metrics
            if hasattr(metrics, "ADVANCED_BANDIT_REWARD_MODEL_MSE"):
                metrics.ADVANCED_BANDIT_REWARD_MODEL_MSE.labels(**labels).set(stats.reward_model_mse)

            if hasattr(metrics, "ADVANCED_BANDIT_TREE_DEPTH"):
                avg_depth = stats.tree_depth_sum / stats.pulls if stats.pulls else 0.0
                metrics.ADVANCED_BANDIT_TREE_DEPTH.labels(**labels).set(avg_depth)

            if hasattr(metrics, "ADVANCED_BANDIT_IMPORTANCE_WEIGHT"):
                avg_weight = stats.importance_weight_sum / stats.pulls if stats.pulls else 0.0
                metrics.ADVANCED_BANDIT_IMPORTANCE_WEIGHT.labels(**labels).set(avg_weight)

            if hasattr(metrics, "ADVANCED_BANDIT_CONFIDENCE_INTERVAL"):
                avg_ci = stats.confidence_interval_width / stats.pulls if stats.pulls else 0.0
                metrics.ADVANCED_BANDIT_CONFIDENCE_INTERVAL.labels(**labels).set(avg_ci)

        except Exception as e:
            logger.debug("Failed to update advanced bandit metrics: %s", e)

    def get_advanced_experiment_summary(self, domain: str) -> dict[str, Any]:
        """Get comprehensive summary of advanced bandit experiment."""
        experiment_id = f"advanced_bandits::{domain}"

        if experiment_id not in self._experiments:
            return {"error": f"No advanced experiment found for domain: {domain}"}

        exp = self._experiments[experiment_id]
        summary = exp.snapshot()

        # Add advanced analysis
        summary["advanced_analysis"] = self._analyze_advanced_performance(exp)

        return summary

    def _analyze_advanced_performance(self, exp: Experiment) -> dict[str, Any]:
        """Analyze advanced bandit performance vs baseline."""
        if exp.control not in exp.stats:
            return {"error": "No baseline data available"}

        baseline_stats = exp.stats[exp.control]
        baseline_reward = baseline_stats.reward_mean

        analysis = {
            "baseline_policy": exp.control,
            "baseline_reward_mean": baseline_reward,
            "variant_comparisons": {},
            "recommendations": [],
        }

        for variant, stats in exp.stats.items():
            if variant == exp.control:
                continue

            if stats.pulls < 10:  # Insufficient data
                analysis["variant_comparisons"][variant] = {
                    "status": "insufficient_data",
                    "pulls": stats.pulls,
                }
                continue

            reward_improvement = (stats.reward_mean - baseline_reward) / baseline_reward if baseline_reward else 0.0

            comparison = {
                "reward_mean": stats.reward_mean,
                "reward_improvement_pct": reward_improvement * 100,
                "pulls": stats.pulls,
                "regret_sum": stats.regret_sum,
            }

            # Add advanced metrics if available
            if isinstance(stats, AdvancedBanditStats):
                comparison.update(
                    {
                        "reward_model_mse": stats.reward_model_mse,
                        "tree_depth_avg": stats.tree_depth_sum / stats.pulls if stats.pulls else 0.0,
                        "importance_weight_avg": stats.importance_weight_sum / stats.pulls if stats.pulls else 0.0,
                        "confidence_interval_avg": stats.confidence_interval_width / stats.pulls
                        if stats.pulls
                        else 0.0,
                    }
                )

            analysis["variant_comparisons"][variant] = comparison

            # Generate recommendations
            if reward_improvement > 0.05:  # 5% improvement threshold
                analysis["recommendations"].append(
                    f"Consider activating {variant}: {reward_improvement * 100:.1f}% improvement"
                )
            elif reward_improvement < -0.10:  # 10% degradation threshold
                analysis["recommendations"].append(
                    f"Consider removing {variant}: {abs(reward_improvement) * 100:.1f}% degradation"
                )

        return analysis


def create_default_advanced_bandit_experiments(
    manager: AdvancedBanditExperimentManager,
) -> None:
    """Create default advanced bandit experiments for common domains."""

    # Only create experiments if advanced bandits are enabled
    if os.getenv("ENABLE_RL_ADVANCED", "").lower() not in {"1", "true", "yes", "on"}:
        logger.debug("Advanced bandit experiments disabled - ENABLE_RL_ADVANCED not set")
        return

    # Default domains for experiments
    domains = [
        "model_routing",
        "content_analysis",
        "transcription_service",
        "memory_retrieval",
    ]

    for domain in domains:
        try:
            manager.register_advanced_bandit_experiment(
                domain=domain,
                baseline_policy="epsilon_greedy",
                advanced_policies={
                    "doubly_robust": 0.25,
                    "offset_tree": 0.25,
                },
                shadow_samples=500,
                description=f"Evaluate advanced bandits for {domain} routing decisions",
            )
        except Exception as e:
            logger.warning("Failed to create advanced experiment for domain %s: %s", domain, e)


__all__ = [
    "AdvancedBanditExperimentManager",
    "AdvancedBanditStats",
    "create_default_advanced_bandit_experiments",
]
