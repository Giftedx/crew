#!/usr/bin/env python3
"""
A/B Testing Framework for AI Router Performance

Comprehensive framework for testing different routing strategies, measuring
effectiveness, and validating AI routing improvements through controlled experiments.
"""

import asyncio
import logging
import random
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class TestStrategy(Enum):
    """Different routing strategies to test."""

    PERFORMANCE_BASED = "performance_based"
    ADAPTIVE_LEARNING = "adaptive_learning"
    COST_OPTIMIZED = "cost_optimized"
    SPEED_OPTIMIZED = "speed_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    RANDOM_BASELINE = "random_baseline"


@dataclass
class ABTestConfig:
    """Configuration for A/B testing experiment."""

    test_name: str
    strategies: list[TestStrategy]
    traffic_split: dict[TestStrategy, float]  # Should sum to 1.0
    min_samples_per_strategy: int = 50
    max_duration_hours: float = 24.0
    success_criteria: dict[str, float] = field(
        default_factory=lambda: {
            "min_success_rate": 0.85,
            "max_avg_latency_ms": 2000,
            "max_avg_cost": 0.01,
        }
    )


@dataclass
class ABTestResult:
    """Result data for an A/B test experiment."""

    strategy: TestStrategy
    sample_count: int
    success_rate: float
    avg_latency_ms: float
    avg_cost: float
    avg_quality_score: float
    confidence_interval: tuple[float, float]
    statistical_significance: bool = False


@dataclass
class ExperimentMetrics:
    """Comprehensive metrics for routing experiment."""

    strategy: TestStrategy
    samples: deque = field(default_factory=lambda: deque(maxlen=1000))
    start_time: float = field(default_factory=time.time)

    def add_sample(self, latency_ms: float, cost: float, quality: float, success: bool):
        """Add a sample to the experiment."""
        self.samples.append(
            {
                "timestamp": time.time(),
                "latency_ms": latency_ms,
                "cost": cost,
                "quality": quality,
                "success": success,
            }
        )

    def get_summary_stats(self) -> dict[str, float]:
        """Get summary statistics for the experiment."""
        if not self.samples:
            return {}

        successes = [s["success"] for s in self.samples]
        latencies = [s["latency_ms"] for s in self.samples]
        costs = [s["cost"] for s in self.samples]
        qualities = [s["quality"] for s in self.samples]

        return {
            "sample_count": len(self.samples),
            "success_rate": sum(successes) / len(successes),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "avg_cost": sum(costs) / len(costs),
            "avg_quality": sum(qualities) / len(qualities),
            "duration_hours": (time.time() - self.start_time) / 3600,
        }


