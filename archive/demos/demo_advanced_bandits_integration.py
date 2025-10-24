#!/usr/bin/env python3
"""
Advanced Contextual Bandits Integration Demo

Comprehensive demonstration of DoublyRobust and OffsetTree algorithms
integrated with the Ultimate Discord Intelligence Bot ecosystem.

This demo showcases:
- Multi-domain bandit optimization (model routing, content analysis, user engagement)
- Real-time A/B testing with shadow evaluation
- Cross-domain learning and adaptation
- Production-ready monitoring and metrics
- Realistic Discord bot interaction scenarios

Usage:
    python demo_advanced_bandits_integration.py --scenario all
    python demo_advanced_bandits_integration.py --scenario model_routing
    python demo_advanced_bandits_integration.py --scenario content_analysis
"""

import argparse
import asyncio
import json
import logging
import random
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Core imports
from src.core.learning_engine import LearningEngine
from src.core.rl.advanced_config import (
    DoublyRobustConfig,
    OffsetTreeConfig,
    get_config_manager,
)
from src.core.rl.advanced_experiments import AdvancedBanditExperimentManager
from src.ultimate_discord_intelligence_bot.tenancy.context import (
    TenantContext,
    with_tenant,
)


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class DiscordMessage:
    """Simulated Discord message for demo."""

    user_id: str
    content: str
    channel_type: str  # text, voice, dm
    message_length: int
    complexity_score: float  # 0-1
    timestamp: datetime
    user_tier: str  # free, premium, enterprise
    previous_interactions: int


@dataclass
class UserContext:
    """Rich user context for bandit decisions."""

    user_tier_numeric: float  # 0=free, 0.5=premium, 1=enterprise
    time_of_day: float  # 0-1 normalized hour
    message_complexity: float  # 0-1 complexity score
    interaction_history: float  # 0-1 normalized interaction count
    channel_type_numeric: float  # 0=dm, 0.5=text, 1=voice
    message_length_normalized: float  # 0-1 normalized length
    day_of_week: float  # 0-1 normalized day
    user_engagement_score: float  # 0-1 predicted engagement


@dataclass
class DecisionOutcome:
    """Results of a bandit decision."""

    decision: str
    latency_ms: float
    quality_score: float
    user_satisfaction: float
    cost_cents: float
    timestamp: datetime
    context: UserContext


