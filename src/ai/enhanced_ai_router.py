#!/usr/bin/env python3
"""
Enhanced AI Router Integration

Integrates the performance-based router with the existing Enhanced OpenRouter Service
to provide intelligent, performance-driven model selection and routing decisions.
"""

import asyncio
import logging
from typing import Any, cast

from core.learning_engine import LearningEngine
from ultimate_discord_intelligence_bot.agent_training.performance_monitor import AgentPerformanceMonitor

from ai.performance_router import create_performance_router

logger = logging.getLogger(__name__)


class EnhancedAIRouter:
    """Enhanced AI router with performance-based intelligence."""

    def __init__(
        self,
        enhanced_openrouter_service: Any = None,
        performance_monitor: AgentPerformanceMonitor | None = None,
        learning_engine: LearningEngine | None = None,
    ):
        self.openrouter_service = enhanced_openrouter_service
        self.performance_router = create_performance_router(performance_monitor)
        self.learning_engine = learning_engine or LearningEngine()
        self.route_history: list[dict[str, Any]] = []

    async def intelligent_route(
        self,
        prompt: str,
        task_type: str = "general",
        optimization_target: str = "balanced",  # "speed", "cost", "quality", "balanced"
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.8,
    ) -> dict[str, Any]:
        """Route request using performance-based intelligence."""

        start_time = asyncio.get_event_loop().time()

        try:
            # Get available models for the task
            available_models = self._get_task_models(task_type)

            # Use performance-based routing if no specific model requested
            if model is None:
                routing_decision = self.performance_router.select_optimal_model(
                    task_type=task_type, available_models=available_models, optimization_target=optimization_target
                )
                selected_model = routing_decision.selected_model
                decision_reasoning = routing_decision.reasoning
                expected_cost = routing_decision.expected_cost
                expected_latency = routing_decision.expected_latency_ms

                logger.info(
                    f"AI Router decision: {selected_model} for {task_type} "
                    f"(target: {optimization_target}, confidence: {routing_decision.confidence:.2f})"
                )
            else:
                selected_model = model
                decision_reasoning = f"User-specified model: {model}"
                expected_cost = 0.003  # Default estimate
                expected_latency = 1000.0  # Default estimate

            # Execute the request using the Enhanced OpenRouter Service
            if self.openrouter_service:
                result = await self.openrouter_service.route_async(
                    prompt=prompt,
                    task_type=task_type,
                    model=selected_model,
                    provider_opts=provider_opts,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                # Fallback simulation for demo
                result = {
                    "status": "success",
                    "model": selected_model,
                    "response": f"[Demo response from {selected_model} for {task_type} task]",
                    "tokens": 50,
                    "tokens_out": 30,
                    "cost": expected_cost,
                }

            # Calculate actual performance metrics
            end_time = asyncio.get_event_loop().time()
            actual_latency_ms = (end_time - start_time) * 1000
            actual_cost = result.get("cost", expected_cost)
            success = result.get("status") == "success"

            # Update performance metrics
            if success:
                # Simple quality assessment (could be enhanced with actual quality scoring)
                quality_score = self._assess_response_quality(result.get("response", ""), task_type)

                self.performance_router.update_model_performance(
                    model=selected_model,
                    latency_ms=actual_latency_ms,
                    cost=actual_cost,
                    success=success,
                    quality_score=quality_score,
                )

                # Update learning engine
                reward = self._calculate_reward(actual_cost, actual_latency_ms, quality_score, optimization_target)
                self.learning_engine.update(task_type, selected_model, reward=reward)

            # Enhance result with routing information
            enhanced_result = dict(result)
            enhanced_result.update(
                {
                    "routing_decision": decision_reasoning,
                    "optimization_target": optimization_target,
                    "expected_latency_ms": expected_latency,
                    "actual_latency_ms": actual_latency_ms,
                    "performance_delta": actual_latency_ms - expected_latency,
                    "intelligence_used": True,
                }
            )

            # Record routing history
            self.route_history.append(
                {
                    "timestamp": start_time,
                    "task_type": task_type,
                    "optimization_target": optimization_target,
                    "selected_model": selected_model,
                    "reasoning": decision_reasoning,
                    "success": success,
                    "actual_latency_ms": actual_latency_ms,
                    "actual_cost": actual_cost,
                }
            )

            return enhanced_result

        except Exception as e:
            logger.error(f"Enhanced AI routing failed: {e}")
            # Fallback to basic routing if available
            if self.openrouter_service:
                fallback_result = cast(
                    dict[str, Any],
                    await self.openrouter_service.route_async(
                        prompt=prompt, task_type=task_type, model=model, provider_opts=provider_opts
                    ),
                )
                return fallback_result
            else:
                return {"status": "error", "error": str(e), "model": model or "unknown"}

    def _get_task_models(self, task_type: str) -> list[str]:
        """Get available models for a specific task type."""
        model_map = {
            "general": [
                "openai/gpt-4o-mini",
                "anthropic/claude-3-haiku-20240307",
                "google/gemini-1.5-flash",
            ],
            "analysis": [
                "openai/gpt-4o",
                "anthropic/claude-3-5-sonnet-20241022",
                "google/gemini-1.5-pro",
            ],
            "creative": [
                "anthropic/claude-3-5-sonnet-20241022",
                "openai/gpt-4o",
                "google/gemini-1.5-pro",
            ],
            "fast": [
                "openai/gpt-4o-mini",
                "google/gemini-1.5-flash",
                "anthropic/claude-3-haiku-20240307",
            ],
        }

        return model_map.get(task_type, model_map["general"])

    def _assess_response_quality(self, response: str, task_type: str) -> float:
        """Simple response quality assessment (could be enhanced)."""
        if not response:
            return 0.0

        # Basic quality factors
        length_score = min(1.0, len(response) / 200)  # Prefer substantial responses
        coherence_score = 0.8  # Would use actual coherence analysis

        # Task-specific adjustments
        task_bonus = 0.0
        if task_type == "analysis" and any(word in response.lower() for word in ["analyze", "evidence", "conclusion"]):
            task_bonus = 0.1
        elif task_type == "creative" and len(response) > 100:
            task_bonus = 0.1

        return min(1.0, length_score * 0.3 + coherence_score * 0.6 + task_bonus)

    def _calculate_reward(
        self, cost: float, latency_ms: float, quality_score: float, optimization_target: str
    ) -> float:
        """Calculate reward for learning engine based on optimization target."""

        # Normalize metrics
        cost_score = max(0, (0.01 - cost) / 0.01)  # Lower cost = higher score
        speed_score = max(0, (2000 - latency_ms) / 2000)  # Lower latency = higher score
        quality_reward = quality_score  # Already normalized

        # Weight based on optimization target
        if optimization_target == "speed":
            reward = speed_score * 0.6 + quality_reward * 0.3 + cost_score * 0.1
        elif optimization_target == "cost":
            reward = cost_score * 0.6 + quality_reward * 0.3 + speed_score * 0.1
        elif optimization_target == "quality":
            reward = quality_reward * 0.6 + speed_score * 0.2 + cost_score * 0.2
        else:  # balanced
            reward = (speed_score + cost_score + quality_reward) / 3

        return reward

    def get_routing_analytics(self) -> dict[str, Any]:
        """Get comprehensive routing analytics."""
        if not self.route_history:
            return {"total_routes": 0}

        # Basic statistics
        total_routes = len(self.route_history)
        successful_routes = sum(1 for r in self.route_history if r["success"])
        success_rate = successful_routes / total_routes

        # Performance statistics
        avg_latency = sum(r["actual_latency_ms"] for r in self.route_history) / total_routes
        avg_cost = sum(r["actual_cost"] for r in self.route_history) / total_routes

        # Model usage distribution
        model_usage: dict[str, int] = {}
        for route in self.route_history:
            model = route["selected_model"]
            model_usage[model] = model_usage.get(model, 0) + 1

        # Optimization target analysis
        target_usage: dict[str, int] = {}
        for route in self.route_history:
            target = route["optimization_target"]
            target_usage[target] = target_usage.get(target, 0) + 1

        # Performance router statistics
        router_stats = self.performance_router.get_routing_stats()

        return {
            "total_routes": total_routes,
            "success_rate": success_rate,
            "avg_latency_ms": avg_latency,
            "avg_cost": avg_cost,
            "model_usage": model_usage,
            "optimization_targets": target_usage,
            "router_confidence": router_stats.get("recent_avg_confidence", 0),
            "learning_data_points": router_stats.get("performance_data_points", 0),
        }


# Factory function for easy integration
def create_enhanced_ai_router(
    enhanced_openrouter_service: Any = None,
    performance_monitor: AgentPerformanceMonitor | None = None,
    learning_engine: LearningEngine | None = None,
) -> EnhancedAIRouter:
    """Create an enhanced AI router instance."""
    return EnhancedAIRouter(enhanced_openrouter_service, performance_monitor, learning_engine)


if __name__ == "__main__":

    async def demo_enhanced_ai_routing() -> None:
        print("🤖 ENHANCED AI ROUTER DEMO")
        print("=" * 50)

        # Create enhanced router (without actual OpenRouter service for demo)
        router = create_enhanced_ai_router()

        # Test different routing scenarios
        test_scenarios = [
            ("Analyze this complex dataset for trends", "analysis", "quality"),
            ("Write a creative story", "creative", "quality"),
            ("Quick summary of this text", "general", "speed"),
            ("Cost-effective content analysis", "general", "cost"),
        ]

        for prompt, task_type, target in test_scenarios:
            print(f"\n📝 Prompt: {prompt[:40]}...")
            print(f"🎯 Task: {task_type} | Target: {target}")

            result = await router.intelligent_route(prompt=prompt, task_type=task_type, optimization_target=target)

            print(f"✅ Model: {result.get('model', 'unknown')}")
            print(f"📊 Reasoning: {result.get('routing_decision', 'N/A')}")
            print(f"⚡ Latency: {result.get('actual_latency_ms', 0):.1f}ms")
            print(f"💰 Cost: ${result.get('cost', 0):.4f}")

        # Show analytics
        analytics = router.get_routing_analytics()
        print("\n📈 ROUTING ANALYTICS:")
        print(f"  • Total routes: {analytics['total_routes']}")
        print(f"  • Success rate: {analytics['success_rate']:.1%}")
        print(f"  • Average latency: {analytics['avg_latency_ms']:.1f}ms")
        print(f"  • Average cost: ${analytics['avg_cost']:.4f}")
        print(f"  • Router confidence: {analytics['router_confidence']:.2f}")

    asyncio.run(demo_enhanced_ai_routing())