class AIRouterABTester:
    """A/B testing framework for AI routing strategies."""

    def __init__(self):
        self.active_experiments: dict[str, ABTestConfig] = {}
        self.experiment_metrics: dict[str, dict[TestStrategy, ExperimentMetrics]] = {}
        self.routing_strategies: dict[TestStrategy, Callable] = {}
        self.global_results: list[ABTestResult] = []

    def register_strategy(self, strategy: TestStrategy, router_function: Callable):
        """Register a routing strategy for testing."""
        self.routing_strategies[strategy] = router_function
        logger.info(f"Registered routing strategy: {strategy.value}")

    def start_experiment(self, config: ABTestConfig) -> str:
        """Start a new A/B testing experiment."""
        # Validate configuration
        if abs(sum(config.traffic_split.values()) - 1.0) > 0.01:
            raise ValueError("Traffic split must sum to 1.0")

        for strategy in config.strategies:
            if strategy not in self.routing_strategies:
                raise ValueError(f"Strategy {strategy.value} not registered")

        # Initialize experiment
        self.active_experiments[config.test_name] = config
        self.experiment_metrics[config.test_name] = {}

        for strategy in config.strategies:
            self.experiment_metrics[config.test_name][strategy] = ExperimentMetrics(strategy)

        logger.info(f"Started A/B test experiment: {config.test_name}")
        return config.test_name

    async def route_with_ab_testing(
        self,
        experiment_name: str,
        prompt: str,
        task_type: str = "general",
        optimization_target: str = "balanced",
        **kwargs,
    ) -> dict[str, Any]:
        """Route request using A/B testing strategy selection."""

        if experiment_name not in self.active_experiments:
            raise ValueError(f"Experiment {experiment_name} not found")

        config = self.active_experiments[experiment_name]

        # Select strategy based on traffic split
        selected_strategy = self._select_strategy(config)

        # Route using selected strategy
        start_time = time.time()
        try:
            router_func = self.routing_strategies[selected_strategy]
            result = await router_func(prompt, task_type, optimization_target, **kwargs)

            # Calculate metrics
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            cost = result.get("cost", 0.0)
            quality = self._assess_quality(result.get("response", ""), task_type)
            success = result.get("status") == "success"

            # Record metrics
            metrics = self.experiment_metrics[experiment_name][selected_strategy]
            metrics.add_sample(latency_ms, cost, quality, success)

            # Enhance result with A/B testing info
            result.update(
                {
                    "ab_test_strategy": selected_strategy.value,
                    "ab_test_experiment": experiment_name,
                    "ab_latency_ms": latency_ms,
                    "ab_quality_score": quality,
                }
            )

            return result

        except Exception as e:
            # Record failure
            latency_ms = (time.time() - start_time) * 1000
            metrics = self.experiment_metrics[experiment_name][selected_strategy]
            metrics.add_sample(latency_ms, 0.0, 0.0, False)

            return {
                "status": "error",
                "error": str(e),
                "ab_test_strategy": selected_strategy.value,
                "ab_test_experiment": experiment_name,
            }

    def _select_strategy(self, config: ABTestConfig) -> TestStrategy:
        """Select strategy based on traffic split configuration."""
        rand = random.random()  # nosec B311 - A/B test traffic split, not cryptographic
        cumulative = 0.0

        for strategy, weight in config.traffic_split.items():
            cumulative += weight
            if rand <= cumulative:
                return strategy

        # Fallback to first strategy
        return next(iter(config.strategies))

    def _assess_quality(self, response: str, task_type: str) -> float:
        """Simple quality assessment for A/B testing."""
        if not response:
            return 0.0

        # Basic quality factors
        length_score = min(1.0, len(response) / 200)
        coherence_score = 0.8  # Simulated

        # Task-specific bonuses
        task_bonus = 0.0
        if (
            task_type == "analysis" and any(word in response.lower() for word in ["analyze", "data", "conclusion"])
        ) or (task_type == "creative" and len(response) > 150):
            task_bonus = 0.1

        return min(1.0, length_score * 0.4 + coherence_score * 0.5 + task_bonus)

    def get_experiment_status(self, experiment_name: str) -> dict[str, Any]:
        """Get current status of an A/B testing experiment."""
        if experiment_name not in self.active_experiments:
            return {"error": "Experiment not found"}

        config = self.active_experiments[experiment_name]
        metrics = self.experiment_metrics[experiment_name]

        status = {"experiment": experiment_name, "strategies": {}, "overall": {}}

        total_samples = 0
        total_duration = 0

        for strategy in config.strategies:
            stats = metrics[strategy].get_summary_stats()
            status["strategies"][strategy.value] = stats
            total_samples += stats.get("sample_count", 0)
            total_duration = max(total_duration, stats.get("duration_hours", 0))

        # Check completion criteria
        min_samples_met = all(
            metrics[s].get_summary_stats().get("sample_count", 0) >= config.min_samples_per_strategy
            for s in config.strategies
        )
        max_duration_reached = total_duration >= config.max_duration_hours

        status["overall"] = {
            "total_samples": total_samples,
            "duration_hours": total_duration,
            "min_samples_met": min_samples_met,
            "max_duration_reached": max_duration_reached,
            "complete": min_samples_met or max_duration_reached,
        }

        return status

    def analyze_experiment_results(self, experiment_name: str) -> list[ABTestResult]:
        """Analyze and compare A/B test results."""
        if experiment_name not in self.active_experiments:
            return []

        config = self.active_experiments[experiment_name]
        metrics = self.experiment_metrics[experiment_name]
        results = []

        for strategy in config.strategies:
            stats = metrics[strategy].get_summary_stats()

            if stats.get("sample_count", 0) > 0:
                # Calculate confidence interval (simplified)
                success_rate = stats["success_rate"]
                n = stats["sample_count"]
                margin_of_error = 1.96 * (success_rate * (1 - success_rate) / n) ** 0.5 if n > 0 else 0

                result = ABTestResult(
                    strategy=strategy,
                    sample_count=stats["sample_count"],
                    success_rate=stats["success_rate"],
                    avg_latency_ms=stats["avg_latency_ms"],
                    avg_cost=stats["avg_cost"],
                    avg_quality_score=stats["avg_quality"],
                    confidence_interval=(
                        max(0, success_rate - margin_of_error),
                        min(1, success_rate + margin_of_error),
                    ),
                )

                # Check success criteria
                criteria = config.success_criteria
                meets_criteria = (
                    result.success_rate >= criteria.get("min_success_rate", 0.85)
                    and result.avg_latency_ms <= criteria.get("max_avg_latency_ms", 2000)
                    and result.avg_cost <= criteria.get("max_avg_cost", 0.01)
                )

                # Statistical significance (simplified)
                result.statistical_significance = result.sample_count >= 30 and meets_criteria

                results.append(result)

        # Sort by composite score (success_rate * quality / (latency * cost))
        def composite_score(r):
            if r.avg_latency_ms > 0 and r.avg_cost > 0:
                return (r.success_rate * r.avg_quality_score) / (r.avg_latency_ms / 1000 * r.avg_cost * 1000)
            return r.success_rate * r.avg_quality_score

        results.sort(key=composite_score, reverse=True)
        self.global_results.extend(results)

        return results

    def stop_experiment(self, experiment_name: str) -> list[ABTestResult]:
        """Stop an experiment and return final results."""
        if experiment_name not in self.active_experiments:
            return []

        results = self.analyze_experiment_results(experiment_name)

        # Clean up
        del self.active_experiments[experiment_name]
        # Keep metrics for historical analysis

        logger.info(f"Stopped A/B test experiment: {experiment_name}")
        return results

    def get_all_experiment_insights(self) -> dict[str, Any]:
        """Get comprehensive insights from all experiments."""
        if not self.global_results:
            return {"status": "no_experiments"}

        # Strategy performance summary
        strategy_performance = defaultdict(list)
        for result in self.global_results:
            strategy_performance[result.strategy].append(result)

        strategy_summary = {}
        for strategy, results in strategy_performance.items():
            if results:
                avg_success_rate = sum(r.success_rate for r in results) / len(results)
                avg_latency = sum(r.avg_latency_ms for r in results) / len(results)
                avg_cost = sum(r.avg_cost for r in results) / len(results)
                avg_quality = sum(r.avg_quality_score for r in results) / len(results)

                strategy_summary[strategy.value] = {
                    "experiments": len(results),
                    "avg_success_rate": avg_success_rate,
                    "avg_latency_ms": avg_latency,
                    "avg_cost": avg_cost,
                    "avg_quality": avg_quality,
                    "statistically_significant": sum(r.statistical_significance for r in results),
                }

        # Best performing strategy
        best_strategy = max(
            strategy_summary.items(),
            key=lambda x: x[1]["avg_success_rate"]
            * x[1]["avg_quality"]
            / (x[1]["avg_latency_ms"] / 1000 * x[1]["avg_cost"] * 1000 + 0.001),
        )

        return {
            "status": "complete",
            "total_experiments": len({r.strategy for r in self.global_results}),
            "total_samples": sum(r.sample_count for r in self.global_results),
            "strategy_performance": strategy_summary,
            "best_strategy": best_strategy[0],
            "best_strategy_score": best_strategy[1],
        }


