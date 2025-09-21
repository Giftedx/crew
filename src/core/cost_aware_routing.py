"""Cost-Aware Routing Shadow Mode Implementation.

This module implements shadow mode cost-aware routing that evaluates model selection
decisions based on cost-utility optimization without affecting production routing.
It tracks potential cost savings and performance improvements that would result
from cost-aware model selection.
"""

from __future__ import annotations

import logging
import os
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from core.time import default_utc_now

logger = logging.getLogger(__name__)


@dataclass
class CostUtilityRecord:
    """Record of a cost-utility evaluation."""

    model: str
    estimated_cost: float
    estimated_utility: float
    actual_reward: float | None = None
    actual_cost: float | None = None
    latency_ms: float | None = None
    timestamp: datetime = field(default_factory=default_utc_now)


@dataclass
class ShadowRoutingResult:
    """Result of shadow cost-aware routing evaluation."""

    baseline_model: str
    cost_aware_model: str
    baseline_cost: float
    cost_aware_cost: float
    baseline_utility: float
    cost_aware_utility: float
    potential_cost_savings: float
    utility_improvement: float
    recommendation_confidence: float
    timestamp: datetime = field(default_factory=default_utc_now)


class CostAwareRoutingShadow:
    """Shadow mode cost-aware routing implementation."""

    def __init__(self, enable_flag: str = "ENABLE_COST_AWARE_ROUTING_SHADOW"):
        self.enable_flag = enable_flag
        self.routing_history: list[CostUtilityRecord] = []
        self.shadow_results: list[ShadowRoutingResult] = []
        self.max_history_size = 1000

        # Cost-utility optimization parameters
        self.cost_weight = 0.3  # Weight for cost in utility calculation
        self.quality_weight = 0.5  # Weight for quality/reward
        self.latency_weight = 0.2  # Weight for latency
        self.min_quality_threshold = 0.6  # Minimum acceptable quality

    def is_enabled(self) -> bool:
        """Check if cost-aware routing shadow mode is enabled."""
        return os.getenv(self.enable_flag, "").lower() in {"1", "true", "yes", "on"}

    def evaluate_routing_decision(
        self,
        task_type: str,
        available_models: list[str],
        baseline_model: str,
        model_costs: dict[str, float],
        model_quality_estimates: dict[str, float],
        model_latency_estimates: dict[str, float],
        prompt_tokens: int,
    ) -> ShadowRoutingResult | None:
        """Evaluate what cost-aware routing would have chosen in shadow mode.

        Args:
            task_type: Type of task being performed
            available_models: List of available model options
            baseline_model: Model actually chosen by current routing
            model_costs: Cost per token for each model
            model_quality_estimates: Expected quality/reward for each model
            model_latency_estimates: Expected latency for each model
            prompt_tokens: Number of input tokens

        Returns:
            Shadow routing result if enabled, None otherwise
        """
        if not self.is_enabled():
            return None

        try:
            # Calculate utility for each model
            model_utilities = {}
            model_total_costs = {}

            for model in available_models:
                if model not in model_costs or model not in model_quality_estimates:
                    continue

                total_cost = model_costs[model] * prompt_tokens
                quality = model_quality_estimates[model]
                latency = model_latency_estimates.get(model, 1000.0)  # Default 1s

                # Skip models below quality threshold
                if quality < self.min_quality_threshold:
                    continue

                # Calculate utility score (higher is better)
                utility = self._calculate_utility(quality, total_cost, latency)

                model_utilities[model] = utility
                model_total_costs[model] = total_cost

            if not model_utilities:
                return None

            # Find cost-aware optimal choice
            cost_aware_model = max(model_utilities.items(), key=lambda x: x[1])[0]

            # Calculate metrics
            baseline_cost = model_total_costs.get(baseline_model, 0.0)
            cost_aware_cost = model_total_costs[cost_aware_model]
            baseline_utility = model_utilities.get(baseline_model, 0.0)
            cost_aware_utility = model_utilities[cost_aware_model]

            potential_savings = baseline_cost - cost_aware_cost
            utility_improvement = cost_aware_utility - baseline_utility

            # Calculate confidence based on utility gap
            confidence = min(1.0, abs(utility_improvement) / max(baseline_utility, 0.001))

            result = ShadowRoutingResult(
                baseline_model=baseline_model,
                cost_aware_model=cost_aware_model,
                baseline_cost=baseline_cost,
                cost_aware_cost=cost_aware_cost,
                baseline_utility=baseline_utility,
                cost_aware_utility=cost_aware_utility,
                potential_cost_savings=potential_savings,
                utility_improvement=utility_improvement,
                recommendation_confidence=confidence,
            )

            self.shadow_results.append(result)
            if len(self.shadow_results) > self.max_history_size:
                self.shadow_results = self.shadow_results[-self.max_history_size :]

            # Log shadow evaluation
            logger.debug(
                "Cost-aware shadow routing: baseline=%s cost=%.4f utility=%.3f, "
                "cost_aware=%s cost=%.4f utility=%.3f, savings=%.4f",
                baseline_model,
                baseline_cost,
                baseline_utility,
                cost_aware_model,
                cost_aware_cost,
                cost_aware_utility,
                potential_savings,
            )

            return result

        except Exception as e:
            logger.debug(f"Cost-aware shadow routing evaluation failed: {e}")
            return None

    def _calculate_utility(self, quality: float, cost: float, latency_ms: float) -> float:
        """Calculate utility score for a model choice.

        Higher utility is better. Combines quality (reward), cost efficiency, and latency.
        """
        # Normalize cost (lower is better)
        cost_score = 1.0 / (1.0 + cost)  # Inverse relationship

        # Normalize latency (lower is better)
        latency_score = 1.0 / (1.0 + latency_ms / 1000.0)  # Convert to seconds

        # Weighted combination
        utility = self.quality_weight * quality + self.cost_weight * cost_score + self.latency_weight * latency_score

        return utility

    def record_actual_outcome(
        self,
        model: str,
        actual_cost: float,
        actual_reward: float,
        latency_ms: float,
    ) -> None:
        """Record actual outcome for utility learning."""
        if not self.is_enabled():
            return

        record = CostUtilityRecord(
            model=model,
            estimated_cost=actual_cost,  # For now, use actual as estimate
            estimated_utility=self._calculate_utility(actual_reward, actual_cost, latency_ms),
            actual_reward=actual_reward,
            actual_cost=actual_cost,
            latency_ms=latency_ms,
        )

        self.routing_history.append(record)
        if len(self.routing_history) > self.max_history_size:
            self.routing_history = self.routing_history[-self.max_history_size :]

    def get_shadow_performance_summary(self, lookback_hours: int = 24) -> dict[str, Any]:
        """Get performance summary of shadow cost-aware routing."""
        if not self.is_enabled():
            return {"enabled": False}
        cutoff_time = default_utc_now() - timedelta(hours=lookback_hours)
        recent_results = [r for r in self.shadow_results if r.timestamp >= cutoff_time]

        if not recent_results:
            return {"enabled": True, "total_evaluations": 0, "message": "No shadow evaluations in time window"}

        # Calculate metrics
        total_potential_savings = sum(r.potential_cost_savings for r in recent_results)
        total_baseline_cost = sum(r.baseline_cost for r in recent_results)
        cost_reduction_percentage = (
            (total_potential_savings / total_baseline_cost * 100) if total_baseline_cost > 0 else 0.0
        )

        utility_improvements = [r.utility_improvement for r in recent_results]
        avg_utility_improvement = statistics.mean(utility_improvements) if utility_improvements else 0.0

        model_switches = sum(1 for r in recent_results if r.baseline_model != r.cost_aware_model)
        switch_rate = model_switches / len(recent_results) if recent_results else 0.0

        # Confidence metrics
        confidences = [r.recommendation_confidence for r in recent_results]
        avg_confidence = statistics.mean(confidences) if confidences else 0.0

        return {
            "enabled": True,
            "lookback_hours": lookback_hours,
            "total_evaluations": len(recent_results),
            "potential_cost_reduction_pct": cost_reduction_percentage,
            "total_potential_savings": total_potential_savings,
            "avg_utility_improvement": avg_utility_improvement,
            "model_switch_rate": switch_rate,
            "avg_recommendation_confidence": avg_confidence,
            "recommendations": {
                "would_switch_models": switch_rate > 0.1,
                "significant_savings": cost_reduction_percentage > 5.0,
                "high_confidence": avg_confidence > 0.7,
            },
        }

    def get_model_performance_stats(self) -> dict[str, dict[str, float]]:
        """Get performance statistics by model."""
        if not self.routing_history:
            return {}

        model_stats = {}
        for record in self.routing_history:
            if record.model not in model_stats:
                model_stats[record.model] = {
                    "count": 0,
                    "avg_cost": 0.0,
                    "avg_reward": 0.0,
                    "avg_latency": 0.0,
                    "avg_utility": 0.0,
                }

            stats = model_stats[record.model]
            count = stats["count"]

            # Running average calculation (with null checks)
            actual_cost = record.actual_cost or 0.0
            actual_reward = record.actual_reward or 0.0
            latency_ms = record.latency_ms or 0.0

            stats["avg_cost"] = (stats["avg_cost"] * count + actual_cost) / (count + 1)
            stats["avg_reward"] = (stats["avg_reward"] * count + actual_reward) / (count + 1)
            stats["avg_latency"] = (stats["avg_latency"] * count + latency_ms) / (count + 1)
            stats["avg_utility"] = (stats["avg_utility"] * count + record.estimated_utility) / (count + 1)
            stats["count"] = count + 1

        return model_stats

    def update_optimization_parameters(
        self,
        cost_weight: float | None = None,
        quality_weight: float | None = None,
        latency_weight: float | None = None,
        min_quality_threshold: float | None = None,
    ) -> None:
        """Update optimization parameters for shadow mode."""
        if cost_weight is not None:
            self.cost_weight = max(0.0, min(1.0, cost_weight))
        if quality_weight is not None:
            self.quality_weight = max(0.0, min(1.0, quality_weight))
        if latency_weight is not None:
            self.latency_weight = max(0.0, min(1.0, latency_weight))
        if min_quality_threshold is not None:
            self.min_quality_threshold = max(0.0, min(1.0, min_quality_threshold))

        # Normalize weights to sum to 1.0
        total_weight = self.cost_weight + self.quality_weight + self.latency_weight
        if total_weight > 0:
            self.cost_weight /= total_weight
            self.quality_weight /= total_weight
            self.latency_weight /= total_weight


# Global instance for the shadow routing system
_shadow_routing_instance: CostAwareRoutingShadow | None = None


def get_cost_aware_shadow() -> CostAwareRoutingShadow:
    """Get the global cost-aware routing shadow instance."""
    global _shadow_routing_instance
    if _shadow_routing_instance is None:
        _shadow_routing_instance = CostAwareRoutingShadow()
    return _shadow_routing_instance


__all__ = [
    "CostAwareRoutingShadow",
    "CostUtilityRecord",
    "ShadowRoutingResult",
    "get_cost_aware_shadow",
]
