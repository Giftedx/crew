"""
Routing Service for intelligent model selection and routing.

This service manages model selection, routing decisions, and performance
tracking for the multi-agent orchestration system.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..step_result import StepResult
from ..tenancy.helpers import require_tenant
from .bandit_policy import BanditPolicy, ModelContext


if TYPE_CHECKING:
    from .openrouter_service import OpenRouterService

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Represents a routing decision with context."""

    model_id: str
    provider: str
    model_config: dict[str, Any]
    selection_score: float
    is_exploration: bool
    context: ModelContext
    timestamp: float


@dataclass
class RoutingOutcome:
    """Represents the outcome of a routing decision."""

    model_id: str
    success: bool
    accuracy_score: float | None = None
    latency_ms: float | None = None
    cost_tokens: int | None = None
    error_message: str | None = None
    timestamp: float = 0.0


class RoutingService:
    """Service for intelligent model routing and selection."""

    def __init__(
        self,
        openrouter_service: OpenRouterService,
        models: list[dict[str, Any]] | None = None,
        exploration_rate: float = 0.1,
    ):
        """Initialize routing service.

        Args:
            openrouter_service: OpenRouter service for model execution
            models: List of available models
            exploration_rate: Rate of exploration vs exploitation
        """
        self.openrouter_service = openrouter_service

        # Default models if none provided
        if models is None:
            models = self._get_default_models()

        self.bandit_policy = BanditPolicy(models, exploration_rate)
        self.routing_history: list[RoutingDecision] = []
        self.outcome_history: list[RoutingOutcome] = []

        logger.info("Initialized RoutingService with %d models", len(models))

    def _get_default_models(self) -> list[dict[str, Any]]:
        """Get default model configurations."""
        return [
            {
                "id": "gpt-4o",
                "provider": "openai",
                "model": "gpt-4o",
                "initial_accuracy": 0.9,
                "initial_latency": 2000.0,
                "cost_per_token": 0.005,
                "context_window": 128000,
                "capabilities": ["reasoning", "analysis", "coding"],
            },
            {
                "id": "gpt-4o-mini",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "initial_accuracy": 0.85,
                "initial_latency": 1000.0,
                "cost_per_token": 0.0015,
                "context_window": 128000,
                "capabilities": ["reasoning", "analysis"],
            },
            {
                "id": "claude-3-5-sonnet",
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "initial_accuracy": 0.92,
                "initial_latency": 1500.0,
                "cost_per_token": 0.003,
                "context_window": 200000,
                "capabilities": ["reasoning", "analysis", "coding"],
            },
            {
                "id": "claude-3-haiku",
                "provider": "anthropic",
                "model": "claude-3-haiku-20240307",
                "initial_accuracy": 0.8,
                "initial_latency": 800.0,
                "cost_per_token": 0.0005,
                "context_window": 200000,
                "capabilities": ["analysis", "generation"],
            },
        ]

    @require_tenant(strict_flag_enabled=False)
    async def route_request(
        self,
        prompt: str,
        task_type: str = "analysis",
        expected_complexity: str = "medium",
        tenant: str = "",
        workspace: str = "",
        **kwargs: Any,
    ) -> StepResult:
        """Route a request to the best available model.

        Args:
            prompt: The input prompt
            task_type: Type of task ('analysis', 'generation', 'reasoning', 'coding')
            expected_complexity: Expected complexity ('simple', 'medium', 'complex')
            tenant: Tenant identifier
            workspace: Workspace identifier
            **kwargs: Additional parameters for model execution

        Returns:
            StepResult with model response and routing information
        """
        try:
            start_time = time.time()

            # Create context for model selection
            context = ModelContext(
                prompt_length=len(prompt),
                expected_complexity=expected_complexity,
                task_type=task_type,
                tenant=tenant,
                workspace=workspace,
            )

            # Select model using bandit policy
            selection_result = self.bandit_policy.select_model(context)
            if not selection_result.success:
                return StepResult.fail(f"Model selection failed: {selection_result.error}")

            selection_data = selection_result.data
            model_id = selection_data["model_id"]
            model_config = selection_data["model_config"]

            # Create routing decision record
            decision = RoutingDecision(
                model_id=model_id,
                provider=model_config.get("provider", "unknown"),
                model_config=model_config,
                selection_score=selection_data["selection_score"],
                is_exploration=selection_data["exploration"],
                context=context,
                timestamp=start_time,
            )
            self.routing_history.append(decision)

            logger.debug(
                "Routing request to model %s (exploration: %s, score: %.3f)",
                model_id,
                decision.is_exploration,
                decision.selection_score,
            )

            # Execute request with selected model
            execution_start = time.time()

            # Execute via OpenRouter
            response_result = self.openrouter_service.route(
                prompt=prompt, task_type=task_type, model=model_config["model"], **kwargs
            )

            execution_time = (time.time() - execution_start) * 1000  # Convert to ms

            # Check if response is successful (route returns dict with content)
            if response_result and "content" in response_result:
                # Calculate success metrics
                response_data: dict[str, Any] = response_result
                accuracy_score = self._calculate_accuracy_score(prompt, response_data)
                cost_tokens = self._estimate_token_cost(prompt, response_data)

                # Create outcome record
                outcome = RoutingOutcome(
                    model_id=model_id,
                    success=True,
                    accuracy_score=accuracy_score,
                    latency_ms=execution_time,
                    cost_tokens=cost_tokens,
                    timestamp=time.time(),
                )
                self.outcome_history.append(outcome)

                # Update bandit policy metrics
                self.bandit_policy.update_metrics(
                    model_id=model_id,
                    success=True,
                    accuracy_score=accuracy_score,
                    latency_ms=execution_time,
                    cost_tokens=cost_tokens,
                )

                logger.debug(
                    "Request completed successfully: model=%s, latency=%.1fms, accuracy=%.3f",
                    model_id,
                    execution_time,
                    accuracy_score,
                )

                return StepResult.ok(
                    data={
                        "response": response_data,
                        "routing_info": {
                            "model_id": model_id,
                            "provider": model_config.get("provider"),
                            "selection_score": decision.selection_score,
                            "is_exploration": decision.is_exploration,
                            "latency_ms": execution_time,
                            "accuracy_score": accuracy_score,
                            "cost_tokens": cost_tokens,
                        },
                    }
                )
            else:
                # Handle failure
                error_msg = "Unknown error" if not response_result else str(response_result)
                outcome = RoutingOutcome(
                    model_id=model_id,
                    success=False,
                    error_message=error_msg,
                    timestamp=time.time(),
                )
                self.outcome_history.append(outcome)

                # Update bandit policy metrics
                self.bandit_policy.update_metrics(
                    model_id=model_id,
                    success=False,
                )

                logger.warning("Request failed with model %s: %s", model_id, error_msg)

                return StepResult.fail(f"Model execution failed: {error_msg}")

        except Exception as e:
            logger.error("Routing request failed: %s", str(e))
            return StepResult.fail(f"Routing request failed: {e!s}")

    def _calculate_accuracy_score(self, prompt: str, response: dict[str, Any]) -> float:
        """Calculate accuracy score for a response.

        Args:
            prompt: Original prompt
            response: Model response

        Returns:
            Accuracy score (0-1)
        """
        # Simple heuristic-based accuracy scoring
        # In production, this would use more sophisticated evaluation

        content = response.get("content", "")
        if not content:
            return 0.0

        # Check for basic quality indicators
        score = 0.5  # Base score

        # Length appropriateness
        prompt_length = len(prompt)
        response_length = len(content)
        if prompt_length > 1000 and response_length > 200:
            score += 0.2
        elif prompt_length < 500 and response_length < 1000:
            score += 0.1

        # Check for structured response
        if any(indicator in content.lower() for indicator in ["##", "1.", "2.", "3.", "- "]):
            score += 0.1

        # Check for completeness
        if len(content.split()) > 50:  # Substantial response
            score += 0.2

        return min(score, 1.0)

    def _estimate_token_cost(self, prompt: str, response: dict[str, Any]) -> int:
        """Estimate token cost for a request.

        Args:
            prompt: Original prompt
            response: Model response

        Returns:
            Estimated token count
        """
        # Simple token estimation (4 chars per token average)
        prompt_tokens = len(prompt) // 4
        response_tokens = len(response.get("content", "")) // 4
        return prompt_tokens + response_tokens

    async def get_routing_stats(self, tenant: str = "", workspace: str = "") -> StepResult:
        """Get routing statistics and performance metrics.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with routing statistics
        """
        try:
            # Get model statistics from bandit policy
            model_stats_result = self.bandit_policy.get_model_stats()
            if not model_stats_result.success:
                return StepResult.fail(f"Failed to get model stats: {model_stats_result.error}")

            # Calculate overall routing metrics
            total_requests = len(self.routing_history)
            successful_requests = len([o for o in self.outcome_history if o.success])
            success_rate = successful_requests / total_requests if total_requests > 0 else 0.0

            # Calculate average latency
            latencies = [o.latency_ms for o in self.outcome_history if o.latency_ms is not None]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

            # Calculate average accuracy
            accuracies = [o.accuracy_score for o in self.outcome_history if o.accuracy_score is not None]
            avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

            # Model usage distribution
            model_usage: dict[str, int] = {}
            for decision in self.routing_history:
                model_id = decision.model_id
                model_usage[model_id] = model_usage.get(model_id, 0) + 1

            return StepResult.ok(
                data={
                    "total_requests": total_requests,
                    "successful_requests": successful_requests,
                    "success_rate": success_rate,
                    "average_latency_ms": avg_latency,
                    "average_accuracy": avg_accuracy,
                    "model_usage": model_usage,
                    "model_stats": model_stats_result.data,
                    "routing_history_count": len(self.routing_history),
                    "outcome_history_count": len(self.outcome_history),
                }
            )

        except Exception as e:
            logger.error("Failed to get routing stats: %s", str(e))
            return StepResult.fail(f"Failed to get routing stats: {e!s}")

    async def reset_routing_data(self) -> StepResult:
        """Reset routing history and metrics.

        Returns:
            StepResult indicating success/failure
        """
        try:
            # Reset bandit policy metrics
            reset_result = self.bandit_policy.reset_metrics()
            if not reset_result.success:
                return StepResult.fail(f"Failed to reset bandit metrics: {reset_result.error}")

            # Clear routing history
            self.routing_history.clear()
            self.outcome_history.clear()

            logger.info("Reset routing data and metrics")
            return StepResult.ok(data={"reset": True})

        except Exception as e:
            logger.error("Failed to reset routing data: %s", str(e))
            return StepResult.fail(f"Failed to reset routing data: {e!s}")

    def get_available_models(self) -> StepResult:
        """Get list of available models.

        Returns:
            StepResult with available models
        """
        try:
            models = []
            for model_id, metrics in self.bandit_policy.metrics.items():
                model_config = next(m for m in self.bandit_policy.models if m["id"] == model_id)
                models.append(
                    {
                        "id": model_id,
                        "provider": metrics.provider,
                        "model": model_config["model"],
                        "success_rate": metrics.success_rate,
                        "accuracy_score": metrics.accuracy_score,
                        "latency_ms": metrics.latency_ms,
                        "cost_per_token": metrics.cost_per_token,
                        "composite_score": metrics.composite_score,
                        "total_requests": metrics.total_requests,
                    }
                )

            return StepResult.ok(data={"models": models})

        except Exception as e:
            logger.error("Failed to get available models: %s", str(e))
            return StepResult.fail(f"Failed to get available models: {e!s}")