# Mock routing strategies for testing
async def performance_based_router(prompt: str, task_type: str, optimization_target: str, **kwargs) -> dict[str, Any]:
    """Mock performance-based routing strategy."""
    await asyncio.sleep(0.1)  # Simulate processing
    return {
        "status": "success",
        "model": "openai/gpt-4o",
        "response": f"Performance-based response for {task_type}",
        "cost": 0.005,
    }


async def adaptive_learning_router(prompt: str, task_type: str, optimization_target: str, **kwargs) -> dict[str, Any]:
    """Mock adaptive learning routing strategy."""
    await asyncio.sleep(0.08)  # Slightly faster
    return {
        "status": "success",
        "model": "anthropic/claude-3-5-sonnet-20241022",
        "response": f"Adaptive learning response for {task_type} with advanced analysis",
        "cost": 0.008,
    }


async def cost_optimized_router(prompt: str, task_type: str, optimization_target: str, **kwargs) -> dict[str, Any]:
    """Mock cost-optimized routing strategy."""
    await asyncio.sleep(0.06)  # Fast
    return {
        "status": "success",
        "model": "google/gemini-1.5-flash",
        "response": f"Cost-optimized response for {task_type}",
        "cost": 0.001,
    }


async def random_baseline_router(prompt: str, task_type: str, optimization_target: str, **kwargs) -> dict[str, Any]:
    """Mock random baseline routing strategy."""
    models = [
        "openai/gpt-4o-mini",
        "google/gemini-1.5-flash",
        "anthropic/claude-3-haiku-20240307",
    ]
    selected_model = random.choice(models)  # nosec B311 - test simulation, not cryptographic
    await asyncio.sleep(random.uniform(0.05, 0.15))  # nosec B311 - test latency simulation
    return {
        "status": "success",
        "model": selected_model,
        "response": f"Random baseline response for {task_type}",
        "cost": random.uniform(0.001, 0.010),  # nosec B311 - test cost simulation
    }


