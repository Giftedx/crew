"""
Advanced Performance Analytics Engine

This module provides sophisticated analytics capabilities that transform raw performance
monitoring data into actionable insights, predictions, and optimization recommendations.

Key Features:
- Predictive performance modeling
- Trend analysis and forecasting
- Anomaly detection and pattern recognition
- Automated optimization recommendations
- Comparative agent performance analysis
- System health prediction
- Cost optimization insights
"""

from __future__ import annotations

import json
import logging
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from core.time import default_utc_now
from scipy import stats

from .enhanced_performance_monitor import EnhancedPerformanceMonitor
from .performance_integration import PerformanceIntegrationManager

logger = logging.getLogger(__name__)


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


class AdvancedPerformanceAnalytics:
    """Advanced analytics engine for performance monitoring data."""

    def __init__(
        self,
        enhanced_monitor: EnhancedPerformanceMonitor | None = None,
        integration_manager: PerformanceIntegrationManager | None = None,
    ):
        """Initialize advanced analytics engine.

        Args:
            enhanced_monitor: Enhanced performance monitor instance
            integration_manager: Performance integration manager instance
        """
        self.enhanced_monitor = enhanced_monitor or EnhancedPerformanceMonitor()
        self.integration_manager = integration_manager or PerformanceIntegrationManager()

        # Analytics storage
        self.historical_trends: dict[str, list[PerformanceTrend]] = defaultdict(list)
        self.detected_anomalies: list[PerformanceAnomaly] = []
        self.active_recommendations: list[OptimizationRecommendation] = []
        self.performance_forecasts: dict[str, PerformanceForecast] = {}

        # Analytics configuration
        self.anomaly_sensitivity = 2.0  # Standard deviations for anomaly detection
        self.trend_window_size = 20  # Number of data points for trend analysis
        self.forecast_horizon = 5  # Number of periods to forecast ahead

        # Performance baselines
        self.performance_baselines: dict[str, dict[str, float]] = defaultdict(dict)

    async def analyze_comprehensive_performance(self, lookback_hours: int = 24) -> dict[str, Any]:
        """Perform comprehensive performance analysis.

        Args:
            lookback_hours: Hours of historical data to analyze

        Returns:
            Dict containing comprehensive performance analysis
        """
        try:
            # Gather current performance data
            dashboard_data = await self.enhanced_monitor.generate_real_time_dashboard_data()

            # Perform trend analysis
            trends = await self._analyze_performance_trends(lookback_hours)

            # Detect anomalies
            anomalies = await self._detect_performance_anomalies(lookback_hours)

            # Generate forecasts
            forecasts = await self._generate_performance_forecasts()

            # Create optimization recommendations
            recommendations = await self._generate_optimization_recommendations(trends, anomalies, dashboard_data)

            # Calculate system health score
            health_score = await self._calculate_system_health_score(trends, anomalies, dashboard_data)

            # Perform comparative analysis
            comparative_insights = await self._perform_comparative_analysis()

            return {
                "analysis_timestamp": default_utc_now().isoformat(),
                "lookback_hours": lookback_hours,
                "system_health": {
                    "overall_score": health_score,
                    "status": self._get_health_status(health_score),
                    "key_indicators": self._get_key_health_indicators(dashboard_data),
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

    async def _analyze_performance_trends(self, lookback_hours: int) -> list[dict[str, Any]]:
        """Analyze performance trends over time."""
        trends = []

        try:
            # Get historical performance data
            if hasattr(self.enhanced_monitor, "real_time_metrics"):
                for agent_name, agent_data in self.enhanced_monitor.real_time_metrics.items():
                    recent_interactions = agent_data.get("recent_interactions", [])

                    if len(recent_interactions) >= 10:  # Need sufficient data
                        # Analyze quality trend
                        quality_trend = self._analyze_metric_trend(
                            [i.get("response_quality", 0) for i in recent_interactions], f"{agent_name}_quality"
                        )
                        trends.append(self._trend_to_dict(quality_trend))

                        # Analyze response time trend
                        time_trend = self._analyze_metric_trend(
                            [i.get("response_time", 0) for i in recent_interactions], f"{agent_name}_response_time"
                        )
                        trends.append(self._trend_to_dict(time_trend))

                        # Analyze error rate trend
                        error_rates = []
                        window_size = 5
                        for i in range(window_size, len(recent_interactions)):
                            window = recent_interactions[i - window_size : i]
                            error_rate = sum(1 for w in window if w.get("error_occurred", False)) / window_size
                            error_rates.append(error_rate)

                        if error_rates:
                            error_trend = self._analyze_metric_trend(error_rates, f"{agent_name}_error_rate")
                            trends.append(self._trend_to_dict(error_trend))

        except Exception as e:
            logger.debug(f"Trend analysis error: {e}")

        return trends

    def _analyze_metric_trend(self, values: list[float], metric_name: str) -> PerformanceTrend:
        """Analyze trend for a specific metric."""
        if len(values) < 5:
            return PerformanceTrend(
                metric_name=metric_name,
                time_period="insufficient_data",
                trend_direction="unknown",
                change_rate=0.0,
                confidence_score=0.0,
                forecast_next_period=values[-1] if values else 0.0,
                trend_stability=0.0,
                data_points=values,
            )

        # Perform linear regression
        x = list(range(len(values)))
        y = values

        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

            # Determine trend direction
            if abs(slope) < 0.001:  # Very small slope
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "improving" if "quality" in metric_name else "declining"
            else:
                trend_direction = "declining" if "quality" in metric_name else "improving"

            # Calculate percentage change rate
            if len(values) > 1 and values[0] != 0:
                change_rate = (slope * len(values)) / values[0] * 100
            else:
                change_rate = 0.0

            # Forecast next period
            forecast_next_period = slope * len(values) + intercept

            # Calculate trend stability (inverse of variance relative to trend line)
            predicted = [slope * i + intercept for i in x]
            residuals = [actual - pred for actual, pred in zip(y, predicted)]
            trend_stability = max(0.0, 1.0 - (statistics.variance(residuals) / max(statistics.variance(y), 0.001)))

            return PerformanceTrend(
                metric_name=metric_name,
                time_period=f"last_{len(values)}_interactions",
                trend_direction=trend_direction,
                change_rate=change_rate,
                confidence_score=abs(r_value),  # R-squared as confidence
                forecast_next_period=forecast_next_period,
                trend_stability=trend_stability,
                data_points=values,
            )

        except Exception as e:
            logger.debug(f"Trend analysis failed for {metric_name}: {e}")
            return PerformanceTrend(
                metric_name=metric_name,
                time_period="analysis_failed",
                trend_direction="unknown",
                change_rate=0.0,
                confidence_score=0.0,
                forecast_next_period=values[-1] if values else 0.0,
                trend_stability=0.0,
                data_points=values,
            )

    async def _detect_performance_anomalies(self, lookback_hours: int) -> list[PerformanceAnomaly]:
        """Detect performance anomalies using statistical methods."""
        anomalies = []

        try:
            if hasattr(self.enhanced_monitor, "real_time_metrics"):
                for agent_name, agent_data in self.enhanced_monitor.real_time_metrics.items():
                    recent_interactions = agent_data.get("recent_interactions", [])

                    if len(recent_interactions) >= 10:
                        # Check for quality anomalies
                        quality_values = [i.get("response_quality", 0) for i in recent_interactions]
                        quality_anomalies = self._detect_anomalies_in_series(quality_values, f"{agent_name}_quality")
                        anomalies.extend(quality_anomalies)

                        # Check for response time anomalies
                        time_values = [i.get("response_time", 0) for i in recent_interactions]
                        time_anomalies = self._detect_anomalies_in_series(time_values, f"{agent_name}_response_time")
                        anomalies.extend(time_anomalies)

        except Exception as e:
            logger.debug(f"Anomaly detection error: {e}")

        return anomalies

    def _detect_anomalies_in_series(self, values: list[float], metric_name: str) -> list[PerformanceAnomaly]:
        """Detect anomalies in a time series using statistical methods."""
        if len(values) < 10:
            return []

        anomalies = []

        try:
            # Calculate rolling statistics
            window_size = min(10, len(values) // 2)

            for i in range(window_size, len(values)):
                window = values[i - window_size : i]
                current_value = values[i]

                # Calculate statistics for the window
                mean_val = statistics.mean(window)
                std_val = statistics.stdev(window) if len(window) > 1 else 0

                if std_val > 0:
                    # Z-score based anomaly detection
                    z_score = abs(current_value - mean_val) / std_val

                    if z_score > self.anomaly_sensitivity:
                        # Determine anomaly type and severity
                        if current_value > mean_val:
                            anomaly_type = "spike"
                        else:
                            anomaly_type = "drop"

                        # Determine severity based on Z-score
                        if z_score > 4:
                            severity = "critical"
                        elif z_score > 3:
                            severity = "high"
                        elif z_score > 2.5:
                            severity = "medium"
                        else:
                            severity = "low"

                        anomaly = PerformanceAnomaly(
                            timestamp=default_utc_now() - timedelta(minutes=(len(values) - i) * 5),
                            metric_name=metric_name,
                            expected_value=mean_val,
                            actual_value=current_value,
                            severity=severity,
                            anomaly_type=anomaly_type,
                            context={
                                "z_score": z_score,
                                "window_mean": mean_val,
                                "window_std": std_val,
                                "position_in_series": i,
                            },
                        )
                        anomalies.append(anomaly)

        except Exception as e:
            logger.debug(f"Anomaly detection failed for {metric_name}: {e}")

        return anomalies

    async def _generate_performance_forecasts(self) -> dict[str, dict[str, Any]]:
        """Generate performance forecasts using time series analysis."""
        forecasts = {}

        try:
            if hasattr(self.enhanced_monitor, "real_time_metrics"):
                for agent_name, agent_data in self.enhanced_monitor.real_time_metrics.items():
                    recent_interactions = agent_data.get("recent_interactions", [])

                    if len(recent_interactions) >= 15:  # Need sufficient data for forecasting
                        # Forecast quality metrics
                        quality_values = [i.get("response_quality", 0) for i in recent_interactions]
                        quality_forecast = self._generate_simple_forecast(quality_values, f"{agent_name}_quality")

                        # Forecast response time metrics
                        time_values = [i.get("response_time", 0) for i in recent_interactions]
                        time_forecast = self._generate_simple_forecast(time_values, f"{agent_name}_response_time")

                        forecasts[agent_name] = {
                            "quality_forecast": self._forecast_to_dict(quality_forecast),
                            "response_time_forecast": self._forecast_to_dict(time_forecast),
                        }

        except Exception as e:
            logger.debug(f"Forecast generation error: {e}")

        return forecasts

    def _generate_simple_forecast(self, values: list[float], metric_name: str) -> PerformanceForecast:
        """Generate a simple linear forecast."""
        if len(values) < 10:
            return PerformanceForecast(
                metric_name=metric_name,
                forecast_horizon=0,
                predicted_values=[],
                confidence_intervals=[],
                forecast_accuracy=0.0,
                model_type="insufficient_data",
            )

        try:
            x = list(range(len(values)))
            y = values

            # Fit linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

            # Generate forecasts
            forecast_points = []
            confidence_intervals = []

            for i in range(1, self.forecast_horizon + 1):
                next_x = len(values) + i
                predicted_y = slope * next_x + intercept

                # Simple confidence interval based on standard error
                margin = (
                    1.96
                    * std_err
                    * math.sqrt(
                        1
                        + 1 / len(values)
                        + (next_x - statistics.mean(x)) ** 2 / sum((xi - statistics.mean(x)) ** 2 for xi in x)
                    )
                )

                forecast_points.append(predicted_y)
                confidence_intervals.append((predicted_y - margin, predicted_y + margin))

            return PerformanceForecast(
                metric_name=metric_name,
                forecast_horizon=self.forecast_horizon,
                predicted_values=forecast_points,
                confidence_intervals=confidence_intervals,
                forecast_accuracy=abs(r_value),  # Use R-value as accuracy proxy
                model_type="linear",
            )

        except Exception as e:
            logger.debug(f"Forecast generation failed for {metric_name}: {e}")
            return PerformanceForecast(
                metric_name=metric_name,
                forecast_horizon=0,
                predicted_values=[],
                confidence_intervals=[],
                forecast_accuracy=0.0,
                model_type="error",
            )

    async def _generate_optimization_recommendations(
        self, trends: list[dict[str, Any]], anomalies: list[PerformanceAnomaly], dashboard_data: dict[str, Any]
    ) -> list[OptimizationRecommendation]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []

        try:
            # Analyze trends for recommendations
            for trend_data in trends:
                if trend_data.get("trend_direction") == "declining" and trend_data.get("confidence_score", 0) > 0.5:
                    metric_name = trend_data.get("metric_name", "")

                    if "quality" in metric_name:
                        recommendations.append(
                            OptimizationRecommendation(
                                category="quality",
                                priority="high",
                                title=f"Address Quality Decline in {metric_name.split('_')[0]}",
                                description=f"Quality metrics show declining trend with {trend_data.get('change_rate', 0):.1f}% negative change rate",
                                expected_impact="10-20% quality improvement",
                                implementation_effort="medium",
                                confidence_score=trend_data.get("confidence_score", 0),
                                supporting_data=trend_data,
                                action_items=[
                                    "Review agent configuration and prompts",
                                    "Analyze tool usage patterns",
                                    "Consider model fine-tuning",
                                    "Implement additional quality gates",
                                ],
                            )
                        )

                    elif "response_time" in metric_name:
                        recommendations.append(
                            OptimizationRecommendation(
                                category="performance",
                                priority="medium",
                                title=f"Optimize Response Time for {metric_name.split('_')[0]}",
                                description=f"Response time increasing by {trend_data.get('change_rate', 0):.1f}% per interaction",
                                expected_impact="15-30% latency reduction",
                                implementation_effort="low",
                                confidence_score=trend_data.get("confidence_score", 0),
                                supporting_data=trend_data,
                                action_items=[
                                    "Profile agent execution pipeline",
                                    "Optimize tool selection logic",
                                    "Implement response caching",
                                    "Review timeout configurations",
                                ],
                            )
                        )

            # Analyze anomalies for recommendations
            critical_anomalies = [a for a in anomalies if a.severity in ["critical", "high"]]
            if len(critical_anomalies) > 3:
                recommendations.append(
                    OptimizationRecommendation(
                        category="reliability",
                        priority="critical",
                        title="Address Frequent Performance Anomalies",
                        description=f"Detected {len(critical_anomalies)} critical/high severity anomalies",
                        expected_impact="50-80% reduction in performance instability",
                        implementation_effort="high",
                        confidence_score=0.9,
                        supporting_data={"anomaly_count": len(critical_anomalies)},
                        action_items=[
                            "Implement automated anomaly alerting",
                            "Add circuit breaker patterns",
                            "Review resource allocation",
                            "Enhance monitoring granularity",
                        ],
                    )
                )

            # System-wide recommendations based on dashboard data
            if "system_health" in dashboard_data:
                health_status = dashboard_data["system_health"].get("overall_status", "unknown")
                if health_status in ["degraded", "critical"]:
                    recommendations.append(
                        OptimizationRecommendation(
                            category="system",
                            priority="critical",
                            title="System Health Optimization Required",
                            description=f"Overall system health is {health_status}",
                            expected_impact="Restore system to healthy state",
                            implementation_effort="high",
                            confidence_score=0.95,
                            supporting_data=dashboard_data.get("system_health", {}),
                            action_items=[
                                "Immediate system health assessment",
                                "Review resource utilization",
                                "Check for cascading failures",
                                "Implement emergency scaling procedures",
                            ],
                        )
                    )

            # Cost optimization recommendations
            recommendations.append(
                OptimizationRecommendation(
                    category="cost",
                    priority="medium",
                    title="Implement Cost-Aware Agent Routing",
                    description="Optimize model selection based on task complexity and cost",
                    expected_impact="20-40% cost reduction",
                    implementation_effort="medium",
                    confidence_score=0.7,
                    supporting_data={},
                    action_items=[
                        "Implement task complexity scoring",
                        "Add cost-aware model selection",
                        "Monitor cost per interaction",
                        "Set up cost alerting thresholds",
                    ],
                )
            )

        except Exception as e:
            logger.debug(f"Recommendation generation error: {e}")

        return recommendations

    async def _calculate_system_health_score(
        self, trends: list[dict[str, Any]], anomalies: list[PerformanceAnomaly], dashboard_data: dict[str, Any]
    ) -> float:
        """Calculate overall system health score (0.0 to 1.0)."""
        try:
            health_factors = []

            # Factor 1: Trend health (30% weight)
            declining_trends = len([t for t in trends if t.get("trend_direction") == "declining"])
            total_trends = len(trends) if trends else 1
            trend_health = max(0.0, 1.0 - (declining_trends / total_trends))
            health_factors.append(("trend_health", trend_health, 0.3))

            # Factor 2: Anomaly severity (25% weight)
            critical_anomalies = len([a for a in anomalies if a.severity in ["critical", "high"]])
            anomaly_health = max(0.0, 1.0 - (critical_anomalies / 10))  # Cap at 10 critical anomalies
            health_factors.append(("anomaly_health", anomaly_health, 0.25))

            # Factor 3: Performance metrics (25% weight)
            avg_quality = 0.75  # Default if no data
            if hasattr(self.enhanced_monitor, "real_time_metrics"):
                quality_scores = []
                for agent_data in self.enhanced_monitor.real_time_metrics.values():
                    recent = agent_data.get("recent_interactions", [])
                    if recent:
                        agent_quality = statistics.mean([i.get("response_quality", 0) for i in recent[-5:]])
                        quality_scores.append(agent_quality)

                if quality_scores:
                    avg_quality = statistics.mean(quality_scores)

            health_factors.append(("performance_health", avg_quality, 0.25))

            # Factor 4: System stability (20% weight)
            # Check for consistent performance vs. high variance
            stability_score = 0.8  # Default assumption
            if hasattr(self.enhanced_monitor, "real_time_metrics"):
                variance_scores = []
                for agent_data in self.enhanced_monitor.real_time_metrics.values():
                    recent = agent_data.get("recent_interactions", [])
                    if len(recent) > 5:
                        quality_values = [i.get("response_quality", 0) for i in recent[-10:]]
                        variance = statistics.variance(quality_values) if len(quality_values) > 1 else 0
                        stability = max(0.0, 1.0 - variance)  # Lower variance = higher stability
                        variance_scores.append(stability)

                if variance_scores:
                    stability_score = statistics.mean(variance_scores)

            health_factors.append(("stability_health", stability_score, 0.2))

            # Calculate weighted health score
            total_weighted_score = sum(score * weight for _, score, weight in health_factors)

            return max(0.0, min(1.0, total_weighted_score))

        except Exception as e:
            logger.debug(f"Health score calculation error: {e}")
            return 0.5  # Default moderate health score

    def _get_health_status(self, health_score: float) -> str:
        """Convert health score to status string."""
        if health_score >= 0.9:
            return "excellent"
        elif health_score >= 0.8:
            return "good"
        elif health_score >= 0.7:
            return "fair"
        elif health_score >= 0.5:
            return "degraded"
        else:
            return "critical"

    def _get_key_health_indicators(self, dashboard_data: dict[str, Any]) -> dict[str, Any]:
        """Extract key health indicators from dashboard data."""
        try:
            if hasattr(self.enhanced_monitor, "real_time_metrics"):
                total_agents = len(self.enhanced_monitor.real_time_metrics)
                active_agents = len(
                    [
                        agent
                        for agent, data in self.enhanced_monitor.real_time_metrics.items()
                        if data.get("recent_interactions", [])
                    ]
                )

                return {
                    "total_agents_monitored": total_agents,
                    "active_agents": active_agents,
                    "monitoring_coverage": active_agents / total_agents if total_agents > 0 else 0,
                    "recent_alerts": len(self.detected_anomalies),
                    "active_recommendations": len(self.active_recommendations),
                }
            else:
                return {
                    "total_agents_monitored": 0,
                    "active_agents": 0,
                    "monitoring_coverage": 0,
                    "recent_alerts": 0,
                    "active_recommendations": 0,
                }
        except Exception:
            return {}

    async def _perform_comparative_analysis(self) -> dict[str, Any]:
        """Perform comparative analysis across agents."""
        try:
            if not hasattr(self.enhanced_monitor, "real_time_metrics"):
                return {"error": "No monitoring data available"}

            agent_performances = {}

            for agent_name, agent_data in self.enhanced_monitor.real_time_metrics.items():
                recent_interactions = agent_data.get("recent_interactions", [])

                if len(recent_interactions) >= 5:
                    quality_scores = [i.get("response_quality", 0) for i in recent_interactions[-10:]]
                    response_times = [i.get("response_time", 0) for i in recent_interactions[-10:]]

                    agent_performances[agent_name] = {
                        "avg_quality": statistics.mean(quality_scores),
                        "quality_consistency": 1.0 - statistics.variance(quality_scores)
                        if len(quality_scores) > 1
                        else 1.0,
                        "avg_response_time": statistics.mean(response_times),
                        "time_consistency": 1.0
                        - (statistics.variance(response_times) / max(statistics.mean(response_times), 1))
                        if len(response_times) > 1
                        else 1.0,
                        "total_interactions": len(recent_interactions),
                    }

            if not agent_performances:
                return {"message": "Insufficient data for comparative analysis"}

            # Find best and worst performers
            best_quality = max(agent_performances.items(), key=lambda x: x[1]["avg_quality"])
            worst_quality = min(agent_performances.items(), key=lambda x: x[1]["avg_quality"])
            fastest_agent = min(agent_performances.items(), key=lambda x: x[1]["avg_response_time"])

            return {
                "total_agents_compared": len(agent_performances),
                "best_performers": {
                    "highest_quality": {
                        "agent": best_quality[0],
                        "quality": best_quality[1]["avg_quality"],
                        "consistency": best_quality[1]["quality_consistency"],
                    },
                    "fastest_response": {
                        "agent": fastest_agent[0],
                        "avg_time": fastest_agent[1]["avg_response_time"],
                        "consistency": fastest_agent[1]["time_consistency"],
                    },
                },
                "needs_attention": {
                    "lowest_quality": {
                        "agent": worst_quality[0],
                        "quality": worst_quality[1]["avg_quality"],
                        "gap_from_best": best_quality[1]["avg_quality"] - worst_quality[1]["avg_quality"],
                    }
                },
                "performance_distribution": {agent: perf["avg_quality"] for agent, perf in agent_performances.items()},
            }

        except Exception as e:
            logger.debug(f"Comparative analysis error: {e}")
            return {"error": str(e)}

    def _generate_actionable_insights(
        self,
        trends: list[dict[str, Any]],
        anomalies: list[PerformanceAnomaly],
        recommendations: list[OptimizationRecommendation],
    ) -> list[str]:
        """Generate concise, actionable insights."""
        insights = []

        try:
            # Insight from trends
            declining_quality_trends = [
                t for t in trends if "quality" in t.get("metric_name", "") and t.get("trend_direction") == "declining"
            ]
            if declining_quality_trends:
                insights.append(
                    f"🔍 Quality declining in {len(declining_quality_trends)} agents - immediate attention needed"
                )

            # Insight from anomalies
            recent_critical = [a for a in anomalies if a.severity == "critical"]
            if recent_critical:
                insights.append(
                    f"🚨 {len(recent_critical)} critical performance anomalies detected - investigate root causes"
                )

            # Insight from recommendations
            critical_recs = [r for r in recommendations if r.priority == "critical"]
            if critical_recs:
                insights.append(f"⚡ {len(critical_recs)} critical optimizations available - high impact potential")

            # System-wide insights
            if len(trends) > 0:
                stable_trends = [t for t in trends if t.get("trend_direction") == "stable"]
                if len(stable_trends) / len(trends) > 0.8:
                    insights.append("✅ System performance is stable - good baseline for optimization")

            # Default insight if no specific issues
            if not insights:
                insights.append("📊 System operating within normal parameters - focus on proactive optimization")

        except Exception as e:
            logger.debug(f"Insights generation error: {e}")
            insights.append("⚠️ Unable to generate insights - check monitoring data availability")

        return insights

    # Helper methods for data conversion
    def _trend_to_dict(self, trend: PerformanceTrend) -> dict[str, Any]:
        """Convert PerformanceTrend to dictionary."""
        return {
            "metric_name": trend.metric_name,
            "time_period": trend.time_period,
            "trend_direction": trend.trend_direction,
            "change_rate": trend.change_rate,
            "confidence_score": trend.confidence_score,
            "forecast_next_period": trend.forecast_next_period,
            "trend_stability": trend.trend_stability,
            "data_points_count": len(trend.data_points),
        }

    def _forecast_to_dict(self, forecast: PerformanceForecast) -> dict[str, Any]:
        """Convert PerformanceForecast to dictionary."""
        return {
            "metric_name": forecast.metric_name,
            "forecast_horizon": forecast.forecast_horizon,
            "predicted_values": forecast.predicted_values,
            "confidence_intervals": forecast.confidence_intervals,
            "forecast_accuracy": forecast.forecast_accuracy,
            "model_type": forecast.model_type,
        }

    async def generate_analytics_report(self, format_type: str = "json") -> str:
        """Generate comprehensive analytics report.

        Args:
            format_type: Output format ("json", "markdown", "html")

        Returns:
            Formatted analytics report
        """
        analysis = await self.analyze_comprehensive_performance()

        if format_type == "json":
            return json.dumps(analysis, indent=2, default=str)
        elif format_type == "markdown":
            return self._format_markdown_report(analysis)
        elif format_type == "html":
            return self._format_html_report(analysis)
        else:
            return json.dumps(analysis, indent=2, default=str)

    def _format_markdown_report(self, analysis: dict[str, Any]) -> str:
        """Format analysis as markdown report."""
        report = f"""# Advanced Performance Analytics Report

**Generated**: {analysis.get("analysis_timestamp")}
**Analysis Period**: {analysis.get("lookback_hours")} hours

## 🏥 System Health

**Overall Score**: {analysis.get("system_health", {}).get("overall_score", 0):.2f}
**Status**: {analysis.get("system_health", {}).get("status", "unknown").title()}

### Key Indicators
"""

        key_indicators = analysis.get("system_health", {}).get("key_indicators", {})
        for indicator, value in key_indicators.items():
            report += f"- **{indicator.replace('_', ' ').title()}**: {value}\n"

        report += "\n## 📈 Performance Trends\n\n"
        trends = analysis.get("performance_trends", [])
        for trend in trends[:5]:  # Top 5 trends
            direction_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(
                trend.get("trend_direction", "stable"), "➡️"
            )
            report += f"- {direction_emoji} **{trend.get('metric_name')}**: {trend.get('trend_direction')} ({trend.get('change_rate', 0):.1f}% change)\n"

        report += "\n## 🚨 Critical Recommendations\n\n"
        critical_recs = analysis.get("optimization_recommendations", {}).get("critical", [])
        for rec in critical_recs:
            report += f"### {rec.title}\n"
            report += f"**Category**: {rec.category.title()}\n"
            report += f"**Expected Impact**: {rec.expected_impact}\n"
            report += f"**Effort**: {rec.implementation_effort.title()}\n\n"

        report += "\n## 💡 Actionable Insights\n\n"
        insights = analysis.get("actionable_insights", [])
        for insight in insights:
            report += f"- {insight}\n"

        return report

    def _format_html_report(self, analysis: dict[str, Any]) -> str:
        """Format analysis as HTML report."""
        health_score = analysis.get("system_health", {}).get("overall_score", 0)
        health_color = "green" if health_score > 0.8 else "orange" if health_score > 0.6 else "red"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Advanced Performance Analytics Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .health-score {{ color: {health_color}; font-size: 24px; font-weight: bold; }}
        .metric {{ background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .recommendation {{ background: #fff3cd; padding: 15px; margin: 10px 0; border-left: 4px solid #ffc107; }}
        .insight {{ background: #d4edda; padding: 10px; margin: 10px 0; border-left: 4px solid #28a745; }}
    </style>
</head>
<body>
    <h1>🔬 Advanced Performance Analytics Report</h1>
    <p><strong>Generated:</strong> {analysis.get("analysis_timestamp")}</p>

    <h2>🏥 System Health</h2>
    <div class="health-score">Score: {health_score:.2f}</div>
    <p><strong>Status:</strong> {analysis.get("system_health", {}).get("status", "unknown").title()}</p>

    <h2>📊 Key Metrics</h2>
    <div class="metric">
        <strong>Performance Trends:</strong> {len(analysis.get("performance_trends", []))} analyzed<br>
        <strong>Anomalies Detected:</strong> {analysis.get("anomalies", {}).get("detected", 0)}<br>
        <strong>Optimization Recommendations:</strong> {
            analysis.get("optimization_recommendations", {}).get("total_recommendations", 0)
        }
    </div>

    <h2>🎯 Top Recommendations</h2>
    {
            "".join(
                f'<div class="recommendation"><strong>{rec.title}</strong><br>{rec.description}</div>'
                for rec in analysis.get("optimization_recommendations", {}).get("critical", [])[:3]
            )
        }

    <h2>💡 Key Insights</h2>
    {"".join(f'<div class="insight">{insight}</div>' for insight in analysis.get("actionable_insights", []))}
</body>
</html>
        """


# Convenience functions for easy usage
async def run_comprehensive_analytics(lookback_hours: int = 24) -> dict[str, Any]:
    """Run comprehensive performance analytics.

    Args:
        lookback_hours: Hours of historical data to analyze

    Returns:
        Dict containing comprehensive analytics results
    """
    analytics_engine = AdvancedPerformanceAnalytics()
    return await analytics_engine.analyze_comprehensive_performance(lookback_hours)


async def generate_optimization_report(format_type: str = "markdown") -> str:
    """Generate optimization report.

    Args:
        format_type: Output format ("json", "markdown", "html")

    Returns:
        Formatted optimization report
    """
    analytics_engine = AdvancedPerformanceAnalytics()
    return await analytics_engine.generate_analytics_report(format_type)
