#!/usr/bin/env python3
"""
Adaptive AI Router with Real-time Performance Learning

Advanced routing system that adapts model selection based on real-time
performance metrics and continuous learning from routing decisions.
"""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveModelMetrics:
    """Real-time adaptive metrics for model performance."""

    model_name: str
    window_size: int = 50

    # Performance windows (recent history)
    latency_window: deque[float] = field(default_factory=lambda: deque(maxlen=50))
    cost_window: deque[float] = field(default_factory=lambda: deque(maxlen=50))
    quality_window: deque[float] = field(default_factory=lambda: deque(maxlen=50))
    success_window: deque[float] = field(default_factory=lambda: deque(maxlen=50))

    # Task-specific performance
    task_performance: dict[str, dict[str, deque[float]]] = field(default_factory=dict)

    # Adaptive weights (learned from feedback)
    adaptive_weights: dict[str, float] = field(default_factory=lambda: {"speed": 0.33, "cost": 0.33, "quality": 0.34})

    def add_performance_data(
        self, latency_ms: float, cost: float, quality_score: float, success: bool, task_type: str
    ) -> None:
        """Add new performance data point."""
        self.latency_window.append(latency_ms)
        self.cost_window.append(cost)
        self.quality_window.append(quality_score)
        self.success_window.append(1.0 if success else 0.0)

        # Update task-specific performance
        if task_type not in self.task_performance:
            self.task_performance[task_type] = {
                "latency": deque(maxlen=20),
                "cost": deque(maxlen=20),
                "quality": deque(maxlen=20),
                "success": deque(maxlen=20),
            }

        task_metrics = self.task_performance[task_type]
        task_metrics["latency"].append(latency_ms)
        task_metrics["cost"].append(cost)
        task_metrics["quality"].append(quality_score)
        task_metrics["success"].append(1.0 if success else 0.0)

    def get_adaptive_score(self, optimization_target: str, task_type: str | None = None) -> float:
        """Get adaptive performance score with learned weights."""
        if not self.latency_window:
            return 0.5  # Neutral score for unknown models

        # Get base metrics
        avg_latency = sum(self.latency_window) / len(self.latency_window)
        avg_cost = sum(self.cost_window) / len(self.cost_window)
        avg_quality = sum(self.quality_window) / len(self.quality_window)
        success_rate = sum(self.success_window) / len(self.success_window)

        # Task-specific adjustments
        task_multiplier = 1.0
        if task_type and task_type in self.task_performance:
            task_metrics = self.task_performance[task_type]
            if len(task_metrics["success"]) > 3:
                task_success_rate = sum(task_metrics["success"]) / len(task_metrics["success"])
                task_multiplier = (task_success_rate + 0.5) / 1.5  # Boost for task-specific success

        # Normalize scores (lower is better for cost/latency, higher for quality)
        latency_score = max(0, (3000 - avg_latency) / 3000)  # Normalize against 3s max
        cost_score = max(0, (0.02 - avg_cost) / 0.02)  # Normalize against $0.02 max
        quality_score = avg_quality  # Already normalized

        # Apply adaptive weights based on optimization target
        if optimization_target == "speed":
            score = latency_score * 0.7 + quality_score * 0.2 + cost_score * 0.1
        elif optimization_target == "cost":
            score = cost_score * 0.7 + quality_score * 0.2 + latency_score * 0.1
        elif optimization_target == "quality":
            score = quality_score * 0.7 + latency_score * 0.15 + cost_score * 0.15
        else:  # balanced
            score = (latency_score + cost_score + quality_score) / 3

        # Apply success rate and task-specific multiplier
        final_score = score * success_rate * task_multiplier

        return min(1.0, max(0.0, final_score))

    def update_adaptive_weights(self, feedback_score: float, optimization_target: str) -> None:
        """Update adaptive weights based on user feedback."""
        learning_rate = 0.1
        current_weight = self.adaptive_weights.get(optimization_target, 0.33)

        # Adjust weight based on feedback (simple gradient descent)
        if feedback_score > 0.7:  # Good performance
            self.adaptive_weights[optimization_target] = min(1.0, current_weight + learning_rate * 0.1)
        elif feedback_score < 0.3:  # Poor performance
            self.adaptive_weights[optimization_target] = max(0.1, current_weight - learning_rate * 0.1)

        # Normalize weights
        total_weight = sum(self.adaptive_weights.values())
        if total_weight > 0:
            for key in self.adaptive_weights:
                self.adaptive_weights[key] /= total_weight

    def get_confidence(self, task_type: str | None = None) -> float:
        """Get confidence score based on data available."""
        base_confidence = min(1.0, len(self.success_window) / self.window_size)

        # Task-specific confidence boost
        task_confidence = base_confidence
        if task_type and task_type in self.task_performance:
            task_data_points = len(self.task_performance[task_type]["success"])
            task_confidence = min(1.0, task_data_points / 10)  # Confidence based on task-specific data

        return (base_confidence + task_confidence) / 2


