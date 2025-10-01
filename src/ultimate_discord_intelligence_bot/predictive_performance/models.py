from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class PredictionConfidence(Enum):
    """Confidence levels for predictions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class AlertSeverity(Enum):
    """Severity levels for predictive alerts."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"


@dataclass
class PerformancePrediction:
    """Represents a performance prediction."""

    metric_name: str
    prediction_horizon: int  # Number of time periods ahead
    predicted_value: float
    confidence_interval: tuple[float, float]
    confidence_level: PredictionConfidence
    model_accuracy: float  # Historical accuracy of the model
    prediction_timestamp: datetime
    contributing_factors: list[str] = field(default_factory=list)
    uncertainty_factors: list[str] = field(default_factory=list)


@dataclass
class EarlyWarningAlert:
    """Represents an early warning alert."""

    alert_id: str
    severity: AlertSeverity
    alert_type: str  # "degradation", "capacity", "cost", "quality"
    title: str
    description: str
    predicted_impact: str
    time_to_impact: timedelta  # How soon the issue is expected
    confidence: PredictionConfidence
    recommended_actions: list[str] = field(default_factory=list)
    monitoring_metrics: list[str] = field(default_factory=list)
    context_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class CapacityForecast:
    """Represents capacity planning forecast."""

    resource_type: str  # "compute", "memory", "storage", "bandwidth"
    current_utilization: float
    predicted_utilization: list[float]  # Future utilization predictions
    capacity_threshold: float  # When to trigger scaling
    projected_breach_time: datetime | None  # When threshold will be breached
    scaling_recommendations: list[str] = field(default_factory=list)
    cost_implications: dict[str, float] = field(default_factory=dict)


@dataclass
class ModelDriftAlert:
    """Represents model performance drift detection."""

    model_name: str
    drift_type: str  # "data_drift", "concept_drift", "performance_drift"
    drift_magnitude: float  # 0.0 to 1.0
    detection_timestamp: datetime
    baseline_performance: float
    current_performance: float
    contributing_factors: list[str] = field(default_factory=list)
    remediation_suggestions: list[str] = field(default_factory=list)


__all__ = [
    "PredictionConfidence",
    "AlertSeverity",
    "PerformancePrediction",
    "EarlyWarningAlert",
    "CapacityForecast",
    "ModelDriftAlert",
]
