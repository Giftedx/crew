"""Advanced model routing service.

This module provides intelligent model routing capabilities for optimizing
LLM usage based on task requirements, performance metrics, and cost considerations.
"""

from __future__ import annotations
import logging
import time
from typing import TYPE_CHECKING, Any
from platform.core.step_result import StepResult

if TYPE_CHECKING:
    from ..tenancy.context import TenantContext
logger = logging.getLogger(__name__)


class ModelRouter:
    """Intelligent model routing service for LLM optimization."""

    def __init__(self, tenant_context: TenantContext):
        """Initialize model router with tenant context.

        Args:
            tenant_context: Tenant context for data isolation
        """
        self.tenant_context = tenant_context
        self.model_performance: dict[str, Any] = {}
        self.routing_rules: list[dict[str, Any]] = []
        self.cost_metrics: dict[str, Any] = {}
        self._initialize_routing_rules()

    def _initialize_routing_rules(self) -> None:
        """Initialize model routing rules."""
        self.routing_rules = [
            {
                "name": "task_complexity_routing",
                "description": "Route based on task complexity",
                "enabled": True,
                "rules": {
                    "simple": ["gpt-3.5-turbo", "claude-3-haiku"],
                    "medium": ["gpt-4", "claude-3-sonnet"],
                    "complex": ["gpt-4-turbo", "claude-3-opus"],
                },
            },
            {
                "name": "cost_optimization",
                "description": "Route based on cost optimization",
                "enabled": True,
                "max_cost_per_request": 0.1,
                "fallback_models": ["gpt-3.5-turbo", "claude-3-haiku"],
            },
            {
                "name": "performance_based_routing",
                "description": "Route based on performance metrics",
                "enabled": True,
                "min_success_rate": 0.95,
                "max_response_time": 30.0,
            },
            {
                "name": "load_balancing",
                "description": "Distribute load across available models",
                "enabled": True,
                "max_concurrent_requests": 10,
                "load_balancing_strategy": "round_robin",
            },
        ]

    def route_request(
        self, task_description: str, task_type: str = "general", requirements: dict[str, Any] | None = None
    ) -> StepResult:
        """Route request to optimal model.

        Args:
            task_description: Description of the task
            task_type: Type of task (analysis, generation, verification, etc.)
            requirements: Specific requirements (max_tokens, temperature, etc.)

        Returns:
            StepResult with routing decision
        """
        try:
            routing_decision: dict[str, Any] = {
                "selected_model": None,
                "routing_reason": "",
                "confidence": 0.0,
                "alternatives": [],
                "estimated_cost": 0.0,
                "estimated_latency": 0.0,
            }
            complexity = self._analyze_task_complexity(task_description, task_type)
            available_models = self._get_available_models()
            candidate_models = self._apply_routing_rules(available_models, complexity, task_type, requirements)
            selected_model = self._select_optimal_model(candidate_models, requirements)
            if selected_model:
                routing_decision["selected_model"] = selected_model["name"]
                routing_decision["routing_reason"] = selected_model["reason"]
                routing_decision["confidence"] = selected_model["confidence"]
                routing_decision["alternatives"] = [
                    model["name"] for model in candidate_models[:3] if model["name"] != selected_model["name"]
                ]
                routing_decision["estimated_cost"] = selected_model.get("estimated_cost", 0.0)
                routing_decision["estimated_latency"] = selected_model.get("estimated_latency", 0.0)
            else:
                routing_decision["routing_reason"] = "No suitable model found"
                routing_decision["confidence"] = 0.0
            return StepResult.ok(
                data={
                    "routing_decision": routing_decision,
                    "task_analysis": {"complexity": complexity, "type": task_type, "requirements": requirements or {}},
                    "tenant": self.tenant_context.tenant,
                    "workspace": self.tenant_context.workspace,
                }
            )
        except Exception as e:
            logger.error(f"Model routing failed: {e}")
            return StepResult.fail(f"Model routing failed: {e!s}")

    def _analyze_task_complexity(self, task_description: str, task_type: str) -> str:
        """Analyze task complexity.

        Args:
            task_description: Task description
            task_type: Task type

        Returns:
            Complexity level (simple, medium, complex)
        """
        complexity_indicators = {
            "simple": ["summarize", "extract", "classify", "simple"],
            "medium": ["analyze", "compare", "evaluate", "generate"],
            "complex": ["synthesize", "create", "design", "complex", "advanced"],
        }
        description_lower = task_description.lower()
        word_count = len(task_description.split())
        for complexity, indicators in complexity_indicators.items():
            if any((indicator in description_lower for indicator in indicators)):
                return complexity
        if word_count < 20 and task_type in ["extraction", "classification"]:
            return "simple"
        elif word_count > 100 or task_type in ["synthesis", "creation"]:
            return "complex"
        else:
            return "medium"

    def _get_available_models(self) -> list[dict[str, Any]]:
        """Get list of available models with their capabilities.

        Returns:
            List of available models
        """
        return [
            {
                "name": "gpt-3.5-turbo",
                "provider": "openai",
                "capabilities": ["text", "chat"],
                "max_tokens": 4096,
                "cost_per_1k_tokens": 0.002,
                "avg_latency": 2.0,
                "success_rate": 0.98,
            },
            {
                "name": "gpt-4",
                "provider": "openai",
                "capabilities": ["text", "chat", "analysis"],
                "max_tokens": 8192,
                "cost_per_1k_tokens": 0.03,
                "avg_latency": 5.0,
                "success_rate": 0.99,
            },
            {
                "name": "gpt-4-turbo",
                "provider": "openai",
                "capabilities": ["text", "chat", "analysis", "vision"],
                "max_tokens": 128000,
                "cost_per_1k_tokens": 0.01,
                "avg_latency": 3.0,
                "success_rate": 0.99,
            },
            {
                "name": "claude-3-haiku",
                "provider": "anthropic",
                "capabilities": ["text", "chat"],
                "max_tokens": 200000,
                "cost_per_1k_tokens": 0.00025,
                "avg_latency": 1.5,
                "success_rate": 0.97,
            },
            {
                "name": "claude-3-sonnet",
                "provider": "anthropic",
                "capabilities": ["text", "chat", "analysis"],
                "max_tokens": 200000,
                "cost_per_1k_tokens": 0.003,
                "avg_latency": 3.0,
                "success_rate": 0.98,
            },
            {
                "name": "claude-3-opus",
                "provider": "anthropic",
                "capabilities": ["text", "chat", "analysis", "reasoning"],
                "max_tokens": 200000,
                "cost_per_1k_tokens": 0.015,
                "avg_latency": 8.0,
                "success_rate": 0.99,
            },
        ]

    def _apply_routing_rules(
        self,
        available_models: list[dict[str, Any]],
        complexity: str,
        task_type: str,
        requirements: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Apply routing rules to filter candidate models.

        Args:
            available_models: Available models
            complexity: Task complexity
            task_type: Task type
            requirements: Task requirements

        Returns:
            Filtered candidate models
        """
        candidates = available_models.copy()
        complexity_rule = next((rule for rule in self.routing_rules if rule["name"] == "task_complexity_routing"), None)
        if complexity_rule and complexity_rule["enabled"]:
            complexity_models = complexity_rule["rules"].get(complexity, [])
            candidates = [model for model in candidates if model["name"] in complexity_models]
        cost_rule = next((rule for rule in self.routing_rules if rule["name"] == "cost_optimization"), None)
        if cost_rule and cost_rule["enabled"]:
            max_cost = cost_rule["max_cost_per_request"]
            estimated_tokens = requirements.get("max_tokens", 1000) if requirements else 1000
            candidates = [
                model for model in candidates if model["cost_per_1k_tokens"] * estimated_tokens / 1000 <= max_cost
            ]
        performance_rule = next(
            (rule for rule in self.routing_rules if rule["name"] == "performance_based_routing"), None
        )
        if performance_rule and performance_rule["enabled"]:
            min_success_rate = performance_rule["min_success_rate"]
            max_response_time = performance_rule["max_response_time"]
            candidates = [
                model
                for model in candidates
                if model["success_rate"] >= min_success_rate and model["avg_latency"] <= max_response_time
            ]
        return candidates

    def _select_optimal_model(
        self, candidate_models: list[dict[str, Any]], requirements: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Select optimal model from candidates.

        Args:
            candidate_models: Candidate models
            requirements: Task requirements

        Returns:
            Selected model with reasoning
        """
        if not candidate_models:
            return None
        scored_models: list[dict[str, Any]] = []
        for model in candidate_models:
            score = 0.0
            reasons: list[str] = []
            cost_score = 1.0 / (model["cost_per_1k_tokens"] + 0.001)
            score += cost_score * 0.3
            reasons.append(f"cost_efficient: {model['cost_per_1k_tokens']}")
            performance_score = model["success_rate"] / (model["avg_latency"] + 0.1)
            score += performance_score * 0.4
            reasons.append(f"performance: {model['success_rate']} success, {model['avg_latency']}s latency")
            capability_score = len(model["capabilities"]) / 5.0
            score += capability_score * 0.2
            reasons.append(f"capabilities: {len(model['capabilities'])} features")
            if requirements and "max_tokens" in requirements:
                required_tokens = requirements["max_tokens"]
                if model["max_tokens"] >= required_tokens:
                    token_score = min(1.0, model["max_tokens"] / required_tokens)
                    score += token_score * 0.1
                    reasons.append(f"token_capacity: {model['max_tokens']}")
            scored_models.append(
                {
                    "name": model["name"],
                    "score": score,
                    "reason": "; ".join(reasons),
                    "confidence": min(1.0, score / 2.0),
                    "estimated_cost": model["cost_per_1k_tokens"],
                    "estimated_latency": model["avg_latency"],
                }
            )
        scored_models.sort(key=lambda x: x["score"], reverse=True)
        return scored_models[0] if scored_models else None

    def update_model_performance(self, model_name: str, success: bool, latency: float, cost: float) -> StepResult:
        """Update model performance metrics.

        Args:
            model_name: Name of the model
            success: Whether the request was successful
            latency: Request latency in seconds
            cost: Request cost

        Returns:
            StepResult with update result
        """
        try:
            if model_name not in self.model_performance:
                self.model_performance[model_name] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "total_latency": 0.0,
                    "total_cost": 0.0,
                    "avg_latency": 0.0,
                    "success_rate": 0.0,
                    "avg_cost": 0.0,
                }
            perf = self.model_performance[model_name]
            perf["total_requests"] += 1
            perf["total_latency"] += latency
            perf["total_cost"] += cost
            if success:
                perf["successful_requests"] += 1
            perf["avg_latency"] = perf["total_latency"] / perf["total_requests"]
            perf["success_rate"] = perf["successful_requests"] / perf["total_requests"]
            perf["avg_cost"] = perf["total_cost"] / perf["total_requests"]
            return StepResult.ok(
                data={
                    "model_name": model_name,
                    "updated_performance": perf,
                    "tenant": self.tenant_context.tenant,
                    "workspace": self.tenant_context.workspace,
                }
            )
        except Exception as e:
            logger.error(f"Failed to update model performance: {e}")
            return StepResult.fail(f"Model performance update failed: {e!s}")

    def get_routing_statistics(self) -> StepResult:
        """Get routing statistics and metrics.

        Returns:
            StepResult with routing statistics
        """
        try:
            stats = {
                "routing_rules": self.routing_rules,
                "model_performance": self.model_performance,
                "cost_metrics": self.cost_metrics,
                "tenant": self.tenant_context.tenant,
                "workspace": self.tenant_context.workspace,
                "timestamp": time.time(),
            }
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f"Failed to get routing statistics: {e}")
            return StepResult.fail(f"Routing statistics retrieval failed: {e!s}")


