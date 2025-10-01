"""Performance baselines and monitoring configuration for the Ultimate Discord Intelligence Bot.

This module establishes performance targets, baselines, and monitoring thresholds
for key system metrics to ensure optimal performance and reliability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PerformanceTier(Enum):
    """Performance tiers for different operational contexts."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class MetricCategory(Enum):
    """Categories of metrics for organization and alerting."""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    RELIABILITY = "reliability"
    RESOURCE = "resource"
    COST = "cost"
    QUALITY = "quality"


@dataclass
class MetricBaseline:
    """Defines acceptable performance ranges for a specific metric."""

    name: str
    category: MetricCategory
    description: str

    # Performance targets
    target_value: float
    acceptable_range_min: float
    acceptable_range_max: float

    # Alerting thresholds
    warning_threshold: float  # Triggers warning alerts
    critical_threshold: float  # Triggers critical alerts

    # Measurement configuration
    unit: str = "units"
    higher_is_better: bool = True  # For metrics where higher values are better

    def is_acceptable(self, value: float) -> bool:
        """Check if a metric value is within acceptable range."""
        return self.acceptable_range_min <= value <= self.acceptable_range_max

    def get_alert_level(self, value: float) -> str:
        """Determine alert level for a metric value."""
        if not self.is_acceptable(value):
            return "critical"
        elif value >= self.warning_threshold:
            return "warning"
        return "normal"


@dataclass
class PerformanceBaselineConfig:
    """Comprehensive performance baseline configuration."""

    tier: PerformanceTier
    metrics: dict[str, MetricBaseline] = field(default_factory=dict)

    def get_baseline(self, metric_name: str) -> MetricBaseline | None:
        """Get baseline configuration for a specific metric."""
        return self.metrics.get(metric_name)

    def get_metrics_by_category(self, category: MetricCategory) -> dict[str, MetricBaseline]:
        """Get all metrics for a specific category."""
        return {name: baseline for name, baseline in self.metrics.items() if baseline.category == category}

    def validate_metric(self, metric_name: str, value: float) -> dict[str, Any]:
        """Validate a metric value against its baseline."""
        baseline = self.get_baseline(metric_name)
        if not baseline:
            return {"valid": False, "error": f"No baseline configured for metric: {metric_name}"}

        is_acceptable = baseline.is_acceptable(value)
        alert_level = baseline.get_alert_level(value)

        return {
            "valid": True,
            "metric_name": metric_name,
            "value": value,
            "baseline": baseline,
            "is_acceptable": is_acceptable,
            "alert_level": alert_level,
            "performance_score": self._calculate_performance_score(baseline, value),
        }

    def _calculate_performance_score(self, baseline: MetricBaseline, value: float) -> float:
        """Calculate performance score (0-100) for a metric value."""
        if baseline.higher_is_better:
            if value >= baseline.target_value:
                return 100.0
            elif value <= baseline.acceptable_range_min:
                return 0.0
            else:
                # Linear interpolation between min and target
                return (
                    (value - baseline.acceptable_range_min) / (baseline.target_value - baseline.acceptable_range_min)
                ) * 100.0
        else:
            if value <= baseline.target_value:
                return 100.0
            elif value >= baseline.acceptable_range_max:
                return 0.0
            else:
                # Linear interpolation between target and max
                return (
                    (baseline.acceptable_range_max - value) / (baseline.acceptable_range_max - baseline.target_value)
                ) * 100.0