@dataclass
class AdaptiveRoutingDecision:
    """Enhanced routing decision with adaptive intelligence."""

    selected_model: str
    reasoning: str
    confidence: float
    expected_cost: float
    expected_latency_ms: float
    expected_quality: float
    adaptive_score: float
    task_specialization: float = 0.0
    fallback_models: list[str] = field(default_factory=list)


class AdaptiveAIRouter:
    """Advanced AI router with adaptive performance learning."""

    def __init__(self) -> None:
        self.model_metrics: dict[str, AdaptiveModelMetrics] = {}
        self.routing_history: deque[dict[str, Any]] = deque(maxlen=1000)
        self.global_feedback: defaultdict[str, float] = defaultdict(float)
        self.task_model_preferences: defaultdict[str, defaultdict[str, float]] = defaultdict(lambda: defaultdict(float))

    def select_optimal_model(
        self,
        task_type: str,
        available_models: list[str],
        optimization_target: str = "balanced",
        context_length: int = 1000,
        complexity_score: float = 0.5,
    ) -> AdaptiveRoutingDecision:
        """Select optimal model using adaptive intelligence."""

        model_scores: dict[str, float] = {}
        model_details: dict[str, dict[str, float]] = {}

        for model in available_models:
            # Initialize metrics if new model
            if model not in self.model_metrics:
                self.model_metrics[model] = AdaptiveModelMetrics(model)

            metrics = self.model_metrics[model]

            # Get adaptive score
            adaptive_score = metrics.get_adaptive_score(optimization_target, task_type)

            # Task specialization score
            specialization_score = self._get_task_specialization_score(model, task_type)

            # Context length penalty/bonus
            context_modifier = self._get_context_length_modifier(model, context_length)

            # Complexity adjustment
            complexity_modifier = self._get_complexity_modifier(model, complexity_score)

            # Global feedback influence
            feedback_modifier = self.global_feedback.get(model, 0.0) * 0.1

            # Final composite score
            final_score = (
                adaptive_score * 0.4
                + specialization_score * 0.25
                + context_modifier * 0.15
                + complexity_modifier * 0.15
                + feedback_modifier * 0.05
            )

            model_scores[model] = final_score
            model_details[model] = {
                "adaptive_score": adaptive_score,
                "specialization": specialization_score,
                "context_modifier": context_modifier,
                "complexity_modifier": complexity_modifier,
                "confidence": metrics.get_confidence(task_type),
            }

        # Select best model
        best_model = max(model_scores.keys(), key=lambda m: model_scores[m])
        best_score = model_scores[best_model]
        best_details = model_details[best_model]

        # Generate fallback models
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
        fallback_models = [model for model, score in sorted_models[1:3]]

        # Estimate performance
        expected_cost, expected_latency, expected_quality = self._estimate_performance(best_model, task_type)

        # Generate reasoning
        reasoning = self._generate_adaptive_reasoning(
            best_model, task_type, optimization_target, best_details, best_score
        )

        return AdaptiveRoutingDecision(
            selected_model=best_model,
            reasoning=reasoning,
            confidence=best_details["confidence"],
            expected_cost=expected_cost,
            expected_latency_ms=expected_latency,
            expected_quality=expected_quality,
            adaptive_score=best_details["adaptive_score"],
            task_specialization=best_details["specialization"],
            fallback_models=fallback_models,
        )

    def update_model_performance(
        self,
        model: str,
        latency_ms: float,
        cost: float,
        success: bool,
        quality_score: float,
        task_type: str,
        user_feedback: float | None = None,
    ) -> None:
        """Update model performance with adaptive learning."""

        if model not in self.model_metrics:
            self.model_metrics[model] = AdaptiveModelMetrics(model)

        # Update core metrics
        self.model_metrics[model].add_performance_data(latency_ms, cost, quality_score, success, task_type)

        # Update task preferences
        if success and quality_score > 0.6:
            self.task_model_preferences[task_type][model] += 0.1

        # Apply user feedback if provided
        if user_feedback is not None:
            self.global_feedback[model] = (self.global_feedback[model] * 0.9) + (user_feedback * 0.1)
            self.model_metrics[model].update_adaptive_weights(user_feedback, "quality")

        # Store routing decision for analysis
        self.routing_history.append(
            {
                "timestamp": asyncio.get_event_loop().time(),
                "model": model,
                "task_type": task_type,
                "latency_ms": latency_ms,
                "cost": cost,
                "success": success,
                "quality_score": quality_score,
                "user_feedback": user_feedback,
            }
        )

    def _get_task_specialization_score(self, model: str, task_type: str) -> float:
        """Get task specialization score for model."""
        # Base specialization scores
        specialization_map = {
            "analysis": {
                "anthropic/claude-3-5-sonnet-20241022": 0.95,
                "openai/gpt-4o": 0.90,
                "google/gemini-1.5-pro": 0.85,
                "openai/gpt-4o-mini": 0.70,
            },
            "creative": {
                "anthropic/claude-3-5-sonnet-20241022": 0.90,
                "openai/gpt-4o": 0.95,
                "google/gemini-1.5-pro": 0.85,
                "openai/gpt-4o-mini": 0.75,
            },
            "general": {
                "openai/gpt-4o-mini": 0.85,
                "google/gemini-1.5-flash": 0.80,
                "anthropic/claude-3-haiku-20240307": 0.75,
            },
        }

        base_score = specialization_map.get(task_type, {}).get(model, 0.5)

        # Adaptive adjustment based on learned preferences
        learned_preference = self.task_model_preferences[task_type].get(model, 0.0)
        adaptive_bonus = min(0.2, learned_preference)

        return min(1.0, base_score + adaptive_bonus)

    def _get_context_length_modifier(self, model: str, context_length: int) -> float:
        """Get context length modifier for model selection."""
        context_limits = {
            "openai/gpt-4o": 128000,
            "openai/gpt-4o-mini": 128000,
            "anthropic/claude-3-5-sonnet-20241022": 200000,
            "anthropic/claude-3-haiku-20240307": 200000,
            "google/gemini-1.5-pro": 1000000,
            "google/gemini-1.5-flash": 1000000,
        }

        limit = context_limits.get(model, 4000)

        if context_length > limit:
            return 0.0  # Cannot handle
        elif context_length > limit * 0.8:
            return 0.7  # Near limit
        elif context_length > limit * 0.5:
            return 0.9  # Comfortable
        else:
            return 1.0  # Well within limits

    def _get_complexity_modifier(self, model: str, complexity_score: float) -> float:
        """Get complexity modifier based on task complexity."""
        model_capabilities = {
            "openai/gpt-4o": 0.95,
            "anthropic/claude-3-5-sonnet-20241022": 0.93,
            "google/gemini-1.5-pro": 0.90,
            "openai/gpt-4o-mini": 0.75,
            "google/gemini-1.5-flash": 0.70,
            "anthropic/claude-3-haiku-20240307": 0.65,
        }

        capability = model_capabilities.get(model, 0.5)

        # Match complexity with capability
        if complexity_score <= capability:
            return 1.0  # Well matched
        else:
            return capability / complexity_score  # Penalize capability mismatch

    def _estimate_performance(self, model: str, task_type: str) -> tuple[float, float, float]:
        """Estimate performance metrics for model."""
        if model in self.model_metrics and self.model_metrics[model].latency_window:
            metrics = self.model_metrics[model]
            avg_cost = sum(metrics.cost_window) / len(metrics.cost_window)
            avg_latency = sum(metrics.latency_window) / len(metrics.latency_window)
            avg_quality = sum(metrics.quality_window) / len(metrics.quality_window)
            return avg_cost, avg_latency, avg_quality

        # Default estimates
        defaults = {
            "openai/gpt-4o": (0.005, 1500, 0.90),
            "openai/gpt-4o-mini": (0.002, 800, 0.75),
            "anthropic/claude-3-5-sonnet-20241022": (0.015, 2000, 0.95),
            "anthropic/claude-3-haiku-20240307": (0.003, 1000, 0.70),
            "google/gemini-1.5-pro": (0.008, 1800, 0.85),
            "google/gemini-1.5-flash": (0.001, 600, 0.65),
        }

        return defaults.get(model, (0.005, 1200, 0.75))

    def _generate_adaptive_reasoning(
        self, model: str, task_type: str, optimization_target: str, details: dict[str, float], score: float
    ) -> str:
        """Generate reasoning for adaptive model selection."""
        model_name = model.split("/")[-1]

        reasons = []

        # Primary selection reason
        if score > 0.8:
            reasons.append(f"Excellent match for {task_type} tasks")
        elif score > 0.6:
            reasons.append(f"Good fit for {task_type} optimization")
        else:
            reasons.append(f"Best available option for {task_type}")

        # Specialization reasoning
        if details["specialization"] > 0.8:
            reasons.append("specialized for this task type")

        # Optimization target reasoning
        if optimization_target == "speed" and "flash" in model or "mini" in model:
            reasons.append("optimized for fast response")
        elif optimization_target == "cost" and ("gemini" in model or "mini" in model):
            reasons.append("cost-effective choice")
        elif optimization_target == "quality" and ("sonnet" in model or "gpt-4o" in model):
            reasons.append("premium quality model")

        # Confidence indicator
        if details["confidence"] > 0.7:
            reasons.append("high confidence based on performance history")
        elif details["confidence"] < 0.3:
            reasons.append("exploratory selection (limited data)")

        return f"Selected {model_name}: {', '.join(reasons)} (adaptive score: {score:.2f})"

    def get_adaptive_analytics(self) -> dict[str, Any]:
        """Get comprehensive adaptive routing analytics."""
        if not self.routing_history:
            return {"status": "no_data"}

        recent_routes = list(self.routing_history)[-50:]  # Last 50 routes

        # Performance trends
        performance_trend = []
        for i in range(0, len(recent_routes), 10):
            batch = recent_routes[i : i + 10]
            avg_quality = sum(r["quality_score"] for r in batch) / len(batch)
            avg_latency = sum(r["latency_ms"] for r in batch) / len(batch)
            avg_cost = sum(r["cost"] for r in batch) / len(batch)
            performance_trend.append({"quality": avg_quality, "latency": avg_latency, "cost": avg_cost})

        # Model performance summary
        model_performance = {}
        for model, metrics in self.model_metrics.items():
            if metrics.latency_window:
                model_performance[model] = {
                    "avg_latency": sum(metrics.latency_window) / len(metrics.latency_window),
                    "avg_cost": sum(metrics.cost_window) / len(metrics.cost_window),
                    "avg_quality": sum(metrics.quality_window) / len(metrics.quality_window),
                    "success_rate": sum(metrics.success_window) / len(metrics.success_window),
                    "data_points": len(metrics.latency_window),
                }

        # Learning insights
        learning_insights = {
            "task_preferences": dict(self.task_model_preferences),
            "global_feedback": dict(self.global_feedback),
            "total_adaptations": len(self.routing_history),
        }

        return {
            "status": "active",
            "performance_trend": performance_trend,
            "model_performance": model_performance,
            "learning_insights": learning_insights,
            "adaptive_intelligence": "enabled",
        }


