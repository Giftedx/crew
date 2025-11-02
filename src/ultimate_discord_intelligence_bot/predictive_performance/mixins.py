from __future__ import annotations

import logging
import statistics
from datetime import timedelta
from platform.time import default_utc_now
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy import stats

from .models import AlertSeverity, EarlyWarningAlert, ModelDriftAlert, PredictionConfidence


if TYPE_CHECKING:
    from collections import deque
logger = logging.getLogger(__name__)


class TrendAnalysisMixin:
    """Methods to analyse trends and contributing/uncertainty factors."""

    def _determine_confidence_level(self, accuracy: float, data_points: int) -> PredictionConfidence:
        if accuracy > 0.9 and data_points > 100:
            return PredictionConfidence.VERY_HIGH
        elif accuracy > 0.8 and data_points > 50:
            return PredictionConfidence.HIGH
        elif accuracy > 0.7 and data_points > 20:
            return PredictionConfidence.MEDIUM
        else:
            return PredictionConfidence.LOW

    def _identify_contributing_factors(self, metric_name: str, historical_data: deque) -> list[str]:
        factors: list[str] = []
        try:
            recent_data = list(historical_data)[-20:]
            if "quality" in metric_name:
                avg_response_time = statistics.mean([d["context"].get("response_time", 0) for d in recent_data])
                error_rate = sum(1 for d in recent_data if d["context"].get("error_occurred", False)) / len(recent_data)
                if avg_response_time > 10:
                    factors.append("High response times correlating with quality")
                if error_rate > 0.1:
                    factors.append("Elevated error rates impacting quality")
                tool_usage: list[str] = []
                for d in recent_data:
                    tool_usage.extend(d["context"].get("tools_used", []))
                if tool_usage:
                    common_tools = [t for t in set(tool_usage) if tool_usage.count(t) > len(recent_data) * 0.3]
                    if common_tools:
                        factors.append(f"Frequent use of tools: {', '.join(common_tools)}"
            elif "response_time" in metric_name:
                avg_complexity = statistics.mean([d["context"].get("complexity", 0) for d in recent_data])
                if avg_complexity > 3:
                    factors.append("High task complexity increasing response time")
                success_rate = sum(1 for d in recent_data if d["context"].get("success", True)) / len(recent_data)
                if success_rate < 0.9:
                    factors.append("Error handling overhead affecting response time")
        except Exception as e:
            logger.debug(f"Contributing factors analysis error: {e}")
        return factors if factors else ["Standard operational patterns"]

    def _identify_uncertainty_factors(self, values: list[float], accuracy: float) -> list[str]:
        factors: list[str] = []
        try:
            if len(values) > 1:
                variance = statistics.variance(values)
                mean_val = statistics.mean(values)
                cv = variance / max(mean_val, 0.001)
                if cv > 0.3:
                    factors.append("High metric variability reduces prediction certainty")
            if len(values) >= 10:
                recent_trend = self._calculate_trend_change(
                    values[-10:], values[-20:-10] if len(values) >= 20 else values[:10]
                )
                if abs(recent_trend) > 0.2:
                    factors.append("Recent trend changes increase uncertainty")
            if accuracy < 0.8:
                factors.append("Limited model accuracy affects prediction reliability")
        except Exception as e:
            logger.debug(f"Uncertainty factors analysis error: {e}")
        return factors if factors else ["Normal prediction uncertainty"]

    def _calculate_trend_change(self, recent_values: list[float], older_values: list[float]) -> float:
        try:
            if len(recent_values) < 2 or len(older_values) < 2:
                return 0.0
            recent_trend = (recent_values[-1] - recent_values[0]) / len(recent_values)
            older_trend = (older_values[-1] - older_values[0]) / len(older_values)
            if abs(older_trend) < 0.001:
                return 0.0
            return (recent_trend - older_trend) / abs(older_trend)
        except Exception:
            return 0.0


class WarningDetectionMixin:
    """Early warning generation methods."""

    def _check_quality_degradation_warning(self, metric_name: str, historical_data: deque) -> EarlyWarningAlert | None:
        try:
            recent_values = [p["value"] for p in list(historical_data)[-10:]]
            older_values = [p["value"] for p in list(historical_data)[-20:-10]] if len(historical_data) >= 20 else []
            if not older_values:
                return None
            recent_avg = statistics.mean(recent_values)
            older_avg = statistics.mean(older_values)
            decline_threshold = 0.15
            decline_ratio = (older_avg - recent_avg) / max(older_avg, 0.001)
            if decline_ratio > decline_threshold:
                agent_name = metric_name.split("_")[0]
                decline_rate = decline_ratio / 10
                critical_threshold = 0.5
                interactions_to_critical = max(
                    1, (recent_avg - critical_threshold) / max(decline_rate * recent_avg, 0.001)
                )
                time_to_impact = timedelta(hours=interactions_to_critical * 0.5)
                return EarlyWarningAlert(
                    alert_id=f"quality_degradation_{agent_name}_{default_utc_now().strftime('%Y%m%d_%H%M%S')}"
                    severity=AlertSeverity.WARNING if decline_ratio < 0.25 else AlertSeverity.CRITICAL,
                    alert_type="quality",
                    title=f"Quality Degradation Detected: {agent_name}",
                    description=f"Quality declined by {decline_ratio:.1%} over recent interactions",
                    predicted_impact=f"Continued decline may reach critical levels in {time_to_impact}",
                    time_to_impact=time_to_impact,
                    confidence=PredictionConfidence.HIGH,
                    recommended_actions=[
                        "Review recent agent configuration changes",
                        "Analyze error patterns in recent interactions",
                        "Check tool performance and availability",
                        "Consider temporary quality gates",
                    ],
                    monitoring_metrics=[metric_name],
                    context_data={
                        "recent_average": recent_avg,
                        "previous_average": older_avg,
                        "decline_percentage": decline_ratio * 100,
                    },
                )
        except Exception as e:
            logger.debug(f"Quality degradation warning check failed: {e}")
        return None

    def _check_performance_degradation_warning(
        self, metric_name: str, historical_data: deque
    ) -> EarlyWarningAlert | None:
        try:
            recent_values = [p["value"] for p in list(historical_data)[-10:]]
            older_values = [p["value"] for p in list(historical_data)[-20:-10]] if len(historical_data) >= 20 else []
            if not older_values:
                return None
            recent_avg = statistics.mean(recent_values)
            older_avg = statistics.mean(older_values)
            increase_threshold = 0.3
            increase_ratio = (recent_avg - older_avg) / max(older_avg, 0.001)
            if increase_ratio > increase_threshold:
                agent_name = metric_name.split("_")[0]
                increase_rate = increase_ratio / 10
                critical_threshold = 30.0
                interactions_to_critical = max(
                    1, (critical_threshold - recent_avg) / max(increase_rate * recent_avg, 0.001)
                )
                time_to_impact = timedelta(hours=interactions_to_critical * 0.5)
                return EarlyWarningAlert(
                    alert_id=f"performance_degradation_{agent_name}_{default_utc_now().strftime('%Y%m%d_%H%M%S')}"
                    severity=AlertSeverity.WARNING if increase_ratio < 0.5 else AlertSeverity.CRITICAL,
                    alert_type="performance",
                    title=f"Performance Degradation Detected: {agent_name}",
                    description=f"Response time increased by {increase_ratio:.1%} over recent interactions",
                    predicted_impact=f"Continued degradation may reach critical levels in {time_to_impact}",
                    time_to_impact=time_to_impact,
                    confidence=PredictionConfidence.HIGH,
                    recommended_actions=[
                        "Profile agent execution pipeline",
                        "Check resource utilization and constraints",
                        "Review tool response times",
                        "Consider performance optimization",
                    ],
                    monitoring_metrics=[metric_name],
                    context_data={
                        "recent_average": recent_avg,
                        "previous_average": older_avg,
                        "increase_percentage": increase_ratio * 100,
                    },
                )
        except Exception as e:
            logger.debug(f"Performance degradation warning check failed: {e}")
        return None

    async def _check_capacity_warnings(self) -> list[EarlyWarningAlert]:
        warnings: list[EarlyWarningAlert] = []
        try:
            if hasattr(self.enhanced_monitor, "real_time_metrics"):
                total_interactions = 0
                agent_loads: dict[str, int] = {}
                for agent_name, agent_data in self.enhanced_monitor.real_time_metrics.items():
                    recent_interactions = len(agent_data.get("recent_interactions", []))
                    agent_loads[agent_name] = recent_interactions
                    total_interactions += recent_interactions
                if total_interactions > 0:
                    load_values = list(agent_loads.values())
                    if len(load_values) > 1:
                        max_load = max(load_values)
                        if max_load / total_interactions > 0.7:
                            overloaded_agent = max(agent_loads.items(), key=lambda x: x[1])[0]
                            warnings.append(
                                EarlyWarningAlert(
                                    alert_id=f"capacity_imbalance_{default_utc_now().strftime('%Y%m%d_%H%M%S')}"
                                    severity=AlertSeverity.WARNING,
                                    alert_type="capacity",
                                    title="Agent Load Imbalance Detected",
                                    description=f"Agent {overloaded_agent} handling {max_load / total_interactions:.1%} of total load",
                                    predicted_impact="Potential bottleneck and degraded performance",
                                    time_to_impact=timedelta(hours=1),
                                    confidence=PredictionConfidence.HIGH,
                                    recommended_actions=[
                                        "Review agent routing logic",
                                        "Consider load balancing adjustments",
                                        "Monitor overloaded agent performance",
                                        "Prepare scaling strategies",
                                    ],
                                    monitoring_metrics=[f"{overloaded_agent}_*"],
                                    context_data={
                                        "overloaded_agent": overloaded_agent,
                                        "load_percentage": max_load / total_interactions * 100,
                                        "agent_loads": agent_loads,
                                    },
                                )
                            )
        except Exception as e:
            logger.debug(f"Capacity warnings check failed: {e}")
        return warnings


class CapacityForecastingMixin:
    """Capacity forecasting logic."""

    def _get_interaction_volume_trend(self) -> list[float]:
        try:
            volume_data: list[float] = []
            if hasattr(self.enhanced_monitor, "real_time_metrics"):
                for agent_data in self.enhanced_monitor.real_time_metrics.values():
                    recent_interactions = agent_data.get("recent_interactions", [])
                    volume_data.append(float(len(recent_interactions)))
            return volume_data
        except Exception:
            return []

    def _forecast_interaction_volume(self, historical_volumes: list[float]) -> dict[str, Any]:
        try:
            x = np.array(range(len(historical_volumes))).reshape(-1, 1)
            y = np.array(historical_volumes)
            from sklearn.linear_model import LinearRegression

            model = LinearRegression()
            model.fit(x, y)
            future_periods = range(len(historical_volumes), len(historical_volumes) + 12)
            predictions = [model.predict([[period]])[0] for period in future_periods]
            current_max = max(historical_volumes) if historical_volumes else 10
            threshold = current_max * 1.2
            breach_time = None
            for i, pred in enumerate(predictions):
                if pred > threshold:
                    breach_time = default_utc_now() + timedelta(hours=i)
                    break
            recommendations: list[str] = []
            if breach_time and breach_time < default_utc_now() + timedelta(days=7):
                recommendations.extend(
                    [
                        "Scale up agent infrastructure within 1 week",
                        "Implement load balancing improvements",
                        "Consider agent performance optimizations",
                    ]
                )
            cost_implications = {
                "current_baseline_cost": 100.0,
                "projected_scaling_cost": 150.0 if breach_time else 100.0,
                "optimization_savings": 20.0,
            }
            return {
                "predictions": predictions,
                "threshold": threshold,
                "breach_time": breach_time,
                "recommendations": recommendations,
                "cost_implications": cost_implications,
            }
        except Exception as e:
            logger.debug(f"Volume forecasting error: {e}")
            return {
                "predictions": [],
                "threshold": 0,
                "breach_time": None,
                "recommendations": [],
                "cost_implications": {},
            }


class DriftDetectionMixin:
    """Model drift detection logic."""

    def _identify_drift_factors(self, baseline_data: list, recent_data: list) -> list[str]:
        factors: list[str] = []
        try:
            baseline_contexts = [p.get("context", {}) for p in baseline_data]
            recent_contexts = [p.get("context", {}) for p in recent_data]
            baseline_errors = sum(1 for ctx in baseline_contexts if ctx.get("error_occurred", False)) / len(
                baseline_contexts
            )
            recent_errors = sum(1 for ctx in recent_contexts if ctx.get("error_occurred", False)) / len(recent_contexts)
            if abs(recent_errors - baseline_errors) > 0.1:
                factors.append(f"Error rate changed from {baseline_errors:.1%} to {recent_errors:.1%}")
            baseline_tools: list[str] = []
            recent_tools: list[str] = []
            for ctx in baseline_contexts:
                baseline_tools.extend(ctx.get("tools_used", []))
            for ctx in recent_contexts:
                recent_tools.extend(ctx.get("tools_used", []))
            if baseline_tools and recent_tools and (set(baseline_tools) != set(recent_tools)):
                factors.append("Changes in tool usage patterns detected")
        except Exception as e:
            logger.debug(f"Drift factors analysis error: {e}")
        return factors if factors else ["Standard operational variance"]

    def _analyze_metric_drift(self, metric_name: str, historical_data: deque) -> ModelDriftAlert | None:
        try:
            data_points = list(historical_data)
            baseline_size = len(data_points) // 2
            baseline_data = data_points[:baseline_size]
            recent_data = data_points[baseline_size:]
            baseline_values = [p["value"] for p in baseline_data]
            recent_values = [p["value"] for p in recent_data]
            baseline_mean = statistics.mean(baseline_values)
            recent_mean = statistics.mean(recent_values)
            ks_statistic, p_value = stats.ks_2samp(baseline_values, recent_values)
            drift_magnitude = abs(recent_mean - baseline_mean) / max(abs(baseline_mean), 0.001)
            if ks_statistic > self.drift_detection_threshold or p_value < 0.05:
                if "quality" in metric_name or "response_time" in metric_name:
                    drift_type = "performance_drift"
                else:
                    drift_type = "data_drift"
                contributing_factors = self._identify_drift_factors(baseline_data, recent_data)
                remediation_suggestions = self._generate_drift_remediation(metric_name, drift_type, drift_magnitude)
                return ModelDriftAlert(
                    model_name=metric_name,
                    drift_type=drift_type,
                    drift_magnitude=min(1.0, drift_magnitude),
                    detection_timestamp=default_utc_now(),
                    baseline_performance=baseline_mean,
                    current_performance=recent_mean,
                    contributing_factors=contributing_factors,
                    remediation_suggestions=remediation_suggestions,
                )
        except Exception as e:
            logger.debug(f"Drift analysis failed for {metric_name}: {e}")
        return None

    def _generate_drift_remediation(self, metric_name: str, drift_type: str, magnitude: float) -> list[str]:
        suggestions: list[str] = []
        if drift_type == "performance_drift":
            if magnitude > 0.3:
                suggestions.extend(
                    [
                        "Immediate performance review and debugging required",
                        "Check for recent configuration or model changes",
                        "Consider temporary rollback to previous version",
                    ]
                )
            else:
                suggestions.extend(
                    [
                        "Monitor performance trends closely",
                        "Review recent changes in operational patterns",
                        "Consider gradual retuning or recalibration",
                    ]
                )
        elif drift_type == "data_drift":
            suggestions.extend(
                [
                    "Analyze input data distribution changes",
                    "Review data preprocessing and validation",
                    "Consider model retraining with recent data",
                    "Implement data quality monitoring",
                ]
            )
        if "quality" in metric_name:
            suggestions.append("Review quality assessment criteria and thresholds")
        elif "response_time" in metric_name:
            suggestions.append("Investigate infrastructure and resource constraints")
        return suggestions


class ScenarioGenerationMixin:
    """Optimization scenarios and recommendations."""

    async def _generate_optimization_scenarios(self) -> dict[str, Any]:
        """Generate optimization scenarios based on current state."""
        scenarios: dict[str, Any] = {}
        try:
            current_state = await self._analyze_current_state()
            scenarios["performance_optimization"] = self._create_performance_scenario(current_state)
            scenarios["cost_optimization"] = self._create_cost_scenario(current_state)
            scenarios["reliability_optimization"] = self._create_reliability_scenario(current_state)
        except Exception as e:
            logger.debug(f"Optimization scenarios generation error: {e}")
        return scenarios

    async def _analyze_current_state(self) -> dict[str, Any]:
        return {
            "total_agents": len(self.historical_metrics) // 2,
            "avg_quality": 0.75,
            "avg_response_time": 5.0,
            "error_rate": 0.05,
            "utilization": 0.6,
        }

    def _create_performance_scenario(self, current_state: dict[str, Any]) -> dict[str, Any]:
        return {
            "scenario_name": "Performance-First Optimization",
            "target_improvements": {
                "response_time_reduction": "30%",
                "quality_improvement": "15%",
                "error_rate_reduction": "50%",
            },
            "required_changes": [
                "Implement aggressive caching strategies",
                "Optimize tool selection algorithms",
                "Add performance monitoring and alerting",
                "Implement circuit breaker patterns",
            ],
            "estimated_timeline": "2-4 weeks",
            "resource_requirements": "Medium",
            "risk_level": "Low",
            "expected_outcomes": {
                "user_satisfaction": "+25%",
                "system_reliability": "+20%",
                "operational_efficiency": "+30%",
            },
        }

    def _create_cost_scenario(self, current_state: dict[str, Any]) -> dict[str, Any]:
        return {
            "scenario_name": "Cost-Efficient Operations",
            "target_improvements": {"cost_reduction": "25%", "resource_utilization": "+40%", "efficiency_gain": "20%"},
            "required_changes": [
                "Implement intelligent model selection",
                "Add request batching and optimization",
                "Deploy cost-aware routing logic",
                "Implement usage-based scaling",
            ],
            "estimated_timeline": "3-6 weeks",
            "resource_requirements": "High",
            "risk_level": "Medium",
            "expected_outcomes": {"operational_cost": "-25%", "resource_efficiency": "+40%", "scalability": "+50%"},
        }

    def _create_reliability_scenario(self, current_state: dict[str, Any]) -> dict[str, Any]:
        return {
            "scenario_name": "Maximum Reliability",
            "target_improvements": {
                "uptime_improvement": "99.9%",
                "error_rate_reduction": "75%",
                "recovery_time": "-60%",
            },
            "required_changes": [
                "Implement comprehensive monitoring",
                "Add automated failover mechanisms",
                "Deploy redundancy and backup systems",
                "Implement predictive maintenance",
            ],
            "estimated_timeline": "4-8 weeks",
            "resource_requirements": "High",
            "risk_level": "Low",
            "expected_outcomes": {
                "system_availability": "99.9%",
                "incident_reduction": "-75%",
                "customer_trust": "+40%",
            },
        }

    def _generate_predictive_recommendations(
        self,
        predictions: dict,
        warnings: list[EarlyWarningAlert],
        capacity_forecasts: dict,
        drift_alerts: list[ModelDriftAlert],
    ) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        try:
            for warning in warnings:
                if warning.severity in [AlertSeverity.CRITICAL, AlertSeverity.URGENT]:
                    recommendations.append(
                        {
                            "priority": "critical",
                            "category": warning.alert_type,
                            "title": f"Address {warning.title}",
                            "description": warning.description,
                            "actions": warning.recommended_actions,
                            "timeline": "immediate",
                            "confidence": warning.confidence.value,
                        }
                    )
            for _name, forecast in capacity_forecasts.items():
                if forecast.projected_breach_time:
                    recommendations.append(
                        {
                            "priority": "high",
                            "category": "capacity",
                            "title": f"Scale {forecast.resource_type.title()} Resources",
                            "description": f"Capacity threshold will be breached by {forecast.projected_breach_time.strftime('%Y-%m-%d')}"
                            "actions": forecast.scaling_recommendations,
                            "timeline": "within_week",
                            "confidence": "high",
                        }
                    )
            for drift_alert in drift_alerts:
                if drift_alert.drift_magnitude > 0.2:
                    recommendations.append(
                        {
                            "priority": "medium",
                            "category": "model_maintenance",
                            "title": f"Address Model Drift in {drift_alert.model_name}",
                            "description": f"{drift_alert.drift_type} detected with {drift_alert.drift_magnitude:.1%} magnitude",
                            "actions": drift_alert.remediation_suggestions,
                            "timeline": "within_month",
                            "confidence": "medium",
                        }
                    )
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "optimization",
                    "title": "Implement Predictive Monitoring",
                    "description": "Deploy comprehensive predictive analytics monitoring",
                    "actions": [
                        "Set up automated trend analysis",
                        "Implement early warning systems",
                        "Configure predictive alerting",
                        "Establish performance baselines",
                    ],
                    "timeline": "within_month",
                    "confidence": "high",
                }
            )
        except Exception as e:
            logger.debug(f"Predictive recommendations generation error: {e}")
        return recommendations
