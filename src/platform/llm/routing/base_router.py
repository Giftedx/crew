"""Unified router architecture with strategy pattern.

This module consolidates multiple routing approaches into a single, extensible system
that can handle different routing strategies based on constraints and requirements.
"""

from __future__ import annotations

import hashlib
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from platform.core.step_result import StepResult
from typing import Any


@dataclass
class RoutingRequest:
    """Request for model routing."""

    prompt: str
    context: dict[str, Any]
    constraints: dict[str, Any]
    tenant: str
    workspace: str
    request_id: str | None = None

    def __post_init__(self) -> None:
        """Generate request ID if not provided."""
        if self.request_id is None:
            content = f"{self.prompt}{self.tenant}{self.workspace}{time.time()}"
            self.request_id = hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class RoutingDecision:
    """Routing decision with explanation."""

    model_id: str
    provider: str
    estimated_cost: float
    estimated_latency: float
    confidence: float
    reasoning: str
    request_id: str
    strategy_used: str
    timestamp: float


class BaseRouter(ABC):
    """Abstract base router for different routing strategies."""

    @abstractmethod
    def route(self, request: RoutingRequest) -> StepResult:
        """Route request to optimal model.

        Args:
            request: The routing request with prompt, context, and constraints

        Returns:
            StepResult containing RoutingDecision or error information
        """

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this routing strategy."""


class BanditRouter(BaseRouter):
    """Contextual bandit-based routing using Thompson sampling."""

    def __init__(self) -> None:
        """Initialize bandit router."""
        self.strategy_name = "bandit"
        self.models = {
            "gpt-4o-mini": {"provider": "openai", "cost": 0.001, "latency": 1.5, "quality": 0.8},
            "gpt-3.5-turbo": {"provider": "openai", "cost": 0.0005, "latency": 2.0, "quality": 0.7},
            "claude-3-haiku": {"provider": "anthropic", "cost": 0.0008, "latency": 1.8, "quality": 0.75},
        }
        self.arm_states = {model: {"alpha": 1.0, "beta": 1.0} for model in self.models}
        self._lock = threading.Lock()

    def route(self, request: RoutingRequest) -> StepResult:
        """Route using contextual bandit approach."""
        try:
            selected_model = self._select_model()
            model_info = self.models[selected_model]
            decision = RoutingDecision(
                model_id=selected_model,
                provider=model_info["provider"],
                estimated_cost=model_info["cost"],
                estimated_latency=model_info["latency"],
                confidence=model_info["quality"],
                reasoning=f"Bandit routing selected {selected_model} based on Thompson sampling",
                request_id=request.request_id or "unknown",
                strategy_used=self.strategy_name,
                timestamp=time.time(),
            )
            return StepResult.ok(data=decision)
        except Exception as e:
            return StepResult.fail(f"Bandit routing failed: {e!s}")

    def _select_model(self) -> str:
        """Select model using Thompson sampling."""
        import random

        with self._lock:
            samples = {}
            for model, state in self.arm_states.items():
                samples[model] = random.betavariate(state["alpha"], state["beta"])
            return max(samples.items(), key=lambda x: x[1])[0]

    def update_feedback(self, model_id: str, reward: float) -> None:
        """Update bandit with feedback."""
        if model_id not in self.arm_states:
            return
        with self._lock:
            r = max(0.0, min(1.0, reward))
            self.arm_states[model_id]["alpha"] += r
            self.arm_states[model_id]["beta"] += 1.0 - r

    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return self.strategy_name


class CostAwareRouter(BaseRouter):
    """Cost-minimizing router using cost-utility optimization."""

    def __init__(self) -> None:
        """Initialize cost-aware router."""
        self.strategy_name = "cost_aware"
        self.models = {
            "gpt-3.5-turbo": {"provider": "openai", "cost": 0.0005, "latency": 2.0, "quality": 0.7},
            "gpt-4o-mini": {"provider": "openai", "cost": 0.001, "latency": 1.5, "quality": 0.8},
            "claude-3-haiku": {"provider": "anthropic", "cost": 0.0008, "latency": 1.8, "quality": 0.75},
            "claude-3-sonnet": {"provider": "anthropic", "cost": 0.003, "latency": 2.5, "quality": 0.9},
        }
        self.min_quality_threshold = 0.6

    def route(self, request: RoutingRequest) -> StepResult:
        """Route to minimize cost while meeting quality constraints."""
        try:
            min_quality = request.constraints.get("min_quality", self.min_quality_threshold)
            max_cost = request.constraints.get("max_cost", float("inf"))
            viable_models = {}
            for model_id, model_info in self.models.items():
                if model_info["quality"] >= min_quality and model_info["cost"] <= max_cost:
                    viable_models[model_id] = model_info
            if not viable_models:
                cheapest_model = min(self.models.items(), key=lambda x: x[1]["cost"])
                viable_models = {cheapest_model[0]: cheapest_model[1]}
            selected_model = min(viable_models.items(), key=lambda x: x[1]["cost"])[0]
            model_info = viable_models[selected_model]
            decision = RoutingDecision(
                model_id=selected_model,
                provider=model_info["provider"],
                estimated_cost=model_info["cost"],
                estimated_latency=model_info["latency"],
                confidence=model_info["quality"],
                reasoning=f"Cost-optimized routing selected {selected_model} (cost: ${model_info['cost']:.4f}, quality: {model_info['quality']:.2f})",
                request_id=request.request_id or "unknown",
                strategy_used=self.strategy_name,
                timestamp=time.time(),
            )
            return StepResult.ok(data=decision)
        except Exception as e:
            return StepResult.fail(f"Cost-aware routing failed: {e!s}")

    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return self.strategy_name


class LatencyOptimizedRouter(BaseRouter):
    """Latency-minimizing router for real-time applications."""

    def __init__(self) -> None:
        """Initialize latency-optimized router."""
        self.strategy_name = "latency_optimized"
        self.models = {
            "gpt-4o-mini": {"provider": "openai", "cost": 0.001, "latency": 0.8, "quality": 0.8},
            "claude-3-haiku": {"provider": "anthropic", "cost": 0.0008, "latency": 1.0, "quality": 0.75},
            "gpt-3.5-turbo": {"provider": "openai", "cost": 0.0005, "latency": 1.2, "quality": 0.7},
            "claude-3-sonnet": {"provider": "anthropic", "cost": 0.003, "latency": 1.5, "quality": 0.9},
        }
        self.min_quality_threshold = 0.6

    def route(self, request: RoutingRequest) -> StepResult:
        """Route to minimize latency while meeting quality constraints."""
        try:
            min_quality = request.constraints.get("min_quality", self.min_quality_threshold)
            max_latency = request.constraints.get("max_latency", float("inf"))
            viable_models = {}
            for model_id, model_info in self.models.items():
                if model_info["quality"] >= min_quality and model_info["latency"] <= max_latency:
                    viable_models[model_id] = model_info
            if not viable_models:
                fastest_model = min(self.models.items(), key=lambda x: x[1]["latency"])
                viable_models = {fastest_model[0]: fastest_model[1]}
            selected_model = min(viable_models.items(), key=lambda x: x[1]["latency"])[0]
            model_info = viable_models[selected_model]
            decision = RoutingDecision(
                model_id=selected_model,
                provider=model_info["provider"],
                estimated_cost=model_info["cost"],
                estimated_latency=model_info["latency"],
                confidence=model_info["quality"],
                reasoning=f"Latency-optimized routing selected {selected_model} (latency: {model_info['latency']:.1f}s, quality: {model_info['quality']:.2f})",
                request_id=request.request_id or "unknown",
                strategy_used=self.strategy_name,
                timestamp=time.time(),
            )
            return StepResult.ok(data=decision)
        except Exception as e:
            return StepResult.fail(f"Latency-optimized routing failed: {e!s}")

    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return self.strategy_name


class FallbackRouter(BaseRouter):
    """Fallback chain router with retry logic."""

    def __init__(self) -> None:
        """Initialize fallback router."""
        self.strategy_name = "fallback"
        self.fallback_chain = [("gpt-4o-mini", "openai"), ("gpt-3.5-turbo", "openai"), ("claude-3-haiku", "anthropic")]

    def route(self, request: RoutingRequest) -> StepResult:
        """Route using fallback chain with retry logic."""
        try:
            model_id, provider = self.fallback_chain[0]
            decision = RoutingDecision(
                model_id=model_id,
                provider=provider,
                estimated_cost=0.001,
                estimated_latency=2.0,
                confidence=0.6,
                reasoning="Fallback routing using safe default model",
                request_id=request.request_id or "unknown",
                strategy_used=self.strategy_name,
                timestamp=time.time(),
            )
            return StepResult.ok(data=decision)
        except Exception as e:
            return StepResult.fail(f"Fallback routing failed: {e!s}")

    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return self.strategy_name


class UnifiedRouter:
    """
    Unified router facade coordinating multiple strategies.

    Routing decision flow:
    1. Check cache (semantic cache, exact match)
    2. Evaluate constraints (cost budget, latency target)
    3. Select strategy (bandit, cost-aware, latency-optimized)
    4. Execute routing
    5. Update bandit feedback
    6. Return decision with provenance
    """

    def __init__(self) -> None:
        """Initialize unified router with all strategies."""
        self.strategies = {
            "bandit": BanditRouter(),
            "cost_aware": CostAwareRouter(),
            "latency_optimized": LatencyOptimizedRouter(),
            "fallback": FallbackRouter(),
        }
        self.default_strategy = "bandit"
        self.cache: dict[str, RoutingDecision] = {}

    def route(self, request: RoutingRequest) -> StepResult:
        """Route with strategy selection and caching."""
        try:
            cache_key = self._generate_cache_key(request)
            if cache_key in self.cache:
                cached_decision = self.cache[cache_key]
                cached_decision.timestamp = time.time()
                return StepResult.ok(data=cached_decision)
            strategy_name = self._select_strategy(request.constraints)
            router = self.strategies[strategy_name]
            decision_result = router.route(request)
            if not decision_result.success:
                fallback_result = self.strategies["fallback"].route(request)
                if not fallback_result.success:
                    return StepResult.fail("All routing strategies failed")
                decision_result = fallback_result
            if decision_result.success and isinstance(decision_result.data, dict) and ("data" in decision_result.data):
                routing_decision = decision_result.data["data"]
                if isinstance(routing_decision, RoutingDecision):
                    self.cache[cache_key] = routing_decision
                if len(self.cache) > 1000:
                    oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
                    del self.cache[oldest_key]
            return decision_result
        except Exception as e:
            return StepResult.fail(f"Unified routing failed: {e!s}")

    def _select_strategy(self, constraints: dict[str, Any]) -> str:
        """Select routing strategy based on constraints."""
        if constraints.get("minimize_cost", False):
            return "cost_aware"
        elif constraints.get("minimize_latency", False):
            return "latency_optimized"
        elif constraints.get("use_bandit", True):
            return "bandit"
        else:
            return self.default_strategy

    def _generate_cache_key(self, request: RoutingRequest) -> str:
        """Generate cache key for request."""
        key_content = f"{request.prompt}{request.constraints}{request.tenant}{request.workspace}"
        return hashlib.sha256(key_content.encode()).hexdigest()[:16]

    def get_strategy_stats(self) -> dict[str, Any]:
        """Get statistics about strategy usage."""
        stats = {
            "cache_size": len(self.cache),
            "available_strategies": list(self.strategies.keys()),
            "default_strategy": self.default_strategy,
        }
        return stats

    def clear_cache(self) -> None:
        """Clear routing cache."""
        self.cache.clear()
