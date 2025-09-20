"""
Predictive Performance Insights Engine

This module provides predictive analytics capabilities that use machine learning
and statistical modeling to forecast performance trends, predict potential issues,
and suggest proactive optimizations.

Key Features:
- Performance trend prediction using time series analysis
- Early warning system for performance degradation
- Capacity planning and resource optimization predictions
- Model performance drift detection
- Automated threshold adjustment recommendations
- Cost trend forecasting and optimization scenarios
"""

from __future__ import annotations

import logging
import statistics
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression

from .advanced_performance_analytics import AdvancedPerformanceAnalytics
from .enhanced_performance_monitor import EnhancedPerformanceMonitor

logger = logging.getLogger(__name__)


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


class PredictivePerformanceInsights:
    """Predictive analytics engine for performance insights."""

    def __init__(
        self,
        analytics_engine: AdvancedPerformanceAnalytics | None = None,
        enhanced_monitor: EnhancedPerformanceMonitor | None = None,
    ):
        """Initialize predictive insights engine.

        Args:
            analytics_engine: Advanced analytics engine instance
            enhanced_monitor: Enhanced performance monitor instance
        """
        self.analytics_engine = analytics_engine or AdvancedPerformanceAnalytics()
        self.enhanced_monitor = enhanced_monitor or EnhancedPerformanceMonitor()

        # Prediction storage
        self.active_predictions: dict[str, list[PerformancePrediction]] = {}
        self.early_warnings: list[EarlyWarningAlert] = []
        self.capacity_forecasts: dict[str, CapacityForecast] = {}
        self.model_drift_alerts: list[ModelDriftAlert] = []

        # Historical data for training
        self.historical_metrics: dict[str, deque] = {}
        self.max_history_size = 1000  # Maximum historical data points to keep

        # Model configuration
        self.prediction_models: dict[str, Any] = {}
        self.model_accuracy_threshold = 0.7  # Minimum accuracy for predictions
        self.drift_detection_threshold = 0.15  # Threshold for drift detection

        # Anomaly detection
        self.isolation_forests: dict[str, IsolationForest] = {}

    async def generate_comprehensive_predictions(self, prediction_horizon: int = 12) -> dict[str, Any]:
        """Generate comprehensive predictive insights.

        Args:
            prediction_horizon: Number of time periods to predict ahead

        Returns:
            Dict containing comprehensive predictive insights
        """
        try:
            # Update historical data
            await self._update_historical_metrics()

            # Generate performance predictions
            predictions = await self._generate_performance_predictions(prediction_horizon)

            # Generate early warning alerts
            warnings = await self._generate_early_warnings()

            # Perform capacity forecasting
            capacity_forecasts = await self._perform_capacity_forecasting()

            # Detect model drift
            drift_alerts = await self._detect_model_drift()

            # Generate optimization scenarios
            optimization_scenarios = await self._generate_optimization_scenarios()

            # Calculate prediction reliability score
            reliability_score = self._calculate_prediction_reliability()

            # Generate actionable recommendations
            actionable_recommendations = self._generate_predictive_recommendations(
                predictions, warnings, capacity_forecasts, drift_alerts
            )

            return {
                "prediction_timestamp": datetime.now().isoformat(),
                "prediction_horizon": prediction_horizon,
                "reliability_score": reliability_score,
                "performance_predictions": {
                    "total_predictions": sum(len(preds) for preds in predictions.values()),
                    "high_confidence": self._count_by_confidence(predictions, PredictionConfidence.HIGH),
                    "predictions_by_agent": predictions,
                },
                "early_warnings": {
                    "total_warnings": len(warnings),
                    "critical": len([w for w in warnings if w.severity == AlertSeverity.CRITICAL]),
                    "urgent": len([w for w in warnings if w.severity == AlertSeverity.URGENT]),
                    "active_warnings": warnings,
                },
                "capacity_forecasts": {
                    "total_forecasts": len(capacity_forecasts),
                    "breach_alerts": len(
                        [f for f in capacity_forecasts.values() if f.projected_breach_time is not None]
                    ),
                    "forecasts": capacity_forecasts,
                },
                "model_drift": {
                    "total_alerts": len(drift_alerts),
                    "significant_drift": len([d for d in drift_alerts if d.drift_magnitude > 0.3]),
                    "drift_alerts": drift_alerts,
                },
                "optimization_scenarios": optimization_scenarios,
                "actionable_recommendations": actionable_recommendations,
                "prediction_confidence": self._assess_overall_confidence(predictions),
            }

        except Exception as e:
            logger.error(f"Comprehensive predictions generation failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _update_historical_metrics(self) -> None:
        """Update historical metrics for prediction models."""
        try:
            if hasattr(self.enhanced_monitor, "real_time_metrics"):
                for agent_name, agent_data in self.enhanced_monitor.real_time_metrics.items():
                    recent_interactions = agent_data.get("recent_interactions", [])

                    for interaction in recent_interactions[-10:]:  # Last 10 interactions
                        timestamp = interaction.get("timestamp", datetime.now())

                        # Store quality metrics
                        quality_key = f"{agent_name}_quality"
                        if quality_key not in self.historical_metrics:
                            self.historical_metrics[quality_key] = deque(maxlen=self.max_history_size)

                        self.historical_metrics[quality_key].append(
                            {
                                "timestamp": timestamp,
                                "value": interaction.get("response_quality", 0),
                                "context": {
                                    "response_time": interaction.get("response_time", 0),
                                    "tools_used": interaction.get("tools_used", []),
                                    "error_occurred": interaction.get("error_occurred", False),
                                },
                            }
                        )

                        # Store response time metrics
                        time_key = f"{agent_name}_response_time"
                        if time_key not in self.historical_metrics:
                            self.historical_metrics[time_key] = deque(maxlen=self.max_history_size)

                        self.historical_metrics[time_key].append(
                            {
                                "timestamp": timestamp,
                                "value": interaction.get("response_time", 0),
                                "context": {
                                    "quality": interaction.get("response_quality", 0),
                                    "complexity": len(interaction.get("tools_used", [])),
                                    "success": not interaction.get("error_occurred", False),
                                },
                            }
                        )

        except Exception as e:
            logger.debug(f"Historical metrics update error: {e}")

    async def _generate_performance_predictions(
        self, prediction_horizon: int
    ) -> dict[str, list[PerformancePrediction]]:
        """Generate performance predictions for all monitored agents."""
        predictions: dict[str, Any] = {}

        try:
            for metric_name, historical_data in self.historical_metrics.items():
                if len(historical_data) >= 20:  # Need sufficient data for prediction
                    prediction = self._create_metric_prediction(metric_name, historical_data, prediction_horizon)

                    if prediction and prediction.confidence_level != PredictionConfidence.LOW:
                        agent_name = metric_name.split("_")[0]
                        if agent_name not in predictions:
                            predictions[agent_name] = []
                        predictions[agent_name].append(prediction)

        except Exception as e:
            logger.debug(f"Performance predictions error: {e}")

        return predictions

    def _create_metric_prediction(
        self, metric_name: str, historical_data: deque, horizon: int
    ) -> PerformancePrediction | None:
        """Create prediction for a specific metric."""
        try:
            # Extract values and timestamps
            values = [point["value"] for point in historical_data]

            # Prepare data for modeling
            X = np.array(range(len(values))).reshape(-1, 1)
            y = np.array(values)

            # Train simple linear regression model
            model = LinearRegression()
            model.fit(X, y)

            # Calculate model accuracy using R-squared
            accuracy = model.score(X, y)

            if accuracy < self.model_accuracy_threshold:
                return None

            # Make prediction
            future_x = len(values) + horizon
            predicted_value = model.predict([[future_x]])[0]

            # Calculate confidence interval using prediction uncertainty
            residuals = y - model.predict(X)
            mse = np.mean(residuals**2)

            # Simple confidence interval calculation
            std_error = np.sqrt(mse * (1 + 1 / len(values)))
            margin = 1.96 * std_error  # 95% confidence interval

            confidence_interval = (predicted_value - margin, predicted_value + margin)

            # Determine confidence level
            confidence_level = self._determine_confidence_level(accuracy, len(values))

            # Identify contributing factors
            contributing_factors = self._identify_contributing_factors(metric_name, historical_data)

            # Identify uncertainty factors
            uncertainty_factors = self._identify_uncertainty_factors(values, accuracy)

            return PerformancePrediction(
                metric_name=metric_name,
                prediction_horizon=horizon,
                predicted_value=predicted_value,
                confidence_interval=confidence_interval,
                confidence_level=confidence_level,
                model_accuracy=accuracy,
                prediction_timestamp=datetime.now(),
                contributing_factors=contributing_factors,
                uncertainty_factors=uncertainty_factors,
            )

        except Exception as e:
            logger.debug(f"Metric prediction failed for {metric_name}: {e}")
            return None

    def _determine_confidence_level(self, accuracy: float, data_points: int) -> PredictionConfidence:
        """Determine confidence level based on model accuracy and data availability."""
        if accuracy > 0.9 and data_points > 100:
            return PredictionConfidence.VERY_HIGH
        elif accuracy > 0.8 and data_points > 50:
            return PredictionConfidence.HIGH
        elif accuracy > 0.7 and data_points > 20:
            return PredictionConfidence.MEDIUM
        else:
            return PredictionConfidence.LOW

    def _identify_contributing_factors(self, metric_name: str, historical_data: deque) -> list[str]:
        """Identify factors contributing to metric trends."""
        factors = []

        try:
            # Analyze context data for patterns
            recent_data = list(historical_data)[-20:]  # Last 20 data points

            if "quality" in metric_name:
                # Analyze quality contributing factors
                avg_response_time = statistics.mean([d["context"].get("response_time", 0) for d in recent_data])
                error_rate = sum(1 for d in recent_data if d["context"].get("error_occurred", False)) / len(recent_data)

                if avg_response_time > 10:
                    factors.append("High response times correlating with quality")
                if error_rate > 0.1:
                    factors.append("Elevated error rates impacting quality")

                # Tool usage patterns
                tool_usage = []
                for d in recent_data:
                    tools = d["context"].get("tools_used", [])
                    tool_usage.extend(tools)

                if tool_usage:
                    common_tools = [tool for tool in set(tool_usage) if tool_usage.count(tool) > len(recent_data) * 0.3]
                    if common_tools:
                        factors.append(f"Frequent use of tools: {', '.join(common_tools)}")

            elif "response_time" in metric_name:
                # Analyze response time contributing factors
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
        """Identify factors that increase prediction uncertainty."""
        factors = []

        try:
            # Check for high variance
            if len(values) > 1:
                variance = statistics.variance(values)
                mean_val = statistics.mean(values)
                cv = variance / max(mean_val, 0.001)  # Coefficient of variation

                if cv > 0.3:
                    factors.append("High metric variability reduces prediction certainty")

            # Check for recent changes in trend
            if len(values) >= 10:
                recent_trend = self._calculate_trend_change(
                    values[-10:], values[-20:-10] if len(values) >= 20 else values[:10]
                )
                if abs(recent_trend) > 0.2:
                    factors.append("Recent trend changes increase uncertainty")

            # Model accuracy concerns
            if accuracy < 0.8:
                factors.append("Limited model accuracy affects prediction reliability")

        except Exception as e:
            logger.debug(f"Uncertainty factors analysis error: {e}")

        return factors if factors else ["Normal prediction uncertainty"]

    def _calculate_trend_change(self, recent_values: list[float], older_values: list[float]) -> float:
        """Calculate trend change between two periods."""
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

    async def _generate_early_warnings(self) -> list[EarlyWarningAlert]:
        """Generate early warning alerts based on predictive analysis."""
        warnings = []

        try:
            # Check for quality degradation warnings
            for metric_name, historical_data in self.historical_metrics.items():
                if "quality" in metric_name and len(historical_data) >= 10:
                    warning = self._check_quality_degradation_warning(metric_name, historical_data)
                    if warning:
                        warnings.append(warning)

                # Check for performance degradation warnings
                elif "response_time" in metric_name and len(historical_data) >= 10:
                    warning = self._check_performance_degradation_warning(metric_name, historical_data)
                    if warning:
                        warnings.append(warning)

            # Check for capacity warnings
            capacity_warning = await self._check_capacity_warnings()
            if capacity_warning:
                warnings.extend(capacity_warning)

        except Exception as e:
            logger.debug(f"Early warnings generation error: {e}")

        return warnings

    def _check_quality_degradation_warning(self, metric_name: str, historical_data: deque) -> EarlyWarningAlert | None:
        """Check for quality degradation warning."""
        try:
            recent_values = [point["value"] for point in list(historical_data)[-10:]]
            older_values = (
                [point["value"] for point in list(historical_data)[-20:-10]] if len(historical_data) >= 20 else []
            )

            if not older_values:
                return None

            recent_avg = statistics.mean(recent_values)
            older_avg = statistics.mean(older_values)

            # Check for significant quality decline
            decline_threshold = 0.15  # 15% decline
            decline_ratio = (older_avg - recent_avg) / max(older_avg, 0.001)

            if decline_ratio > decline_threshold:
                agent_name = metric_name.split("_")[0]

                # Calculate time to critical impact
                decline_rate = decline_ratio / 10  # Per interaction
                critical_threshold = 0.5  # Quality score below which it's critical
                interactions_to_critical = max(
                    1, (recent_avg - critical_threshold) / max(decline_rate * recent_avg, 0.001)
                )
                time_to_impact = timedelta(hours=interactions_to_critical * 0.5)  # Assume 30min per interaction

                return EarlyWarningAlert(
                    alert_id=f"quality_degradation_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
        """Check for performance degradation warning."""
        try:
            recent_values = [point["value"] for point in list(historical_data)[-10:]]
            older_values = (
                [point["value"] for point in list(historical_data)[-20:-10]] if len(historical_data) >= 20 else []
            )

            if not older_values:
                return None

            recent_avg = statistics.mean(recent_values)
            older_avg = statistics.mean(older_values)

            # Check for significant response time increase
            increase_threshold = 0.3  # 30% increase
            increase_ratio = (recent_avg - older_avg) / max(older_avg, 0.001)

            if increase_ratio > increase_threshold:
                agent_name = metric_name.split("_")[0]

                # Calculate time to critical impact
                increase_rate = increase_ratio / 10  # Per interaction
                critical_threshold = 30.0  # 30 seconds response time
                interactions_to_critical = max(
                    1, (critical_threshold - recent_avg) / max(increase_rate * recent_avg, 0.001)
                )
                time_to_impact = timedelta(hours=interactions_to_critical * 0.5)

                return EarlyWarningAlert(
                    alert_id=f"performance_degradation_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
        """Check for capacity-related warnings."""
        warnings = []

        try:
            # Check agent load distribution
            if hasattr(self.enhanced_monitor, "real_time_metrics"):
                total_interactions = 0
                agent_loads = {}

                for agent_name, agent_data in self.enhanced_monitor.real_time_metrics.items():
                    recent_interactions = len(agent_data.get("recent_interactions", []))
                    agent_loads[agent_name] = recent_interactions
                    total_interactions += recent_interactions

                if total_interactions > 0:
                    # Check for uneven load distribution
                    load_values = list(agent_loads.values())
                    if len(load_values) > 1:
                        max_load = max(load_values)  # Alert if one agent is handling more than 70% of load
                    if max_load / total_interactions > 0.7:
                        overloaded_agent = max(agent_loads.items(), key=lambda x: x[1])[0]

                        warnings.append(
                            EarlyWarningAlert(
                                alert_id=f"capacity_imbalance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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

    async def _perform_capacity_forecasting(self) -> dict[str, CapacityForecast]:
        """Perform capacity forecasting for resource planning."""
        forecasts = {}

        try:
            # Analyze interaction volume trends
            total_interactions_over_time = self._get_interaction_volume_trend()

            if len(total_interactions_over_time) >= 10:
                # Forecast interaction volume
                volume_forecast = self._forecast_interaction_volume(total_interactions_over_time)

                forecasts["interaction_volume"] = CapacityForecast(
                    resource_type="compute",
                    current_utilization=total_interactions_over_time[-1] if total_interactions_over_time else 0,
                    predicted_utilization=volume_forecast["predictions"],
                    capacity_threshold=volume_forecast["threshold"],
                    projected_breach_time=volume_forecast["breach_time"],
                    scaling_recommendations=volume_forecast["recommendations"],
                    cost_implications=volume_forecast["cost_implications"],
                )

        except Exception as e:
            logger.debug(f"Capacity forecasting error: {e}")

        return forecasts

    def _get_interaction_volume_trend(self) -> list[float]:
        """Get interaction volume trend over time."""
        try:
            # Aggregate interaction counts by time periods
            volume_data = []

            if hasattr(self.enhanced_monitor, "real_time_metrics"):
                for agent_data in self.enhanced_monitor.real_time_metrics.values():
                    recent_interactions = agent_data.get("recent_interactions", [])
                    volume_data.append(float(len(recent_interactions)))

            return volume_data

        except Exception:
            return []

    def _forecast_interaction_volume(self, historical_volumes: list[float]) -> dict[str, Any]:
        """Forecast interaction volume and capacity needs."""
        try:
            # Simple linear trend forecast
            x = np.array(range(len(historical_volumes))).reshape(-1, 1)
            y = np.array(historical_volumes)

            model = LinearRegression()
            model.fit(x, y)

            # Forecast next 12 periods
            future_periods = range(len(historical_volumes), len(historical_volumes) + 12)
            predictions = [model.predict([[period]])[0] for period in future_periods]

            # Set capacity threshold at 80% of current maximum capacity
            current_max = max(historical_volumes) if historical_volumes else 10
            threshold = current_max * 1.2  # 20% above current max

            # Find when threshold will be breached
            breach_time = None
            for i, pred in enumerate(predictions):
                if pred > threshold:
                    breach_time = datetime.now() + timedelta(hours=i)
                    break

            # Generate recommendations
            recommendations = []
            if breach_time and breach_time < datetime.now() + timedelta(days=7):
                recommendations.extend(
                    [
                        "Scale up agent infrastructure within 1 week",
                        "Implement load balancing improvements",
                        "Consider agent performance optimizations",
                    ]
                )

            # Cost implications
            cost_implications = {
                "current_baseline_cost": 100.0,  # Placeholder
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

    async def _detect_model_drift(self) -> list[ModelDriftAlert]:
        """Detect model performance drift."""
        drift_alerts = []

        try:
            for metric_name, historical_data in self.historical_metrics.items():
                if len(historical_data) >= 50:  # Need sufficient data for drift detection
                    drift_alert = self._analyze_metric_drift(metric_name, historical_data)
                    if drift_alert:
                        drift_alerts.append(drift_alert)

        except Exception as e:
            logger.debug(f"Model drift detection error: {e}")

        return drift_alerts

    def _analyze_metric_drift(self, metric_name: str, historical_data: deque) -> ModelDriftAlert | None:
        """Analyze drift for a specific metric."""
        try:
            data_points = list(historical_data)

            # Split data into baseline and recent periods
            baseline_size = len(data_points) // 2
            baseline_data = data_points[:baseline_size]
            recent_data = data_points[baseline_size:]

            baseline_values = [point["value"] for point in baseline_data]
            recent_values = [point["value"] for point in recent_data]

            # Calculate performance drift using statistical tests
            baseline_mean = statistics.mean(baseline_values)
            recent_mean = statistics.mean(recent_values)

            # Perform Kolmogorov-Smirnov test for distribution drift
            ks_statistic, p_value = stats.ks_2samp(baseline_values, recent_values)

            # Calculate drift magnitude
            drift_magnitude = abs(recent_mean - baseline_mean) / max(abs(baseline_mean), 0.001)

            # Check if drift is significant
            if ks_statistic > self.drift_detection_threshold or p_value < 0.05:
                # Determine drift type
                if "quality" in metric_name:
                    drift_type = "performance_drift"
                elif "response_time" in metric_name:
                    drift_type = "performance_drift"
                else:
                    drift_type = "data_drift"

                # Identify contributing factors
                contributing_factors = self._identify_drift_factors(baseline_data, recent_data)

                # Generate remediation suggestions
                remediation_suggestions = self._generate_drift_remediation(metric_name, drift_type, drift_magnitude)

                return ModelDriftAlert(
                    model_name=metric_name,
                    drift_type=drift_type,
                    drift_magnitude=min(1.0, drift_magnitude),
                    detection_timestamp=datetime.now(),
                    baseline_performance=baseline_mean,
                    current_performance=recent_mean,
                    contributing_factors=contributing_factors,
                    remediation_suggestions=remediation_suggestions,
                )

        except Exception as e:
            logger.debug(f"Drift analysis failed for {metric_name}: {e}")

        return None

    def _identify_drift_factors(self, baseline_data: list, recent_data: list) -> list[str]:
        """Identify factors contributing to model drift."""
        factors = []

        try:
            # Analyze context changes
            baseline_contexts = [point.get("context", {}) for point in baseline_data]
            recent_contexts = [point.get("context", {}) for point in recent_data]

            # Check for changes in error rates
            baseline_errors = sum(1 for ctx in baseline_contexts if ctx.get("error_occurred", False)) / len(
                baseline_contexts
            )
            recent_errors = sum(1 for ctx in recent_contexts if ctx.get("error_occurred", False)) / len(recent_contexts)

            if abs(recent_errors - baseline_errors) > 0.1:
                factors.append(f"Error rate changed from {baseline_errors:.1%} to {recent_errors:.1%}")

            # Check for changes in tool usage patterns
            baseline_tools = []
            recent_tools = []

            for ctx in baseline_contexts:
                baseline_tools.extend(ctx.get("tools_used", []))

            for ctx in recent_contexts:
                recent_tools.extend(ctx.get("tools_used", []))

            if baseline_tools and recent_tools:
                baseline_tool_set = set(baseline_tools)
                recent_tool_set = set(recent_tools)

                if baseline_tool_set != recent_tool_set:
                    factors.append("Changes in tool usage patterns detected")

        except Exception as e:
            logger.debug(f"Drift factors analysis error: {e}")

        return factors if factors else ["Standard operational variance"]

    def _generate_drift_remediation(self, metric_name: str, drift_type: str, magnitude: float) -> list[str]:
        """Generate remediation suggestions for model drift."""
        suggestions = []

        if drift_type == "performance_drift":
            if magnitude > 0.3:  # High magnitude drift
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

        # Add metric-specific suggestions
        if "quality" in metric_name:
            suggestions.append("Review quality assessment criteria and thresholds")
        elif "response_time" in metric_name:
            suggestions.append("Investigate infrastructure and resource constraints")

        return suggestions

    async def _generate_optimization_scenarios(self) -> dict[str, Any]:
        """Generate optimization scenarios based on predictions."""
        scenarios = {}

        try:
            # Current state analysis
            current_state = await self._analyze_current_state()

            # Generate different optimization scenarios
            scenarios["performance_optimization"] = self._create_performance_scenario(current_state)
            scenarios["cost_optimization"] = self._create_cost_scenario(current_state)
            scenarios["reliability_optimization"] = self._create_reliability_scenario(current_state)

        except Exception as e:
            logger.debug(f"Optimization scenarios generation error: {e}")

        return scenarios

    async def _analyze_current_state(self) -> dict[str, Any]:
        """Analyze current system state for optimization scenarios."""
        return {
            "total_agents": len(self.historical_metrics) // 2,  # Rough estimate
            "avg_quality": 0.75,  # Placeholder
            "avg_response_time": 5.0,  # Placeholder
            "error_rate": 0.05,  # Placeholder
            "utilization": 0.6,  # Placeholder
        }

    def _create_performance_scenario(self, current_state: dict[str, Any]) -> dict[str, Any]:
        """Create performance optimization scenario."""
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
        """Create cost optimization scenario."""
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
        """Create reliability optimization scenario."""
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

    def _calculate_prediction_reliability(self) -> float:
        """Calculate overall prediction reliability score."""
        try:
            reliability_scores = []

            for predictions in self.active_predictions.values():
                for prediction in predictions:
                    # Weight by confidence level
                    confidence_weight = {
                        PredictionConfidence.VERY_HIGH: 1.0,
                        PredictionConfidence.HIGH: 0.8,
                        PredictionConfidence.MEDIUM: 0.6,
                        PredictionConfidence.LOW: 0.3,
                    }.get(prediction.confidence_level, 0.5)

                    weighted_accuracy = prediction.model_accuracy * confidence_weight
                    reliability_scores.append(weighted_accuracy)

            return statistics.mean(reliability_scores) if reliability_scores else 0.7

        except Exception:
            return 0.7  # Default moderate reliability

    def _count_by_confidence(self, predictions: dict, confidence_level: PredictionConfidence) -> int:
        """Count predictions by confidence level."""
        count = 0
        for agent_predictions in predictions.values():
            count += sum(1 for pred in agent_predictions if pred.confidence_level == confidence_level)
        return count

    def _assess_overall_confidence(self, predictions: dict) -> dict[str, Any]:
        """Assess overall confidence in predictions."""
        total_predictions = sum(len(preds) for preds in predictions.values())

        if total_predictions == 0:
            return {"overall_confidence": "insufficient_data", "confidence_score": 0.0}

        confidence_distribution = {
            "very_high": self._count_by_confidence(predictions, PredictionConfidence.VERY_HIGH),
            "high": self._count_by_confidence(predictions, PredictionConfidence.HIGH),
            "medium": self._count_by_confidence(predictions, PredictionConfidence.MEDIUM),
            "low": self._count_by_confidence(predictions, PredictionConfidence.LOW),
        }

        # Calculate weighted confidence score
        weights = {"very_high": 1.0, "high": 0.8, "medium": 0.6, "low": 0.3}
        weighted_score = (
            sum(count * weights[level] for level, count in confidence_distribution.items()) / total_predictions
        )

        # Determine overall confidence level
        if weighted_score >= 0.8:
            overall_confidence = "high"
        elif weighted_score >= 0.6:
            overall_confidence = "medium"
        else:
            overall_confidence = "low"

        return {
            "overall_confidence": overall_confidence,
            "confidence_score": weighted_score,
            "distribution": confidence_distribution,
            "total_predictions": total_predictions,
        }

    def _generate_predictive_recommendations(
        self,
        predictions: dict,
        warnings: list[EarlyWarningAlert],
        capacity_forecasts: dict,
        drift_alerts: list[ModelDriftAlert],
    ) -> list[dict[str, Any]]:
        """Generate actionable recommendations based on predictive analysis."""
        recommendations = []

        try:
            # High-priority recommendations from warnings
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

            # Capacity-based recommendations
            for forecast_name, forecast in capacity_forecasts.items():
                if forecast.projected_breach_time:
                    recommendations.append(
                        {
                            "priority": "high",
                            "category": "capacity",
                            "title": f"Scale {forecast.resource_type.title()} Resources",
                            "description": f"Capacity threshold will be breached by {forecast.projected_breach_time.strftime('%Y-%m-%d')}",
                            "actions": forecast.scaling_recommendations,
                            "timeline": "within_week",
                            "confidence": "high",
                        }
                    )

            # Drift-based recommendations
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

            # General optimization recommendations
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


# Convenience functions for easy usage
async def run_predictive_analysis(prediction_horizon: int = 12) -> dict[str, Any]:
    """Run comprehensive predictive performance analysis.

    Args:
        prediction_horizon: Number of time periods to predict ahead

    Returns:
        Dict containing comprehensive predictive insights
    """
    predictive_engine = PredictivePerformanceInsights()
    return await predictive_engine.generate_comprehensive_predictions(prediction_horizon)


async def get_early_warning_alerts() -> list[EarlyWarningAlert]:
    """Get current early warning alerts.

    Returns:
        List of active early warning alerts
    """
    predictive_engine = PredictivePerformanceInsights()
    return await predictive_engine._generate_early_warnings()