class AdvancedBanditsDemo:
    """Comprehensive demo of advanced contextual bandits."""

    def __init__(self, tenant_id: str = "demo", workspace_id: str = "integration"):
        self.tenant_context = TenantContext(tenant_id, workspace_id)
        self.learning_engine = LearningEngine()
        self.experiment_manager = AdvancedBanditExperimentManager()
        self.config_manager = get_config_manager()

        # Demo state
        self.demo_results = {
            "model_routing": [],
            "content_analysis": [],
            "user_engagement": [],
            "experiments": {},
            "performance_metrics": {},
        }

        # Simulation parameters
        self.model_options = [
            "gpt-4-turbo",  # High quality, high cost, medium speed
            "gpt-3.5-turbo",  # Medium quality, low cost, high speed
            "claude-3-opus",  # High quality, high cost, low speed
            "claude-3-sonnet",  # Medium quality, medium cost, medium speed
        ]

        self.content_processors = [
            "fast_nlp",  # Quick processing, basic quality
            "advanced_nlp",  # Slower, high quality analysis
            "specialized_tech",  # For technical content
            "multimedia_processor",  # For content with images/video
        ]

        self.engagement_strategies = [
            "immediate_response",  # Quick, direct responses
            "detailed_analysis",  # Thorough, comprehensive responses
            "interactive_followup",  # Engage with questions
            "educational_context",  # Provide learning opportunities
        ]

        logger.info(f"Advanced Bandits Demo initialized for tenant: {tenant_id}, workspace: {workspace_id}")

    async def setup_demo_environment(self):
        """Initialize the demo environment with advanced bandit configurations."""
        logger.info("Setting up advanced bandits demo environment...")

        with with_tenant(self.tenant_context):
            # Configure DoublyRobust for model routing
            model_routing_config = DoublyRobustConfig(
                alpha=1.5,  # Moderate exploration
                learning_rate=0.1,  # Standard learning rate
                lr_decay=0.999,  # Slow decay
                dim=8,  # 8 context features
                max_weight=4.0,  # Reasonable importance weight cap
            )

            # Configure OffsetTree for content analysis
            content_analysis_config = OffsetTreeConfig(
                max_depth=4,  # Allow deeper trees
                min_samples_split=20,  # Conservative splitting
                split_threshold=0.15,  # Moderate threshold
                split_strategy="information_gain",
                max_nodes=1000,  # Reasonable tree size
            )

            # Configure DoublyRobust for user engagement
            engagement_config = DoublyRobustConfig(
                alpha=2.0,  # Higher exploration for user preferences
                learning_rate=0.08,  # Slightly slower learning
                lr_decay=0.998,  # Standard decay
                dim=8,  # Same context dimension
                max_weight=5.0,  # Higher weight tolerance
            )

            # Set domain configurations
            self.config_manager.set_domain_config("model_routing", doubly_robust_config=model_routing_config)

            self.config_manager.set_domain_config("content_analysis", offset_tree_config=content_analysis_config)

            self.config_manager.set_domain_config("user_engagement", doubly_robust_config=engagement_config)

            # Register domains with appropriate policies
            self.learning_engine.register_domain("model_routing", policy="doubly_robust")
            self.learning_engine.register_domain("content_analysis", policy="offset_tree")
            self.learning_engine.register_domain("user_engagement", policy="doubly_robust")

            # Set up A/B experiments
            self.experiment_manager.register_advanced_bandit_experiment(
                domain="model_routing",
                baseline_policy="epsilon_greedy",
                advanced_policies={"doubly_robust": 0.6, "offset_tree": 0.2},
                shadow_samples=50,
                description="Model routing optimization experiment",
            )

            self.experiment_manager.register_advanced_bandit_experiment(
                domain="content_analysis",
                baseline_policy="thompson",
                advanced_policies={"offset_tree": 0.8},
                shadow_samples=30,
                description="Content analysis routing experiment",
            )

            self.experiment_manager.register_advanced_bandit_experiment(
                domain="user_engagement",
                baseline_policy="linucb",
                advanced_policies={"doubly_robust": 0.7},
                shadow_samples=40,
                description="User engagement optimization experiment",
            )

        logger.info("Demo environment setup complete!")

    def generate_realistic_discord_message(self) -> DiscordMessage:
        """Generate a realistic Discord message for simulation."""

        # Weighted user tiers (more free users)
        user_tier = random.choices(["free", "premium", "enterprise"], weights=[0.7, 0.25, 0.05])[0]

        # Message content patterns based on complexity
        complexity = random.random()
        if complexity < 0.3:
            # Simple messages
            content_templates = [
                "hi",
                "help",
                "what can you do?",
                "thanks",
                "ok",
                "how are you?",
                "good morning",
                "any updates?",
            ]
            content = random.choice(content_templates)
        elif complexity < 0.7:
            # Medium complexity
            content_templates = [
                "Can you help me understand how to use the Discord bot features?",
                "I'm looking for information about machine learning algorithms",
                "What's the best way to optimize my content strategy?",
                "How do I integrate this with my existing workflow?",
            ]
            content = random.choice(content_templates)
        else:
            # High complexity
            content_templates = [
                "I need a detailed analysis of the performance implications of using transformer models versus traditional NLP approaches in a production environment with high throughput requirements",
                "Can you provide a comprehensive comparison of different contextual bandit algorithms and their suitability for multi-armed bandit problems in e-commerce recommendation systems?",
                "I'm implementing a distributed system and need guidance on handling eventual consistency while maintaining strong performance characteristics across multiple data centers",
            ]
            content = random.choice(content_templates)

        channel_type = random.choices(["text", "voice", "dm"], weights=[0.6, 0.2, 0.2])[0]

        return DiscordMessage(
            user_id=f"user_{random.randint(1000, 9999)}",
            content=content,
            channel_type=channel_type,
            message_length=len(content),
            complexity_score=complexity,
            timestamp=datetime.now(UTC),
            user_tier=user_tier,
            previous_interactions=random.randint(0, 100),
        )

    def extract_user_context(self, message: DiscordMessage) -> UserContext:
        """Extract rich context features from Discord message."""

        # Convert categorical to numerical
        tier_mapping = {"free": 0.0, "premium": 0.5, "enterprise": 1.0}
        channel_mapping = {"dm": 0.0, "text": 0.5, "voice": 1.0}

        # Time-based features
        hour = message.timestamp.hour
        day_of_week = message.timestamp.weekday()

        # Engagement prediction (simulated)
        engagement_factors = [
            message.complexity_score,
            tier_mapping[message.user_tier],
            min(message.previous_interactions / 50, 1.0),
            1.0 - (abs(hour - 14) / 24),  # Peak engagement around 2 PM
        ]
        engagement_score = sum(engagement_factors) / len(engagement_factors)

        return UserContext(
            user_tier_numeric=tier_mapping[message.user_tier],
            time_of_day=hour / 24.0,
            message_complexity=message.complexity_score,
            interaction_history=min(message.previous_interactions / 100, 1.0),
            channel_type_numeric=channel_mapping[message.channel_type],
            message_length_normalized=min(message.message_length / 500, 1.0),
            day_of_week=day_of_week / 7.0,
            user_engagement_score=engagement_score,
        )

    def context_to_dict(self, context: UserContext) -> dict[str, float]:
        """Convert UserContext to dictionary for bandit algorithms."""
        return asdict(context)

    async def demonstrate_model_routing(self, message: DiscordMessage) -> DecisionOutcome:
        """Demonstrate intelligent model routing based on context."""

        context = self.extract_user_context(message)
        context_dict = self.context_to_dict(context)

        with with_tenant(self.tenant_context):
            # Get model recommendation
            selected_model = self.learning_engine.recommend("model_routing", context_dict, self.model_options)

        # Simulate model execution and measure outcomes

        # Model characteristics (simplified simulation)
        model_characteristics = {
            "gpt-4-turbo": {"quality_base": 0.9, "latency_base": 800, "cost_base": 20},
            "gpt-3.5-turbo": {
                "quality_base": 0.75,
                "latency_base": 300,
                "cost_base": 5,
            },
            "claude-3-opus": {
                "quality_base": 0.92,
                "latency_base": 1200,
                "cost_base": 25,
            },
            "claude-3-sonnet": {
                "quality_base": 0.8,
                "latency_base": 600,
                "cost_base": 12,
            },
        }

        char = model_characteristics[selected_model]

        # Add realistic variance and context-dependent adjustments
        complexity_penalty = message.complexity_score * 0.3
        quality_score = char["quality_base"] - complexity_penalty * 0.2 + random.gauss(0, 0.05)
        quality_score = max(0.1, min(1.0, quality_score))

        latency_ms = char["latency_base"] * (1 + complexity_penalty) + random.gauss(0, 100)
        latency_ms = max(100, latency_ms)

        cost_cents = char["cost_base"] * (1 + message.complexity_score * 0.5)

        # User satisfaction model (based on quality, latency, and user tier)
        satisfaction_factors = [
            quality_score,
            max(0, 1 - (latency_ms - 500) / 2000),  # Latency tolerance
            context.user_tier_numeric * 0.2 + 0.8,  # Higher tier users more satisfied
        ]
        user_satisfaction = sum(satisfaction_factors) / len(satisfaction_factors)
        user_satisfaction = max(0.1, min(1.0, user_satisfaction + random.gauss(0, 0.1)))

        outcome = DecisionOutcome(
            decision=selected_model,
            latency_ms=latency_ms,
            quality_score=quality_score,
            user_satisfaction=user_satisfaction,
            cost_cents=cost_cents,
            timestamp=datetime.now(UTC),
            context=context,
        )

        # Calculate composite reward (multi-objective)
        latency_penalty = max(0, (latency_ms - 1000) / 1000)
        cost_penalty = cost_cents / 100
        reward = (
            0.4 * quality_score
            + 0.3 * user_satisfaction
            + 0.2 * max(0, 1 - latency_penalty)
            + 0.1 * max(0, 1 - cost_penalty)
        )

        # Record the outcome
        with with_tenant(self.tenant_context):
            self.learning_engine.record("model_routing", context_dict, selected_model, reward)

            # Record advanced metrics if using advanced algorithms
            if hasattr(self.learning_engine._policies["model_routing"], "get_state"):
                self.experiment_manager.record_advanced_metrics(
                    "advanced_bandits::model_routing",
                    "doubly_robust",
                    reward,
                    context_dict,
                    self.learning_engine._policies["model_routing"],
                )

        self.demo_results["model_routing"].append(
            {
                "message_id": f"msg_{len(self.demo_results['model_routing'])}",
                "selected_model": selected_model,
                "context": asdict(context),
                "outcome": asdict(outcome),
                "reward": reward,
                "timestamp": outcome.timestamp.isoformat(),
            }
        )

        logger.info(
            f"Model routing: {selected_model} -> Quality: {quality_score:.3f}, "
            f"Latency: {latency_ms:.0f}ms, Satisfaction: {user_satisfaction:.3f}, "
            f"Reward: {reward:.3f}"
        )

        return outcome

    async def demonstrate_content_analysis(self, message: DiscordMessage) -> DecisionOutcome:
        """Demonstrate intelligent content analysis routing."""

        context = self.extract_user_context(message)
        context_dict = self.context_to_dict(context)

        with with_tenant(self.tenant_context):
            # Get content processor recommendation
            selected_processor = self.learning_engine.recommend(
                "content_analysis", context_dict, self.content_processors
            )

        # Simulate content processing
        processor_characteristics = {
            "fast_nlp": {"quality_base": 0.6, "latency_base": 200, "accuracy": 0.75},
            "advanced_nlp": {
                "quality_base": 0.85,
                "latency_base": 800,
                "accuracy": 0.92,
            },
            "specialized_tech": {
                "quality_base": 0.9,
                "latency_base": 1000,
                "accuracy": 0.95,
            },
            "multimedia_processor": {
                "quality_base": 0.8,
                "latency_base": 1500,
                "accuracy": 0.88,
            },
        }

        char = processor_characteristics[selected_processor]

        # Adjust based on content complexity
        complexity_boost = message.complexity_score if "advanced" in selected_processor else 0
        quality_score = char["quality_base"] + complexity_boost * 0.1 + random.gauss(0, 0.05)
        quality_score = max(0.1, min(1.0, quality_score))

        latency_ms = char["latency_base"] * (1 + message.complexity_score * 0.3) + random.gauss(0, 50)
        latency_ms = max(50, latency_ms)

        # Processing cost (simulated)
        cost_cents = {
            "fast_nlp": 2,
            "advanced_nlp": 8,
            "specialized_tech": 12,
            "multimedia_processor": 15,
        }[selected_processor]

        # User satisfaction for content analysis
        accuracy_satisfaction = char["accuracy"]
        speed_satisfaction = max(0, 1 - (latency_ms - 300) / 1000)
        user_satisfaction = (accuracy_satisfaction + speed_satisfaction) / 2
        user_satisfaction = max(0.1, min(1.0, user_satisfaction + random.gauss(0, 0.1)))

        outcome = DecisionOutcome(
            decision=selected_processor,
            latency_ms=latency_ms,
            quality_score=quality_score,
            user_satisfaction=user_satisfaction,
            cost_cents=cost_cents,
            timestamp=datetime.now(UTC),
            context=context,
        )

        # Calculate reward for content analysis
        reward = 0.5 * quality_score + 0.3 * user_satisfaction + 0.2 * max(0, 1 - (latency_ms - 500) / 1500)

        # Record the outcome
        with with_tenant(self.tenant_context):
            self.learning_engine.record("content_analysis", context_dict, selected_processor, reward)

            # Record advanced metrics for OffsetTree
            if hasattr(self.learning_engine._policies["content_analysis"], "tree_nodes"):
                self.experiment_manager.record_advanced_metrics(
                    "advanced_bandits::content_analysis",
                    "offset_tree",
                    reward,
                    context_dict,
                    self.learning_engine._policies["content_analysis"],
                )

        self.demo_results["content_analysis"].append(
            {
                "message_id": f"msg_{len(self.demo_results['content_analysis'])}",
                "selected_processor": selected_processor,
                "context": asdict(context),
                "outcome": asdict(outcome),
                "reward": reward,
                "timestamp": outcome.timestamp.isoformat(),
            }
        )

        logger.info(
            f"Content analysis: {selected_processor} -> Quality: {quality_score:.3f}, "
            f"Latency: {latency_ms:.0f}ms, Satisfaction: {user_satisfaction:.3f}, "
            f"Reward: {reward:.3f}"
        )

        return outcome

    async def demonstrate_user_engagement(self, message: DiscordMessage) -> DecisionOutcome:
        """Demonstrate user engagement optimization."""

        context = self.extract_user_context(message)
        context_dict = self.context_to_dict(context)

        with with_tenant(self.tenant_context):
            # Get engagement strategy recommendation
            selected_strategy = self.learning_engine.recommend(
                "user_engagement", context_dict, self.engagement_strategies
            )

        # Simulate engagement strategy execution
        strategy_characteristics = {
            "immediate_response": {"satisfaction_base": 0.7, "engagement_boost": 0.6},
            "detailed_analysis": {"satisfaction_base": 0.85, "engagement_boost": 0.9},
            "interactive_followup": {
                "satisfaction_base": 0.8,
                "engagement_boost": 0.85,
            },
            "educational_context": {"satisfaction_base": 0.75, "engagement_boost": 0.8},
        }

        char = strategy_characteristics[selected_strategy]

        # Adjust based on user context
        tier_boost = context.user_tier_numeric * 0.1
        complexity_match = 1.0 - abs(message.complexity_score - 0.5)  # Good for medium complexity

        if selected_strategy == "detailed_analysis" and message.complexity_score > 0.7:
            complexity_match = 1.0  # Perfect match for complex queries
        elif selected_strategy == "immediate_response" and message.complexity_score < 0.3:
            complexity_match = 1.0  # Perfect match for simple queries

        satisfaction_score = char["satisfaction_base"] + tier_boost + complexity_match * 0.1
        satisfaction_score = max(0.1, min(1.0, satisfaction_score + random.gauss(0, 0.05)))

        engagement_score = char["engagement_boost"] * context.user_engagement_score
        engagement_score = max(0.1, min(1.0, engagement_score + random.gauss(0, 0.1)))

        # Simulated latency based on strategy
        latency_map = {
            "immediate_response": 150,
            "detailed_analysis": 800,
            "interactive_followup": 400,
            "educational_context": 600,
        }
        latency_ms = latency_map[selected_strategy] + random.gauss(0, 50)
        latency_ms = max(50, latency_ms)

        outcome = DecisionOutcome(
            decision=selected_strategy,
            latency_ms=latency_ms,
            quality_score=engagement_score,
            user_satisfaction=satisfaction_score,
            cost_cents=5.0,  # Engagement strategies have minimal cost
            timestamp=datetime.now(UTC),
            context=context,
        )

        # Calculate reward for user engagement
        reward = 0.6 * satisfaction_score + 0.4 * engagement_score

        # Record the outcome
        with with_tenant(self.tenant_context):
            self.learning_engine.record("user_engagement", context_dict, selected_strategy, reward)

            # Record advanced metrics
            self.experiment_manager.record_advanced_metrics(
                "advanced_bandits::user_engagement",
                "doubly_robust",
                reward,
                context_dict,
                self.learning_engine._policies["user_engagement"],
            )

        self.demo_results["user_engagement"].append(
            {
                "message_id": f"msg_{len(self.demo_results['user_engagement'])}",
                "selected_strategy": selected_strategy,
                "context": asdict(context),
                "outcome": asdict(outcome),
                "reward": reward,
                "timestamp": outcome.timestamp.isoformat(),
            }
        )

        logger.info(
            f"User engagement: {selected_strategy} -> Satisfaction: {satisfaction_score:.3f}, "
            f"Engagement: {engagement_score:.3f}, Reward: {reward:.3f}"
        )

        return outcome

    async def run_integrated_scenario(self, num_interactions: int = 100):
        """Run a complete integrated scenario with multiple domains."""

        logger.info(f"Starting integrated scenario with {num_interactions} interactions...")

        start_time = time.time()

        for i in range(num_interactions):
            # Generate realistic Discord message
            message = self.generate_realistic_discord_message()

            # Run all three domains in parallel for each message
            tasks = [
                self.demonstrate_model_routing(message),
                self.demonstrate_content_analysis(message),
                self.demonstrate_user_engagement(message),
            ]

            await asyncio.gather(*tasks)

            # Log progress every 25 interactions
            if (i + 1) % 25 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                logger.info(f"Processed {i + 1}/{num_interactions} interactions ({rate:.1f} interactions/sec)")

        elapsed_time = time.time() - start_time
        total_interactions = num_interactions * 3  # 3 domains per message

        logger.info(
            f"Completed integrated scenario: {total_interactions} decisions "
            f"in {elapsed_time:.2f}s ({total_interactions / elapsed_time:.1f} decisions/sec)"
        )

    def generate_performance_report(self) -> dict[str, Any]:
        """Generate comprehensive performance analysis."""

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "summary": {},
            "domain_analysis": {},
            "experiment_results": {},
            "recommendations": [],
        }

        # Overall summary
        total_decisions = sum(len(results) for results in self.demo_results.values() if isinstance(results, list))
        report["summary"] = {
            "total_decisions": total_decisions,
            "domains_evaluated": len([k for k, v in self.demo_results.items() if isinstance(v, list) and v]),
            "average_decisions_per_domain": total_decisions / 3 if total_decisions > 0 else 0,
        }

        # Domain-specific analysis
        for domain, results in self.demo_results.items():
            if not isinstance(results, list) or not results:
                continue

            rewards = [r["reward"] for r in results]
            latencies = [r["outcome"]["latency_ms"] for r in results]
            satisfactions = [r["outcome"]["user_satisfaction"] for r in results]

            # Decision distribution
            decisions = [
                r.get("selected_model") or r.get("selected_processor") or r.get("selected_strategy") for r in results
            ]
            decision_counts = {}
            for decision in decisions:
                decision_counts[decision] = decision_counts.get(decision, 0) + 1

            report["domain_analysis"][domain] = {
                "total_decisions": len(results),
                "reward_stats": {
                    "mean": sum(rewards) / len(rewards),
                    "min": min(rewards),
                    "max": max(rewards),
                    "latest_10": rewards[-10:] if len(rewards) >= 10 else rewards,
                },
                "latency_stats": {
                    "mean_ms": sum(latencies) / len(latencies),
                    "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
                    "min_ms": min(latencies),
                    "max_ms": max(latencies),
                },
                "satisfaction_stats": {
                    "mean": sum(satisfactions) / len(satisfactions),
                    "min": min(satisfactions),
                    "max": max(satisfactions),
                },
                "decision_distribution": decision_counts,
                "top_performer": max(decision_counts.items(), key=lambda x: x[1])[0] if decision_counts else None,
            }

        # Experiment results
        with with_tenant(self.tenant_context):
            for domain in ["model_routing", "content_analysis", "user_engagement"]:
                try:
                    summary = self.experiment_manager.get_advanced_experiment_summary(domain)
                    if "error" not in summary:
                        report["experiment_results"][domain] = summary
                except Exception as e:
                    logger.warning(f"Could not get experiment summary for {domain}: {e}")

        # Generate recommendations
        recommendations = []

        for domain, analysis in report["domain_analysis"].items():
            if analysis["reward_stats"]["mean"] < 0.7:
                recommendations.append(f"{domain}: Consider tuning algorithm parameters - mean reward below 0.7")

            if analysis["latency_stats"]["p95_ms"] > 1000:
                recommendations.append(f"{domain}: High latency detected - p95 above 1000ms")

            if analysis["satisfaction_stats"]["mean"] < 0.75:
                recommendations.append(f"{domain}: Low user satisfaction - mean below 0.75")

            # Check for over-concentration on single decision
            total_decisions = analysis["total_decisions"]
            max_decision_count = (
                max(analysis["decision_distribution"].values()) if analysis["decision_distribution"] else 0
            )
            if total_decisions > 0 and max_decision_count / total_decisions > 0.8:
                recommendations.append(f"{domain}: Possible under-exploration - single option chosen >80% of time")

        if not recommendations:
            recommendations.append("All domains performing well - no immediate optimizations needed")

        report["recommendations"] = recommendations

        return report

    def save_demo_results(self, output_path: str = "advanced_bandits_demo_results.json"):
        """Save complete demo results to file."""

        # Generate performance report
        performance_report = self.generate_performance_report()

        # Combine all results
        complete_results = {
            "demo_metadata": {
                "timestamp": datetime.now(UTC).isoformat(),
                "tenant_id": self.tenant_context.tenant_id,
                "workspace_id": self.tenant_context.workspace_id,
                "total_interactions": sum(len(v) for v in self.demo_results.values() if isinstance(v, list)),
            },
            "raw_results": self.demo_results,
            "performance_analysis": performance_report,
            "configuration": {
                "model_options": self.model_options,
                "content_processors": self.content_processors,
                "engagement_strategies": self.engagement_strategies,
            },
        }

        # Save to file
        output_file = Path(output_path)
        output_file.write_text(json.dumps(complete_results, indent=2, default=str))

        logger.info(f"Demo results saved to: {output_file.absolute()}")
        return str(output_file.absolute())


