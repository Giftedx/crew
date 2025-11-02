"""Predictive Performance Insights Engine (facade).

This module now provides a thin compatibility layer that re-exports the
predictive performance insights APIs from the modular implementation under
``ultimate_discord_intelligence_bot.predictive_performance``. This preserves
import stability while dramatically improving maintainability.
"""

from __future__ import annotations

from .predictive_performance.engine import (
    PredictivePerformanceInsights,
    get_early_warning_alerts,
    run_predictive_analysis,
)
from .predictive_performance.models import (
    AlertSeverity,
    CapacityForecast,
    EarlyWarningAlert,
    ModelDriftAlert,
    PerformancePrediction,
    PredictionConfidence,
)


__all__ = [
    "AlertSeverity",
    "CapacityForecast",
    "EarlyWarningAlert",
    "ModelDriftAlert",
    "PerformancePrediction",
    "PredictionConfidence",
    "PredictivePerformanceInsights",
    "get_early_warning_alerts",
    "run_predictive_analysis",
]
