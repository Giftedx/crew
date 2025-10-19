"""Cost-aware routing strategy implementation."""

from __future__ import annotations

import logging
from typing import Any

from ... import token_meter
from ...learning_engine import LearningEngine
from ..base_router import RoutingContext, RoutingStrategy

logger = logging.getLogger(__name__)


class CostAwareStrategy(RoutingStrategy):
    """Cost-aware routing strategy that optimizes for budget constraints."""

    def __init__(
        self,
        max_cost_per_request: float = 5.0,
        cost_alert_threshold: float = 0.8,
        learning_engine: LearningEngine | None = None,
        prioritize_cheap: bool = True,
    ) -> None:
        """Initialize cost-aware strategy.

        Args:
            max_cost_per_request: Maximum cost allowed per request
            cost_alert_threshold: Threshold for cost alerts (0-1)
            learning_engine: Optional learning engine for cost optimization
            prioritize_cheap: Whether to prioritize cheaper models
        """
        self.max_cost_per_request = max_cost_per_request
        self.cost_alert_threshold = cost_alert_threshold
        self.learning_engine = learning_engine
        self.prioritize_cheap = prioritize_cheap

    def select_model(self, context: RoutingContext) -> str:
        """Select model based on cost constraints."""
        if not self.validate_candidates(context.candidates):
            raise ValueError("No candidates available")

        # Calculate costs for all candidates
        model_costs = {}
        for model in context.candidates:
            cost = self._estimate_cost(context, model)
            model_costs[model] = cost

        # Filter models that fit within budget
        affordable_models = [model for model, cost in model_costs.items() if cost <= self.max_cost_per_request]

        if not affordable_models:
            # If no model fits budget, use the cheapest one
            cheapest_model = min(model_costs.items(), key=lambda x: x[1])[0]
            logger.warning(
                f"No model fits budget (${self.max_cost_per_request}), "
                f"using cheapest: {cheapest_model} (${model_costs[cheapest_model]:.4f})"
            )
            return cheapest_model

        if self.prioritize_cheap:
            # Select the cheapest affordable model
            selected_model = min(affordable_models, key=lambda m: model_costs[m])
        else:
            # Use learning engine if available to select from affordable models
            if self.learning_engine:
                try:
                    selected_model = self.learning_engine.recommend(
                        "cost_routing", context.metadata or {}, affordable_models
                    )
                except Exception as e:
                    logger.warning(f"Learning engine failed, using cheapest: {e}")
                    selected_model = min(affordable_models, key=lambda m: model_costs[m])
            else:
                # Use first affordable model
                selected_model = affordable_models[0]

        cost = model_costs[selected_model]
        logger.debug(
            f"Cost-aware strategy selected {selected_model} (cost: ${cost:.4f}, budget: ${self.max_cost_per_request})"
        )

        # Check if we should issue a cost alert
        if cost >= self.max_cost_per_request * self.cost_alert_threshold:
            logger.warning(f"High cost request: ${cost:.4f} approaches budget limit ${self.max_cost_per_request}")

        return selected_model

    def _estimate_cost(self, context: RoutingContext, model: str) -> float:
        """Estimate cost for a model and context."""
        tokens_in = token_meter.estimate_tokens(context.prompt)
        return token_meter.estimate(tokens_in, context.expected_output_tokens, model)

    def get_strategy_name(self) -> str:
        """Return strategy name."""
        return "cost_aware"

    def update_cost_feedback(self, model: str, actual_cost: float, context: dict[str, Any]) -> None:
        """Update strategy with actual cost feedback for learning."""
        if not self.learning_engine:
            return

        try:
            # Calculate reward based on cost efficiency
            estimated_cost = self._estimate_cost_from_context(context, model)
            if estimated_cost > 0:
                # Reward inversely proportional to cost overrun
                reward = max(0, 1 - (actual_cost - estimated_cost) / estimated_cost)
                self.learning_engine.record("cost_routing", context, model, reward)
                logger.debug(f"Updated cost feedback for {model}: actual=${actual_cost:.4f}, reward={reward:.3f}")
        except Exception as e:
            logger.warning(f"Failed to update cost feedback: {e}")

    def _estimate_cost_from_context(self, context: dict[str, Any], model: str) -> float:
        """Estimate cost from context dictionary."""
        prompt = context.get("prompt", "")
        expected_tokens = context.get("expected_output_tokens", 1000)
        tokens_in = token_meter.estimate_tokens(prompt)
        return token_meter.estimate(tokens_in, expected_tokens, model)

    def update_reward(self, model: str, reward: float, context: RoutingContext) -> None:
        """Update the strategy's internal state based on a reward."""
        if self.learning_engine:
            try:
                self.learning_engine.record("cost_routing", context.metadata or {}, model, reward)
                logger.debug(f"Cost-aware strategy updated reward for model {model} with reward {reward}")
            except Exception as e:
                logger.error(f"Failed to update cost-aware strategy reward for model {model}: {e}")
        else:
            logger.debug(f"Cost-aware strategy received reward for {model}, but no learning engine available")

    def get_cost_analysis(self, context: RoutingContext) -> dict[str, Any]:
        """Get detailed cost analysis for all candidates."""
        analysis = {}
        for model in context.candidates:
            cost = self._estimate_cost(context, model)
            analysis[model] = {
                "cost": cost,
                "affordable": cost <= self.max_cost_per_request,
                "cost_ratio": cost / self.max_cost_per_request if self.max_cost_per_request > 0 else 0,
            }
        return analysis
