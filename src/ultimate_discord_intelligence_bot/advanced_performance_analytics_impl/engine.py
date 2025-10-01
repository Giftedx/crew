"""Engine implementation for Advanced Performance Analytics (split from facade)."""

from __future__ import annotations

import json
import logging
from typing import Any

from core.time import default_utc_now
from ultimate_discord_intelligence_bot.enhanced_performance_monitor import (
    EnhancedPerformanceMonitor,
)
from ultimate_discord_intelligence_bot.performance_integration import (
    PerformanceIntegrationManager,
)

from .anomalies import detect_performance_anomalies
from .forecast import generate_performance_forecasts
from .health import (
    calculate_system_health_score,
    get_health_status,
    get_key_health_indicators,
    perform_comparative_analysis,
)
from .models import (
    OptimizationRecommendation,
    PerformanceAnomaly,
    PerformanceForecast,
    PerformanceTrend,
)
from .recommendations import generate_recommendations
from .reports import format_html_report, format_markdown_report
from .trends import analyze_performance_trends

logger = logging.getLogger(__name__)


class AdvancedPerformanceAnalytics:
    """Advanced analytics engine for performance monitoring data."""

    def __init__(
        self,
        enhanced_monitor: EnhancedPerformanceMonitor | None = None,
        integration_manager: PerformanceIntegrationManager | None = None,
    ):
        self.enhanced_monitor = enhanced_monitor or EnhancedPerformanceMonitor()
        self.integration_manager = integration_manager or PerformanceIntegrationManager()
        # Stores and config
        self.historical_trends: dict[str, list[PerformanceTrend]] = {}
        self.detected_anomalies: list[PerformanceAnomaly] = []
        self.active_recommendations: list[OptimizationRecommendation] = []
        self.performance_forecasts: dict[str, PerformanceForecast] = {}
        self.anomaly_sensitivity = 2.0
        self.trend_window_size = 20
        self.forecast_horizon = 5
        self.performance_baselines: dict[str, dict[str, float]] = {}

    async def analyze_comprehensive_performance(self, lookback_hours: int = 24) -> dict[str, Any]:
        """Perform comprehensive performance analysis using helper modules."""
        try:
            dashboard_data = await self.enhanced_monitor.generate_real_time_dashboard_data()

            trends = analyze_performance_trends(self, lookback_hours)
            anomalies = detect_performance_anomalies(self, lookback_hours)
            forecasts = generate_performance_forecasts(self)
            recommendations = generate_recommendations(trends, anomalies, dashboard_data)
            health_score = calculate_system_health_score(self, trends, anomalies, dashboard_data)
            comparative_insights = perform_comparative_analysis(self)

            return {
                "analysis_timestamp": default_utc_now().isoformat(),
                "lookback_hours": lookback_hours,
                "system_health": {
                    "overall_score": health_score,
                    "status": get_health_status(health_score),
                    "key_indicators": get_key_health_indicators(self),
                },
                "performance_trends": trends,
                "anomalies": {
                    "detected": len(anomalies),
                    "critical": len([a for a in anomalies if a.severity == "critical"]),
                    "recent": anomalies[-5:] if anomalies else [],
                },
                "forecasts": forecasts,
                "optimization_recommendations": {
                    "critical": [r for r in recommendations if r.priority == "critical"],
                    "high": [r for r in recommendations if r.priority == "high"],
                    "medium": [r for r in recommendations if r.priority == "medium"],
                    "total_recommendations": len(recommendations),
                },
                "comparative_insights": comparative_insights,
                "actionable_insights": self._generate_actionable_insights(trends, anomalies, recommendations),
            }
        except Exception as e:
            logger.error(f"Comprehensive performance analysis failed: {e}")
            return {"error": str(e), "timestamp": default_utc_now().isoformat()}

    def _generate_actionable_insights(
        self,
        trends: list[dict[str, Any]],
        anomalies: list[PerformanceAnomaly],
        recommendations: list[OptimizationRecommendation],
    ) -> list[str]:
        insights: list[str] = []
        try:
            declining_quality_trends = [
                t for t in trends if "quality" in t.get("metric_name", "") and t.get("trend_direction") == "declining"
            ]
            if declining_quality_trends:
                insights.append(
                    f"🔍 Quality declining in {len(declining_quality_trends)} agents - immediate attention needed"
                )
            recent_critical = [a for a in anomalies if a.severity == "critical"]
            if recent_critical:
                insights.append(
                    f"🚨 {len(recent_critical)} critical performance anomalies detected - investigate root causes"
                )
            critical_recs = [r for r in recommendations if r.priority == "critical"]
            if critical_recs:
                insights.append(f"⚡ {len(critical_recs)} critical optimizations available - high impact potential")
            if len(trends) > 0:
                stable_trends = [t for t in trends if t.get("trend_direction") == "stable"]
                if len(stable_trends) / len(trends) > 0.8:
                    insights.append("✅ System performance is stable - good baseline for optimization")
            if not insights:
                insights.append("📊 System operating within normal parameters - focus on proactive optimization")
        except Exception as e:
            logger.debug(f"Insights generation error: {e}")
            insights.append("⚠️ Unable to generate insights - check monitoring data availability")
        return insights

    # Convenience wrappers
    async def generate_analytics_report(self, format_type: str = "json") -> str:
        analysis = await self.analyze_comprehensive_performance()
        if format_type == "json":
            return json.dumps(analysis, indent=2, default=str)
        if format_type == "markdown":
            return format_markdown_report(analysis)
        if format_type == "html":
            return format_html_report(analysis)
        return json.dumps(analysis, indent=2, default=str)


async def run_comprehensive_analytics(lookback_hours: int = 24) -> dict[str, Any]:
    eng = AdvancedPerformanceAnalytics()
    return await eng.analyze_comprehensive_performance(lookback_hours)


async def generate_optimization_report(format_type: str = "markdown") -> str:
    eng = AdvancedPerformanceAnalytics()
    return await eng.generate_analytics_report(format_type)
