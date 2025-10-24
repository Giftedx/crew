"""
Bandit Policy for RL-based model routing.

This module implements Thompson sampling for contextual bandit-based
model selection, optimizing for accuracy, latency, and cost.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any

import numpy as np

from ..step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class ModelContext:
    """Context for model selection decisions."""

    prompt_length: int
    expected_complexity: str  # 'simple', 'medium', 'complex'
    task_type: str  # 'analysis', 'generation', 'reasoning', 'coding'
    tenant: str
    workspace: str


@dataclass
class ModelMetrics:
    """Metrics for a specific model."""

    model_id: str
    provider: str
    accuracy_score: float = 0.0
    latency_ms: float = 0.0
    cost_per_token: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    total_requests: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.success_count / self.total_requests

    @property
    def composite_score(self) -> float:
        """Calculate composite score balancing accuracy, latency, and cost."""
        # Normalize metrics (higher is better)
        accuracy_norm = self.accuracy_score
        latency_norm = max(0, 1 - (self.latency_ms / 10000))  # Penalize high latency
        cost_norm = max(0, 1 - (self.cost_per_token * 1000))  # Penalize high cost

        # Weighted combination
        return 0.5 * accuracy_norm + 0.3 * latency_norm + 0.2 * cost_norm


class BanditPolicy:
    """Thompson sampling bandit policy for model selection."""

    def __init__(self, models: list[dict[str, Any]], exploration_rate: float = 0.1):
        """Initialize bandit policy.

        Args:
            models: List of model configurations
            exploration_rate: Rate of exploration vs exploitation
        """
        self.models = models
        self.exploration_rate = exploration_rate
        self.metrics: dict[str, ModelMetrics] = {}

        # Initialize metrics for each model
        for model in models:
            model_id = model["id"]
            self.metrics[model_id] = ModelMetrics(
                model_id=model_id,
                provider=model.get("provider", "unknown"),
                accuracy_score=model.get("initial_accuracy", 0.5),
                latency_ms=model.get("initial_latency", 1000.0),
                cost_per_token=model.get("cost_per_token", 0.001),
            )

        logger.info("Initialized BanditPolicy with %d models", len(models))

    def select_model(self, context: ModelContext) -> StepResult:
        """Select the best model using Thompson sampling.

        Args:
            context: Context for model selection

        Returns:
            StepResult with selected model information
        """
        try:
            if not self.models:
                return StepResult.fail("No models available for selection")

            # Calculate Thompson sampling probabilities
            model_scores = {}

            for model_id, metrics in self.metrics.items():
                # Thompson sampling: sample from Beta distribution
                alpha = metrics.success_count + 1
                beta = metrics.failure_count + 1

                # Sample from Beta distribution
                sampled_score = np.random.beta(alpha, beta)

                # Apply context-based adjustments
                context_factor = self._calculate_context_factor(context, model_id)
                final_score = sampled_score * context_factor

                model_scores[model_id] = final_score

            # Select model with highest score
            selected_model_id = max(model_scores, key=lambda k: model_scores[k])
            selected_model = next(m for m in self.models if m["id"] == selected_model_id)

            logger.debug(
                "Selected model %s (score: %.3f, context: %s)",
                selected_model_id,
                model_scores[selected_model_id],
                context.task_type,
            )

            return StepResult.ok(
                data={
                    "model_id": selected_model_id,
                    "model_config": selected_model,
                    "selection_score": model_scores[selected_model_id],
                    "exploration": random.random() < self.exploration_rate,
                }
            )

        except Exception as e:
            logger.error("Model selection failed: %s", str(e))
            return StepResult.fail(f"Model selection failed: {e!s}")

    def update_metrics(
        self,
        model_id: str,
        success: bool,
        accuracy_score: float | None = None,
        latency_ms: float | None = None,
        cost_tokens: int | None = None,
    ) -> StepResult:
        """Update metrics for a model based on outcome.

        Args:
            model_id: ID of the model
            success: Whether the request was successful
            accuracy_score: Accuracy score (0-1)
            latency_ms: Request latency in milliseconds
            cost_tokens: Number of tokens used

        Returns:
            StepResult indicating success/failure
        """
        try:
            if model_id not in self.metrics:
                return StepResult.fail(f"Unknown model ID: {model_id}")

            metrics = self.metrics[model_id]

            # Update counts
            metrics.total_requests += 1
            if success:
                metrics.success_count += 1
            else:
                metrics.failure_count += 1

            # Update performance metrics
            if accuracy_score is not None:
                # Exponential moving average
                alpha = 0.1
                metrics.accuracy_score = alpha * accuracy_score + (1 - alpha) * metrics.accuracy_score

            if latency_ms is not None:
                # Exponential moving average
                alpha = 0.1
                metrics.latency_ms = alpha * latency_ms + (1 - alpha) * metrics.latency_ms

            if cost_tokens is not None:
                # Update cost per token
                cost = cost_tokens * 0.001  # Assume $0.001 per token
                metrics.cost_per_token = alpha * cost + (1 - alpha) * metrics.cost_per_token

            logger.debug(
                "Updated metrics for model %s: success_rate=%.3f, accuracy=%.3f, latency=%.1fms",
                model_id,
                metrics.success_rate,
                metrics.accuracy_score,
                metrics.latency_ms,
            )

            return StepResult.ok(data={"updated": True})

        except Exception as e:
            logger.error("Failed to update metrics for model %s: %s", model_id, str(e))
            return StepResult.fail(f"Failed to update metrics: {e!s}")

    def _calculate_context_factor(self, context: ModelContext, model_id: str) -> float:
        """Calculate context-based adjustment factor for model selection.

        Args:
            context: Selection context
            model_id: Model identifier

        Returns:
            Adjustment factor (0-1)
        """
        factor = 1.0

        # Adjust based on prompt length
        if context.prompt_length > 4000:
            # Prefer models with larger context windows
            if "gpt-4" in model_id or "claude-3" in model_id:
                factor *= 1.2
        elif context.prompt_length < 500:
            # Prefer faster, cheaper models for short prompts
            if "gpt-3.5" in model_id or "claude-haiku" in model_id:
                factor *= 1.1

        # Adjust based on task complexity
        if context.expected_complexity == "complex":
            if "gpt-4" in model_id or "claude-3-opus" in model_id:
                factor *= 1.3
        elif context.expected_complexity == "simple":
            if "gpt-3.5" in model_id or "claude-haiku" in model_id:
                factor *= 1.2

        # Adjust based on task type
        if context.task_type == "reasoning":
            if "gpt-4" in model_id or "claude-3" in model_id:
                factor *= 1.2
        elif context.task_type == "coding":
            if "claude" in model_id:  # Claude is generally better at coding
                factor *= 1.1

        return min(factor, 2.0)  # Cap at 2x multiplier

    def get_model_stats(self) -> StepResult:
        """Get statistics for all models.

        Returns:
            StepResult with model statistics
        """
        try:
            stats_data = {}

            for model_id, metrics in self.metrics.items():
                stats_data[model_id] = {
                    "success_rate": metrics.success_rate,
                    "accuracy_score": metrics.accuracy_score,
                    "latency_ms": metrics.latency_ms,
                    "cost_per_token": metrics.cost_per_token,
                    "composite_score": metrics.composite_score,
                    "total_requests": metrics.total_requests,
                    "success_count": metrics.success_count,
                    "failure_count": metrics.failure_count,
                }

            return StepResult.ok(data=stats_data)

        except Exception as e:
            logger.error("Failed to get model stats: %s", str(e))
            return StepResult.fail(f"Failed to get model stats: {e!s}")

    def reset_metrics(self) -> StepResult:
        """Reset all model metrics.

        Returns:
            StepResult indicating success/failure
        """
        try:
            for metrics in self.metrics.values():
                metrics.success_count = 0
                metrics.failure_count = 0
                metrics.total_requests = 0
                # Keep initial performance values

            logger.info("Reset metrics for all models")
            return StepResult.ok(data={"reset": True})

        except Exception as e:
            logger.error("Failed to reset metrics: %s", str(e))
            return StepResult.fail(f"Failed to reset metrics: {e!s}")