async def main():
    """Main demo orchestrator."""

    parser = argparse.ArgumentParser(description="Advanced Contextual Bandits Integration Demo")
    parser.add_argument(
        "--scenario",
        choices=["all", "model_routing", "content_analysis", "user_engagement"],
        default="all",
        help="Demo scenario to run",
    )
    parser.add_argument(
        "--interactions",
        type=int,
        default=150,
        help="Number of interactions to simulate",
    )
    parser.add_argument(
        "--output",
        default="advanced_bandits_demo_results.json",
        help="Output file for results",
    )

    args = parser.parse_args()

    # Initialize demo
    demo = AdvancedBanditsDemo()

    # Setup environment
    await demo.setup_demo_environment()

    logger.info("🚀 Starting Advanced Contextual Bandits Demo")
    logger.info(f"   Scenario: {args.scenario}")
    logger.info(f"   Interactions: {args.interactions}")
    logger.info(f"   Output: {args.output}")

    # Run demo scenarios
    if args.scenario == "all":
        await demo.run_integrated_scenario(args.interactions)
    else:
        # Single domain demo
        for i in range(args.interactions):
            message = demo.generate_realistic_discord_message()

            if args.scenario == "model_routing":
                await demo.demonstrate_model_routing(message)
            elif args.scenario == "content_analysis":
                await demo.demonstrate_content_analysis(message)
            elif args.scenario == "user_engagement":
                await demo.demonstrate_user_engagement(message)

            if (i + 1) % 50 == 0:
                logger.info(f"Completed {i + 1}/{args.interactions} {args.scenario} decisions")

    # Generate and save results
    results_path = demo.save_demo_results(args.output)

    # Display summary
    report = demo.generate_performance_report()

    print("\n" + "=" * 80)
    print("🎯 ADVANCED CONTEXTUAL BANDITS DEMO COMPLETE")
    print("=" * 80)

    print("\n📊 Summary:")
    print(f"   Total Decisions: {report['summary']['total_decisions']}")
    print(f"   Domains Evaluated: {report['summary']['domains_evaluated']}")

    print("\n🎭 Domain Performance:")
    for domain, analysis in report["domain_analysis"].items():
        print(f"   {domain}:")
        print(f"      Decisions: {analysis['total_decisions']}")
        print(f"      Avg Reward: {analysis['reward_stats']['mean']:.3f}")
        print(f"      Avg Latency: {analysis['latency_stats']['mean_ms']:.0f}ms")
        print(f"      Avg Satisfaction: {analysis['satisfaction_stats']['mean']:.3f}")
        print(f"      Top Choice: {analysis['top_performer']}")

    print("\n💡 Recommendations:")
    for rec in report["recommendations"]:
        print(f"   • {rec}")

    print(f"\n📁 Results saved to: {results_path}")
    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    # Set up environment variables for demo
    import os

    os.environ.update(
        {
            "ENABLE_RL_ADVANCED": "true",
            "ENABLE_RL_SHADOW_EVAL": "true",
            "ENABLE_RL_MONITORING": "true",
            "ENABLE_EXPERIMENT_HARNESS": "true",
            "RL_ROLLOUT_PERCENTAGE": "1.0",  # Full rollout for demo
            "RL_ROLLOUT_DOMAINS": "model_routing,content_analysis,user_engagement",
        }
    )

    asyncio.run(main())
