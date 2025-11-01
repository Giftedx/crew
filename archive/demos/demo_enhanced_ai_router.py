#!/usr/bin/env python3
"""
Enhanced AI Router Demo (Standalone)

Demonstrates the enhanced AI router with intelligent routing capabilities
without requiring full project dependencies.
"""

import asyncio
import logging
import sys
from typing import Any


# Add the src directory to Python path for imports
sys.path.insert(0, "/home/crew/src")

try:
    from ai.performance_router import create_performance_router
except ImportError:
    print("⚠️  Could not import performance router. Running basic demo...")

    # Simple mock for demonstration
    class MockRouter:
        def select_optimal_model(self, task_type, available_models, optimization_target):
            # Simple selection logic for demo
            if optimization_target == "speed":
                return type(
                    "",
                    (),
                    {
                        "selected_model": "openai/gpt-4o-mini",
                        "reasoning": "Selected fastest model for speed optimization",
                        "confidence": 0.85,
                        "expected_cost": 0.002,
                        "expected_latency_ms": 800,
                    },
                )()
            elif optimization_target == "cost":
                return type(
                    "",
                    (),
                    {
                        "selected_model": "google/gemini-1.5-flash",
                        "reasoning": "Selected most cost-effective model",
                        "confidence": 0.78,
                        "expected_cost": 0.001,
                        "expected_latency_ms": 1200,
                    },
                )()
            elif optimization_target == "quality":
                return type(
                    "",
                    (),
                    {
                        "selected_model": "anthropic/claude-3-5-sonnet-20241022",
                        "reasoning": "Selected highest quality model for analysis",
                        "confidence": 0.92,
                        "expected_cost": 0.015,
                        "expected_latency_ms": 2000,
                    },
                )()
            else:  # balanced
                return type(
                    "",
                    (),
                    {
                        "selected_model": "openai/gpt-4o",
                        "reasoning": "Balanced choice for optimal cost/quality/speed",
                        "confidence": 0.75,
                        "expected_cost": 0.005,
                        "expected_latency_ms": 1500,
                    },
                )()

        def update_model_performance(self, model, latency_ms, cost, success, quality_score):
            pass

        def get_routing_stats(self):
            return {"recent_avg_confidence": 0.8, "performance_data_points": 15}

    def create_performance_router(monitor=None):
        router = MockRouter()
        if monitor is not None:
            monitor_attr = getattr(monitor, "__class__", None)
            monitor_name = getattr(monitor_attr, "__name__", "monitor")
            logging.getLogger(__name__).debug("Attaching monitor %s to demo router", monitor_name)
            router.monitor = monitor
        return router


logger = logging.getLogger(__name__)


