#!/usr/bin/env python3
"""
Model Routing Service.

This service implements intelligent model selection based on task requirements,
cost optimization, and performance characteristics using a mixture-of-experts approach.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..step_result import StepResult


@dataclass
class ModelCapability:
    """Model capability definition."""

    name: str
    provider: str
    cost_per_token: float
    latency_ms: float
    accuracy_score: float
    max_tokens: int
    capabilities: List[str]
    reliability_score: float


@dataclass
class RoutingDecision:
    """Model routing decision."""

    selected_model: str
    provider: str
    confidence: float
    reasoning: str
    expected_cost: float
    expected_latency: float
    fallback_model: Optional[str] = None


class ModelRouter:
    """Intelligent model routing service."""

    def __init__(self):
        """Initialize the model router."""
        self.models = self._initialize_models()
        self.routing_stats = {
            "total_requests": 0,
            "routing_decisions": {},
            "cost_savings": 0.0,
            "latency_improvements": 0.0,
        }
        self.routing_policies = {
            "cost_weight": 0.4,
            "latency_weight": 0.3,
            "accuracy_weight": 0.3,
            "reliability_threshold": 0.8,
            "fallback_enabled": True,
        }

    def _initialize_models(self) -> Dict[str, ModelCapability]:
        """Initialize available models with their capabilities."""
        return {
            "gpt-4o": ModelCapability(
                name="gpt-4o",
                provider="openai",
                cost_per_token=0.00003,
                latency_ms=1200,
                accuracy_score=0.95,
                max_tokens=128000,
                capabilities=[
                    "text_generation",
                    "analysis",
                    "reasoning",
                    "code_generation",
                    "multimodal",
                ],
                reliability_score=0.98,
            ),
            "gpt-4o-mini": ModelCapability(
                name="gpt-4o-mini",
                provider="openai",
                cost_per_token=0.000015,
                latency_ms=800,
                accuracy_score=0.88,
                max_tokens=128000,
                capabilities=[
                    "text_generation",
                    "analysis",
                    "reasoning",
                    "code_generation",
                ],
                reliability_score=0.95,
            ),
            "claude-3-5-sonnet": ModelCapability(
                name="claude-3-5-sonnet",
                provider="anthropic",
                cost_per_token=0.00003,
                latency_ms=1000,
                accuracy_score=0.93,
                max_tokens=200000,
                capabilities=[
                    "text_generation",
                    "analysis",
                    "reasoning",
                    "long_context",
                ],
                reliability_score=0.97,
            ),
            "claude-3-haiku": ModelCapability(
                name="claude-3-haiku",
                provider="anthropic",
                cost_per_token=0.00000025,
                latency_ms=400,
                accuracy_score=0.85,
                max_tokens=200000,
                capabilities=[
                    "text_generation",
                    "analysis",
                    "fast_processing",
                ],
                reliability_score=0.94,
            ),
            "llama-3.1-8b": ModelCapability(
                name="llama-3.1-8b",
                provider="meta",
                cost_per_token=0.0000002,
                latency_ms=600,
                accuracy_score=0.82,
                max_tokens=128000,
                capabilities=[
                    "text_generation",
                    "analysis",
                    "cost_effective",
                ],
                reliability_score=0.92,
            ),
            "gemini-pro": ModelCapability(
                name="gemini-pro",
                provider="google",
                cost_per_token=0.0000005,
                latency_ms=700,
                accuracy_score=0.87,
                max_tokens=30720,
                capabilities=[
                    "text_generation",
                    "analysis",
                    "multimodal",
                ],
                reliability_score=0.93,
            ),
        }

    def route_model(
        self,
        task_type: str,
        task_complexity: str,
        token_count: int,
        latency_requirement: Optional[float] = None,
        cost_budget: Optional[float] = None,
        accuracy_requirement: Optional[float] = None,
    ) -> StepResult:
        """
        Route to the optimal model for a given task.

        Args:
            task_type: Type of task (e.g., 'content_analysis', 'fact_checking')
            task_complexity: Complexity level ('simple', 'moderate', 'complex')
            token_count: Estimated token count
            latency_requirement: Maximum acceptable latency in seconds
            cost_budget: Maximum acceptable cost
            accuracy_requirement: Minimum required accuracy

        Returns:
            StepResult with routing decision
        """
        try:
            # Filter models based on requirements
            eligible_models = self._filter_eligible_models(
                task_type=task_type,
                token_count=token_count,
                latency_requirement=latency_requirement,
                cost_budget=cost_budget,
                accuracy_requirement=accuracy_requirement,
            )

            if not eligible_models:
                return StepResult.fail("No eligible models found for requirements")

            # Score and rank models
            scored_models = self._score_models(
                eligible_models=eligible_models,
                task_type=task_type,
                task_complexity=task_complexity,
                token_count=token_count,
            )

            # Select best model
            best_model = scored_models[0]
            fallback_model = scored_models[1] if len(scored_models) > 1 else None

            # Create routing decision
            decision = RoutingDecision(
                selected_model=best_model["model"].name,
                provider=best_model["model"].provider,
                confidence=best_model["confidence"],
                reasoning=best_model["reasoning"],
                expected_cost=best_model["expected_cost"],
                expected_latency=best_model["expected_latency"],
                fallback_model=fallback_model["model"].name if fallback_model else None,
            )

            # Record routing decision
            self._record_routing_decision(decision, task_type)

            return StepResult.ok(data=decision)

        except Exception as e:
            return StepResult.fail(f"Model routing failed: {str(e)}")

    def _filter_eligible_models(
        self,
        task_type: str,
        token_count: int,
        latency_requirement: Optional[float],
        cost_budget: Optional[float],
        accuracy_requirement: Optional[float],
    ) -> List[ModelCapability]:
        """
        Filter models based on requirements.

        Args:
            task_type: Type of task
            token_count: Token count
            latency_requirement: Latency requirement
            cost_budget: Cost budget
            accuracy_requirement: Accuracy requirement

        Returns:
            List of eligible models
        """
        eligible = []

        for model in self.models.values():
            # Check capability - use more flexible matching
            if not self._model_supports_task(model, task_type):
                continue

            # Check token limit
            if token_count > model.max_tokens:
                continue

            # Check latency requirement
            if latency_requirement and model.latency_ms > latency_requirement * 1000:
                continue

            # Check cost budget
            if cost_budget and (model.cost_per_token * token_count) > cost_budget:
                continue

            # Check accuracy requirement
            if accuracy_requirement and model.accuracy_score < accuracy_requirement:
                continue

            # Check reliability
            if model.reliability_score < self.routing_policies["reliability_threshold"]:
                continue

            eligible.append(model)

        return eligible

    def _model_supports_task(self, model: ModelCapability, task_type: str) -> bool:
        """
        Check if model supports the given task type.

        Args:
            model: Model capability
            task_type: Task type

        Returns:
            True if model supports the task
        """
        # Direct capability match
        if task_type in model.capabilities:
            return True

        # Flexible matching for common task types
        task_mappings = {
            "content_analysis": ["text_generation", "analysis", "reasoning"],
            "fact_checking": ["analysis", "reasoning"],
            "debate_scoring": ["analysis", "reasoning"],
            "sentiment_analysis": ["analysis", "text_generation"],
            "summarization": ["text_generation", "analysis"],
            "code_generation": ["code_generation", "text_generation"],
        }

        if task_type in task_mappings:
            required_capabilities = task_mappings[task_type]
            return any(cap in model.capabilities for cap in required_capabilities)

        # Default to allowing if no specific requirements
        return True

    def _score_models(
        self,
        eligible_models: List[ModelCapability],
        task_type: str,
        task_complexity: str,
        token_count: int,
    ) -> List[Dict[str, Any]]:
        """
        Score and rank eligible models.

        Args:
            eligible_models: List of eligible models
            task_type: Type of task
            task_complexity: Task complexity
            token_count: Token count

        Returns:
            List of scored models sorted by score
        """
        scored_models = []

        for model in eligible_models:
            # Calculate cost score (lower is better)
            expected_cost = model.cost_per_token * token_count
            cost_score = 1.0 / (1.0 + expected_cost * 1000)  # Normalize

            # Calculate latency score (lower is better)
            latency_score = 1.0 / (1.0 + model.latency_ms / 1000)  # Normalize

            # Calculate accuracy score (higher is better)
            accuracy_score = model.accuracy_score

            # Calculate reliability score (higher is better)
            reliability_score = model.reliability_score

            # Calculate complexity bonus
            complexity_bonus = self._calculate_complexity_bonus(model, task_complexity)

            # Calculate weighted score
            total_score = (
                cost_score * self.routing_policies["cost_weight"]
                + latency_score * self.routing_policies["latency_weight"]
                + accuracy_score * self.routing_policies["accuracy_weight"]
                + reliability_score * 0.1  # 10% weight for reliability
                + complexity_bonus * 0.1  # 10% weight for complexity match
            )

            # Generate reasoning
            reasoning = self._generate_reasoning(
                model, expected_cost, model.latency_ms, total_score
            )

            scored_models.append(
                {
                    "model": model,
                    "score": total_score,
                    "confidence": min(0.95, total_score),
                    "reasoning": reasoning,
                    "expected_cost": expected_cost,
                    "expected_latency": model.latency_ms / 1000,
                }
            )

        # Sort by score (descending)
        scored_models.sort(key=lambda x: x["score"], reverse=True)

        return scored_models

    def _calculate_complexity_bonus(
        self,
        model: ModelCapability,
        task_complexity: str,
    ) -> float:
        """
        Calculate complexity bonus for model-task matching.

        Args:
            model: Model capability
            task_complexity: Task complexity level

        Returns:
            Complexity bonus score
        """
        # High-end models for complex tasks
        if task_complexity == "complex":
            if model.name in ["gpt-4o", "claude-3-5-sonnet"]:
                return 0.2
            elif model.name in ["gpt-4o-mini", "claude-3-haiku"]:
                return 0.1
            else:
                return 0.0

        # Mid-range models for moderate tasks
        elif task_complexity == "moderate":
            if model.name in ["gpt-4o-mini", "claude-3-haiku", "gemini-pro"]:
                return 0.15
            elif model.name in ["gpt-4o", "claude-3-5-sonnet"]:
                return 0.1
            else:
                return 0.05

        # Cost-effective models for simple tasks
        else:  # simple
            if model.name in ["llama-3.1-8b", "claude-3-haiku"]:
                return 0.2
            elif model.name in ["gpt-4o-mini", "gemini-pro"]:
                return 0.15
            else:
                return 0.05

    def _generate_reasoning(
        self,
        model: ModelCapability,
        expected_cost: float,
        expected_latency: float,
        score: float,
    ) -> str:
        """
        Generate human-readable reasoning for model selection.

        Args:
            model: Selected model
            expected_cost: Expected cost
            expected_latency: Expected latency
            score: Model score

        Returns:
            Reasoning string
        """
        reasons = []

        if score > 0.8:
            reasons.append("excellent overall performance")
        elif score > 0.6:
            reasons.append("good performance")
        else:
            reasons.append("acceptable performance")

        if expected_cost < 0.001:
            reasons.append("very cost-effective")
        elif expected_cost < 0.01:
            reasons.append("cost-effective")

        if expected_latency < 1000:
            reasons.append("fast response time")
        elif expected_latency < 2000:
            reasons.append("reasonable response time")

        if model.accuracy_score > 0.9:
            reasons.append("high accuracy")
        elif model.accuracy_score > 0.8:
            reasons.append("good accuracy")

        return f"Selected {model.name} for {', '.join(reasons)}"

    def _record_routing_decision(
        self,
        decision: RoutingDecision,
        task_type: str,
    ) -> None:
        """
        Record routing decision for analytics.

        Args:
            decision: Routing decision
            task_type: Task type
        """
        self.routing_stats["total_requests"] += 1

        if task_type not in self.routing_stats["routing_decisions"]:
            self.routing_stats["routing_decisions"][task_type] = {}

        if (
            decision.selected_model
            not in self.routing_stats["routing_decisions"][task_type]
        ):
            self.routing_stats["routing_decisions"][task_type][
                decision.selected_model
            ] = 0

        self.routing_stats["routing_decisions"][task_type][decision.selected_model] += 1

    def get_routing_analytics(self) -> Dict[str, Any]:
        """
        Get model routing analytics.

        Returns:
            Routing analytics data
        """
        total_requests = self.routing_stats["total_requests"]

        # Calculate model usage distribution
        model_usage = {}
        for task_type, models in self.routing_stats["routing_decisions"].items():
            for model, count in models.items():
                if model not in model_usage:
                    model_usage[model] = 0
                model_usage[model] += count

        # Calculate cost and latency averages
        avg_cost = sum(
            model.cost_per_token * 1000  # Average for 1000 tokens
            for model in self.models.values()
        ) / len(self.models)

        avg_latency = sum(model.latency_ms for model in self.models.values()) / len(
            self.models
        )

        return {
            "total_requests": total_requests,
            "model_usage": model_usage,
            "average_cost_per_1k_tokens": avg_cost,
            "average_latency_ms": avg_latency,
            "cost_savings": self.routing_stats["cost_savings"],
            "latency_improvements": self.routing_stats["latency_improvements"],
        }

    def optimize_routing_policies(self) -> StepResult:
        """
        Optimize routing policies based on performance data.

        Returns:
            StepResult with optimization results
        """
        try:
            analytics = self.get_routing_analytics()

            # Adjust weights based on performance
            if analytics["cost_savings"] > 0.2:  # Good cost savings
                self.routing_policies["cost_weight"] = min(
                    0.5, self.routing_policies["cost_weight"] + 0.05
                )
            elif analytics["cost_savings"] < 0.1:  # Poor cost savings
                self.routing_policies["cost_weight"] = max(
                    0.3, self.routing_policies["cost_weight"] - 0.05
                )

            if analytics["latency_improvements"] > 0.3:  # Good latency improvements
                self.routing_policies["latency_weight"] = min(
                    0.4, self.routing_policies["latency_weight"] + 0.05
                )
            elif analytics["latency_improvements"] < 0.1:  # Poor latency improvements
                self.routing_policies["latency_weight"] = max(
                    0.2, self.routing_policies["latency_weight"] - 0.05
                )

            # Adjust reliability threshold
            if analytics["total_requests"] > 100:  # Enough data
                avg_reliability = sum(
                    model.reliability_score for model in self.models.values()
                ) / len(self.models)

                if avg_reliability > 0.95:
                    self.routing_policies["reliability_threshold"] = min(
                        0.9, self.routing_policies["reliability_threshold"] + 0.02
                    )
                elif avg_reliability < 0.9:
                    self.routing_policies["reliability_threshold"] = max(
                        0.7, self.routing_policies["reliability_threshold"] - 0.02
                    )

            return StepResult.ok(
                data={
                    "optimization_applied": True,
                    "new_policies": self.routing_policies,
                    "analytics": analytics,
                }
            )

        except Exception as e:
            return StepResult.fail(f"Routing optimization failed: {str(e)}")

    def get_optimization_recommendations(self) -> List[str]:
        """
        Get model routing optimization recommendations.

        Returns:
            List of optimization recommendations
        """
        recommendations = []
        analytics = self.get_routing_analytics()

        if analytics["cost_savings"] < 0.1:
            recommendations.append(
                "Consider adjusting cost weights for better cost optimization"
            )

        if analytics["latency_improvements"] < 0.2:
            recommendations.append(
                "Consider prioritizing faster models for latency-sensitive tasks"
            )

        # Check for model overuse
        if analytics["model_usage"]:
            most_used = max(analytics["model_usage"], key=analytics["model_usage"].get)
            usage_ratio = (
                analytics["model_usage"][most_used] / analytics["total_requests"]
            )

            if usage_ratio > 0.8:
                recommendations.append(
                    f"Consider diversifying model usage (currently {most_used} used {usage_ratio:.1%} of the time)"
                )

        if not recommendations:
            recommendations.append("Model routing performance is optimal")

        return recommendations
