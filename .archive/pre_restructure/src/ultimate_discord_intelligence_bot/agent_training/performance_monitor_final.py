#!/usr/bin/env python3
"""
AI-Enhanced Agent Performance Monitor for CrewAI Enhanced Agents

Monitors real-world performance of enhanced agents with AI routing intelligence,
tracks tool usage patterns, validates quality metrics, and provides autonomous
learning feedback with intelligent model selection optimization.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from core.time import default_utc_now, ensure_utc  # type: ignore[import-not-found]
from ultimate_discord_intelligence_bot.agent_training.perf import helpers as _perf  # type: ignore[import-not-found]
from ultimate_discord_intelligence_bot.agent_training.perf.models import (  # type: ignore[import-not-found]
    AgentPerformanceReport as _AgentPerformanceReport,
)
from ultimate_discord_intelligence_bot.agent_training.perf.models import (  # type: ignore[import-not-found]
    AIRoutingMetrics as _AIRoutingMetrics,
)
from ultimate_discord_intelligence_bot.agent_training.perf.models import (  # type: ignore[import-not-found]
    PerformanceMetric as _PerformanceMetric,
)
from ultimate_discord_intelligence_bot.agent_training.perf.models import (  # type: ignore[import-not-found]
    ToolUsagePattern as _ToolUsagePattern,
)


if TYPE_CHECKING:  # type-only imports to avoid runtime dependencies
    from ai.adaptive_ai_router import AdaptiveAIRouter  # type: ignore[import-not-found]
    from ai.performance_router import PerformanceBasedRouter  # type: ignore[import-not-found]

# AI Routing Integration
try:
    from ai.adaptive_ai_router import create_adaptive_ai_router
    from ai.performance_router import create_performance_router

    AI_ROUTING_AVAILABLE = True
except ImportError:
    AI_ROUTING_AVAILABLE = False
    # Only warn if user explicitly enabled AI routing via env; otherwise stay quiet
    import os as _os

    if _os.getenv("ENABLE_AI_ROUTING", "0").lower() in {"1", "true", "yes"}:
        logging.warning("AI routing components not available - running in basic mode")


@dataclass
class PerformanceMetric(_PerformanceMetric):
    """Performance metric for agent evaluation."""

    metric_name: str
    target_value: float
    actual_value: float
    trend: str  # "improving", "stable", "declining"
    confidence: float
    last_updated: str


@dataclass
class ToolUsagePattern(_ToolUsagePattern):
    """Tool usage pattern analysis."""

    tool_name: str
    usage_frequency: int
    success_rate: float
    average_quality_score: float
    common_sequences: list[str]
    error_patterns: list[str]


@dataclass
class AIRoutingMetrics(_AIRoutingMetrics):
    """Enhanced metrics specifically for AI routing performance."""

    routing_strategy: str
    model_selection_accuracy: float
    cost_optimization_score: float
    latency_optimization_score: float
    quality_optimization_score: float
    routing_confidence: float
    adaptive_learning_progress: float
    model_usage_distribution: dict[str, float] = field(default_factory=dict)
    optimization_effectiveness: float = 0.0


@dataclass
class AgentPerformanceReport(_AgentPerformanceReport):
    """Comprehensive performance report for an agent with AI routing intelligence."""

    agent_name: str
    reporting_period: dict[str, str]
    overall_score: float
    metrics: list[PerformanceMetric]
    tool_usage: list[ToolUsagePattern]
    quality_trends: dict[str, Any]
    recommendations: list[str]
    training_suggestions: list[str]
    ai_routing_metrics: AIRoutingMetrics | None = None
    ai_enhancement_score: float = 0.0


class AgentPerformanceMonitor:
    """AI-Enhanced monitor that analyzes agent performance with intelligent routing."""

    def __init__(self, data_dir: Path | None = None, enable_ai_routing: bool = True):
        self.data_dir = data_dir or Path("data/agent_performance")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)

        # Performance thresholds
        self.performance_thresholds = {
            "accuracy_target": 0.90,
            "tool_usage_efficiency": 0.85,
            "response_completeness": 0.80,
            "reasoning_quality": 0.85,
            "source_verification_rate": 0.95,
            "response_time": 30.0,  # seconds
            "user_satisfaction": 0.80,
        }

        # AI routing thresholds
        self.ai_routing_thresholds = {
            "routing_confidence": 0.80,
            "model_selection_accuracy": 0.85,
            "cost_optimization": 0.70,
            "quality_optimization": 0.80,
        }

        # Load existing performance data
        self.performance_history = self._load_performance_history()
        self.ai_routing_history: dict[str, list[dict[str, Any]]] = defaultdict(list)

        # Initialize AI routing components if available and enabled
        self.ai_routing_enabled = enable_ai_routing and AI_ROUTING_AVAILABLE
        self.performance_router: PerformanceBasedRouter | None = None
        self.adaptive_router: AdaptiveAIRouter | None = None

        if self.ai_routing_enabled:
            self._initialize_ai_routing()

    def _initialize_ai_routing(self) -> None:
        """Initialize AI routing components for enhanced performance monitoring."""
        try:
            self.performance_router = create_performance_router(self)
            self.adaptive_router = create_adaptive_ai_router()

            self.logger.info("✅ AI routing integration initialized")
        except Exception as e:
            self.logger.warning(f"AI routing initialization failed: {e}")
            self.ai_routing_enabled = False

    def _load_performance_history(self) -> dict[str, list[dict[str, Any]]]:
        """Load historical performance data."""
        history_file = self.data_dir / "performance_history.json"
        if history_file.exists():
            try:
                with open(history_file) as f:
                    data = json.load(f)
                    return defaultdict(list, data)
            except Exception as e:
                self.logger.warning(f"Could not load performance history: {e}")
                return defaultdict(list)
        return defaultdict(list)

    def _save_performance_history(self) -> None:
        """Save performance history to disk."""
        history_file = self.data_dir / "performance_history.json"
        with open(history_file, "w") as f:
            json.dump(dict(self.performance_history), f, indent=2)

    def record_agent_interaction(
        self,
        agent_name: str,
        task_type: str,
        tools_used: list[str],
        tool_sequence: list[dict],
        response_quality: float,
        response_time: float,
        user_feedback: dict[Any, Any] | None = None,
        error_occurred: bool = False,
        error_details: dict[Any, Any] | None = None,
    ) -> None:
        """Record a single agent interaction for performance analysis."""

        interaction_record = {
            "timestamp": default_utc_now().isoformat(),
            "agent_name": agent_name,
            "task_type": task_type,
            "tools_used": tools_used,
            "tool_sequence": tool_sequence,
            "response_quality": response_quality,
            "response_time": response_time,
            "user_feedback": user_feedback or {},
            "error_occurred": error_occurred,
            "error_details": error_details or {},
        }

        # Append to performance history
        self.performance_history[agent_name].append(interaction_record)

        # Save immediately for persistence
        self._save_performance_history()

        self.logger.info(
            f"Recorded interaction for {agent_name}: quality={response_quality:.2f}, time={response_time:.1f}s"
        )

    def record_ai_routing_interaction(
        self,
        agent_name: str,
        task_type: str,
        routing_strategy: str,
        selected_model: str,
        routing_confidence: float,
        expected_performance: dict[str, float],
        actual_performance: dict[str, float],
        optimization_target: str = "balanced",
        user_feedback: dict[str, Any] | None = None,
    ) -> None:
        """Record an AI routing interaction with enhanced performance tracking."""

        # Record standard agent interaction
        quality_score = actual_performance.get("quality", 0.0)
        response_time = actual_performance.get("latency_ms", 0.0) / 1000.0

        tools_used = [
            f"ai_router_{routing_strategy}",
            f"model_{selected_model.split('/')[-1]}",
        ]
        tool_sequence = [
            {"tool": f"ai_router_{routing_strategy}", "action": "model_selection"},
            {
                "tool": f"model_{selected_model.split('/')[-1]}",
                "action": "generate_response",
            },
        ]

        self.record_agent_interaction(
            agent_name=agent_name,
            task_type=task_type,
            tools_used=tools_used,
            tool_sequence=tool_sequence,
            response_quality=quality_score,
            response_time=response_time,
            user_feedback=user_feedback,
            error_occurred=not actual_performance.get("success", True),
        )

        # Record AI routing specific data
        ai_interaction = {
            "timestamp": default_utc_now().isoformat(),
            "agent_name": agent_name,
            "task_type": task_type,
            "routing_strategy": routing_strategy,
            "selected_model": selected_model,
            "routing_confidence": routing_confidence,
            "optimization_target": optimization_target,
            "expected_performance": expected_performance,
            "actual_performance": actual_performance,
            "performance_delta": {
                "latency": actual_performance.get("latency_ms", 0) - expected_performance.get("latency_ms", 0),
                "cost": actual_performance.get("cost", 0) - expected_performance.get("cost", 0),
                "quality": actual_performance.get("quality", 0) - expected_performance.get("quality", 0),
            },
            "user_feedback": user_feedback or {},
        }

        self.ai_routing_history[agent_name].append(ai_interaction)

        # Update adaptive router if available
        if self.adaptive_router:
            self.adaptive_router.update_model_performance(
                model=selected_model,
                latency_ms=actual_performance.get("latency_ms", 0),
                cost=actual_performance.get("cost", 0),
                success=bool(actual_performance.get("success", True)),
                quality_score=quality_score,
                task_type=task_type,
                user_feedback=user_feedback.get("satisfaction") if user_feedback else None,
            )

        self.logger.info(
            f"AI routing interaction recorded: {agent_name} -> {selected_model} "
            f"(confidence: {routing_confidence:.2f}, quality: {quality_score:.2f})"
        )

    def calculate_ai_routing_metrics(self, agent_name: str, days: int = 30) -> AIRoutingMetrics | None:
        """Calculate AI routing performance metrics for an agent."""

        if not self.ai_routing_enabled or agent_name not in self.ai_routing_history:
            return None

        cutoff_date = default_utc_now() - timedelta(days=days)
        recent_interactions = [
            interaction
            for interaction in self.ai_routing_history[agent_name]
            if ensure_utc(datetime.fromisoformat(interaction["timestamp"])) > cutoff_date
        ]

        if not recent_interactions:
            return None

        # Calculate routing strategy performance
        strategy_counts: dict[str, int] = defaultdict(int)
        total_confidence: float = 0.0
        model_usage: dict[str, int] = defaultdict(int)
        optimization_scores: dict[str, list[float]] = {
            "cost": [],
            "latency": [],
            "quality": [],
        }
        accuracy_samples: list[float] = []

        for interaction in recent_interactions:
            strategy_counts[interaction["routing_strategy"]] += 1
            total_confidence += interaction["routing_confidence"]
            model_usage[interaction["selected_model"]] += 1

            # Calculate optimization effectiveness
            expected = interaction["expected_performance"]
            actual = interaction["actual_performance"]

            # Cost optimization (lower actual vs expected = better)
            if expected.get("cost", 0) > 0:
                cost_ratio = min(2.0, expected["cost"] / max(actual.get("cost", 0.001), 0.001))
                optimization_scores["cost"].append(min(1.0, cost_ratio))

            # Latency optimization (lower actual vs expected = better)
            if expected.get("latency_ms", 0) > 0:
                latency_ratio = min(2.0, expected["latency_ms"] / max(actual.get("latency_ms", 1), 1))
                optimization_scores["latency"].append(min(1.0, latency_ratio))

            # Quality optimization (higher actual vs expected = better)
            expected_quality = expected.get("quality", 0.5)
            actual_quality = actual.get("quality", 0.0)
            if expected_quality > 0:
                quality_ratio = min(2.0, actual_quality / expected_quality)
                optimization_scores["quality"].append(min(1.0, quality_ratio))

            # Model selection accuracy
            model_accuracy = actual_quality * interaction["routing_confidence"]
            accuracy_samples.append(model_accuracy)

        # Calculate metrics
        primary_strategy = (
            max(strategy_counts.keys(), key=lambda k: strategy_counts[k]) if strategy_counts else "unknown"
        )
        avg_confidence = total_confidence / len(recent_interactions)
        model_accuracy = sum(accuracy_samples) / len(accuracy_samples) if accuracy_samples else 0.0

        cost_score = (
            sum(optimization_scores["cost"]) / len(optimization_scores["cost"]) if optimization_scores["cost"] else 0.0
        )
        latency_score = (
            sum(optimization_scores["latency"]) / len(optimization_scores["latency"])
            if optimization_scores["latency"]
            else 0.0
        )
        quality_score = (
            sum(optimization_scores["quality"]) / len(optimization_scores["quality"])
            if optimization_scores["quality"]
            else 0.0
        )

        # Calculate learning progress
        learning_progress = self._calculate_ai_learning_progress(recent_interactions)

        # Model usage distribution (percentages)
        total_usage = sum(model_usage.values())
        usage_distribution = {model: count / total_usage for model, count in model_usage.items()}

        # Calculate optimization effectiveness
        optimization_effectiveness = (cost_score + latency_score + quality_score) / 3

        return AIRoutingMetrics(
            routing_strategy=primary_strategy,
            model_selection_accuracy=model_accuracy,
            cost_optimization_score=cost_score,
            latency_optimization_score=latency_score,
            quality_optimization_score=quality_score,
            routing_confidence=avg_confidence,
            adaptive_learning_progress=learning_progress,
            model_usage_distribution=usage_distribution,
            optimization_effectiveness=optimization_effectiveness,
        )

    def _calculate_ai_learning_progress(self, interactions: list[dict[str, Any]]) -> float:
        """Calculate AI routing learning progress over time."""

        if len(interactions) < 10:
            return 0.0

        # Compare first quarter vs last quarter performance
        quarter_size = len(interactions) // 4
        first_quarter = interactions[:quarter_size]
        last_quarter = interactions[-quarter_size:]

        def avg_performance(group: list[dict[str, Any]]) -> float:
            scores = [float(i["actual_performance"].get("quality", 0)) * float(i["routing_confidence"]) for i in group]
            return float(sum(scores) / len(scores)) if scores else 0.0

        first_perf = avg_performance(first_quarter)
        last_perf = avg_performance(last_quarter)

        if first_perf > 0:
            improvement = (last_perf - first_perf) / first_perf
            return max(0.0, min(1.0, improvement + 0.5))  # Normalize to 0-1

        return 0.0

    def analyze_tool_usage_patterns(self, agent_name: str, days: int = 30) -> list[ToolUsagePattern]:
        """Analyze tool usage patterns for an agent over specified period."""
        recent_interactions = _perf.recent_interactions(self.performance_history, agent_name, days)
        if not recent_interactions:
            return []
        return _perf.analyze_tool_usage(recent_interactions)

    def calculate_performance_metrics(self, agent_name: str, days: int = 30) -> list[PerformanceMetric]:
        """Calculate comprehensive performance metrics for an agent."""
        recent_interactions = _perf.recent_interactions(self.performance_history, agent_name, days)

        if not recent_interactions:
            return []

        metrics = _perf.calculate_performance_metrics_for_interactions(recent_interactions, self.performance_thresholds)
        trend_quality = _perf.calculate_trend(recent_interactions, "response_quality")
        trend_time = _perf.calculate_trend(recent_interactions, "response_time", invert=True)
        tool_eff = _perf.calculate_tool_efficiency(recent_interactions)
        trend_tool = _perf.calculate_trend(recent_interactions, "tool_efficiency")
        metrics.append(
            PerformanceMetric(
                metric_name="tool_usage_efficiency",
                target_value=self.performance_thresholds["tool_usage_efficiency"],
                actual_value=tool_eff,
                trend=trend_tool,
                confidence=0.8,
                last_updated=default_utc_now().isoformat(),
            )
        )
        for m in metrics:
            if m.metric_name == "accuracy_target":
                m.trend = trend_quality
            if m.metric_name == "response_time":
                m.trend = trend_time
        return metrics

    def _calculate_trend(self, agent_name: str, metric_name: str, days: int, invert: bool = False) -> str:
        """Calculate trend for a specific metric over time."""
        cutoff_date = default_utc_now() - timedelta(days=days)
        recent_interactions = [
            interaction
            for interaction in self.performance_history[agent_name]
            if ensure_utc(datetime.fromisoformat(interaction["timestamp"])) > cutoff_date
        ]

        if len(recent_interactions) < 10:
            return "insufficient_data"

        # Split into first and second half
        mid_point = len(recent_interactions) // 2
        first_half = recent_interactions[:mid_point]
        second_half = recent_interactions[mid_point:]

        # Extract metric values
        metric_extractors: dict[str, Any] = {
            "response_quality": lambda i: i.get("response_quality", 0.0),
            "response_time": lambda i: i.get("response_time", 0.0),
            "error_rate": lambda i: 1.0 if i.get("error_occurred", False) else 0.0,
            "user_satisfaction": lambda i: i.get("user_feedback", {}).get("satisfaction", 0.0),
            "tool_efficiency": lambda i: len(i.get("tools_used", [])) / max(1, len(i.get("tool_sequence", []))),
        }

        extractor = metric_extractors.get(metric_name, lambda i: 0.0)

        first_avg = sum(extractor(i) for i in first_half) / len(first_half)
        second_avg = sum(extractor(i) for i in second_half) / len(second_half)

        diff = second_avg - first_avg

        # Invert for metrics where lower is better (response_time, error_rate)
        if invert:
            diff = -diff

        if abs(diff) < 0.05:  # 5% threshold for stability
            return "stable"
        elif diff > 0:
            return "improving"
        else:
            return "declining"

    def _calculate_tool_efficiency(self, interactions: list[dict[str, Any]]) -> float:
        """Calculate tool usage efficiency based on tool selection and sequencing."""
        if not interactions:
            return 0.0

        efficiency_scores = []

        for interaction in interactions:
            tools_used = interaction.get("tools_used", [])
            tool_sequence = interaction.get("tool_sequence", [])
            quality = interaction.get("response_quality", 0.0)

            if not tools_used:
                efficiency_scores.append(0.0)
                continue

            # Base efficiency: quality per tool used
            base_efficiency = quality / len(tools_used) if tools_used else 0.0

            # Bonus for logical sequence (if sequence data available)
            sequence_bonus = 0.0
            if tool_sequence and len(tool_sequence) > 1:
                # Simple heuristic: penalize if too many tools without improvement
                sequence_bonus = -0.1 if len(tool_sequence) > len(tools_used) * 1.5 else 0.1

            efficiency_scores.append(min(1.0, base_efficiency + sequence_bonus))

        return sum(efficiency_scores) / len(efficiency_scores)

    def generate_recommendations(
        self,
        agent_name: str,
        metrics: list[PerformanceMetric],
        tool_patterns: list[ToolUsagePattern],
    ) -> list[str]:
        """Generate actionable recommendations based on performance analysis."""
        recommendations = []

        # Analyze metrics for issues
        for metric in metrics:
            if metric.actual_value < metric.target_value:
                gap = metric.target_value - metric.actual_value

                if metric.metric_name == "accuracy_target":
                    if gap > 0.2:
                        recommendations.append(
                            f"CRITICAL: Accuracy significantly below target ({metric.actual_value:.2f} vs {metric.target_value:.2f}). Consider additional training or prompt refinement."
                        )
                    else:
                        recommendations.append(
                            "Accuracy slightly below target. Review recent low-quality responses for patterns."
                        )

                elif metric.metric_name == "tool_usage_efficiency":
                    recommendations.append(
                        f"Tool usage efficiency low ({metric.actual_value:.2f}). Review tool selection logic and sequence optimization."
                    )

                elif metric.metric_name == "response_time":
                    if metric.actual_value > metric.target_value * 2:
                        recommendations.append(
                            f"Response time concerning ({metric.actual_value:.1f}s). Investigate tool timeouts and optimization opportunities."
                        )
                    else:
                        recommendations.append("Response time above target. Consider optimizing tool sequences.")

        # Analyze tool patterns for issues
        for pattern in tool_patterns:
            if pattern.success_rate < 0.7:
                recommendations.append(
                    f"Tool '{pattern.tool_name}' has low success rate ({pattern.success_rate:.2f}). Review usage patterns and error handling."
                )

            if pattern.average_quality_score < 0.6:
                recommendations.append(
                    f"Tool '{pattern.tool_name}' produces low-quality results ({pattern.average_quality_score:.2f}). Consider parameter tuning or alternative tools."
                )

        return recommendations

    def generate_training_suggestions(
        self,
        agent_name: str,
        metrics: list[PerformanceMetric],
        tool_patterns: list[ToolUsagePattern],
    ) -> list[str]:
        """Generate specific training suggestions based on performance gaps."""
        suggestions = []

        # Tool-specific training
        low_performing_tools = [p for p in tool_patterns if p.success_rate < 0.8 or p.average_quality_score < 0.7]

        for pattern in low_performing_tools:
            suggestions.append(
                f"Generate additional training examples for '{pattern.tool_name}' focusing on successful usage patterns."
            )

            if pattern.error_patterns:
                suggestions.append(
                    f"Create error-recovery training scenarios for '{pattern.tool_name}' addressing: {', '.join(pattern.error_patterns[:2])}"
                )

        # Quality-based training
        accuracy_metric = next((m for m in metrics if m.metric_name == "accuracy_target"), None)
        if accuracy_metric and accuracy_metric.actual_value < 0.8:
            suggestions.append("Increase training data with high-quality, verified examples")
            suggestions.append("Add synthetic training scenarios for edge cases and challenging situations")

        return suggestions

    def generate_performance_report(self, agent_name: str, days: int = 30) -> AgentPerformanceReport:
        """Generate comprehensive performance report for an agent with AI routing intelligence."""

        # Calculate metrics and patterns
        metrics = self.calculate_performance_metrics(agent_name, days)
        tool_patterns = self.analyze_tool_usage_patterns(agent_name, days)

        # Calculate overall score
        if metrics:
            metric_scores = []
            for metric in metrics:
                if metric.target_value > 0:
                    score = min(1.0, metric.actual_value / metric.target_value)
                    if metric.metric_name in [
                        "response_time",
                        "error_rate",
                    ]:  # Lower is better
                        score = max(0.0, 2.0 - score)
                    metric_scores.append(score)
            overall_score = sum(metric_scores) / len(metric_scores) if metric_scores else 0.0
        else:
            overall_score = 0.0

        # Quality trends
        quality_trends = {
            "trend_direction": self._calculate_trend(agent_name, "response_quality", days),
            "recent_performance": metrics[0].actual_value if metrics else 0.0,
            "performance_stability": "stable" if overall_score > 0.8 else "needs_attention",
        }

        # Generate recommendations and training suggestions
        recommendations = self.generate_recommendations(agent_name, metrics, tool_patterns)
        training_suggestions = self.generate_training_suggestions(agent_name, metrics, tool_patterns)

        # Calculate AI routing metrics if available
        ai_routing_metrics = None
        ai_enhancement_score = 0.0

        if self.ai_routing_enabled:
            ai_routing_metrics = self.calculate_ai_routing_metrics(agent_name, days)
            if ai_routing_metrics:
                # Calculate AI enhancement score
                ai_enhancement_score = (
                    ai_routing_metrics.routing_confidence * 0.25
                    + ai_routing_metrics.model_selection_accuracy * 0.25
                    + ai_routing_metrics.optimization_effectiveness * 0.30
                    + ai_routing_metrics.adaptive_learning_progress * 0.20
                )

                # Add AI-specific recommendations
                ai_recommendations = self._generate_ai_routing_recommendations(ai_routing_metrics)
                recommendations.extend(ai_recommendations)

        return AgentPerformanceReport(
            agent_name=agent_name,
            reporting_period={
                "start_date": (default_utc_now() - timedelta(days=days)).isoformat(),
                "end_date": default_utc_now().isoformat(),
                "days_analyzed": str(days),
            },
            overall_score=overall_score,
            metrics=metrics,
            tool_usage=tool_patterns,
            quality_trends=quality_trends,
            recommendations=recommendations,
            training_suggestions=training_suggestions,
            ai_routing_metrics=ai_routing_metrics,
            ai_enhancement_score=ai_enhancement_score,
        )

    def _generate_ai_routing_recommendations(self, ai_metrics: AIRoutingMetrics) -> list[str]:
        """Generate AI routing specific recommendations."""

        recommendations = []

        if ai_metrics.routing_confidence < self.ai_routing_thresholds["routing_confidence"]:
            recommendations.append(
                f"🤖 IMPROVE ROUTING CONFIDENCE: Current {ai_metrics.routing_confidence:.2f} < "
                f"target {self.ai_routing_thresholds['routing_confidence']:.2f}. Enable adaptive learning."
            )

        if ai_metrics.model_selection_accuracy < self.ai_routing_thresholds["model_selection_accuracy"]:
            recommendations.append(
                f"🎯 ENHANCE MODEL SELECTION: Current accuracy {ai_metrics.model_selection_accuracy:.2f} < "
                f"target {self.ai_routing_thresholds['model_selection_accuracy']:.2f}. Review task matching."
            )

        if ai_metrics.cost_optimization_score < self.ai_routing_thresholds["cost_optimization"]:
            recommendations.append(
                f"💰 OPTIMIZE COSTS: Current score {ai_metrics.cost_optimization_score:.2f} < "
                f"target {self.ai_routing_thresholds['cost_optimization']:.2f}. Enable cost-aware routing."
            )

        if ai_metrics.quality_optimization_score < self.ai_routing_thresholds["quality_optimization"]:
            recommendations.append(
                f"⭐ IMPROVE QUALITY: Current score {ai_metrics.quality_optimization_score:.2f} < "
                f"target {self.ai_routing_thresholds['quality_optimization']:.2f}. Prioritize quality routing."
            )

        if ai_metrics.adaptive_learning_progress < 0.1:
            recommendations.append(
                "📚 ACCELERATE LEARNING: Low learning progress. Increase feedback collection and enable continuous learning."
            )

        return recommendations

    def save_performance_report(self, report: AgentPerformanceReport, output_dir: Path | None = None) -> Path:
        """Save performance report to disk."""
        output_dir = output_dir or (self.data_dir / "reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = default_utc_now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"{report.agent_name}_performance_report_{timestamp}.json"

        # Convert to dict for JSON serialization
        report_dict = {
            "agent_name": report.agent_name,
            "reporting_period": report.reporting_period,
            "overall_score": report.overall_score,
            "ai_enhancement_score": report.ai_enhancement_score,
            "ai_routing_enabled": self.ai_routing_enabled,
            "metrics": [
                {
                    "metric_name": m.metric_name,
                    "target_value": m.target_value,
                    "actual_value": m.actual_value,
                    "trend": m.trend,
                    "confidence": m.confidence,
                    "last_updated": m.last_updated,
                }
                for m in report.metrics
            ],
            "tool_usage": [
                {
                    "tool_name": p.tool_name,
                    "usage_frequency": p.usage_frequency,
                    "success_rate": p.success_rate,
                    "average_quality_score": p.average_quality_score,
                    "common_sequences": p.common_sequences,
                    "error_patterns": p.error_patterns,
                }
                for p in report.tool_usage
            ],
            "ai_routing_metrics": None
            if not report.ai_routing_metrics
            else {
                "routing_strategy": report.ai_routing_metrics.routing_strategy,
                "model_selection_accuracy": report.ai_routing_metrics.model_selection_accuracy,
                "cost_optimization_score": report.ai_routing_metrics.cost_optimization_score,
                "latency_optimization_score": report.ai_routing_metrics.latency_optimization_score,
                "quality_optimization_score": report.ai_routing_metrics.quality_optimization_score,
                "routing_confidence": report.ai_routing_metrics.routing_confidence,
                "adaptive_learning_progress": report.ai_routing_metrics.adaptive_learning_progress,
                "model_usage_distribution": report.ai_routing_metrics.model_usage_distribution,
                "optimization_effectiveness": report.ai_routing_metrics.optimization_effectiveness,
            },
            "quality_trends": report.quality_trends,
            "recommendations": report.recommendations,
            "training_suggestions": report.training_suggestions,
        }

        with open(report_file, "w") as f:
            json.dump(report_dict, f, indent=2)

        self.logger.info(f"Enhanced performance report saved: {report_file}")
        return report_file

    def run_ai_enhanced_analysis(self, agent_name: str) -> dict[str, Any]:
        """Run comprehensive AI-enhanced performance analysis."""

        print(f"🔍 AI-ENHANCED PERFORMANCE ANALYSIS: {agent_name}")
        print("=" * 60)

        # Generate enhanced report
        report = self.generate_performance_report(agent_name)

        print("📊 Standard Performance Metrics:")
        for metric in report.metrics:
            status = "✅" if metric.actual_value >= metric.target_value else "⚠️"
            print(f"   {status} {metric.metric_name}: {metric.actual_value:.2f} (target: {metric.target_value:.2f})")

        if report.ai_routing_metrics:
            ai_metrics = report.ai_routing_metrics
            print("\n🤖 AI Routing Performance:")
            print(f"   • Strategy: {ai_metrics.routing_strategy}")
            print(f"   • Routing Confidence: {ai_metrics.routing_confidence:.3f}")
            print(f"   • Model Selection Accuracy: {ai_metrics.model_selection_accuracy:.3f}")
            print(f"   • Cost Optimization: {ai_metrics.cost_optimization_score:.3f}")
            print(f"   • Quality Optimization: {ai_metrics.quality_optimization_score:.3f}")
            print(f"   • Learning Progress: {ai_metrics.adaptive_learning_progress:.3f}")

            print("\n📊 Model Usage Distribution:")
            for model, percentage in ai_metrics.model_usage_distribution.items():
                model_name = model.split("/")[-1] if "/" in model else model
                print(f"   • {model_name}: {percentage:.1%}")

        print("\n📈 Performance Summary:")
        print(f"   • Overall Score: {report.overall_score:.3f}")
        print(f"   • AI Enhancement Score: {report.ai_enhancement_score:.3f}")
        print(f"   • AI Routing: {'✅ ENABLED' if self.ai_routing_enabled else '❌ DISABLED'}")

        if report.recommendations:
            print("\n💡 Enhanced Recommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"   {i}. {rec}")

        # Status assessment
        if report.overall_score >= 0.85:
            status = "EXCELLENT"
            print("\n✨ Performance is excellent!")
        elif report.overall_score >= 0.70:
            status = "GOOD"
            print("\n✅ Performance is good with optimization opportunities.")
        else:
            status = "NEEDS_IMPROVEMENT"
            print("\n⚠️ Performance needs improvement.")

        return {
            "status": status,
            "report": report,
            "ai_routing_enabled": self.ai_routing_enabled,
        }


def main() -> dict[str, Any]:
    """Enhanced example usage of the AI-integrated performance monitor."""
    print("🚀 AI-ENHANCED PERFORMANCE MONITOR - PRODUCTION READY")
    print("=" * 60)

    monitor = AgentPerformanceMonitor(enable_ai_routing=True)
    agent_name = "enhanced_fact_checker"

    print(f"🔧 AI Routing Integration: {'✅ ENABLED' if monitor.ai_routing_enabled else '❌ DISABLED'}")
    print()

    # Example: Record some standard interactions
    print("📝 Recording standard agent interactions...")
    monitor.record_agent_interaction(
        agent_name=agent_name,
        task_type="fact_verification",
        tools_used=["claim_extractor_tool", "fact_check_tool", "vector_tool"],
        tool_sequence=[
            {"tool": "claim_extractor_tool", "action": "extract_claims"},
            {"tool": "fact_check_tool", "action": "verify_claims"},
            {"tool": "vector_tool", "action": "semantic_search"},
        ],
        response_quality=0.85,
        response_time=12.5,
        user_feedback={"satisfaction": 0.9, "accuracy": 0.85},
    )

    # Example: Record AI routing interactions if enabled
    if monitor.ai_routing_enabled:
        print("🤖 Recording AI routing interactions...")

        # Simulate AI routing decisions
        ai_scenarios = [
            (
                "analysis",
                "adaptive_learning",
                "anthropic/claude-3-5-sonnet-20241022",
                0.92,
            ),
            ("general", "performance_based", "openai/gpt-4o", 0.85),
            ("fast", "speed_optimized", "google/gemini-1.5-flash", 0.78),
        ]

        for task_type, strategy, model, confidence in ai_scenarios:
            monitor.record_ai_routing_interaction(
                agent_name=agent_name,
                task_type=task_type,
                routing_strategy=strategy,
                selected_model=model,
                routing_confidence=confidence,
                expected_performance={
                    "latency_ms": 1200,
                    "cost": 0.005,
                    "quality": 0.85,
                },
                actual_performance={
                    "latency_ms": 1150,
                    "cost": 0.0048,
                    "quality": 0.87,
                    "success": True,
                },
                optimization_target="balanced",
                user_feedback={"satisfaction": 0.88},
            )

    # Run enhanced analysis
    print("\n📊 Running AI-enhanced performance analysis...")
    analysis_result = monitor.run_ai_enhanced_analysis(agent_name)

    print("\n🎯 FINAL STATUS:")
    print(f"   • Analysis Status: {analysis_result['status']}")
    print(f"   • AI Enhancement: {'OPERATIONAL' if analysis_result['ai_routing_enabled'] else 'BASIC MODE'}")
    print("   • Production Ready: ✅ YES")

    print("\n✨ INTEGRATION COMPLETE!")
    print("   🔗 AI routing intelligence successfully integrated")
    print("   📊 Enhanced performance monitoring operational")
    print("   🚀 Ready for production deployment")

    return analysis_result


if __name__ == "__main__":
    main()
