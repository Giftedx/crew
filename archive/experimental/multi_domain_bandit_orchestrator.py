"""
Multi-Domain Advanced Bandit Orchestrator

A centralized orchestrator that coordinates advanced bandit decisions across
multiple domains with cross-domain learning and optimization.

Key Features:
- Cross-domain context sharing and learning
- Hierarchical decision making with domain priorities
- Global optimization strategies
- Resource-aware routing
- Performance correlation analysis
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class GlobalContext:
    """Global context shared across all domains."""

    user_id: str
    session_id: str
    timestamp: datetime
    request_priority: float  # 0-1, higher = more important
    resource_budget: float  # Available computational budget
    latency_requirement: float  # Maximum acceptable latency
    quality_requirement: float  # Minimum acceptable quality
    cost_sensitivity: float  # 0-1, higher = more cost sensitive

    # Cross-domain state
    previous_decisions: dict[str, str]
    performance_history: dict[str, list[float]]
    user_satisfaction_trend: float  # Rolling average

    # Contextual features
    user_tier: str  # free, premium, enterprise
    content_complexity: float  # 0-1
    interaction_count: int
    time_of_day: float  # 0-1 normalized


@dataclass
class DomainDecision:
    """Decision made by a domain."""

    domain: str
    decision: str
    confidence: float  # 0-1
    expected_latency: float  # milliseconds
    expected_quality: float  # 0-1
    expected_cost: float  # normalized cost
    reasoning: str
    timestamp: datetime


@dataclass
class GlobalDecisionPlan:
    """Coordinated decision plan across all domains."""

    session_id: str
    global_context: GlobalContext
    domain_decisions: dict[str, DomainDecision]
    execution_order: list[str]  # Order to execute decisions
    total_expected_latency: float
    total_expected_cost: float
    overall_quality_score: float
    optimization_strategy: str
    timestamp: datetime


class DomainInterface:
    """Abstract interface for domain-specific bandit policies."""

    def __init__(self, name: str):
        self.name = name
        self.decision_history = []
        self.performance_metrics = {
            "avg_reward": 0.0,
            "avg_latency": 0.0,
            "decision_count": 0,
            "success_rate": 1.0,
        }

    async def make_decision(self, global_context: GlobalContext, candidates: list[str]) -> DomainDecision:
        """Make a decision based on global context and available candidates."""
        raise NotImplementedError

    def update_performance(self, decision: str, reward: float, latency: float, success: bool):
        """Update performance metrics based on execution results."""
        metrics = self.performance_metrics
        count = metrics["decision_count"]

        # Update rolling averages
        metrics["avg_reward"] = (metrics["avg_reward"] * count + reward) / (count + 1)
        metrics["avg_latency"] = (metrics["avg_latency"] * count + latency) / (count + 1)
        metrics["success_rate"] = (metrics["success_rate"] * count + (1.0 if success else 0.0)) / (count + 1)
        metrics["decision_count"] = count + 1

        logger.info(
            f"Domain {self.name} performance: reward={metrics['avg_reward']:.3f}, "
            f"latency={metrics['avg_latency']:.1f}ms, success={metrics['success_rate']:.3f}"
        )


class ModelRoutingDomain(DomainInterface):
    """Advanced model routing domain using DoublyRobust-like logic."""

    def __init__(self):
        super().__init__("model_routing")
        self.models = {
            "gpt-4-turbo": {
                "quality": 0.9,
                "latency": 800,
                "cost": 20,
                "complexity_boost": 0.1,
            },
            "gpt-3.5-turbo": {
                "quality": 0.75,
                "latency": 300,
                "cost": 5,
                "complexity_boost": -0.1,
            },
            "claude-3-opus": {
                "quality": 0.92,
                "latency": 1200,
                "cost": 25,
                "complexity_boost": 0.15,
            },
            "claude-3-sonnet": {
                "quality": 0.8,
                "latency": 600,
                "cost": 12,
                "complexity_boost": 0.05,
            },
        }
        self.alpha = 1.5  # Exploration parameter

    async def make_decision(self, global_context: GlobalContext, candidates: list[str] | None = None) -> DomainDecision:
        if candidates is None:
            candidates = list(self.models.keys())

        # Calculate utility scores for each model
        best_model = None
        best_score = -float("inf")

        for model in candidates:
            if model not in self.models:
                continue

            specs = self.models[model]

            # Base quality with complexity adjustment
            quality = specs["quality"] + specs["complexity_boost"] * global_context.content_complexity
            quality = max(0.1, min(1.0, quality))

            # Latency penalty based on requirements
            latency_penalty = max(0, (specs["latency"] - global_context.latency_requirement) / 1000)

            # Cost penalty based on sensitivity
            cost_penalty = specs["cost"] / 30 * global_context.cost_sensitivity

            # Quality bonus for high requirements
            quality_bonus = quality * global_context.quality_requirement

            # Priority boost for important requests
            priority_boost = global_context.request_priority * 0.2

            # Exploration bonus (UCB-like)
            exploration_bonus = self.alpha * (global_context.interaction_count + 1) ** -0.5

            # Composite score
            score = quality_bonus + priority_boost + exploration_bonus - latency_penalty - cost_penalty

            if score > best_score:
                best_score = score
                best_model = model

        if best_model is None:
            best_model = candidates[0]  # Fallback

        specs = self.models[best_model]
        confidence = min(1.0, best_score / 2.0)  # Normalize confidence

        return DomainDecision(
            domain=self.name,
            decision=best_model,
            confidence=confidence,
            expected_latency=specs["latency"],
            expected_quality=specs["quality"],
            expected_cost=specs["cost"],
            reasoning=f"Selected based on quality={specs['quality']:.2f}, latency={specs['latency']}ms, cost={specs['cost']}, score={best_score:.3f}",
            timestamp=datetime.now(UTC),
        )


class ContentAnalysisDomain(DomainInterface):
    """Content analysis domain using OffsetTree-like logic."""

    def __init__(self):
        super().__init__("content_analysis")
        self.processors = {
            "fast_nlp": {"quality": 0.6, "latency": 200, "complexity_threshold": 0.3},
            "advanced_nlp": {
                "quality": 0.85,
                "latency": 800,
                "complexity_threshold": 0.6,
            },
            "specialized_tech": {
                "quality": 0.9,
                "latency": 1000,
                "complexity_threshold": 0.8,
            },
            "multimedia_processor": {
                "quality": 0.8,
                "latency": 1500,
                "complexity_threshold": 0.5,
            },
        }
        self.decision_tree = self._build_decision_tree()

    def _build_decision_tree(self):
        """Build a simple decision tree for content routing."""
        return {
            "root": {
                "feature": "content_complexity",
                "threshold": 0.4,
                "left": {  # Low complexity
                    "feature": "latency_requirement",
                    "threshold": 500,
                    "left": "fast_nlp",  # Low complexity, fast required
                    "right": "advanced_nlp",  # Low complexity, quality focus
                },
                "right": {  # High complexity
                    "feature": "user_tier",
                    "threshold": 0.5,  # premium+
                    "left": "advanced_nlp",  # High complexity, free user
                    "right": "specialized_tech",  # High complexity, premium user
                },
            }
        }

    def _traverse_tree(self, node, context: GlobalContext) -> str:
        """Traverse decision tree to make routing decision."""
        if isinstance(node, str):
            return node  # Leaf node

        feature_value = getattr(context, node["feature"], 0.0)
        if node["feature"] == "user_tier":
            tier_map = {"free": 0.0, "premium": 0.5, "enterprise": 1.0}
            feature_value = tier_map.get(context.user_tier, 0.0)

        if feature_value <= node["threshold"]:
            return self._traverse_tree(node["left"], context)
        else:
            return self._traverse_tree(node["right"], context)

    async def make_decision(self, global_context: GlobalContext, candidates: list[str] | None = None) -> DomainDecision:
        if candidates is None:
            candidates = list(self.processors.keys())

        # Use decision tree for initial selection
        selected_processor = self._traverse_tree(self.decision_tree["root"], global_context)

        # Validate selection is in candidates
        if selected_processor not in candidates:
            # Fall back to best available option
            best_option = None
            best_fit = -1

            for proc in candidates:
                if proc not in self.processors:
                    continue
                specs = self.processors[proc]
                fit_score = specs["quality"] * global_context.quality_requirement + (1 - specs["latency"] / 2000) * (
                    1 - global_context.cost_sensitivity
                )
                if fit_score > best_fit:
                    best_fit = fit_score
                    best_option = proc

            selected_processor = best_option or candidates[0]

        specs = self.processors[selected_processor]

        # Calculate confidence based on tree depth and context fit
        complexity_match = 1.0 - abs(global_context.content_complexity - specs["complexity_threshold"])
        confidence = max(0.3, min(1.0, complexity_match))

        return DomainDecision(
            domain=self.name,
            decision=selected_processor,
            confidence=confidence,
            expected_latency=specs["latency"],
            expected_quality=specs["quality"],
            expected_cost=8.0,  # Normalized processing cost
            reasoning=f"Tree-based selection: complexity={global_context.content_complexity:.2f}, threshold={specs['complexity_threshold']:.2f}",
            timestamp=datetime.now(UTC),
        )


class UserEngagementDomain(DomainInterface):
    """User engagement optimization domain."""

    def __init__(self):
        super().__init__("user_engagement")
        self.strategies = {
            "immediate_response": {
                "satisfaction": 0.7,
                "engagement": 0.6,
                "latency": 150,
            },
            "detailed_analysis": {
                "satisfaction": 0.85,
                "engagement": 0.9,
                "latency": 800,
            },
            "interactive_followup": {
                "satisfaction": 0.8,
                "engagement": 0.85,
                "latency": 400,
            },
            "educational_context": {
                "satisfaction": 0.75,
                "engagement": 0.8,
                "latency": 600,
            },
        }
        self.user_preferences = {}  # Track per-user preferences

    async def make_decision(self, global_context: GlobalContext, candidates: list[str] | None = None) -> DomainDecision:
        if candidates is None:
            candidates = list(self.strategies.keys())

        # Analyze user satisfaction trend
        satisfaction_trend = global_context.user_satisfaction_trend

        # Choose strategy based on context and trends
        best_strategy = None
        best_score = -float("inf")

        for strategy in candidates:
            if strategy not in self.strategies:
                continue

            specs = self.strategies[strategy]

            # Base satisfaction and engagement
            satisfaction_score = specs["satisfaction"]
            engagement_score = specs["engagement"]

            # Adjust based on user tier
            tier_bonus = {"free": 0.0, "premium": 0.1, "enterprise": 0.2}.get(global_context.user_tier, 0.0)

            # Adjust based on satisfaction trend
            if satisfaction_trend < 0.7 and strategy == "detailed_analysis":
                satisfaction_score += 0.1  # Boost for quality when satisfaction is low
            elif satisfaction_trend > 0.8 and strategy == "immediate_response":
                satisfaction_score += 0.1  # Boost for speed when satisfaction is high

            # Latency penalty
            latency_penalty = max(0, (specs["latency"] - global_context.latency_requirement) / 1000)

            # Composite score
            score = 0.6 * satisfaction_score + 0.4 * engagement_score + tier_bonus - 0.2 * latency_penalty

            if score > best_score:
                best_score = score
                best_strategy = strategy

        if best_strategy is None:
            best_strategy = candidates[0]

        specs = self.strategies[best_strategy]
        confidence = min(1.0, best_score)

        return DomainDecision(
            domain=self.name,
            decision=best_strategy,
            confidence=confidence,
            expected_latency=specs["latency"],
            expected_quality=specs["satisfaction"],
            expected_cost=2.0,  # Low cost for engagement strategies
            reasoning=f"Engagement optimization: satisfaction_trend={satisfaction_trend:.2f}, tier={global_context.user_tier}",
            timestamp=datetime.now(UTC),
        )


class MultiBanditOrchestrator:
    """Orchestrates decisions across multiple bandit domains."""

    def __init__(self):
        self.domains = {
            "model_routing": ModelRoutingDomain(),
            "content_analysis": ContentAnalysisDomain(),
            "user_engagement": UserEngagementDomain(),
        }

        self.optimization_strategies = {
            "balanced": self._balanced_optimization,
            "quality_focused": self._quality_focused_optimization,
            "speed_focused": self._speed_focused_optimization,
            "cost_optimized": self._cost_optimized_optimization,
        }

        self.global_stats = {
            "total_requests": 0,
            "avg_satisfaction": 0.0,
            "avg_latency": 0.0,
            "success_rate": 1.0,
        }

        logger.info("Multi-Domain Bandit Orchestrator initialized")

    def _determine_optimization_strategy(self, context: GlobalContext) -> str:
        """Determine the best optimization strategy based on context."""

        # High priority requests -> quality focused
        if context.request_priority > 0.8:
            return "quality_focused"

        # Cost sensitive -> cost optimized
        if context.cost_sensitivity > 0.7:
            return "cost_optimized"

        # Strict latency requirements -> speed focused
        if context.latency_requirement < 500:
            return "speed_focused"

        # Default to balanced
        return "balanced"

    async def _balanced_optimization(self, context: GlobalContext) -> GlobalDecisionPlan:
        """Balanced optimization across all objectives."""

        # Get decisions from all domains
        domain_decisions = {}
        for domain_name, domain in self.domains.items():
            decision = await domain.make_decision(context)
            domain_decisions[domain_name] = decision

        # Determine execution order (model routing first, then content, then engagement)
        execution_order = ["model_routing", "content_analysis", "user_engagement"]

        # Calculate overall metrics
        total_latency = sum(d.expected_latency for d in domain_decisions.values())
        total_cost = sum(d.expected_cost for d in domain_decisions.values())
        avg_quality = sum(d.expected_quality for d in domain_decisions.values()) / len(domain_decisions)

        return GlobalDecisionPlan(
            session_id=context.session_id,
            global_context=context,
            domain_decisions=domain_decisions,
            execution_order=execution_order,
            total_expected_latency=total_latency,
            total_expected_cost=total_cost,
            overall_quality_score=avg_quality,
            optimization_strategy="balanced",
            timestamp=datetime.now(UTC),
        )

    async def _quality_focused_optimization(self, context: GlobalContext) -> GlobalDecisionPlan:
        """Quality-focused optimization."""

        # Modify context to emphasize quality
        quality_context = GlobalContext(
            **{k: v for k, v in asdict(context).items() if k != "quality_requirement"},
            quality_requirement=min(1.0, context.quality_requirement + 0.2),
        )

        domain_decisions = {}
        for domain_name, domain in self.domains.items():
            decision = await domain.make_decision(quality_context)
            domain_decisions[domain_name] = decision

        # Prioritize high-quality options even if slower
        execution_order = ["model_routing", "content_analysis", "user_engagement"]

        total_latency = sum(d.expected_latency for d in domain_decisions.values())
        total_cost = sum(d.expected_cost for d in domain_decisions.values())
        avg_quality = sum(d.expected_quality for d in domain_decisions.values()) / len(domain_decisions)

        return GlobalDecisionPlan(
            session_id=context.session_id,
            global_context=context,
            domain_decisions=domain_decisions,
            execution_order=execution_order,
            total_expected_latency=total_latency,
            total_expected_cost=total_cost,
            overall_quality_score=avg_quality,
            optimization_strategy="quality_focused",
            timestamp=datetime.now(UTC),
        )

    async def _speed_focused_optimization(self, context: GlobalContext) -> GlobalDecisionPlan:
        """Speed-focused optimization."""

        # Modify context to emphasize speed
        speed_context = GlobalContext(
            **{k: v for k, v in asdict(context).items() if k != "latency_requirement"},
            latency_requirement=max(100, context.latency_requirement - 200),
        )

        domain_decisions = {}
        for domain_name, domain in self.domains.items():
            decision = await domain.make_decision(speed_context)
            domain_decisions[domain_name] = decision

        # Optimize execution order for speed (parallel where possible)
        execution_order = ["model_routing", "content_analysis", "user_engagement"]

        total_latency = sum(d.expected_latency for d in domain_decisions.values())
        total_cost = sum(d.expected_cost for d in domain_decisions.values())
        avg_quality = sum(d.expected_quality for d in domain_decisions.values()) / len(domain_decisions)

        return GlobalDecisionPlan(
            session_id=context.session_id,
            global_context=context,
            domain_decisions=domain_decisions,
            execution_order=execution_order,
            total_expected_latency=total_latency * 0.8,  # Assume some parallelization
            total_expected_cost=total_cost,
            overall_quality_score=avg_quality,
            optimization_strategy="speed_focused",
            timestamp=datetime.now(UTC),
        )

    async def _cost_optimized_optimization(self, context: GlobalContext) -> GlobalDecisionPlan:
        """Cost-optimized decision making."""

        # Modify context to emphasize cost efficiency
        cost_context = GlobalContext(
            **{k: v for k, v in asdict(context).items() if k != "cost_sensitivity"},
            cost_sensitivity=min(1.0, context.cost_sensitivity + 0.3),
        )

        domain_decisions = {}
        for domain_name, domain in self.domains.items():
            decision = await domain.make_decision(cost_context)
            domain_decisions[domain_name] = decision

        execution_order = ["model_routing", "content_analysis", "user_engagement"]

        total_latency = sum(d.expected_latency for d in domain_decisions.values())
        total_cost = sum(d.expected_cost for d in domain_decisions.values())
        avg_quality = sum(d.expected_quality for d in domain_decisions.values()) / len(domain_decisions)

        return GlobalDecisionPlan(
            session_id=context.session_id,
            global_context=context,
            domain_decisions=domain_decisions,
            execution_order=execution_order,
            total_expected_latency=total_latency,
            total_expected_cost=total_cost,
            overall_quality_score=avg_quality,
            optimization_strategy="cost_optimized",
            timestamp=datetime.now(UTC),
        )

    async def orchestrate_decision(self, context: GlobalContext) -> GlobalDecisionPlan:
        """Orchestrate a global decision across all domains."""

        # Determine optimization strategy
        strategy_name = self._determine_optimization_strategy(context)
        optimization_func = self.optimization_strategies[strategy_name]

        logger.info(f"Using optimization strategy: {strategy_name} for request {context.session_id}")

        # Generate global decision plan
        start_time = time.time()
        plan = await optimization_func(context)
        orchestration_time = (time.time() - start_time) * 1000

        logger.info(
            f"Orchestration complete in {orchestration_time:.1f}ms: "
            f"strategy={strategy_name}, quality={plan.overall_quality_score:.3f}, "
            f"latency={plan.total_expected_latency:.0f}ms, cost={plan.total_expected_cost:.1f}"
        )

        return plan

    async def execute_plan(self, plan: GlobalDecisionPlan) -> dict[str, Any]:
        """Execute a global decision plan and return results."""

        start_time = time.time()
        results = {
            "session_id": plan.session_id,
            "execution_results": {},
            "actual_metrics": {},
            "success": True,
        }

        try:
            # Execute domains in order
            total_latency = 0
            total_cost = 0
            quality_scores = []

            for domain_name in plan.execution_order:
                decision = plan.domain_decisions[domain_name]

                # Simulate execution (in real implementation, this would call actual services)
                execution_time = decision.expected_latency + (time.time() * 1000) % 100  # Add some variance
                execution_cost = decision.expected_cost * (0.8 + (time.time() % 1) * 0.4)  # ±20% variance

                # Simulate quality with some variance
                quality = decision.expected_quality + ((time.time() % 1) - 0.5) * 0.1
                quality = max(0.1, min(1.0, quality))

                # Update domain performance
                reward = quality * 0.7 + (1 - execution_time / 2000) * 0.3  # Quality + speed reward
                success = quality > 0.5 and execution_time < decision.expected_latency * 1.5

                domain = self.domains[domain_name]
                domain.update_performance(decision.decision, reward, execution_time, success)

                # Accumulate metrics
                total_latency += execution_time
                total_cost += execution_cost
                quality_scores.append(quality)

                results["execution_results"][domain_name] = {
                    "decision": decision.decision,
                    "latency_ms": execution_time,
                    "cost": execution_cost,
                    "quality": quality,
                    "reward": reward,
                    "success": success,
                }

                # Short delay to simulate realistic execution
                await asyncio.sleep(0.01)

            # Calculate overall metrics
            avg_quality = sum(quality_scores) / len(quality_scores)
            overall_satisfaction = min(1.0, avg_quality * 1.1)  # Slight boost for coordination

            results["actual_metrics"] = {
                "total_latency_ms": total_latency,
                "total_cost": total_cost,
                "average_quality": avg_quality,
                "overall_satisfaction": overall_satisfaction,
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

            # Update global stats
            self._update_global_stats(results["actual_metrics"], True)

        except Exception as e:
            logger.error(f"Plan execution failed: {e}")
            results["success"] = False
            results["error"] = str(e)
            self._update_global_stats({}, False)

        return results

    def _update_global_stats(self, metrics: dict[str, Any], success: bool):
        """Update global orchestrator statistics."""

        stats = self.global_stats
        count = stats["total_requests"]

        if success and metrics:
            # Update rolling averages
            stats["avg_satisfaction"] = (stats["avg_satisfaction"] * count + metrics["overall_satisfaction"]) / (
                count + 1
            )
            stats["avg_latency"] = (stats["avg_latency"] * count + metrics["total_latency_ms"]) / (count + 1)

        stats["success_rate"] = (stats["success_rate"] * count + (1.0 if success else 0.0)) / (count + 1)
        stats["total_requests"] = count + 1

    def get_performance_summary(self) -> dict[str, Any]:
        """Get comprehensive performance summary."""

        summary = {
            "timestamp": datetime.now(UTC).isoformat(),
            "global_stats": self.global_stats,
            "domain_performance": {},
            "recommendations": [],
        }

        # Domain performance
        for domain_name, domain in self.domains.items():
            summary["domain_performance"][domain_name] = domain.performance_metrics

        # Generate recommendations
        recommendations = []

        if self.global_stats["avg_satisfaction"] < 0.7:
            recommendations.append("Consider tuning domain policies - global satisfaction below 70%")

        if self.global_stats["avg_latency"] > 1500:
            recommendations.append("High average latency detected - consider speed optimizations")

        if self.global_stats["success_rate"] < 0.95:
            recommendations.append("Success rate below 95% - investigate failure modes")

        # Domain-specific recommendations
        for domain_name, metrics in summary["domain_performance"].items():
            if metrics["avg_reward"] < 0.6:
                recommendations.append(f"{domain_name}: Low average reward - review decision logic")
            if metrics["avg_latency"] > 1000:
                recommendations.append(f"{domain_name}: High latency in domain - optimize execution")

        if not recommendations:
            recommendations.append("All systems performing well - no immediate optimizations needed")

        summary["recommendations"] = recommendations

        return summary


async def demo_orchestrator():
    """Demonstrate the multi-domain orchestrator."""

    orchestrator = MultiBanditOrchestrator()

    print("🚀 Multi-Domain Advanced Bandit Orchestrator Demo")
    print("=" * 60)

    # Demo scenarios
    scenarios = [
        {
            "name": "High Priority Enterprise Request",
            "context": GlobalContext(
                user_id="enterprise_user_001",
                session_id="sess_hp_001",
                timestamp=datetime.now(UTC),
                request_priority=0.9,
                resource_budget=1.0,
                latency_requirement=1000,
                quality_requirement=0.9,
                cost_sensitivity=0.3,
                previous_decisions={},
                performance_history={},
                user_satisfaction_trend=0.85,
                user_tier="enterprise",
                content_complexity=0.8,
                interaction_count=15,
                time_of_day=0.5,
            ),
        },
        {
            "name": "Cost-Sensitive Free User",
            "context": GlobalContext(
                user_id="free_user_001",
                session_id="sess_cs_001",
                timestamp=datetime.now(UTC),
                request_priority=0.3,
                resource_budget=0.5,
                latency_requirement=800,
                quality_requirement=0.6,
                cost_sensitivity=0.9,
                previous_decisions={},
                performance_history={},
                user_satisfaction_trend=0.65,
                user_tier="free",
                content_complexity=0.3,
                interaction_count=3,
                time_of_day=0.7,
            ),
        },
        {
            "name": "Speed-Critical Real-time Request",
            "context": GlobalContext(
                user_id="premium_user_001",
                session_id="sess_rt_001",
                timestamp=datetime.now(UTC),
                request_priority=0.7,
                resource_budget=0.8,
                latency_requirement=300,
                quality_requirement=0.7,
                cost_sensitivity=0.5,
                previous_decisions={},
                performance_history={},
                user_satisfaction_trend=0.75,
                user_tier="premium",
                content_complexity=0.5,
                interaction_count=8,
                time_of_day=0.3,
            ),
        },
    ]

    results = []

    for i, scenario in enumerate(scenarios):
        print(f"\n📋 Scenario {i + 1}: {scenario['name']}")
        print("-" * 40)

        # Generate decision plan
        plan = await orchestrator.orchestrate_decision(scenario["context"])

        print(f"Strategy: {plan.optimization_strategy}")
        print(f"Expected Quality: {plan.overall_quality_score:.3f}")
        print(f"Expected Latency: {plan.total_expected_latency:.0f}ms")
        print(f"Expected Cost: {plan.total_expected_cost:.1f}")

        print("\nDomain Decisions:")
        for domain, decision in plan.domain_decisions.items():
            print(f"  {domain}: {decision.decision} (confidence: {decision.confidence:.2f})")

        # Execute plan
        execution_result = await orchestrator.execute_plan(plan)

        print("\nExecution Results:")
        if execution_result["success"]:
            metrics = execution_result["actual_metrics"]
            print(f"  Actual Quality: {metrics['average_quality']:.3f}")
            print(f"  Actual Latency: {metrics['total_latency_ms']:.0f}ms")
            print(f"  Actual Cost: {metrics['total_cost']:.1f}")
            print(f"  Satisfaction: {metrics['overall_satisfaction']:.3f}")
        else:
            print(f"  ❌ Execution failed: {execution_result.get('error', 'Unknown error')}")

        results.append(
            {
                "scenario": scenario["name"],
                "plan": asdict(plan),
                "execution": execution_result,
            }
        )

        # Small delay between scenarios
        await asyncio.sleep(0.1)

    # Final performance summary
    print("\n📊 Performance Summary")
    print("=" * 40)

    summary = orchestrator.get_performance_summary()

    print(f"Total Requests: {summary['global_stats']['total_requests']}")
    print(f"Average Satisfaction: {summary['global_stats']['avg_satisfaction']:.3f}")
    print(f"Average Latency: {summary['global_stats']['avg_latency']:.0f}ms")
    print(f"Success Rate: {summary['global_stats']['success_rate']:.3f}")

    print("\nDomain Performance:")
    for domain, metrics in summary["domain_performance"].items():
        print(f"  {domain}:")
        print(f"    Avg Reward: {metrics['avg_reward']:.3f}")
        print(f"    Avg Latency: {metrics['avg_latency']:.0f}ms")
        print(f"    Success Rate: {metrics['success_rate']:.3f}")

    print("\n💡 Recommendations:")
    for rec in summary["recommendations"]:
        print(f"  • {rec}")

    # Save results
    output_file = Path("multi_domain_orchestrator_results.json")
    with open(output_file, "w") as f:
        json.dump(
            {
                "demo_results": results,
                "performance_summary": summary,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            f,
            indent=2,
            default=str,
        )

    print(f"\n📁 Results saved to: {output_file.absolute()}")
    print("\n✅ Multi-Domain Orchestrator Demo Complete!")


if __name__ == "__main__":
    asyncio.run(demo_orchestrator())
