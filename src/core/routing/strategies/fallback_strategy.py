"""Fallback routing strategy implementation."""

from __future__ import annotations

import logging
from typing import Any

from ..base_router import RoutingContext, RoutingStrategy

logger = logging.getLogger(__name__)


class FallbackStrategy(RoutingStrategy):
    """Simple fallback strategy that provides basic routing functionality."""

    def __init__(self, default_selection: str = "first") -> None:
        """Initialize fallback strategy.

        Args:
            default_selection: How to select from candidates ("first", "last", "random")
        """
        self.default_selection = default_selection

    def select_model(self, context: RoutingContext) -> str:
        """Select model using simple fallback logic."""
        if not self.validate_candidates(context.candidates):
            raise ValueError("No candidates available")

        if self.default_selection == "first":
            model = context.candidates[0]
        elif self.default_selection == "last":
            model = context.candidates[-1]
        elif self.default_selection == "random":
            import random

            model = random.choice(context.candidates)
        else:
            model = context.candidates[0]

        logger.debug(f"Fallback strategy selected model: {model} (method: {self.default_selection})")
        return model

    def get_strategy_name(self) -> str:
        """Return strategy name."""
        return "fallback"

    def update_reward(self, model: str, reward: float, context: RoutingContext) -> None:
        """Update the strategy's internal state based on a reward."""
        # Fallback strategy doesn't learn from rewards
        logger.debug(f"Fallback strategy received reward for {model}, but does not update state")


class PerformanceStrategy(RoutingStrategy):
    """Performance-focused routing strategy that prioritizes speed."""

    def __init__(self, learning_engine: Any = None) -> None:
        """Initialize performance strategy."""
        self.learning_engine = learning_engine
        # Performance scores based on typical model characteristics
        self.performance_scores = {
            "gpt-4": 0.9,
            "gpt-4-turbo": 0.95,
            "gpt-4o": 0.98,
            "gpt-3.5-turbo": 0.95,
            "claude-3-opus": 0.85,
            "claude-3-sonnet": 0.9,
            "claude-3-haiku": 0.98,
            "claude-3-5-sonnet": 0.92,
            "gemini-pro": 0.88,
            "gemini-pro-vision": 0.85,
            "llama-2-70b": 0.75,
            "llama-3-70b": 0.8,
        }

    def select_model(self, context: RoutingContext) -> str:
        """Select model based on performance metrics."""
        if not self.validate_candidates(context.candidates):
            raise ValueError("No candidates available")

        # Score all candidates
        scored_models = []
        for model in context.candidates:
            # Use stored performance score or default
            score = self.performance_scores.get(model, 0.8)

            # Adjust score based on context if available
            if context.metadata:
                # Boost score for specific tasks that benefit from speed
                if context.metadata.get("task") in ["summarization", "translation", "simple_qa"]:
                    score *= 1.1
                # Reduce score for complex tasks that need quality
                elif context.metadata.get("task") in ["analysis", "reasoning", "creative"]:
                    score *= 0.95

            scored_models.append((model, score))

        # Select model with highest performance score
        best_model = max(scored_models, key=lambda x: x[1])[0]

        logger.debug(f"Performance strategy selected model: {best_model}")
        return best_model

    def get_strategy_name(self) -> str:
        """Return strategy name."""
        return "performance"

    def update_reward(self, model: str, reward: float, context: RoutingContext) -> None:
        """Update the strategy's internal state based on a reward."""
        if self.learning_engine:
            try:
                self.learning_engine.record("performance_routing", context.metadata or {}, model, reward)
                logger.debug(f"Performance strategy updated reward for model {model} with reward {reward}")
            except Exception as e:
                logger.error(f"Failed to update performance strategy reward for model {model}: {e}")
        else:
            logger.debug(f"Performance strategy received reward for {model}, but no learning engine available")

    def update_performance_score(self, model: str, latency_ms: float, success: bool) -> None:
        """Update performance score based on actual metrics."""
        if not success:
            return

        # Calculate performance score based on latency
        # Lower latency = higher score
        if latency_ms < 1000:
            score = 1.0
        elif latency_ms < 2000:
            score = 0.9
        elif latency_ms < 5000:
            score = 0.8
        else:
            score = 0.7

        # Update score with exponential moving average
        current_score = self.performance_scores.get(model, 0.8)
        alpha = 0.1  # Learning rate
        new_score = alpha * score + (1 - alpha) * current_score
        self.performance_scores[model] = new_score

        logger.debug(f"Updated performance score for {model}: {new_score:.3f} (latency: {latency_ms}ms)")