# Production Performance Baselines
PRODUCTION_BASELINES = PerformanceBaselineConfig(
    tier=PerformanceTier.PRODUCTION,
    metrics={
        # Latency Metrics
        "http_request_latency_seconds": MetricBaseline(
            name="http_request_latency_seconds",
            category=MetricCategory.LATENCY,
            description="HTTP request response time",
            target_value=2.0,
            acceptable_range_min=0.1,
            acceptable_range_max=10.0,
            warning_threshold=5.0,
            critical_threshold=8.0,
            unit="seconds",
            higher_is_better=False,
        ),
        "pipeline_total_duration_seconds": MetricBaseline(
            name="pipeline_total_duration_seconds",
            category=MetricCategory.LATENCY,
            description="End-to-end pipeline execution time",
            target_value=30.0,
            acceptable_range_min=1.0,
            acceptable_range_max=120.0,
            warning_threshold=60.0,
            critical_threshold=90.0,
            unit="seconds",
            higher_is_better=False,
        ),
        "llm_latency_seconds": MetricBaseline(
            name="llm_latency_seconds",
            category=MetricCategory.LATENCY,
            description="LLM API response time",
            target_value=5.0,
            acceptable_range_min=0.5,
            acceptable_range_max=15.0,
            warning_threshold=10.0,
            critical_threshold=12.0,
            unit="seconds",
            higher_is_better=False,
        ),
        # Throughput Metrics
        "requests_per_minute": MetricBaseline(
            name="requests_per_minute",
            category=MetricCategory.THROUGHPUT,
            description="System throughput",
            target_value=60.0,
            acceptable_range_min=10.0,
            acceptable_range_max=300.0,
            warning_threshold=30.0,
            critical_threshold=20.0,
            unit="requests/min",
            higher_is_better=True,
        ),
        # Reliability Metrics
        "pipeline_success_rate": MetricBaseline(
            name="pipeline_success_rate",
            category=MetricCategory.RELIABILITY,
            description="Pipeline execution success rate",
            target_value=0.95,
            acceptable_range_min=0.85,
            acceptable_range_max=1.0,
            warning_threshold=0.90,
            critical_threshold=0.80,
            unit="ratio",
            higher_is_better=True,
        ),
        "http_error_rate": MetricBaseline(
            name="http_error_rate",
            category=MetricCategory.RELIABILITY,
            description="HTTP request error rate",
            target_value=0.05,
            acceptable_range_min=0.0,
            acceptable_range_max=0.20,
            warning_threshold=0.10,
            critical_threshold=0.15,
            unit="ratio",
            higher_is_better=False,
        ),
        # Resource Metrics
        "memory_usage_percent": MetricBaseline(
            name="memory_usage_percent",
            category=MetricCategory.RESOURCE,
            description="System memory utilization",
            target_value=70.0,
            acceptable_range_min=0.0,
            acceptable_range_max=90.0,
            warning_threshold=80.0,
            critical_threshold=85.0,
            unit="percent",
            higher_is_better=False,
        ),
        "cpu_usage_percent": MetricBaseline(
            name="cpu_usage_percent",
            category=MetricCategory.RESOURCE,
            description="System CPU utilization",
            target_value=60.0,
            acceptable_range_min=0.0,
            acceptable_range_max=85.0,
            warning_threshold=75.0,
            critical_threshold=80.0,
            unit="percent",
            higher_is_better=False,
        ),
        # Cost Metrics
        "cost_per_interaction_usd": MetricBaseline(
            name="cost_per_interaction_usd",
            category=MetricCategory.COST,
            description="Average cost per user interaction",
            target_value=0.10,
            acceptable_range_min=0.01,
            acceptable_range_max=0.50,
            warning_threshold=0.25,
            critical_threshold=0.40,
            unit="USD",
            higher_is_better=False,
        ),
        # Quality Metrics
        "cache_hit_rate": MetricBaseline(
            name="cache_hit_rate",
            category=MetricCategory.QUALITY,
            description="Cache hit rate for improved performance",
            target_value=0.80,
            acceptable_range_min=0.50,
            acceptable_range_max=1.0,
            warning_threshold=0.70,
            critical_threshold=0.60,
            unit="ratio",
            higher_is_better=True,
        ),
        "response_relevance_score": MetricBaseline(
            name="response_relevance_score",
            category=MetricCategory.QUALITY,
            description="LLM response relevance to user queries",
            target_value=0.85,
            acceptable_range_min=0.60,
            acceptable_range_max=1.0,
            warning_threshold=0.75,
            critical_threshold=0.65,
            unit="score",
            higher_is_better=True,
        ),
    },
)

# Development Performance Baselines (more lenient)
DEVELOPMENT_BASELINES = PerformanceBaselineConfig(
    tier=PerformanceTier.DEVELOPMENT,
    metrics={
        # More lenient latency requirements for development
        "http_request_latency_seconds": MetricBaseline(
            name="http_request_latency_seconds",
            category=MetricCategory.LATENCY,
            description="HTTP request response time",
            target_value=5.0,
            acceptable_range_min=0.1,
            acceptable_range_max=20.0,
            warning_threshold=10.0,
            critical_threshold=15.0,
            unit="seconds",
            higher_is_better=False,
        ),
        # More lenient reliability for development
        "pipeline_success_rate": MetricBaseline(
            name="pipeline_success_rate",
            category=MetricCategory.RELIABILITY,
            description="Pipeline execution success rate",
            target_value=0.80,
            acceptable_range_min=0.60,
            acceptable_range_max=1.0,
            warning_threshold=0.70,
            critical_threshold=0.50,
            unit="ratio",
            higher_is_better=True,
        ),
        # Keep other metrics similar to production but with wider tolerances
        **{
            k: v
            for k, v in PRODUCTION_BASELINES.metrics.items()
            if k not in ["http_request_latency_seconds", "pipeline_success_rate"]
        },
    },
)

# Staging Performance Baselines (between development and production)
STAGING_BASELINES = PerformanceBaselineConfig(
    tier=PerformanceTier.STAGING,
    metrics={
        **PRODUCTION_BASELINES.metrics,
        # Slightly more lenient than production
        "http_request_latency_seconds": MetricBaseline(
            name="http_request_latency_seconds",
            category=MetricCategory.LATENCY,
            description="HTTP request response time",
            target_value=3.0,
            acceptable_range_min=0.1,
            acceptable_range_max=12.0,
            warning_threshold=6.0,
            critical_threshold=9.0,
            unit="seconds",
            higher_is_better=False,
        ),
    },
)


def get_performance_baselines(tier: PerformanceTier | None = None) -> PerformanceBaselineConfig:
    """Get performance baselines for the specified tier.

    If no tier is specified, defaults to PRODUCTION for safety.
    """
    if tier is None:
        tier = PerformanceTier.PRODUCTION

    baseline_map = {
        PerformanceTier.DEVELOPMENT: DEVELOPMENT_BASELINES,
        PerformanceTier.STAGING: STAGING_BASELINES,
        PerformanceTier.PRODUCTION: PRODUCTION_BASELINES,
    }

    return baseline_map.get(tier, PRODUCTION_BASELINES)


def get_current_performance_tier() -> PerformanceTier:
    """Determine current performance tier from environment."""
    import os

    env = os.getenv("ENV", "").lower()
    if env in ("development", "dev"):
        return PerformanceTier.DEVELOPMENT
    elif env in ("staging", "stage"):
        return PerformanceTier.STAGING
    else:
        return PerformanceTier.PRODUCTION


__all__ = [
    "PerformanceTier",
    "MetricCategory",
    "MetricBaseline",
    "PerformanceBaselineConfig",
    "PRODUCTION_BASELINES",
    "DEVELOPMENT_BASELINES",
    "STAGING_BASELINES",
    "get_performance_baselines",
    "get_current_performance_tier",
]
