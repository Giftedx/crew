from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PerformanceMetric:
    """Performance metric for agent evaluation."""

    metric_name: str
    target_value: float
    actual_value: float
    trend: str  # "improving", "stable", "declining", or "insufficient_data"
    confidence: float
    last_updated: str


@dataclass
class ToolUsagePattern:
    """Tool usage pattern analysis."""

    tool_name: str
    usage_frequency: int
    success_rate: float
    average_quality_score: float
    common_sequences: list[str]
    error_patterns: list[str]


@dataclass
class AIRoutingMetrics:
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
class AgentPerformanceReport:
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


__all__ = [
    "PerformanceMetric",
    "ToolUsagePattern",
    "AIRoutingMetrics",
    "AgentPerformanceReport",
]
