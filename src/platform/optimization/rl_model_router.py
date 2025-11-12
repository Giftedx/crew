"""
Reinforcement Learning Model Router for Performance Optimization

This module provides RL-based model routing capabilities for the performance
optimization system, enabling intelligent model selection based on task
characteristics and performance history.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity enumeration for routing decisions."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class RoutingContext:
    """Context for model routing decisions."""

    task_type: str
    complexity: TaskComplexity
    token_estimate: int
    latency_requirement_ms: int | None = None
    cost_budget_usd: float | None = None
    quality_requirement: float = 0.8
    tenant: str = ""
    workspace: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelSelection:
    """Model selection result."""

    model_id: str
    provider: str
    confidence: float
    expected_reward: float
    reasoning: str
    fallback_models: list[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_latency_ms: float = 0.0


class RLModelRouter:
    """Reinforcement learning-based model router for performance optimization."""

    def __init__(self):
        """Initialize the RL model router."""
        self.model_capabilities = self._initialize_default_models()
        self.routing_history = []
        self.performance_metrics = {
            "total_routes": 0,
            "successful_routes": 0,
            "average_latency": 0.0,
            "average_cost": 0.0,
            "average_quality": 0.0,
        }

    def _initialize_default_models(self) -> dict[str, dict[str, Any]]:
        """Initialize default model capabilities."""
        return {
            "gpt-4": {
                "provider": "openai",
                "max_tokens": 8192,
                "cost_per_1k_tokens": 0.03,
                "average_latency_ms": 2000,
                "accuracy_score": 0.95,
                "reliability_score": 0.98,
                "capabilities": ["text_generation", "reasoning", "analysis"],
            },
            "gpt-3.5-turbo": {
                "provider": "openai",
                "max_tokens": 4096,
                "cost_per_1k_tokens": 0.002,
                "average_latency_ms": 1000,
                "accuracy_score": 0.85,
                "reliability_score": 0.95,
                "capabilities": ["text_generation", "summarization"],
            },
            "claude-3-opus": {
                "provider": "anthropic",
                "max_tokens": 200000,
                "cost_per_1k_tokens": 0.015,
                "average_latency_ms": 3000,
                "accuracy_score": 0.97,
                "reliability_score": 0.99,
                "capabilities": ["text_generation", "analysis", "reasoning"],
            },
            "claude-3-sonnet": {
                "provider": "anthropic",
                "max_tokens": 200000,
                "cost_per_1k_tokens": 0.003,
                "average_latency_ms": 1500,
                "accuracy_score": 0.92,
                "reliability_score": 0.97,
                "capabilities": ["text_generation", "analysis"],
            },
        }

    async def route_request(self, context: RoutingContext) -> StepResult:
        """
        Route request to optimal model based on context.

        Args:
            context: Routing context with task requirements

        Returns:
            StepResult with model selection
        """
        try:
            # Simple routing logic based on complexity and requirements
            selected_model = self._select_model(context)

            if not selected_model:
                return StepResult.fail("No suitable model found for routing context")

            model_data = self.model_capabilities[selected_model]

            selection = ModelSelection(
                model_id=selected_model,
                provider=model_data["provider"],
                confidence=0.85,  # Placeholder confidence
                expected_reward=self._calculate_expected_reward(model_data, context),
                reasoning=self._generate_routing_reason(model_data, context),
                fallback_models=self._get_fallback_models(selected_model, context),
                estimated_cost=self._estimate_cost(model_data, context.token_estimate),
                estimated_latency_ms=model_data["average_latency_ms"],
            )

            self.performance_metrics["total_routes"] += 1

            return StepResult.ok(
                data={
                    "model_selection": selection,
                    "context": context,
                    "routing_metadata": {
                        "available_models": len(self.model_capabilities),
                        "routing_timestamp": datetime.utcnow().isoformat(),
                    },
                }
            )
        except Exception as e:
            logger.error(f"Model routing failed: {e}")
            return StepResult.fail(f"Model routing failed: {e!s}")

    def _select_model(self, context: RoutingContext) -> str | None:
        """Select appropriate model based on routing context."""
        # Simple selection logic - can be enhanced with RL
        if context.complexity == TaskComplexity.CRITICAL:
            # Use highest accuracy model for critical tasks
            return "claude-3-opus"
        elif context.complexity == TaskComplexity.COMPLEX:
            # Use balanced model for complex tasks
            return "gpt-4"
        elif context.latency_requirement_ms and context.latency_requirement_ms < 2000:
            # Use faster model for low latency requirements
            return "gpt-3.5-turbo"
        elif context.cost_budget_usd and context.cost_budget_usd < 0.01:
            # Use cost-effective model for budget constraints
            return "gpt-3.5-turbo"
        else:
            # Default to balanced performance
            return "claude-3-sonnet"

    def _calculate_expected_reward(self, model_data: dict[str, Any], context: RoutingContext) -> float:
        """Calculate expected reward for a model given context."""
        reward = 0.0
        reward += model_data["accuracy_score"] * 0.4
        reward += model_data["reliability_score"] * 0.3

        if context.latency_requirement_ms:
            latency_penalty = max(0, (model_data["average_latency_ms"] - context.latency_requirement_ms) / 1000.0)
            reward -= latency_penalty * 0.2

        estimated_cost = self._estimate_cost(model_data, context.token_estimate)
        if context.cost_budget_usd and estimated_cost > context.cost_budget_usd:
            cost_penalty = (estimated_cost - context.cost_budget_usd) / context.cost_budget_usd
            reward -= cost_penalty * 0.3

        if model_data["accuracy_score"] >= context.quality_requirement:
            reward += 0.1

        return max(0.0, min(1.0, reward))

    def _generate_routing_reason(self, model_data: dict[str, Any], context: RoutingContext) -> str:
        """Generate human-readable routing reason."""
        reasons = []

        if context.complexity == TaskComplexity.CRITICAL and model_data["accuracy_score"] >= 0.95:
            reasons.append("high accuracy for critical task")
        elif context.complexity == TaskComplexity.SIMPLE and model_data["cost_per_1k_tokens"] <= 0.005:
            reasons.append("cost-effective for simple task")

        if context.latency_requirement_ms and model_data["average_latency_ms"] <= context.latency_requirement_ms:
            reasons.append("meets latency requirements")

        estimated_cost = self._estimate_cost(model_data, context.token_estimate)
        if context.cost_budget_usd and estimated_cost <= context.cost_budget_usd:
            reasons.append("within cost budget")

        if model_data["accuracy_score"] >= context.quality_requirement:
            reasons.append("meets quality requirements")

        return ", ".join(reasons) if reasons else "general suitability"

    def _get_fallback_models(self, primary_model_id: str, context: RoutingContext) -> list[str]:
        """Get fallback models for the primary selection."""
        all_models = list(self.model_capabilities.keys())
        fallbacks = [model for model in all_models if model != primary_model_id]
        # Return up to 2 fallback models
        return fallbacks[:2]

    def _estimate_cost(self, model_data: dict[str, Any], token_estimate: int) -> float:
        """Estimate cost for a model and token count."""
        return (token_estimate / 1000.0) * model_data["cost_per_1k_tokens"]

    async def update_reward(self, model_id: str, task_id: str, reward_data: dict[str, Any]) -> StepResult:
        """
        Update model performance with observed reward.

        Args:
            model_id: Model that was used
            task_id: Task identifier
            reward_data: Reward data

        Returns:
            StepResult with update status
        """
        try:
            reward_entry = {
                "model_id": model_id,
                "task_id": task_id,
                "reward": reward_data.get("reward", 0.0),
                "latency_ms": reward_data.get("latency_ms", 0.0),
                "cost_usd": reward_data.get("cost_usd", 0.0),
                "quality_score": reward_data.get("quality_score", 0.0),
                "success": reward_data.get("success", False),
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.routing_history.append(reward_entry)

            # Update performance metrics
            self._update_performance_metrics(reward_entry)

            # Update model capabilities based on performance
            self._update_model_capabilities(model_id, reward_entry)

            return StepResult.ok(
                data={
                    "model_id": model_id,
                    "task_id": task_id,
                    "reward": reward_entry["reward"],
                    "updated_metrics": self.performance_metrics,
                }
            )
        except Exception as e:
            logger.error(f"Reward update failed: {e}")
            return StepResult.fail(f"Reward update failed: {e!s}")

    def _update_performance_metrics(self, reward_entry: dict[str, Any]):
        """Update performance metrics with new reward."""
        self.performance_metrics["total_routes"] += 1
        if reward_entry["success"]:
            self.performance_metrics["successful_routes"] += 1

        alpha = 0.1  # Learning rate
        self.performance_metrics["average_latency"] = (1 - alpha) * self.performance_metrics[
            "average_latency"
        ] + alpha * reward_entry["latency_ms"]
        self.performance_metrics["average_cost"] = (1 - alpha) * self.performance_metrics[
            "average_cost"
        ] + alpha * reward_entry["cost_usd"]
        self.performance_metrics["average_quality"] = (1 - alpha) * self.performance_metrics[
            "average_quality"
        ] + alpha * reward_entry["quality_score"]

    def _update_model_capabilities(self, model_id: str, reward_entry: dict[str, Any]):
        """Update model capabilities based on observed performance."""
        if model_id not in self.model_capabilities:
            return

        model = self.model_capabilities[model_id]
        alpha = 0.1  # Learning rate

        # Update running averages
        model["average_latency_ms"] = (1 - alpha) * model["average_latency_ms"] + alpha * reward_entry["latency_ms"]
        model["accuracy_score"] = (1 - alpha) * model["accuracy_score"] + alpha * reward_entry["quality_score"]

        # Update reliability based on success
        reliability_update = 1.0 if reward_entry["success"] else 0.0
        model["reliability_score"] = (1 - alpha) * model["reliability_score"] + alpha * reliability_update

    def get_routing_statistics(self) -> StepResult:
        """
        Get routing statistics and performance metrics.

        Returns:
            StepResult with routing statistics
        """
        try:
            stats = {
                "performance_metrics": self.performance_metrics,
                "model_capabilities": self.model_capabilities,
                "routing_history_size": len(self.routing_history),
                "recent_performance": self._get_recent_performance(),
            }
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f"Failed to get routing statistics: {e}")
            return StepResult.fail(f"Failed to get routing statistics: {e!s}")

    def _get_recent_performance(self) -> dict[str, Any]:
        """Get recent performance metrics."""
        if not self.routing_history:
            return {}

        recent_entries = self.routing_history[-100:]  # Last 100 entries
        return {
            "recent_success_rate": sum(1 for r in recent_entries if r["success"]) / len(recent_entries),
            "recent_average_latency": sum(r["latency_ms"] for r in recent_entries) / len(recent_entries),
            "recent_average_cost": sum(r["cost_usd"] for r in recent_entries) / len(recent_entries),
            "recent_average_quality": sum(r["quality_score"] for r in recent_entries) / len(recent_entries),
            "recent_count": len(recent_entries),
        }

    def save_state(self, filepath: str) -> StepResult:
        """Save router state to file."""
        try:
            import json

            state = {
                "model_capabilities": self.model_capabilities,
                "routing_history": self.routing_history[-1000:],  # Keep last 1000 entries
                "performance_metrics": self.performance_metrics,
            }

            with open(filepath, "w") as f:
                json.dump(state, f, indent=2)

            return StepResult.ok(data={"saved_to": filepath})
        except Exception as e:
            logger.error(f"Failed to save router state: {e}")
            return StepResult.fail(f"Failed to save router state: {e!s}")

    def load_state(self, filepath: str) -> StepResult:
        """Load router state from file."""
        try:
            import json

            with open(filepath) as f:
                state = json.load(f)

            self.model_capabilities = state.get("model_capabilities", self._initialize_default_models())
            self.routing_history = state.get("routing_history", [])
            self.performance_metrics = state.get("performance_metrics", self.performance_metrics)

            return StepResult.ok(data={"loaded_from": filepath})
        except Exception as e:
            logger.error(f"Failed to load router state: {e}")
            return StepResult.fail(f"Failed to load router state: {e!s}")