# Factory function
def create_adaptive_ai_router() -> AdaptiveAIRouter:
    """Create an adaptive AI router instance."""
    return AdaptiveAIRouter()


if __name__ == "__main__":

    async def demo_adaptive_ai_routing() -> None:
        """Demonstrate adaptive AI routing with learning."""
        print("🧠 ADAPTIVE AI ROUTER DEMO")
        print("=" * 50)

        router = create_adaptive_ai_router()

        # Simulate learning through multiple routing decisions
        scenarios = [
            ("Complex data analysis task", "analysis", "quality", 2000, 0.8),
            ("Quick content summary", "general", "speed", 500, 0.3),
            ("Creative writing project", "creative", "quality", 1500, 0.7),
            ("Cost-effective content analysis", "general", "cost", 800, 0.4),
            ("Technical documentation analysis", "analysis", "balanced", 3000, 0.9),
        ]

        available_models = [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "anthropic/claude-3-5-sonnet-20241022",
            "google/gemini-1.5-flash",
            "google/gemini-1.5-pro",
        ]

        print("🎯 Running adaptive routing scenarios...")

        for i, (task, task_type, target, context_len, complexity) in enumerate(scenarios, 1):
            print(f"\n🔍 Scenario {i}/5:")
            print(f"📝 Task: {task}")
            print(f"🎯 Type: {task_type} | Target: {target}")
            print(f"📏 Context: {context_len} tokens | Complexity: {complexity:.1f}")

            # Get routing decision
            decision = router.select_optimal_model(
                task_type=task_type,
                available_models=available_models,
                optimization_target=target,
                context_length=context_len,
                complexity_score=complexity,
            )

            print(f"✅ Selected: {decision.selected_model}")
            print(f"📊 Reasoning: {decision.reasoning}")
            print(f"🎯 Confidence: {decision.confidence:.2f}")
            print(f"🧠 Adaptive Score: {decision.adaptive_score:.2f}")
            print(f"⚡ Expected Latency: {decision.expected_latency_ms:.0f}ms")
            print(f"💰 Expected Cost: ${decision.expected_cost:.4f}")

            # Simulate execution and feedback
            simulated_latency = decision.expected_latency_ms + ((hash(task) % 400) - 200)  # ±200ms variation
            simulated_cost = decision.expected_cost * (0.8 + (hash(task) % 40) / 100)  # ±20% variation
            simulated_quality = min(1.0, decision.expected_quality + ((hash(task) % 20) - 10) / 100)  # ±10% variation
            simulated_success = simulated_quality > 0.5

            # Update performance (simulate learning)
            router.update_model_performance(
                model=decision.selected_model,
                latency_ms=simulated_latency,
                cost=simulated_cost,
                success=simulated_success,
                quality_score=simulated_quality,
                task_type=task_type,
                user_feedback=simulated_quality + (0.1 if simulated_success else -0.1),
            )

            print(f"📈 Actual: {simulated_latency:.0f}ms, ${simulated_cost:.4f}, Q:{simulated_quality:.2f}")

        # Show adaptive learning results
        print("\n🧠 ADAPTIVE LEARNING ANALYTICS:")
        print("=" * 40)

        analytics = router.get_adaptive_analytics()

        print("📊 Model Performance Summary:")
        for model, perf in analytics["model_performance"].items():
            model_name = model.split("/")[-1]
            print(
                f"  • {model_name}: Q:{perf['avg_quality']:.2f} "
                f"L:{perf['avg_latency']:.0f}ms C:${perf['avg_cost']:.3f} "
                f"({perf['data_points']} samples)"
            )

        print("\n🎯 Task-Model Preferences (Learned):")
        for task, models in analytics["learning_insights"]["task_preferences"].items():
            if models:
                best_model = max(models.items(), key=lambda x: x[1])
                print(f"  • {task}: {best_model[0].split('/')[-1]} (preference: {best_model[1]:.2f})")

        print("\n📈 Performance Trend (Recent):")
        if analytics["performance_trend"]:
            latest = analytics["performance_trend"][-1]
            print(
                f"  • Latest batch avg: Q:{latest['quality']:.2f} L:{latest['latency']:.0f}ms C:${latest['cost']:.3f}"
            )

        print("\n✨ Adaptive Intelligence: LEARNING COMPLETE! ✨")

    asyncio.run(demo_adaptive_ai_routing())