class EnhancedAIRouterDemo:
    """Enhanced AI router demonstration."""

    def __init__(self):
        self.performance_router = create_performance_router()
        self.route_history: list[dict[str, Any]] = []

    async def intelligent_route(
        self,
        prompt: str,
        task_type: str = "general",
        optimization_target: str = "balanced",
        model: str | None = None,
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
                    task_type=task_type,
                    available_models=available_models,
                    optimization_target=optimization_target,
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
                expected_cost = 0.003
                expected_latency = 1000.0

            # Simulate API call
            await asyncio.sleep(0.1)  # Simulate network delay
            result = {
                "status": "success",
                "model": selected_model,
                "response": f"[AI Response from {selected_model} for {task_type} task]",
                "tokens": 45,
                "tokens_out": 28,
                "cost": expected_cost,
            }

            # Calculate actual performance metrics
            end_time = asyncio.get_event_loop().time()
            actual_latency_ms = (end_time - start_time) * 1000
            actual_cost = result.get("cost", expected_cost)
            success = result.get("status") == "success"

            # Update performance metrics
            if success:
                quality_score = self._assess_response_quality(result.get("response", ""), task_type)

                self.performance_router.update_model_performance(
                    model=selected_model,
                    latency_ms=actual_latency_ms,
                    cost=actual_cost,
                    success=success,
                    quality_score=quality_score,
                )

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
        """Simple response quality assessment."""
        if not response:
            return 0.0

        # Basic quality factors
        length_score = min(1.0, len(response) / 200)
        coherence_score = 0.8  # Simulated

        # Task-specific adjustments
        task_bonus = 0.0
        if (task_type == "analysis" and any(word in response.lower() for word in ["analyze", "evidence"])) or (
            task_type == "creative" and len(response) > 100
        ):
            task_bonus = 0.1

        return min(1.0, length_score * 0.3 + coherence_score * 0.6 + task_bonus)

    def get_routing_analytics(self) -> dict[str, Any]:
        """Get comprehensive routing analytics."""
        if not self.route_history:
            return {"total_routes": 0}

        total_routes = len(self.route_history)
        successful_routes = sum(1 for r in self.route_history if r["success"])
        success_rate = successful_routes / total_routes

        avg_latency = sum(r["actual_latency_ms"] for r in self.route_history) / total_routes
        avg_cost = sum(r["actual_cost"] for r in self.route_history) / total_routes

        model_usage = {}
        for route in self.route_history:
            model = route["selected_model"]
            model_usage[model] = model_usage.get(model, 0) + 1

        target_usage = {}
        for route in self.route_history:
            target = route["optimization_target"]
            target_usage[target] = target_usage.get(target, 0) + 1

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


async def demo_enhanced_ai_routing():
    """Demonstrate enhanced AI routing capabilities."""
    print("🤖 ENHANCED AI ROUTER DEMO")
    print("=" * 50)

    # Create enhanced router
    router = EnhancedAIRouterDemo()

    # Test different routing scenarios
    test_scenarios = [
        ("Analyze this complex dataset for trends and patterns", "analysis", "quality"),
        ("Write a creative story about space exploration", "creative", "quality"),
        ("Quick summary of this technical document", "general", "speed"),
        ("Cost-effective content analysis for social media", "general", "cost"),
        ("Balanced approach for general AI assistance", "general", "balanced"),
    ]

    for i, (prompt, task_type, target) in enumerate(test_scenarios, 1):
        print(f"\n🔍 Test {i}/5:")
        print(f"📝 Prompt: {prompt[:50]}...")
        print(f"🎯 Task: {task_type} | Target: {target}")

        result = await router.intelligent_route(prompt=prompt, task_type=task_type, optimization_target=target)

        print(f"✅ Model: {result.get('model', 'unknown')}")
        print(f"📊 Reasoning: {result.get('routing_decision', 'N/A')}")
        print(f"⚡ Latency: {result.get('actual_latency_ms', 0):.1f}ms")
        print(f"💰 Cost: ${result.get('cost', 0):.4f}")
        print(f"🎯 Target Match: {result.get('optimization_target', 'N/A')}")

    # Show comprehensive analytics
    print("\n📈 ROUTING ANALYTICS:")
    print("=" * 30)
    analytics = router.get_routing_analytics()

    print(f"📊 Total routes: {analytics['total_routes']}")
    print(f"✅ Success rate: {analytics['success_rate']:.1%}")
    print(f"⚡ Average latency: {analytics['avg_latency_ms']:.1f}ms")
    print(f"💰 Average cost: ${analytics['avg_cost']:.4f}")
    print(f"🧠 Router confidence: {analytics['router_confidence']:.2f}")
    print(f"📚 Learning data points: {analytics['learning_data_points']}")

    print("\n🎯 Optimization Target Usage:")
    for target, count in analytics["optimization_targets"].items():
        print(f"  • {target}: {count} requests")

    print("\n🤖 Model Usage Distribution:")
    for model, count in analytics["model_usage"].items():
        print(f"  • {model.split('/')[-1]}: {count} requests")

    print("\n✨ AI-001: LiteLLM Router Integration - ENHANCED! ✨")


if __name__ == "__main__":
    asyncio.run(demo_enhanced_ai_routing())
