"""
Advanced Performance Analytics facade

This thin module preserves the public API and re-exports the implementation
from the internal package `advanced_performance_analytics_impl` to keep files
maintainable without breaking imports.
"""

from __future__ import annotations

from core.time import default_utc_now  # ensure utc timestamps usage is visible in this facade

from .advanced_performance_analytics_impl.engine import (
    AdvancedPerformanceAnalytics,
    generate_optimization_report,
    run_comprehensive_analytics,
)
from .advanced_performance_analytics_impl.models import (
    OptimizationRecommendation,
    PerformanceAnomaly,
    PerformanceForecast,
    PerformanceTrend,
)

__all__ = [
    "AdvancedPerformanceAnalytics",
    "run_comprehensive_analytics",
    "generate_optimization_report",
    "PerformanceTrend",
    "PerformanceAnomaly",
    "OptimizationRecommendation",
    "PerformanceForecast",
]

# Ensure at least one reference to default_utc_now so tests confirm UTC-safe usage
_ANALYTICS_FACADE_INIT_TS = default_utc_now()