class ModelRoutingManager:
    """Manager for model routing across tenants."""

    def __init__(self):
        """Initialize model routing manager."""
        self.routers: dict[str, ModelRouter] = {}

    def get_router(self, tenant_context: TenantContext) -> ModelRouter:
        """Get or create model router for tenant.

        Args:
            tenant_context: Tenant context

        Returns:
            Model router for the tenant
        """
        key = f"{tenant_context.tenant}:{tenant_context.workspace}"
        if key not in self.routers:
            self.routers[key] = ModelRouter(tenant_context)
        return self.routers[key]

    def route_request(
        self,
        tenant_context: TenantContext,
        task_description: str,
        task_type: str = "general",
        requirements: dict[str, Any] | None = None,
    ) -> StepResult:
        """Route request for tenant.

        Args:
            tenant_context: Tenant context
            task_description: Task description
            task_type: Task type
            requirements: Task requirements

        Returns:
            StepResult with routing decision
        """
        router = self.get_router(tenant_context)
        return router.route_request(task_description, task_type, requirements)


_model_routing_manager = ModelRoutingManager()


def get_model_router(tenant_context: TenantContext) -> ModelRouter:
    """Get model router for tenant.

    Args:
        tenant_context: Tenant context

    Returns:
        Model router for the tenant
    """
    return _model_routing_manager.get_router(tenant_context)


def route_model_request(
    tenant_context: TenantContext,
    task_description: str,
    task_type: str = "general",
    requirements: dict[str, Any] | None = None,
) -> StepResult:
    """Route model request for tenant.

    Args:
        tenant_context: Tenant context
        task_description: Task description
        task_type: Task type
        requirements: Task requirements

    Returns:
        StepResult with routing decision
    """
    return _model_routing_manager.route_request(tenant_context, task_description, task_type, requirements)
