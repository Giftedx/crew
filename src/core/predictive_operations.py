"""
Predictive Performance Optimization System for Ultimate Discord Intelligence Bot.

This module provides AI-driven performance optimization including:
- Real-time performance prediction and forecasting
- Intelligent resource allocation and scaling
- Automated performance tuning and optimization
- Proactive bottleneck detection and resolution
- Advanced telemetry and performance analytics
"""

from __future__ import annotations

import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .error_handling import log_error

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Performance optimization strategies."""

    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    ADAPTIVE = "adaptive"


class ResourceType(Enum):
    """Types of system resources."""

    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    STORAGE = "storage"
    CONNECTIONS = "connections"


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""

    timestamp: datetime
    metric_name: str
    value: float
    resource_type: ResourceType
    component: str
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class ResourcePrediction:
    """Resource usage prediction."""

    resource_type: ResourceType
    predicted_value: float
    confidence: float
    time_horizon: timedelta
    prediction_timestamp: datetime = field(default_factory=datetime.utcnow)
    factors: list[str] = field(default_factory=list)


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation."""

    recommendation_id: str
    strategy: OptimizationStrategy
    description: str
    expected_improvement: float
    implementation_effort: str  # low, medium, high
    priority: str  # low, medium, high, critical
    affected_components: list[str]
    implementation_steps: list[str]
    estimated_impact: dict[str, float] = field(default_factory=dict)


@dataclass
class SystemCapacity:
    """System capacity analysis."""

    current_utilization: dict[ResourceType, float]
    peak_utilization: dict[ResourceType, float]
    projected_utilization: dict[ResourceType, float]
    capacity_headroom: dict[ResourceType, float]
    scale_triggers: dict[ResourceType, float]