class BalancedStrategy(RoutingStrategy):
    """Balanced routing strategy that considers multiple factors."""

    def __init__(
        self,
        cost_weight: float = 0.4,
        performance_weight: float = 0.3,
        quality_weight: float = 0.3,
        learning_engine: Any = None,
    ) -> None:
        """Initialize balanced strategy.

        Args:
            cost_weight: Weight for cost factor (0-1)
            performance_weight: Weight for performance factor (0-1)
            quality_weight: Weight for quality factor (0-1)
            learning_engine: Optional learning engine
        """
        # Normalize weights to sum to 1
        total_weight = cost_weight + performance_weight + quality_weight
        self.cost_weight = cost_weight / total_weight
        self.performance_weight = performance_weight / total_weight
        self.quality_weight = quality_weight / total_weight
        self.learning_engine = learning_engine

        # Quality scores based on model capabilities
        self.quality_scores = {
            "gpt-4": 0.95,
            "gpt-4-turbo": 0.9,
            "gpt-4o": 0.92,
            "gpt-3.5-turbo": 0.85,
            "claude-3-opus": 0.98,
            "claude-3-sonnet": 0.95,
            "claude-3-haiku": 0.8,
            "claude-3-5-sonnet": 0.97,
            "gemini-pro": 0.88,
            "gemini-pro-vision": 0.85,
            "llama-2-70b": 0.75,
            "llama-3-70b": 0.8,
        }

    def select_model(self, context: RoutingContext) -> str:
        """Select model based on balanced scoring."""
        if not self.validate_candidates(context.candidates):
            raise ValueError("No candidates available")

        scores = {}
        for model in context.candidates:
            cost_score = self._calculate_cost_score(context, model)
            performance_score = self._calculate_performance_score(model)
            quality_score = self._calculate_quality_score(model)

            total_score = (
                self.cost_weight * cost_score
                + self.performance_weight * performance_score
                + self.quality_weight * quality_score
            )
            scores[model] = {
                "total": total_score,
                "cost": cost_score,
                "performance": performance_score,
                "quality": quality_score,
            }

        best_model = max(scores, key=lambda m: scores[m]["total"])

        logger.debug(
            f"Balanced strategy selected {best_model} "
            f"(total: {scores[best_model]['total']:.3f}, "
            f"cost: {scores[best_model]['cost']:.3f}, "
            f"perf: {scores[best_model]['performance']:.3f}, "
            f"quality: {scores[best_model]['quality']:.3f})"
        )
        return best_model

    def _calculate_cost_score(self, context: RoutingContext, model: str) -> float:
        """Calculate cost score (lower cost = higher score)."""
        from ... import token_meter

        tokens_in = token_meter.estimate_tokens(context.prompt)
        cost = token_meter.estimate(tokens_in, context.expected_output_tokens, model)
        # Normalize to 0-1 scale (assuming max cost of $10)
        return max(0, 1 - (cost / 10.0))

    def _calculate_performance_score(self, model: str) -> float:
        """Calculate performance score based on model characteristics."""
        # Use simple performance mapping
        performance_map = {
            "gpt-4": 0.9,
            "gpt-4-turbo": 0.95,
            "gpt-4o": 0.98,
            "gpt-3.5-turbo": 0.95,
            "claude-3-opus": 0.85,
            "claude-3-sonnet": 0.9,
            "claude-3-haiku": 0.98,
            "claude-3-5-sonnet": 0.92,
        }
        return performance_map.get(model, 0.8)

    def _calculate_quality_score(self, model: str) -> float:
        """Calculate quality score based on model capabilities."""
        return self.quality_scores.get(model, 0.8)

    def get_strategy_name(self) -> str:
        """Return strategy name."""
        return "balanced"

    def update_reward(self, model: str, reward: float, context: RoutingContext) -> None:
        """Update the strategy's internal state based on a reward."""
        if self.learning_engine:
            try:
                self.learning_engine.record("balanced_routing", context.metadata or {}, model, reward)
                logger.debug(f"Balanced strategy updated reward for model {model} with reward {reward}")
            except Exception as e:
                logger.error(f"Failed to update balanced strategy reward for model {model}: {e}")
        else:
            logger.debug(f"Balanced strategy received reward for {model}, but no learning engine available")

    def get_detailed_scores(self, context: RoutingContext) -> dict[str, dict[str, float]]:
        """Get detailed scoring breakdown for all candidates."""
        scores = {}
        for model in context.candidates:
            scores[model] = {
                "cost": self._calculate_cost_score(context, model),
                "performance": self._calculate_performance_score(model),
                "quality": self._calculate_quality_score(model),
            }
            scores[model]["total"] = (
                self.cost_weight * scores[model]["cost"]
                + self.performance_weight * scores[model]["performance"]
                + self.quality_weight * scores[model]["quality"]
            )
        return scores
