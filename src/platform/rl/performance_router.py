"""
Intelligent LLM Router with Performance-Based Routing

Enhances the existing LiteLLM integration with performance-driven routing decisions,
leveraging our performance monitoring infrastructure for optimal model selection.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from platform.time import default_utc_now
from typing import Any

from ultimate_discord_intelligence_bot.agent_training.performance_monitor import AgentPerformanceMonitor


logger = logging.getLogger(__name__)


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a specific model."""

    model_name: str
    avg_latency_ms: float = 0.0
    avg_cost: float = 0.0
    success_rate: float = 1.0
    quality_score: float = 0.8
    total_requests: int = 0
    last_updated: datetime = field(default_factory=default_utc_now)


@dataclass
class RoutingDecision:
    """Represents a routing decision with performance rationale."""

    selected_model: str
    confidence: float
    reasoning: str
    alternatives: list[str]
    expected_latency_ms: float
    expected_cost: float
    quality_prediction: float


class PerformanceBasedRouter:
    """Intelligent router that makes decisions based on performance metrics."""

    def __init__(self, performance_monitor: AgentPerformanceMonitor | None = None):
        self.performance_monitor = performance_monitor or AgentPerformanceMonitor()
        self.model_metrics: dict[str, ModelPerformanceMetrics] = {}
        self.routing_history: list[RoutingDecision] = []
        self._initialize_baseline_metrics()

    def _initialize_baseline_metrics(self) -> None:
        """Initialize baseline performance metrics for known models."""
        baseline_models = {
            "openai/gpt-4o-mini": ModelPerformanceMetrics(
                model_name="openai/gpt-4o-mini",
                avg_latency_ms=800.0,
                avg_cost=0.0015,
                success_rate=0.98,
                quality_score=0.85,
                total_requests=100,
            ),
            "openai/gpt-4o": ModelPerformanceMetrics(
                model_name="openai/gpt-4o",
                avg_latency_ms=1500.0,
                avg_cost=0.005,
                success_rate=0.99,
                quality_score=0.95,
                total_requests=100,
            ),
            "anthropic/claude-3-5-sonnet-20241022": ModelPerformanceMetrics(
                model_name="anthropic/claude-3-5-sonnet-20241022",
                avg_latency_ms=1200.0,
                avg_cost=0.003,
                success_rate=0.97,
                quality_score=0.92,
                total_requests=100,
            ),
            "google/gemini-1.5-flash": ModelPerformanceMetrics(
                model_name="google/gemini-1.5-flash",
                avg_latency_ms=600.0,
                avg_cost=0.001,
                success_rate=0.95,
                quality_score=0.8,
                total_requests=100,
            ),
        }
        self.model_metrics.update(baseline_models)
        logger.info(f"Initialized baseline metrics for {len(baseline_models)} models")

    def update_model_performance(
        self, model: str, latency_ms: float, cost: float, success: bool, quality_score: float | None = None
    ) -> None:
        """Update performance metrics for a model based on actual usage."""
        if model not in self.model_metrics:
            self.model_metrics[model] = ModelPerformanceMetrics(model_name=model)
        metrics = self.model_metrics[model]
        alpha = 0.1
        metrics.avg_latency_ms = (1 - alpha) * metrics.avg_latency_ms + alpha * latency_ms
        metrics.avg_cost = (1 - alpha) * metrics.avg_cost + alpha * cost
        metrics.success_rate = (1 - alpha) * metrics.success_rate + alpha * (1.0 if success else 0.0)
        if quality_score is not None:
            metrics.quality_score = (1 - alpha) * metrics.quality_score + alpha * quality_score
        metrics.total_requests += 1
        metrics.last_updated = default_utc_now()
        logger.debug(f"Updated {model} metrics: latency={metrics.avg_latency_ms:.1f}ms, cost=${metrics.avg_cost:.4f}")

    def select_optimal_model(
        self, task_type: str, available_models: list[str], optimization_target: str = "balanced"
    ) -> RoutingDecision:
        """Select the optimal model based on performance metrics and optimization target."""
        if not available_models:
            raise ValueError("No available models provided")
        candidate_models = [m for m in available_models if m in self.model_metrics]
        if not candidate_models:
            return RoutingDecision(
                selected_model=available_models[0],
                confidence=0.5,
                reasoning="No performance data available, using fallback",
                alternatives=available_models[1:],
                expected_latency_ms=1000.0,
                expected_cost=0.003,
                quality_prediction=0.8,
            )
        model_scores = {}
        for model in candidate_models:
            metrics = self.model_metrics[model]
            score = self._calculate_model_score(metrics, optimization_target, task_type)
            model_scores[model] = score
        best_model = max(model_scores.keys(), key=lambda m: model_scores[m])
        best_metrics = self.model_metrics[best_model]
        scores = list(model_scores.values())
        scores.sort(reverse=True)
        confidence = 0.9 if len(scores) == 1 else min(0.95, 0.5 + (scores[0] - scores[1]) / 2)
        reasoning = self._build_reasoning(best_model, best_metrics, optimization_target, task_type)
        alternatives = sorted(
            [m for m in candidate_models if m != best_model], key=lambda m: model_scores[m], reverse=True
        )[:3]
        decision = RoutingDecision(
            selected_model=best_model,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            expected_latency_ms=best_metrics.avg_latency_ms,
            expected_cost=best_metrics.avg_cost,
            quality_prediction=best_metrics.quality_score,
        )
        self.routing_history.append(decision)
        logger.info(f"Selected {best_model} for {task_type} (confidence: {confidence:.2f})")
        return decision

    def _calculate_model_score(
        self, metrics: ModelPerformanceMetrics, optimization_target: str, task_type: str
    ) -> float:
        """Calculate a composite score for model selection."""
        speed_score = max(0, 2000 - metrics.avg_latency_ms) / 2000
        cost_score = max(0, 0.01 - metrics.avg_cost) / 0.01
        quality_score = metrics.quality_score
        reliability_score = metrics.success_rate
        task_multipliers = self._get_task_multipliers(task_type)
        if optimization_target == "speed":
            weights = {"speed": 0.5, "cost": 0.1, "quality": 0.2, "reliability": 0.2}
        elif optimization_target == "cost":
            weights = {"speed": 0.1, "cost": 0.5, "quality": 0.2, "reliability": 0.2}
        elif optimization_target == "quality":
            weights = {"speed": 0.1, "cost": 0.1, "quality": 0.6, "reliability": 0.2}
        else:
            weights = {"speed": 0.25, "cost": 0.25, "quality": 0.3, "reliability": 0.2}
        score = (
            speed_score * weights["speed"] * task_multipliers.get("speed", 1.0)
            + cost_score * weights["cost"] * task_multipliers.get("cost", 1.0)
            + quality_score * weights["quality"] * task_multipliers.get("quality", 1.0)
            + reliability_score * weights["reliability"] * task_multipliers.get("reliability", 1.0)
        )
        if metrics.total_requests > 10:
            recent_bonus = min(0.1, metrics.total_requests / 1000)
            score += recent_bonus
        return score

    def _get_task_multipliers(self, task_type: str) -> dict[str, float]:
        """Get task-specific multipliers for scoring."""
        multipliers = {
            "analysis": {"quality": 1.2, "speed": 0.8},
            "creative": {"quality": 1.3, "cost": 0.9},
            "general": {"speed": 1.0, "cost": 1.0, "quality": 1.0, "reliability": 1.0},
            "fast": {"speed": 1.5, "cost": 0.8},
            "summary": {"speed": 1.2, "cost": 1.1},
        }
        return multipliers.get(task_type, {})

    def _build_reasoning(
        self, model: str, metrics: ModelPerformanceMetrics, optimization_target: str, task_type: str
    ) -> str:
        """Build human-readable reasoning for the routing decision."""
        reasons = []
        if optimization_target == "speed":
            reasons.append(f"optimized for speed ({metrics.avg_latency_ms:.0f}ms avg latency)")
        elif optimization_target == "cost":
            reasons.append(f"optimized for cost (${metrics.avg_cost:.4f} avg cost)")
        elif optimization_target == "quality":
            reasons.append(f"optimized for quality ({metrics.quality_score:.2f} quality score)")
        else:
            reasons.append("balanced optimization")
        if task_type != "general":
            reasons.append(f"specialized for {task_type} tasks")
        if metrics.success_rate > 0.98:
            reasons.append("excellent reliability")
        elif metrics.success_rate > 0.95:
            reasons.append("good reliability")
        if metrics.total_requests > 100:
            reasons.append("proven performance")
        return f"Selected for {', '.join(reasons)}"

    def get_routing_stats(self) -> dict[str, Any]:
        """Get comprehensive routing statistics."""
        total_decisions = len(self.routing_history)
        if total_decisions == 0:
            return {"total_decisions": 0, "models": {}}
        model_usage = {}
        for decision in self.routing_history:
            model = decision.selected_model
            if model not in model_usage:
                model_usage[model] = {"count": 0, "avg_confidence": 0.0}
            model_usage[model]["count"] += 1
            model_usage[model]["avg_confidence"] += decision.confidence
        for model_data in model_usage.values():
            model_data["avg_confidence"] /= model_data["count"]
        recent_decisions = self.routing_history[-10:] if total_decisions >= 10 else self.routing_history
        avg_confidence = sum(d.confidence for d in recent_decisions) / len(recent_decisions)
        return {
            "total_decisions": total_decisions,
            "recent_avg_confidence": avg_confidence,
            "model_usage": model_usage,
            "available_models": len(self.model_metrics),
            "performance_data_points": sum(m.total_requests for m in self.model_metrics.values()),
        }