class TimeSeriesAnalyzer:
    """Time series analysis for performance prediction."""

    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.metrics_buffer: dict[str, deque[PerformanceMetric]] = defaultdict(lambda: deque(maxlen=window_size))

    def add_metric(self, metric: PerformanceMetric) -> None:
        """Add new metric to time series."""
        key = f"{metric.component}:{metric.metric_name}"
        self.metrics_buffer[key].append(metric)

    def predict_trend(self, component: str, metric_name: str, horizon_minutes: int = 30) -> ResourcePrediction | None:
        """Predict metric trend using time series analysis."""
        key = f"{component}:{metric_name}"
        metrics_data = list(self.metrics_buffer.get(key, []))

        if len(metrics_data) < 10:  # Need minimum data points
            return None

        # Extract values and timestamps
        values = [m.value for m in metrics_data]
        timestamps = [m.timestamp.timestamp() for m in metrics_data]

        # Simple linear regression for trend prediction
        predicted_value, confidence = self._linear_regression_predict(timestamps, values, horizon_minutes * 60)

        # Determine resource type from first metric
        resource_type = metrics_data[0].resource_type

        return ResourcePrediction(
            resource_type=resource_type,
            predicted_value=predicted_value,
            confidence=confidence,
            time_horizon=timedelta(minutes=horizon_minutes),
            factors=self._identify_trend_factors(values),
        )

    def detect_anomalies(self, component: str, metric_name: str) -> list[PerformanceMetric]:
        """Detect anomalous performance metrics."""
        key = f"{component}:{metric_name}"
        metrics_data = list(self.metrics_buffer.get(key, []))

        if len(metrics_data) < 20:
            return []

        values = [m.value for m in metrics_data]

        # Calculate statistical thresholds
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0

        # Identify anomalies (values beyond 2 standard deviations)
        anomalies = []
        threshold = 2 * std_val

        for metric in metrics_data[-10:]:  # Check recent metrics
            if abs(metric.value - mean_val) > threshold:
                anomalies.append(metric)

        return anomalies

    def calculate_seasonality(self, component: str, metric_name: str) -> dict[str, float]:
        """Calculate seasonal patterns in metrics."""
        key = f"{component}:{metric_name}"
        metrics_data = list(self.metrics_buffer.get(key, []))

        if len(metrics_data) < 100:
            return {}

        # Group by hour of day
        hourly_patterns = defaultdict(list)
        for metric in metrics_data:
            hour = metric.timestamp.hour
            hourly_patterns[hour].append(metric.value)

        # Calculate average for each hour
        patterns = {}
        for hour, values in hourly_patterns.items():
            if values:
                patterns[f"hour_{hour}"] = statistics.mean(values)

        return patterns

    def _linear_regression_predict(
        self, x_values: list[float], y_values: list[float], future_x: float
    ) -> tuple[float, float]:
        """Simple linear regression prediction."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0, 0.0

        n = len(x_values)

        # Calculate regression coefficients
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        # Avoid division by zero
        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-10:
            return statistics.mean(y_values), 0.5

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        # Predict future value
        last_x = max(x_values)
        predicted_x = last_x + future_x
        predicted_value = slope * predicted_x + intercept

        # Calculate confidence (simplified R-squared)
        y_mean = statistics.mean(y_values)
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values))

        confidence = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.5
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

        return predicted_value, confidence

    def _identify_trend_factors(self, values: list[float]) -> list[str]:
        """Identify factors contributing to trends."""
        factors = []

        if len(values) < 2:
            return factors

        # Calculate trend direction
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        if statistics.mean(second_half) > statistics.mean(first_half):
            factors.append("increasing_trend")
        elif statistics.mean(second_half) < statistics.mean(first_half):
            factors.append("decreasing_trend")
        else:
            factors.append("stable_trend")

        # Check volatility
        if len(values) > 1:
            volatility = statistics.stdev(values) / statistics.mean(values) if statistics.mean(values) != 0 else 0
            if volatility > 0.3:
                factors.append("high_volatility")
            elif volatility < 0.1:
                factors.append("low_volatility")

        return factors


class PerformanceOptimizer:
    """Intelligent performance optimization engine."""

    def __init__(self, strategy: OptimizationStrategy = OptimizationStrategy.BALANCED):
        self.strategy = strategy
        self.optimization_rules = self._load_optimization_rules()
        self.applied_optimizations: dict[str, datetime] = {}

    def analyze_system_performance(self, metrics: list[PerformanceMetric]) -> list[OptimizationRecommendation]:
        """Analyze system performance and generate recommendations."""
        recommendations = []

        # Group metrics by component and resource type
        component_metrics = self._group_metrics_by_component(metrics)

        for component, comp_metrics in component_metrics.items():
            comp_recommendations = self._analyze_component_performance(component, comp_metrics)
            recommendations.extend(comp_recommendations)

        # Sort by priority and expected impact
        recommendations.sort(key=lambda x: (self._priority_score(x.priority), -x.expected_improvement))

        return recommendations

    def optimize_resource_allocation(self, capacity: SystemCapacity) -> dict[ResourceType, float]:
        """Optimize resource allocation based on predictions."""
        optimized_allocation = {}

        for resource_type, current_util in capacity.current_utilization.items():
            projected_util = capacity.projected_utilization.get(resource_type, current_util)
            headroom = capacity.capacity_headroom.get(resource_type, 0.2)

            # Calculate optimal allocation
            if projected_util > 0.8:  # High utilization
                optimized_allocation[resource_type] = min(1.0, projected_util + headroom)
            elif projected_util < 0.3:  # Low utilization
                optimized_allocation[resource_type] = max(0.1, projected_util - headroom / 2)
            else:
                optimized_allocation[resource_type] = projected_util

        return optimized_allocation

    def generate_scaling_recommendations(
        self, predictions: list[ResourcePrediction]
    ) -> list[OptimizationRecommendation]:
        """Generate scaling recommendations based on predictions."""
        recommendations = []

        for prediction in predictions:
            if prediction.confidence < 0.6:  # Low confidence predictions
                continue

            if prediction.predicted_value > 0.85:  # Scale up trigger
                rec = OptimizationRecommendation(
                    recommendation_id=f"scale_up_{prediction.resource_type.value}_{int(time.time())}",
                    strategy=self.strategy,
                    description=f"Scale up {prediction.resource_type.value} resources",
                    expected_improvement=0.3,
                    implementation_effort="medium",
                    priority="high",
                    affected_components=[prediction.resource_type.value],
                    implementation_steps=[
                        f"Increase {prediction.resource_type.value} allocation by 25%",
                        "Monitor performance impact",
                        "Adjust allocation as needed",
                    ],
                    estimated_impact={
                        "latency_reduction": 15.0,
                        "throughput_increase": 20.0,
                    },
                )
                recommendations.append(rec)

            elif prediction.predicted_value < 0.3:  # Scale down opportunity
                rec = OptimizationRecommendation(
                    recommendation_id=f"scale_down_{prediction.resource_type.value}_{int(time.time())}",
                    strategy=self.strategy,
                    description=f"Scale down {prediction.resource_type.value} resources",
                    expected_improvement=0.2,
                    implementation_effort="low",
                    priority="medium",
                    affected_components=[prediction.resource_type.value],
                    implementation_steps=[
                        f"Reduce {prediction.resource_type.value} allocation by 15%",
                        "Monitor for performance degradation",
                        "Implement gradual reduction",
                    ],
                    estimated_impact={
                        "cost_reduction": 15.0,
                        "efficiency_increase": 10.0,
                    },
                )
                recommendations.append(rec)

        return recommendations

    def _group_metrics_by_component(self, metrics: list[PerformanceMetric]) -> dict[str, list[PerformanceMetric]]:
        """Group metrics by component."""
        component_metrics = defaultdict(list)
        for metric in metrics:
            component_metrics[metric.component].append(metric)
        return dict(component_metrics)

    def _analyze_component_performance(
        self, component: str, metrics: list[PerformanceMetric]
    ) -> list[OptimizationRecommendation]:
        """Analyze performance of a specific component."""
        recommendations = []

        # Analyze CPU metrics
        cpu_metrics = [m for m in metrics if m.resource_type == ResourceType.CPU]
        if cpu_metrics:
            cpu_recommendations = self._analyze_cpu_performance(component, cpu_metrics)
            recommendations.extend(cpu_recommendations)

        # Analyze memory metrics
        memory_metrics = [m for m in metrics if m.resource_type == ResourceType.MEMORY]
        if memory_metrics:
            memory_recommendations = self._analyze_memory_performance(component, memory_metrics)
            recommendations.extend(memory_recommendations)

        # Analyze network metrics
        network_metrics = [m for m in metrics if m.resource_type == ResourceType.NETWORK]
        if network_metrics:
            network_recommendations = self._analyze_network_performance(component, network_metrics)
            recommendations.extend(network_recommendations)

        return recommendations

    def _analyze_cpu_performance(
        self, component: str, metrics: list[PerformanceMetric]
    ) -> list[OptimizationRecommendation]:
        """Analyze CPU performance and generate recommendations."""
        recommendations = []

        if not metrics:
            return recommendations

        avg_cpu = statistics.mean([m.value for m in metrics])

        if avg_cpu > 0.8:  # High CPU usage
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=f"cpu_opt_{component}_{int(time.time())}",
                    strategy=self.strategy,
                    description=f"Optimize CPU usage for {component}",
                    expected_improvement=0.25,
                    implementation_effort="medium",
                    priority="high",
                    affected_components=[component],
                    implementation_steps=[
                        "Profile CPU-intensive operations",
                        "Implement caching for expensive computations",
                        "Optimize algorithms and data structures",
                        "Consider asynchronous processing",
                    ],
                    estimated_impact={
                        "cpu_reduction": 20.0,
                        "response_time_improvement": 15.0,
                    },
                )
            )

        return recommendations

    def _analyze_memory_performance(
        self, component: str, metrics: list[PerformanceMetric]
    ) -> list[OptimizationRecommendation]:
        """Analyze memory performance and generate recommendations."""
        recommendations = []

        if not metrics:
            return recommendations

        avg_memory = statistics.mean([m.value for m in metrics])

        if avg_memory > 0.85:  # High memory usage
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=f"memory_opt_{component}_{int(time.time())}",
                    strategy=self.strategy,
                    description=f"Optimize memory usage for {component}",
                    expected_improvement=0.3,
                    implementation_effort="high",
                    priority="high",
                    affected_components=[component],
                    implementation_steps=[
                        "Analyze memory allocation patterns",
                        "Implement memory pooling",
                        "Optimize data structures",
                        "Add garbage collection tuning",
                    ],
                    estimated_impact={
                        "memory_reduction": 25.0,
                        "gc_pause_reduction": 30.0,
                    },
                )
            )

        return recommendations

    def _analyze_network_performance(
        self, component: str, metrics: list[PerformanceMetric]
    ) -> list[OptimizationRecommendation]:
        """Analyze network performance and generate recommendations."""
        recommendations = []

        if not metrics:
            return recommendations

        # Analyze for high latency patterns
        latency_metrics = [m for m in metrics if "latency" in m.metric_name.lower()]
        if latency_metrics:
            avg_latency = statistics.mean([m.value for m in latency_metrics])

            if avg_latency > 100:  # High latency (100ms)
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=f"network_opt_{component}_{int(time.time())}",
                        strategy=self.strategy,
                        description=f"Optimize network performance for {component}",
                        expected_improvement=0.4,
                        implementation_effort="medium",
                        priority="medium",
                        affected_components=[component],
                        implementation_steps=[
                            "Implement connection pooling",
                            "Add request batching",
                            "Optimize serialization",
                            "Consider CDN for static content",
                        ],
                        estimated_impact={
                            "latency_reduction": 35.0,
                            "throughput_increase": 25.0,
                        },
                    )
                )

        return recommendations

    def _load_optimization_rules(self) -> dict[str, Any]:
        """Load optimization rules and thresholds."""
        return {
            "cpu_thresholds": {
                "high": 0.8,
                "critical": 0.9,
            },
            "memory_thresholds": {
                "high": 0.85,
                "critical": 0.95,
            },
            "latency_thresholds": {
                "high": 100,  # ms
                "critical": 500,  # ms
            },
        }

    def _priority_score(self, priority: str) -> int:
        """Convert priority to numeric score for sorting."""
        scores = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return scores.get(priority, 4)


class PredictiveOperationsEngine:
    """Main predictive operations orchestrator."""

    def __init__(self):
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.performance_optimizer = PerformanceOptimizer()
        self.metrics_history: dict[str, list[PerformanceMetric]] = defaultdict(list)

    async def process_performance_data(self, metrics: list[PerformanceMetric]) -> dict[str, Any]:
        """Process performance data and generate insights."""
        try:
            # Store metrics for historical analysis
            for metric in metrics:
                self.time_series_analyzer.add_metric(metric)
                key = f"{metric.component}:{metric.metric_name}"
                self.metrics_history[key].append(metric)

            # Generate predictions
            predictions = await self._generate_predictions(metrics)

            # Generate optimization recommendations
            recommendations = self.performance_optimizer.analyze_system_performance(metrics)

            # Detect anomalies
            anomalies = await self._detect_performance_anomalies(metrics)

            # Calculate system capacity
            capacity = self._calculate_system_capacity(metrics)

            # Generate scaling recommendations
            scaling_recommendations = self.performance_optimizer.generate_scaling_recommendations(predictions)

            return {
                "predictions": predictions,
                "recommendations": recommendations + scaling_recommendations,
                "anomalies": anomalies,
                "capacity_analysis": capacity,
                "optimization_summary": self._generate_optimization_summary(recommendations),
            }

        except Exception as e:
            log_error(e, message="Failed to process performance data")
            return {}

    async def _generate_predictions(self, metrics: list[PerformanceMetric]) -> list[ResourcePrediction]:
        """Generate performance predictions."""
        predictions = []

        # Get unique component-metric combinations
        unique_combinations = set()
        for metric in metrics:
            unique_combinations.add((metric.component, metric.metric_name))

        # Generate predictions for each combination
        for component, metric_name in unique_combinations:
            prediction = self.time_series_analyzer.predict_trend(component, metric_name)
            if prediction:
                predictions.append(prediction)

        return predictions

    async def _detect_performance_anomalies(self, metrics: list[PerformanceMetric]) -> list[PerformanceMetric]:
        """Detect performance anomalies."""
        all_anomalies = []

        # Get unique component-metric combinations
        unique_combinations = set()
        for metric in metrics:
            unique_combinations.add((metric.component, metric.metric_name))

        # Detect anomalies for each combination
        for component, metric_name in unique_combinations:
            anomalies = self.time_series_analyzer.detect_anomalies(component, metric_name)
            all_anomalies.extend(anomalies)

        return all_anomalies

    def _calculate_system_capacity(self, metrics: list[PerformanceMetric]) -> SystemCapacity:
        """Calculate current system capacity."""
        # Group metrics by resource type
        resource_metrics = defaultdict(list)
        for metric in metrics:
            resource_metrics[metric.resource_type].append(metric.value)

        current_utilization = {}
        peak_utilization = {}
        projected_utilization = {}
        capacity_headroom = {}
        scale_triggers = {}

        for resource_type, values in resource_metrics.items():
            if values:
                current_utilization[resource_type] = statistics.mean(values)
                peak_utilization[resource_type] = max(values)

                # Simple projection (could be more sophisticated)
                projected_utilization[resource_type] = min(1.0, current_utilization[resource_type] * 1.1)

                # Calculate headroom
                capacity_headroom[resource_type] = 1.0 - peak_utilization[resource_type]

                # Set scale triggers
                scale_triggers[resource_type] = 0.8  # Scale when 80% utilized

        return SystemCapacity(
            current_utilization=current_utilization,
            peak_utilization=peak_utilization,
            projected_utilization=projected_utilization,
            capacity_headroom=capacity_headroom,
            scale_triggers=scale_triggers,
        )

    def _generate_optimization_summary(self, recommendations: list[OptimizationRecommendation]) -> dict[str, Any]:
        """Generate optimization summary."""
        if not recommendations:
            return {
                "total_recommendations": 0,
                "potential_improvement": 0.0,
                "priority_breakdown": {},
            }

        priority_breakdown = defaultdict(int)
        total_improvement = 0.0

        for rec in recommendations:
            priority_breakdown[rec.priority] += 1
            total_improvement += rec.expected_improvement

        return {
            "total_recommendations": len(recommendations),
            "potential_improvement": total_improvement,
            "priority_breakdown": dict(priority_breakdown),
            "top_recommendation": recommendations[0].description if recommendations else None,
        }


__all__ = [
    "PredictiveOperationsEngine",
    "PerformanceOptimizer",
    "TimeSeriesAnalyzer",
    "PerformanceMetric",
    "ResourcePrediction",
    "OptimizationRecommendation",
    "SystemCapacity",
    "OptimizationStrategy",
    "ResourceType",
]
