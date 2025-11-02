"""Datamodels for Advanced Performance Analytics (split from facade)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class PerformanceTrend:
    """Represents a performance trend analysis."""

    metric_name: str
    time_period: str
    trend_direction: str  # "improving", "declining", "stable"
    change_rate: float  # Percentage change per unit time
    confidence_score: float  # 0.0 to 1.0
    forecast_next_period: float
    trend_stability: float  # How consistent the trend is
    data_points: list[float] = field(default_factory=list)


@dataclass
class PerformanceAnomaly:
    """Represents an anomaly in performance data."""

    timestamp: datetime
    metric_name: str
    expected_value: float
    actual_value: float
    severity: str  # "low", "medium", "high", "critical"
    anomaly_type: str  # "spike", "drop", "drift", "outlier"
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationRecommendation:
    """Represents an optimization recommendation."""

    category: str  # "performance", "cost", "quality", "reliability"
    priority: str  # "critical", "high", "medium", "low"
    title: str
    description: str
    expected_impact: str
    implementation_effort: str  # "low", "medium", "high"
    confidence_score: float  # 0.0 to 1.0
    supporting_data: dict[str, Any] = field(default_factory=dict)
    action_items: list[str] = field(default_factory=list)


@dataclass
class PerformanceForecast:
    """Represents a performance forecast."""

    metric_name: str
    forecast_horizon: int  # Number of periods ahead
    predicted_values: list[float]
    confidence_intervals: list[tuple[float, float]]  # (lower, upper) bounds
    forecast_accuracy: float  # Historical accuracy score
    model_type: str  # "linear", "polynomial", "exponential", "seasonal"