def create_performance_router(performance_monitor: AgentPerformanceMonitor | None = None) -> PerformanceBasedRouter:
    """Create a performance-based router instance."""
    return PerformanceBasedRouter(performance_monitor)


if __name__ == "__main__":

    async def demo_performance_routing() -> None:
        print("🧠 PERFORMANCE-BASED ROUTING DEMO")
        print("=" * 50)
        router = create_performance_router()
        scenarios = [
            ("analysis", ["openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022"], "quality"),
            ("general", ["openai/gpt-4o-mini", "google/gemini-1.5-flash"], "cost"),
            ("fast", ["google/gemini-1.5-flash", "openai/gpt-4o-mini"], "speed"),
        ]
        for task_type, models, target in scenarios:
            decision = router.select_optimal_model(task_type, models, target)
            print(f"\n📋 Task: {task_type} | Target: {target}")
            print(f"  🎯 Selected: {decision.selected_model}")
            print(f"  📊 Confidence: {decision.confidence:.2f}")
            print(f"  💡 Reasoning: {decision.reasoning}")
            print(f"  ⚡ Expected: {decision.expected_latency_ms:.0f}ms, ${decision.expected_cost:.4f}")
        stats = router.get_routing_stats()
        print("\n📈 ROUTING STATISTICS:")
        print(f"  • Total decisions: {stats['total_decisions']}"
        print(f"  • Average confidence: {stats['recent_avg_confidence']:.2f}"
        print(f"  • Available models: {stats['available_models']}"

    asyncio.run(demo_performance_routing())
