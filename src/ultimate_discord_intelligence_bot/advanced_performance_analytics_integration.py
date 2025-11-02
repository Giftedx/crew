"""
Advanced Performance Analytics Integration

This module provides a unified interface to the complete Advanced Performance Analytics
ecosystem, integrating analytics, predictive insights, and optimization capabilities
into a cohesive system.

Key Features:
- Unified analytics dashboard combining all performance insights
- Coordinated execution of analytics, predictions, and optimizations
- Comprehensive reporting across all performance dimensions
- Automated performance management workflows
- Integration with existing monitoring infrastructure
"""

from __future__ import annotations

import asyncio
import logging
from platform.time import default_utc_now
from typing import TYPE_CHECKING, Any

from .advanced_performance_analytics import AdvancedPerformanceAnalytics
from .enhanced_performance_monitor import EnhancedPerformanceMonitor
from .performance_optimization_engine import PerformanceOptimizationEngine
from .predictive_performance_insights import PredictivePerformanceInsights


if TYPE_CHECKING:
    from datetime import datetime
logger = logging.getLogger(__name__)


class AdvancedPerformanceAnalyticsSystem:
    """Unified Advanced Performance Analytics System."""

    def __init__(self, enhanced_monitor: EnhancedPerformanceMonitor | None = None):
        """Initialize the integrated analytics system.

        Args:
            enhanced_monitor: Enhanced performance monitor instance
        """
        self.enhanced_monitor = enhanced_monitor or EnhancedPerformanceMonitor()
        self.analytics_engine = AdvancedPerformanceAnalytics(enhanced_monitor=self.enhanced_monitor)
        self.predictive_engine = PredictivePerformanceInsights(
            analytics_engine=self.analytics_engine, enhanced_monitor=self.enhanced_monitor
        )
        self.optimization_engine = PerformanceOptimizationEngine(
            analytics_engine=self.analytics_engine,
            predictive_engine=self.predictive_engine,
            enhanced_monitor=self.enhanced_monitor,
        )
        self.last_full_analysis: datetime | None = None
        self.system_insights: dict[str, Any] = {}

    async def run_comprehensive_performance_analysis(
        self, lookback_hours: int = 24, include_optimization: bool = False
    ) -> dict[str, Any]:
        """Run comprehensive performance analysis across all components.

        Args:
            lookback_hours: Hours of historical data to analyze
            include_optimization: Whether to include optimization execution

        Returns:
            Dict containing comprehensive analysis results
        """
        analysis_start = default_utc_now()
        try:
            logger.info("Starting comprehensive performance analysis")
            analytics_task = self.analytics_engine.analyze_comprehensive_performance(lookback_hours)
            predictive_task = self.predictive_engine.generate_comprehensive_predictions(12)
            analytics_results, predictive_results = await asyncio.gather(analytics_task, predictive_task)
            optimization_recommendations = await self.optimization_engine.get_optimization_status()
            optimization_results = None
            if include_optimization:
                optimization_results = await self.optimization_engine.execute_comprehensive_optimization()
            comprehensive_results = self._synthesize_results(
                analytics_results, predictive_results, optimization_recommendations, optimization_results
            )
            self.system_insights = comprehensive_results
            self.last_full_analysis = analysis_start
            analysis_duration = default_utc_now() - analysis_start
            comprehensive_results["analysis_metadata"] = {
                "analysis_duration_seconds": analysis_duration.total_seconds(),
                "analysis_timestamp": analysis_start.isoformat(),
                "components_analyzed": ["analytics", "predictive", "optimization"],
                "optimization_executed": include_optimization,
            }
            logger.info(f"Comprehensive analysis completed in {analysis_duration.total_seconds():.2f} seconds")
            return comprehensive_results
        except Exception as e:
            logger.error(f"Comprehensive performance analysis failed: {e}")
            return {"error": str(e), "analysis_timestamp": analysis_start.isoformat(), "partial_results": True}

    def _synthesize_results(
        self,
        analytics: dict[str, Any],
        predictive: dict[str, Any],
        optimization_status: dict[str, Any],
        optimization_results: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Synthesize results from all components into unified insights."""
        try:
            system_health_score = analytics.get("system_health", {}).get("overall_score", 0.5)
            prediction_reliability = predictive.get("reliability_score", 0.5)
            optimization_success_rate = optimization_status.get("recent_success_rate", 0.0)
            overall_score = (system_health_score + prediction_reliability + optimization_success_rate) / 3
            all_insights = []
            all_insights.extend(analytics.get("actionable_insights", []))
            if "actionable_recommendations" in predictive:
                all_insights.extend(
                    [
                        rec.get("title", "Predictive recommendation")
                        for rec in predictive["actionable_recommendations"][:3]
                    ]
                )
            priority_recommendations = []
            critical_analytics = analytics.get("optimization_recommendations", {}).get("critical", [])
            priority_recommendations.extend(
                [
                    {
                        "source": "analytics",
                        "priority": "critical",
                        "title": getattr(rec, "title", "Analytics Recommendation"),
                        "description": getattr(rec, "description", ""),
                        "category": getattr(rec, "category", "performance"),
                    }
                    for rec in critical_analytics[:2]
                ]
            )
            urgent_warnings = predictive.get("early_warnings", {}).get("active_warnings", [])
            critical_warnings = [
                w for w in urgent_warnings if hasattr(w, "severity") and w.severity.value in ["critical", "urgent"]
            ]
            priority_recommendations.extend(
                [
                    {
                        "source": "predictive",
                        "priority": "urgent",
                        "title": getattr(warning, "title", "Predictive Warning"),
                        "description": getattr(warning, "description", ""),
                        "category": getattr(warning, "alert_type", "performance"),
                    }
                    for warning in critical_warnings[:2]
                ]
            )
            if optimization_results and "optimization_report" in optimization_results:
                next_focus = (
                    optimization_results["optimization_report"]
                    .get("optimization_recommendations", {})
                    .get("next_focus_areas", [])
                )
                priority_recommendations.extend(
                    [
                        {
                            "source": "optimization",
                            "priority": "high",
                            "title": f"Focus on {area.replace('_', ' ').title()}"
                            "description": f"Optimization opportunity identified in {area}",
                            "category": area,
                        }
                        for area in next_focus[:2]
                    ]
                )
            status_indicators = {
                "analytics_health": "healthy" if system_health_score > 0.7 else "degraded",
                "prediction_confidence": "high"
                if prediction_reliability > 0.8
                else "medium"
                if prediction_reliability > 0.6
                else "low",
                "optimization_effectiveness": "effective"
                if optimization_success_rate > 0.8
                else "moderate"
                if optimization_success_rate > 0.6
                else "needs_improvement",
            }
            return {
                "executive_summary": {
                    "overall_performance_score": overall_score,
                    "system_status": "excellent"
                    if overall_score > 0.8
                    else "good"
                    if overall_score > 0.6
                    else "needs_attention",
                    "key_insights_count": len(all_insights),
                    "priority_recommendations_count": len(priority_recommendations),
                    "analysis_completeness": "comprehensive",
                },
                "component_results": {
                    "analytics": {
                        "health_score": system_health_score,
                        "trends_analyzed": len(analytics.get("performance_trends", [])),
                        "anomalies_detected": analytics.get("anomalies", {}).get("detected", 0),
                        "recommendations_generated": analytics.get("optimization_recommendations", {}).get(
                            "total_recommendations", 0
                        ),
                    },
                    "predictive": {
                        "reliability_score": prediction_reliability,
                        "predictions_generated": predictive.get("performance_predictions", {}).get(
                            "total_predictions", 0
                        ),
                        "early_warnings": predictive.get("early_warnings", {}).get("total_warnings", 0),
                        "forecast_accuracy": predictive.get("prediction_confidence", {}).get("confidence_score", 0.0),
                    },
                    "optimization": {
                        "engine_status": optimization_status.get("engine_status", "inactive"),
                        "success_rate": optimization_success_rate,
                        "active_optimizations": optimization_status.get("active_optimizations", 0),
                        "results": optimization_results.get("successful_optimizations", 0)
                        if optimization_results
                        else 0,
                    },
                },
                "system_insights": {
                    "key_insights": all_insights[:10],
                    "performance_trends": self._extract_trend_summary(analytics),
                    "predictive_alerts": self._extract_alert_summary(predictive),
                    "optimization_opportunities": self._extract_optimization_summary(optimization_results),
                },
                "priority_recommendations": sorted(
                    priority_recommendations,
                    key=lambda x: {"critical": 3, "urgent": 3, "high": 2, "medium": 1}.get(x["priority"], 0),
                    reverse=True,
                )[:5],
                "status_indicators": status_indicators,
                "detailed_results": {
                    "analytics_full": analytics,
                    "predictive_full": predictive,
                    "optimization_status_full": optimization_status,
                    "optimization_results_full": optimization_results,
                },
            }
        except Exception as e:
            logger.error(f"Results synthesis failed: {e}")
            return {
                "synthesis_error": str(e),
                "raw_results": {
                    "analytics": analytics,
                    "predictive": predictive,
                    "optimization_status": optimization_status,
                    "optimization_results": optimization_results,
                },
            }

    def _extract_trend_summary(self, analytics: dict[str, Any]) -> dict[str, Any]:
        """Extract trend summary from analytics results."""
        try:
            trends = analytics.get("performance_trends", [])
            if not trends:
                return {"status": "no_trends_available"}
            improving_trends = [t for t in trends if t.get("trend_direction") == "improving"]
            declining_trends = [t for t in trends if t.get("trend_direction") == "declining"]
            stable_trends = [t for t in trends if t.get("trend_direction") == "stable"]
            return {
                "total_trends": len(trends),
                "improving": len(improving_trends),
                "declining": len(declining_trends),
                "stable": len(stable_trends),
                "trend_health": "good"
                if len(improving_trends) > len(declining_trends)
                else "concerning"
                if len(declining_trends) > len(improving_trends)
                else "stable",
                "key_declining_metrics": [t.get("metric_name", "") for t in declining_trends[:3]],
            }
        except Exception as e:
            logger.debug(f"Trend summary extraction error: {e}")
            return {"status": "extraction_error", "error": str(e)}

    def _extract_alert_summary(self, predictive: dict[str, Any]) -> dict[str, Any]:
        """Extract alert summary from predictive results."""
        try:
            warnings = predictive.get("early_warnings", {})
            total_warnings = warnings.get("total_warnings", 0)
            critical_warnings = warnings.get("critical", 0)
            urgent_warnings = warnings.get("urgent", 0)
            alert_level = (
                "high" if critical_warnings + urgent_warnings > 0 else "medium" if total_warnings > 2 else "low"
            )
            return {
                "total_alerts": total_warnings,
                "critical_alerts": critical_warnings,
                "urgent_alerts": urgent_warnings,
                "alert_level": alert_level,
                "requires_immediate_attention": critical_warnings + urgent_warnings > 0,
                "capacity_alerts": predictive.get("capacity_forecasts", {}).get("breach_alerts", 0),
            }
        except Exception as e:
            logger.debug(f"Alert summary extraction error: {e}")
            return {"status": "extraction_error", "error": str(e)}

    def _extract_optimization_summary(self, optimization_results: dict[str, Any] | None) -> dict[str, Any]:
        """Extract optimization summary from optimization results."""
        try:
            if not optimization_results:
                return {"status": "no_optimization_executed"}
            execution_summary = optimization_results.get("optimization_report", {}).get("execution_summary", {})
            performance_improvements = optimization_results.get("optimization_report", {}).get(
                "performance_improvements", {}
            )
            return {
                "optimizations_executed": execution_summary.get("successful_executions", 0),
                "success_rate": execution_summary.get("success_rate", 0.0),
                "performance_gains": list(performance_improvements.keys()),
                "optimization_effectiveness": "high"
                if execution_summary.get("success_rate", 0) > 0.8
                else "moderate"
                if execution_summary.get("success_rate", 0) > 0.5
                else "low",
                "next_cycle_recommended": optimization_results.get("next_optimization_cycle", ""),
            }
        except Exception as e:
            logger.debug(f"Optimization summary extraction error: {e}")
            return {"status": "extraction_error", "error": str(e)}

    async def get_real_time_dashboard_data(self) -> dict[str, Any]:
        """Get real-time dashboard data combining all components."""
        try:
            dashboard_data = await self.enhanced_monitor.generate_real_time_dashboard_data()
            optimization_status = await self.optimization_engine.get_optimization_status()
            dashboard_data["advanced_analytics"] = {
                "last_full_analysis": self.last_full_analysis.isoformat() if self.last_full_analysis else None,
                "system_insights_available": len(self.system_insights) > 0,
                "optimization_engine_active": optimization_status.get("engine_status") == "active",
                "predictive_capabilities": "enabled",
            }
            if self.system_insights:
                dashboard_data["recent_insights"] = {
                    "overall_score": self.system_insights.get("executive_summary", {}).get(
                        "overall_performance_score", 0.5
                    ),
                    "system_status": self.system_insights.get("executive_summary", {}).get("system_status", "unknown"),
                    "priority_recommendations": len(self.system_insights.get("priority_recommendations", [])),
                    "key_insights": self.system_insights.get("system_insights", {}).get("key_insights", [])[:3],
                }
            return dashboard_data
        except Exception as e:
            logger.error(f"Real-time dashboard data generation failed: {e}")
            return {"error": str(e), "timestamp": default_utc_now().isoformat()}

    async def generate_executive_report(self, format_type: str = "markdown") -> str:
        """Generate executive-level performance report.

        Args:
            format_type: Output format ("markdown", "html", "json")

        Returns:
            Formatted executive report
        """
        try:
            if not self.last_full_analysis or (default_utc_now() - self.last_full_analysis).total_seconds() > 6 * 3600:
                await self.run_comprehensive_performance_analysis()
            if format_type == "markdown":
                return self._format_executive_markdown_report()
            elif format_type == "html":
                return self._format_executive_html_report()
            else:
                return str(self.system_insights)
        except Exception as e:
            logger.error(f"Executive report generation failed: {e}")
            return f"Report generation failed: {e}"

    def _format_executive_markdown_report(self) -> str:
        """Format executive report as markdown."""
        try:
            insights = self.system_insights
            summary = insights.get("executive_summary", {})
            components = insights.get("component_results", {})
            recommendations = insights.get("priority_recommendations", [])
            report = f"# 🎯 Executive Performance Analytics Report\n\n**Generated**: {default_utc_now().strftime('%Y-%m-%d %H:%M:%S')}\n\n## 📊 Executive Summary\n\n**Overall Performance Score**: {summary.get('overall_performance_score', 0):.2f}/1.0\n**System Status**: {summary.get('system_status', 'unknown').title()}\n**Analysis Completeness**: {summary.get('analysis_completeness', 'partial').title()}\n\n### Key Metrics\n- **Performance Trends Analyzed**: {components.get('analytics', {}).get('trends_analyzed', 0)}\n- **Predictions Generated**: {components.get('predictive', {}).get('predictions_generated', 0)}\n- **Optimizations Success Rate**: {components.get('optimization', {}).get('success_rate', 0):.1%}\n\n## 🚨 Priority Recommendations\n\n"
            for i, rec in enumerate(recommendations[:3], 1):
                report += f"### {i}. {rec.get('title', 'Recommendation')} ({rec.get('priority', 'medium').title()} Priority)\n"
                report += f"**Source**: {rec.get('source', 'system').title()}\n"
                report += f"**Description**: {rec.get('description', 'No description available')}\n\n"
            report += "## 🔮 Predictive Insights\n\n"
            alert_summary = insights.get("system_insights", {}).get("predictive_alerts", {})
            report += f"- **Total Alerts**: {alert_summary.get('total_alerts', 0)}\n"
            report += f"- **Critical Alerts**: {alert_summary.get('critical_alerts', 0)}\n"
            report += f"- **Alert Level**: {alert_summary.get('alert_level', 'unknown').title()}\n\n"
            report += "## ⚙️ Optimization Status\n\n"
            opt_summary = insights.get("system_insights", {}).get("optimization_opportunities", {})
            report += (
                f"- **Engine Status**: {components.get('optimization', {}).get('engine_status', 'inactive').title()}\n"
            )
            report += f"- **Recent Success Rate**: {components.get('optimization', {}).get('success_rate', 0):.1%}\n"
            report += f"- **Optimization Effectiveness**: {opt_summary.get('optimization_effectiveness', 'unknown').title()}\n\n"
            report += "---\n*Report generated by Advanced Performance Analytics System*"
            return report
        except Exception as e:
            return f"Markdown report formatting failed: {e}"

    def _format_executive_html_report(self) -> str:
        """Format executive report as HTML."""
        try:
            insights = self.system_insights
            summary = insights.get("executive_summary", {})
            score = summary.get("overall_performance_score", 0)
            status = summary.get("system_status", "unknown")
            score_color = "green" if score > 0.8 else "orange" if score > 0.6 else "red"
            status_color = "green" if status == "excellent" else "orange" if status == "good" else "red"
            return f'\n<!DOCTYPE html>\n<html>\n<head>\n    <title>Executive Performance Analytics Report</title>\n    <style>\n        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}\n        .header {{ background: #343a40; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}\n        .metric-card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}\n        .score {{ font-size: 24px; font-weight: bold; color: {score_color}; }}\n        .status {{ font-size: 20px; font-weight: bold; color: {status_color}; }}\n        .recommendation {{ background: #fff3cd; padding: 15px; margin: 10px 0; border-left: 4px solid #ffc107; border-radius: 4px; }}\n        .insight {{ background: #d4edda; padding: 10px; margin: 10px 0; border-left: 4px solid #28a745; border-radius: 4px; }}\n        .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}\n    </style>\n</head>\n<body>\n    <div class="header">\n        <h1>🎯 Executive Performance Analytics Report</h1>\n    <p>Generated: {default_utc_now().strftime('%Y-%m-%d %H:%M:%S')}</p>\n    </div>\n\n    <div class="metric-card">\n        <h2>📊 Executive Summary</h2>\n        <div class="score">Overall Score: {score:.2f}/1.0</div>\n        <div class="status">Status: {status.title()}</div>\n    </div>\n\n    <div class="grid">\n        <div class="metric-card">\n            <h3>📈 Analytics</h3>\n            <p><strong>Health Score:</strong> {insights.get('component_results', {}).get('analytics', {}).get('health_score', 0):.2f}</p>\n            <p><strong>Trends:</strong> {insights.get('component_results', {}).get('analytics', {}).get('trends_analyzed', 0)}</p>\n        </div>\n        <div class="metric-card">\n            <h3>🔮 Predictive</h3>\n            <p><strong>Reliability:</strong> {insights.get('component_results', {}).get('predictive', {}).get('reliability_score', 0):.2f}</p>\n            <p><strong>Warnings:</strong> {insights.get('component_results', {}).get('predictive', {}).get('early_warnings', 0)}</p>\n        </div>\n        <div class="metric-card">\n            <h3>⚙️ Optimization</h3>\n            <p><strong>Success Rate:</strong> {insights.get('component_results', {}).get('optimization', {}).get('success_rate', 0):.1%}</p>\n            <p><strong>Status:</strong> {insights.get('component_results', {}).get('optimization', {}).get('engine_status', 'inactive').title()}</p>\n        </div>\n    </div>\n\n    <div class="metric-card">\n        <h2>🚨 Priority Recommendations</h2>\n        {''.join(f'\n        <div class="recommendation">\n            <strong>{rec.get('title', 'Recommendation')}</strong> ({rec.get('priority', 'medium').title()})\n            <br><small>Source: {rec.get('source', 'system').title()}</small>\n            <p>{rec.get('description', 'No description available')}</p>\n        </div>\n            ' for rec in insights.get('priority_recommendations', [])[:3])}\n    </div>\n</body>\n</html>\n            '
        except Exception as e:
            return f"<html><body><h1>HTML Report Error</h1><p>{e}</p></body></html>"


async def run_full_performance_analysis(lookback_hours: int = 24, include_optimization: bool = False) -> dict[str, Any]:
    """Run full performance analysis across all components.

    Args:
        lookback_hours: Hours of historical data to analyze
        include_optimization: Whether to include optimization execution

    Returns:
        Dict containing comprehensive analysis results
    """
    system = AdvancedPerformanceAnalyticsSystem()
    return await system.run_comprehensive_performance_analysis(lookback_hours, include_optimization)


async def get_performance_dashboard() -> dict[str, Any]:
    """Get real-time performance dashboard data.

    Returns:
        Dict containing dashboard data
    """
    system = AdvancedPerformanceAnalyticsSystem()
    return await system.get_real_time_dashboard_data()


async def generate_executive_performance_report(format_type: str = "markdown") -> str:
    """Generate executive performance report.

    Args:
        format_type: Output format ("markdown", "html", "json")

    Returns:
        Formatted executive report
    """
    system = AdvancedPerformanceAnalyticsSystem()
    return await system.generate_executive_report(format_type)