if __name__ == "__main__":

    async def demo_ab_testing():
        """Demonstrate A/B testing framework for AI routing."""
        print("🧪 AI ROUTER A/B TESTING DEMO")
        print("=" * 50)

        # Create A/B tester
        tester = AIRouterABTester()

        # Register routing strategies
        tester.register_strategy(TestStrategy.PERFORMANCE_BASED, performance_based_router)
        tester.register_strategy(TestStrategy.ADAPTIVE_LEARNING, adaptive_learning_router)
        tester.register_strategy(TestStrategy.COST_OPTIMIZED, cost_optimized_router)
        tester.register_strategy(TestStrategy.RANDOM_BASELINE, random_baseline_router)

        # Configure experiment
        config = ABTestConfig(
            test_name="routing_strategy_comparison",
            strategies=[
                TestStrategy.PERFORMANCE_BASED,
                TestStrategy.ADAPTIVE_LEARNING,
                TestStrategy.COST_OPTIMIZED,
                TestStrategy.RANDOM_BASELINE,
            ],
            traffic_split={
                TestStrategy.PERFORMANCE_BASED: 0.25,
                TestStrategy.ADAPTIVE_LEARNING: 0.25,
                TestStrategy.COST_OPTIMIZED: 0.25,
                TestStrategy.RANDOM_BASELINE: 0.25,
            },
            min_samples_per_strategy=20,
            max_duration_hours=0.1,  # 6 minutes for demo
        )

        # Start experiment
        experiment_name = tester.start_experiment(config)
        print(f"🚀 Started experiment: {experiment_name}")

        # Simulate traffic for 60 routing requests
        test_scenarios = [
            ("Analyze customer feedback data", "analysis", "quality"),
            ("Generate creative marketing copy", "creative", "quality"),
            ("Quick content summary", "general", "speed"),
            ("Cost-effective data processing", "general", "cost"),
        ]

        print("\n📊 Running A/B test traffic...")
        for i in range(60):
            scenario = random.choice(test_scenarios)
            prompt, task_type, target = scenario

            result = await tester.route_with_ab_testing(
                experiment_name=experiment_name,
                prompt=prompt,
                task_type=task_type,
                optimization_target=target,
            )

            if i % 15 == 0:  # Progress update every 15 requests
                status = tester.get_experiment_status(experiment_name)
                print(f"  Progress: {status['overall']['total_samples']}/60 samples collected")

        print("✅ Traffic simulation complete!")

        # Get final status
        status = tester.get_experiment_status(experiment_name)
        print("\n📈 EXPERIMENT STATUS:")
        print(f"  • Total samples: {status['overall']['total_samples']}")
        print(f"  • Duration: {status['overall']['duration_hours']:.2f} hours")
        print(f"  • Complete: {status['overall']['complete']}")

        print("\n📊 STRATEGY PERFORMANCE:")
        for strategy_name, stats in status["strategies"].items():
            print(
                f"  • {strategy_name}: {stats['sample_count']} samples, "
                f"{stats['success_rate']:.1%} success, "
                f"{stats['avg_latency_ms']:.0f}ms, "
                f"${stats['avg_cost']:.3f}, "
                f"Q:{stats['avg_quality']:.2f}"
            )

        # Analyze results
        results = tester.analyze_experiment_results(experiment_name)
        print("\n🏆 RESULTS ANALYSIS (Ranked by Performance):")

        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.strategy.value}:")
            print(
                f"     • Success Rate: {result.success_rate:.1%} ± {result.confidence_interval[1] - result.success_rate:.1%}"
            )
            print(f"     • Avg Latency: {result.avg_latency_ms:.0f}ms")
            print(f"     • Avg Cost: ${result.avg_cost:.4f}")
            print(f"     • Avg Quality: {result.avg_quality_score:.2f}")
            print(f"     • Statistical Significance: {'✅' if result.statistical_significance else '❌'}")

        # Stop experiment and get insights
        tester.stop_experiment(experiment_name)
        insights = tester.get_all_experiment_insights()

        print("\n🧠 EXPERIMENT INSIGHTS:")
        print(f"  • Best Strategy: {insights['best_strategy']}")
        print(f"  • Performance Score: {insights['best_strategy_score']['avg_success_rate']:.1%} success rate")
        print(f"  • Quality Score: {insights['best_strategy_score']['avg_quality']:.2f}")
        print(f"  • Cost Efficiency: ${insights['best_strategy_score']['avg_cost']:.4f}")

        print("\n✨ A/B Testing Framework: VALIDATION COMPLETE! ✨")

    asyncio.run(demo_ab_testing())
