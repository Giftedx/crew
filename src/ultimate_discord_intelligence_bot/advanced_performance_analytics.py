"""
Advanced Performance Analytics facade

This thin module preserves the public API and re-exports the implementation
from the internal package `advanced_performance_analytics_impl` to keep files
maintainable without breaking imports.
"""
from __future__ import annotations
from platform.time import default_utc_now
from .advanced_performance_analytics_impl.engine import AdvancedPerformanceAnalytics, generate_optimization_report, run_comprehensive_analytics
from .advanced_performance_analytics_impl.models import OptimizationRecommendation, PerformanceAnomaly, PerformanceForecast, PerformanceTrend
__all__ = ['AdvancedPerformanceAnalytics', 'OptimizationRecommendation', 'PerformanceAnomaly', 'PerformanceForecast', 'PerformanceTrend', 'generate_optimization_report', 'run_comprehensive_analytics']
_ANALYTICS_FACADE_INIT_TS = default_utc_now()