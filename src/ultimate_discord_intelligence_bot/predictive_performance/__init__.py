"""Predictive Performance package.

This package contains the modularized implementation of the predictive
performance insights engine. Public APIs are re-exported from
``ultimate_discord_intelligence_bot.predictive_performance_insights`` for
backwards compatibility.
"""

from __future__ import annotations

from .engine import PredictivePerformanceInsights, get_early_warning_alerts, run_predictive_analysis
from .models import (
    AlertSeverity,
    CapacityForecast,
    EarlyWarningAlert,
    ModelDriftAlert,
    PerformancePrediction,
    PredictionConfidence,
)

__all__ = [
    "PredictionConfidence",
    "AlertSeverity",
    "PerformancePrediction",
    "EarlyWarningAlert",
    "CapacityForecast",
    "ModelDriftAlert",
    "PredictivePerformanceInsights",
    "run_predictive_analysis",
    "get_early_warning_alerts",
]
