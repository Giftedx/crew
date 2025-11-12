"""
Trend forecasting tool for long-term trend prediction and analysis.

This tool provides comprehensive trend forecasting including:
- Long-term trend prediction (7-30 day forecasts)
- Seasonal pattern detection and analysis
- Market cycle identification
- Trend lifecycle modeling (emergence, growth, maturity, decline)
- Cross-platform trend propagation prediction
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


class TrendDataPoint(TypedDict, total=False):
    """Individual trend data point for forecasting."""

    timestamp: float
    platform: str
    content_id: str
    engagement_metrics: dict[str, Any]
    content_metadata: dict[str, Any]
    trend_indicators: dict[str, Any]


class TrendLifecycleForecast(TypedDict, total=False):
    """Trend lifecycle forecasting result."""

    trend_id: str
    current_stage: str
    predicted_duration: float
    peak_prediction: dict[str, Any]
    decline_prediction: dict[str, Any]
    next_stage_probability: float
    confidence_score: float


class SeasonalForecast(TypedDict, total=False):
    """Seasonal pattern forecasting result."""

    pattern_type: str
    seasonal_cycle: float
    amplitude: float
    phase_offset: float
    next_peak_time: float
    next_trough_time: float
    confidence: float


class PropagationForecast(TypedDict, total=False):
    """Cross-platform trend propagation forecast."""

    source_platform: str
    target_platforms: list[str]
    propagation_delays: dict[str, float]
    amplification_factors: dict[str, float]
    total_reach_prediction: int
    propagation_confidence: float


class MarketCycleForecast(TypedDict, total=False):
    """Market cycle forecasting result."""

    cycle_type: str
    cycle_duration: float
    current_phase: str
    phase_duration: float
    next_phase_transition: float
    cycle_amplitude: float
    confidence: float


class TrendForecast(TypedDict, total=False):
    """Individual trend forecast result."""

    trend_id: str
    forecast_horizon: int
    predicted_values: list[float]
    confidence_intervals: list[dict[str, float]]
    trend_direction: str
    volatility_prediction: float
    key_events: list[dict[str, Any]]


class TrendForecastingResult(TypedDict, total=False):
    """Complete trend forecasting result."""

    lifecycle_forecasts: list[TrendLifecycleForecast]
    seasonal_forecasts: list[SeasonalForecast]
    propagation_forecasts: list[PropagationForecast]
    market_cycle_forecasts: list[MarketCycleForecast]
    trend_forecasts: list[TrendForecast]
    forecasting_insights: dict[str, Any]
    model_performance: dict[str, Any]
    processing_time: float
    metadata: dict[str, Any]


class TrendForecastingTool(BaseTool[StepResult]):
    """Advanced trend forecasting with long-term prediction capabilities."""

    name: str = "Trend Forecasting Tool"
    description: str = "Provides long-term trend forecasting, seasonal pattern detection, market cycle identification, and cross-platform trend propagation prediction."

    def __init__(
        self,
        enable_lifecycle_forecasting: bool = True,
        enable_seasonal_analysis: bool = True,
        enable_propagation_forecasting: bool = True,
        enable_market_cycle_analysis: bool = True,
        forecast_horizon_days: int = 30,
        seasonal_analysis_window: int = 90,
        confidence_threshold: float = 0.6,
    ):
        super().__init__()
        self._enable_lifecycle_forecasting = enable_lifecycle_forecasting
        self._enable_seasonal_analysis = enable_seasonal_analysis
        self._enable_propagation_forecasting = enable_propagation_forecasting
        self._enable_market_cycle_analysis = enable_market_cycle_analysis
        self._forecast_horizon_days = forecast_horizon_days
        self._seasonal_analysis_window = seasonal_analysis_window
        self._confidence_threshold = confidence_threshold
        self._metrics = get_metrics()

    def _run(
        self,
        trend_data: list[TrendDataPoint],
        historical_data: dict[str, Any] | None = None,
        forecasting_config: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
        forecast_mode: str = "comprehensive",
    ) -> StepResult:
        """
        Perform comprehensive trend forecasting analysis.

        Args:
            trend_data: Historical trend data points for analysis
            historical_data: Additional historical context data
            forecasting_config: Configuration for forecasting models
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier
            forecast_mode: Forecasting mode (basic, comprehensive, detailed)

        Returns:
            StepResult with comprehensive trend forecasting results
        """
        start_time = time.monotonic()
        try:
            if not trend_data:
                return StepResult.fail("Trend data cannot be empty")
            if tenant and workspace:
                self.note(f"Starting trend forecasting for {len(trend_data)} data points")
            lifecycle_forecasts = (
                self._forecast_trend_lifecycles(trend_data) if self._enable_lifecycle_forecasting else []
            )
            seasonal_forecasts = self._predict_seasonal_patterns(trend_data) if self._enable_seasonal_analysis else []
            propagation_forecasts = (
                self._model_cross_platform_propagation(trend_data) if self._enable_propagation_forecasting else []
            )
            market_cycle_forecasts = (
                self._identify_market_cycles(trend_data) if self._enable_market_cycle_analysis else []
            )
            trend_forecasts = self._generate_trend_forecasts(trend_data)
            forecasting_insights = self._analyze_forecasting_insights(
                lifecycle_forecasts, seasonal_forecasts, propagation_forecasts
            )
            model_performance = self._assess_model_performance(trend_data, historical_data)
            processing_time = time.monotonic() - start_time
            result: TrendForecastingResult = {
                "lifecycle_forecasts": lifecycle_forecasts,
                "seasonal_forecasts": seasonal_forecasts,
                "propagation_forecasts": propagation_forecasts,
                "market_cycle_forecasts": market_cycle_forecasts,
                "trend_forecasts": trend_forecasts,
                "forecasting_insights": forecasting_insights,
                "model_performance": model_performance,
                "processing_time": processing_time,
                "metadata": {
                    "forecast_mode": forecast_mode,
                    "data_points_analyzed": len(trend_data),
                    "forecast_horizon_days": self._forecast_horizon_days,
                    "tenant": tenant,
                    "workspace": workspace,
                    "timestamp": time.time(),
                },
            }
            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "success"}).inc()
            self._metrics.histogram("tool_run_seconds", processing_time, labels={"tool": self.name})
            return StepResult.ok(data=result)
        except Exception as e:
            processing_time = time.monotonic() - start_time
            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "error"}).inc()
            logging.exception("Trend forecasting failed")
            return StepResult.fail(f"Trend forecasting failed: {e!s}")

    def _forecast_trend_lifecycles(self, trend_data: list[TrendDataPoint]) -> list[TrendLifecycleForecast]:
        """Forecast trend lifecycles with stage predictions."""
        forecasts = []
        time.time()
        trend_groups = self._group_trends_by_characteristics(trend_data)
        for group_id, group_data in trend_groups.items():
            if len(group_data) < 5:
                continue
            current_stage = self._determine_current_lifecycle_stage(group_data)
            predicted_duration = self._predict_lifecycle_duration(group_data, current_stage)
            peak_prediction = self._predict_lifecycle_peak(group_data, current_stage)
            decline_prediction = self._predict_lifecycle_decline(group_data, current_stage)
            next_stage_probability = self._calculate_next_stage_probability(group_data, current_stage)
            confidence_score = self._calculate_lifecycle_confidence(group_data)
            if confidence_score >= self._confidence_threshold:
                forecast: TrendLifecycleForecast = {
                    "trend_id": group_id,
                    "current_stage": current_stage,
                    "predicted_duration": predicted_duration,
                    "peak_prediction": peak_prediction,
                    "decline_prediction": decline_prediction,
                    "next_stage_probability": next_stage_probability,
                    "confidence_score": confidence_score,
                }
                forecasts.append(forecast)
        return forecasts

    def _predict_seasonal_patterns(self, trend_data: list[TrendDataPoint]) -> list[SeasonalForecast]:
        """Predict seasonal patterns in trend data."""
        forecasts = []
        time.time()
        time_groups = self._group_trends_by_time_patterns(trend_data)
        for pattern_type, pattern_data in time_groups.items():
            if len(pattern_data) < 20:
                continue
            seasonal_cycle = self._detect_seasonal_cycle(pattern_data)
            amplitude = self._calculate_seasonal_amplitude(pattern_data)
            phase_offset = self._calculate_phase_offset(pattern_data)
            next_peak_time = self._predict_next_peak(pattern_data, seasonal_cycle, phase_offset)
            next_trough_time = self._predict_next_trough(pattern_data, seasonal_cycle, phase_offset)
            confidence = self._calculate_seasonal_confidence(pattern_data)
            if confidence >= self._confidence_threshold:
                forecast: SeasonalForecast = {
                    "pattern_type": pattern_type,
                    "seasonal_cycle": seasonal_cycle,
                    "amplitude": amplitude,
                    "phase_offset": phase_offset,
                    "next_peak_time": next_peak_time,
                    "next_trough_time": next_trough_time,
                    "confidence": confidence,
                }
                forecasts.append(forecast)
        return forecasts

    def _model_cross_platform_propagation(self, trend_data: list[TrendDataPoint]) -> list[PropagationForecast]:
        """Model cross-platform trend propagation."""
        forecasts = []
        time.time()
        cross_platform_trends = self._identify_cross_platform_trends(trend_data)
        for trend_id, trend_info in cross_platform_trends.items():
            source_platform = trend_info["source_platform"]
            target_platforms = trend_info["target_platforms"]
            propagation_delays = self._calculate_propagation_delays(trend_data, source_platform, target_platforms)
            amplification_factors = self._calculate_amplification_factors(trend_data, source_platform, target_platforms)
            total_reach_prediction = self._predict_total_reach(trend_data, source_platform, target_platforms)
            propagation_confidence = self._calculate_propagation_confidence(trend_data, trend_id)
            if propagation_confidence >= self._confidence_threshold:
                forecast: PropagationForecast = {
                    "source_platform": source_platform,
                    "target_platforms": target_platforms,
                    "propagation_delays": propagation_delays,
                    "amplification_factors": amplification_factors,
                    "total_reach_prediction": total_reach_prediction,
                    "propagation_confidence": propagation_confidence,
                }
                forecasts.append(forecast)
        return forecasts

    def _identify_market_cycles(self, trend_data: list[TrendDataPoint]) -> list[MarketCycleForecast]:
        """Identify and forecast market cycles."""
        forecasts = []
        time.time()
        market_cycles = self._detect_market_cycles(trend_data)
        for cycle_data in market_cycles.values():
            cycle_type = cycle_data["cycle_type"]
            cycle_duration = cycle_data["cycle_duration"]
            current_phase = cycle_data["current_phase"]
            phase_duration = cycle_data["phase_duration"]
            next_phase_transition = self._predict_next_phase_transition(cycle_data)
            cycle_amplitude = cycle_data["cycle_amplitude"]
            confidence = cycle_data["confidence"]
            if confidence >= self._confidence_threshold:
                forecast: MarketCycleForecast = {
                    "cycle_type": cycle_type,
                    "cycle_duration": cycle_duration,
                    "current_phase": current_phase,
                    "phase_duration": phase_duration,
                    "next_phase_transition": next_phase_transition,
                    "cycle_amplitude": cycle_amplitude,
                    "confidence": confidence,
                }
                forecasts.append(forecast)
        return forecasts

    def _generate_trend_forecasts(self, trend_data: list[TrendDataPoint]) -> list[TrendForecast]:
        """Generate individual trend forecasts."""
        forecasts = []
        time.time()
        trend_groups = self._group_trends_for_forecasting(trend_data)
        for trend_id, group_data in trend_groups.items():
            if len(group_data) < 10:
                continue
            forecast_horizon = self._forecast_horizon_days
            predicted_values = self._predict_trend_values(group_data, forecast_horizon)
            confidence_intervals = self._calculate_confidence_intervals(group_data, predicted_values)
            trend_direction = self._determine_trend_direction(predicted_values)
            volatility_prediction = self._predict_volatility(group_data)
            key_events = self._identify_key_events(group_data, predicted_values)
            forecast: TrendForecast = {
                "trend_id": trend_id,
                "forecast_horizon": forecast_horizon,
                "predicted_values": predicted_values,
                "confidence_intervals": confidence_intervals,
                "trend_direction": trend_direction,
                "volatility_prediction": volatility_prediction,
                "key_events": key_events,
            }
            forecasts.append(forecast)
        return forecasts

    def _group_trends_by_characteristics(self, trend_data: list[TrendDataPoint]) -> dict[str, list[TrendDataPoint]]:
        """Group trends by content characteristics."""
        groups: dict[str, list[TrendDataPoint]] = defaultdict(list)
        for data_point in trend_data:
            content_metadata = data_point.get("content_metadata", {})
            platform = data_point.get("platform", "unknown")
            content_type = content_metadata.get("content_type", "unknown")
            group_key = f"{platform}_{content_type}"
            groups[group_key].append(data_point)
        return dict(groups)

    def _group_trends_by_time_patterns(self, trend_data: list[TrendDataPoint]) -> dict[str, list[TrendDataPoint]]:
        """Group trends by time patterns."""
        groups: dict[str, list[TrendDataPoint]] = defaultdict(list)
        for data_point in trend_data:
            timestamp = data_point.get("timestamp", 0)
            hour = time.localtime(timestamp).tm_hour
            if 6 <= hour < 12:
                time_group = "morning"
            elif 12 <= hour < 18:
                time_group = "afternoon"
            elif 18 <= hour < 22:
                time_group = "evening"
            else:
                time_group = "night"
            groups[time_group].append(data_point)
        return dict(groups)

    def _identify_cross_platform_trends(self, trend_data: list[TrendDataPoint]) -> dict[str, dict[str, Any]]:
        """Identify trends that appear across multiple platforms."""
        cross_platform_trends = {}
        current_time = time.time()
        content_groups = self._group_by_content_similarity(trend_data)
        for group_id, group_data in content_groups.items():
            platforms = list({data.get("platform", "") for data in group_data})
            if len(platforms) >= 2:
                source_platform = min(
                    platforms,
                    key=lambda p: min(
                        data.get("timestamp", current_time) for data in group_data if data.get("platform") == p
                    ),
                )
                target_platforms = [p for p in platforms if p != source_platform]
                cross_platform_trends[group_id] = {
                    "source_platform": source_platform,
                    "target_platforms": target_platforms,
                    "data": group_data,
                }
        return cross_platform_trends

    def _group_by_content_similarity(self, trend_data: list[TrendDataPoint]) -> dict[str, list[TrendDataPoint]]:
        """Group trends by content similarity."""
        groups: dict[str, list[TrendDataPoint]] = defaultdict(list)
        for data_point in trend_data:
            content_metadata = data_point.get("content_metadata", {})
            keywords = content_metadata.get("keywords", [])
            if keywords:
                similarity_key = "_".join(sorted(keywords[:3]))
            else:
                similarity_key = f"unknown_{data_point.get('content_id', '')}"
            groups[similarity_key].append(data_point)
        return dict(groups)

    def _group_trends_for_forecasting(self, trend_data: list[TrendDataPoint]) -> dict[str, list[TrendDataPoint]]:
        """Group trends for individual forecasting."""
        groups: dict[str, list[TrendDataPoint]] = defaultdict(list)
        for data_point in trend_data:
            platform = data_point.get("platform", "unknown")
            content_metadata = data_point.get("content_metadata", {})
            content_type = content_metadata.get("content_type", "unknown")
            forecast_key = f"{platform}_{content_type}"
            groups[forecast_key].append(data_point)
        return dict(groups)

    def _determine_current_lifecycle_stage(self, trend_data: list[TrendDataPoint]) -> str:
        """Determine current lifecycle stage of a trend."""
        if len(trend_data) < 3:
            return "unknown"
        sorted_data = sorted(trend_data, key=lambda x: x.get("timestamp", 0))
        recent_engagement = []
        for data in sorted_data[-3:]:
            engagement = data.get("engagement_metrics", {}).get("total_engagement", 0)
            recent_engagement.append(engagement)
        if len(recent_engagement) < 2:
            return "unknown"
        growth_rate = (recent_engagement[-1] - recent_engagement[0]) / max(1, recent_engagement[0])
        if growth_rate > 0.5:
            return "growth"
        elif growth_rate > 0.1:
            return "maturity"
        elif growth_rate > -0.1:
            return "stability"
        else:
            return "decline"

    def _predict_lifecycle_duration(self, trend_data: list[TrendDataPoint], current_stage: str) -> float:
        """Predict total lifecycle duration."""
        base_durations = {"growth": 7.0, "maturity": 14.0, "stability": 21.0, "decline": 5.0}
        base_duration = base_durations.get(current_stage, 10.0)
        content_metadata = trend_data[0].get("content_metadata", {})
        content_type = content_metadata.get("content_type", "unknown")
        type_multipliers = {"video": 1.5, "image": 1.0, "text": 0.8, "audio": 1.2}
        multiplier = type_multipliers.get(content_type, 1.0)
        return base_duration * multiplier

    def _predict_lifecycle_peak(self, trend_data: list[TrendDataPoint], current_stage: str) -> dict[str, Any]:
        """Predict lifecycle peak characteristics."""
        if current_stage == "growth":
            time_to_peak = 3.0
            peak_engagement = (
                max(data.get("engagement_metrics", {}).get("total_engagement", 0) for data in trend_data) * 1.5
            )
        elif current_stage == "maturity":
            time_to_peak = 1.0
            peak_engagement = (
                max(data.get("engagement_metrics", {}).get("total_engagement", 0) for data in trend_data) * 1.2
            )
        else:
            time_to_peak = 0.0
            peak_engagement = max(data.get("engagement_metrics", {}).get("total_engagement", 0) for data in trend_data)
        return {"time_to_peak": time_to_peak, "peak_engagement": peak_engagement, "peak_duration": 2.0}

    def _predict_lifecycle_decline(self, trend_data: list[TrendDataPoint], current_stage: str) -> dict[str, Any]:
        """Predict lifecycle decline characteristics."""
        if current_stage in ["growth", "maturity"]:
            decline_start = 5.0
            decline_rate = 0.1
        else:
            decline_start = 0.0
            decline_rate = 0.2
        return {"decline_start": decline_start, "decline_rate": decline_rate, "final_engagement": 0.1}

    def _calculate_next_stage_probability(self, trend_data: list[TrendDataPoint], current_stage: str) -> float:
        """Calculate probability of transitioning to next stage."""
        stage_transitions = {
            "growth": {"maturity": 0.7, "decline": 0.3},
            "maturity": {"stability": 0.5, "decline": 0.5},
            "stability": {"decline": 0.8, "growth": 0.2},
            "decline": {"growth": 0.1, "stability": 0.1},
        }
        transitions = stage_transitions.get(current_stage, {})
        return max(transitions.values()) if transitions else 0.5

    def _calculate_lifecycle_confidence(self, trend_data: list[TrendDataPoint]) -> float:
        """Calculate confidence in lifecycle prediction."""
        if len(trend_data) < 5:
            return 0.3
        data_confidence = min(1.0, len(trend_data) / 20)
        engagement_values = [data.get("engagement_metrics", {}).get("total_engagement", 0) for data in trend_data]
        if engagement_values:
            consistency = 1.0 - (max(engagement_values) - min(engagement_values)) / max(1, max(engagement_values))
            consistency_confidence = max(0.0, consistency)
        else:
            consistency_confidence = 0.5
        return (data_confidence + consistency_confidence) / 2

    def _detect_seasonal_cycle(self, pattern_data: list[TrendDataPoint]) -> float:
        """Detect seasonal cycle length in days."""
        if len(pattern_data) < 10:
            return 7.0
        timestamps = [data.get("timestamp", 0) for data in pattern_data]
        timestamps.sort()
        time_diffs = []
        for i in range(1, len(timestamps)):
            diff = timestamps[i] - timestamps[i - 1]
            time_diffs.append(diff / 86400)
        if time_diffs:
            avg_diff = sum(time_diffs) / len(time_diffs)
            cycle_length = max(1.0, avg_diff * 4)
            return min(30.0, cycle_length)
        return 7.0

    def _calculate_seasonal_amplitude(self, pattern_data: list[TrendDataPoint]) -> float:
        """Calculate seasonal amplitude."""
        engagement_values = [data.get("engagement_metrics", {}).get("total_engagement", 0) for data in pattern_data]
        if len(engagement_values) < 2:
            return 0.0
        max_engagement = max(engagement_values)
        min_engagement = min(engagement_values)
        if max_engagement > 0:
            amplitude = (max_engagement - min_engagement) / max_engagement
            return min(1.0, amplitude)
        return 0.0

    def _calculate_phase_offset(self, pattern_data: list[TrendDataPoint]) -> float:
        """Calculate phase offset for seasonal pattern."""
        if len(pattern_data) < 5:
            return 0.0
        max_engagement = 0
        peak_time = 0
        for data in pattern_data:
            engagement = data.get("engagement_metrics", {}).get("total_engagement", 0)
            if engagement > max_engagement:
                max_engagement = engagement
                peak_time = data.get("timestamp", 0)
        current_time = time.time()
        time_since_peak = (current_time - peak_time) / 86400
        phase_offset = time_since_peak % 7 / 7 * 2 * 3.14159
        return phase_offset

    def _predict_next_peak(self, pattern_data: list[TrendDataPoint], cycle_length: float, phase_offset: float) -> float:
        """Predict next peak time."""
        current_time = time.time()
        cycle_progress = phase_offset / (2 * 3.14159)
        time_to_next_peak = cycle_length * (1 - cycle_progress)
        return current_time + time_to_next_peak * 86400

    def _predict_next_trough(
        self, pattern_data: list[TrendDataPoint], cycle_length: float, phase_offset: float
    ) -> float:
        """Predict next trough time."""
        current_time = time.time()
        cycle_progress = phase_offset / (2 * 3.14159)
        time_to_next_trough = cycle_length * (0.5 - cycle_progress)
        return current_time + time_to_next_trough * 86400

    def _calculate_seasonal_confidence(self, pattern_data: list[TrendDataPoint]) -> float:
        """Calculate confidence in seasonal pattern."""
        if len(pattern_data) < 10:
            return 0.3
        data_confidence = min(1.0, len(pattern_data) / 30)
        engagement_values = [data.get("engagement_metrics", {}).get("total_engagement", 0) for data in pattern_data]
        if len(engagement_values) >= 4:
            sorted_values = sorted(engagement_values)
            mid_point = len(sorted_values) // 2
            low_values = sorted_values[:mid_point]
            high_values = sorted_values[mid_point:]
            low_avg = sum(low_values) / len(low_values)
            high_avg = sum(high_values) / len(high_values)
            if high_avg > 0:
                pattern_strength = (high_avg - low_avg) / high_avg
                pattern_confidence = min(1.0, pattern_strength * 2)
            else:
                pattern_confidence = 0.3
        else:
            pattern_confidence = 0.3
        return (data_confidence + pattern_confidence) / 2

    def _calculate_propagation_delays(
        self, trend_data: list[TrendDataPoint], source_platform: str, target_platforms: list[str]
    ) -> dict[str, float]:
        """Calculate propagation delays between platforms."""
        delays = {}
        for target_platform in target_platforms:
            source_times = [data.get("timestamp", 0) for data in trend_data if data.get("platform") == source_platform]
            target_times = [data.get("timestamp", 0) for data in trend_data if data.get("platform") == target_platform]
            if source_times and target_times:
                source_earliest = min(source_times)
                target_earliest = min(target_times)
                delay_hours = (target_earliest - source_earliest) / 3600
                delays[target_platform] = max(0.0, delay_hours)
            else:
                delays[target_platform] = 24.0
        return delays

    def _calculate_amplification_factors(
        self, trend_data: list[TrendDataPoint], source_platform: str, target_platforms: list[str]
    ) -> dict[str, float]:
        """Calculate amplification factors for each platform."""
        factors = {}
        source_engagement = [
            data.get("engagement_metrics", {}).get("total_engagement", 0)
            for data in trend_data
            if data.get("platform") == source_platform
        ]
        source_avg = sum(source_engagement) / max(1, len(source_engagement))
        for target_platform in target_platforms:
            target_engagement = [
                data.get("engagement_metrics", {}).get("total_engagement", 0)
                for data in trend_data
                if data.get("platform") == target_platform
            ]
            if target_engagement and source_avg > 0:
                target_avg = sum(target_engagement) / len(target_engagement)
                factor = target_avg / source_avg
                factors[target_platform] = min(5.0, max(0.1, factor))
            else:
                factors[target_platform] = 1.0
        return factors

    def _predict_total_reach(
        self, trend_data: list[TrendDataPoint], source_platform: str, target_platforms: list[str]
    ) -> int:
        """Predict total reach across all platforms."""
        total_reach = 0
        for platform in [source_platform, *target_platforms]:
            platform_data = [data for data in trend_data if data.get("platform") == platform]
            for data in platform_data:
                reach = data.get("engagement_metrics", {}).get("reach", 0)
                total_reach += reach
        amplification_factors = self._calculate_amplification_factors(trend_data, source_platform, target_platforms)
        total_amplification = sum(amplification_factors.values()) + 1.0
        predicted_reach = int(total_reach * total_amplification)
        return max(total_reach, predicted_reach)

    def _calculate_propagation_confidence(self, trend_data: list[TrendDataPoint], trend_id: str) -> float:
        """Calculate confidence in propagation prediction."""
        platform_count = len({data.get("platform", "") for data in trend_data})
        data_confidence = min(1.0, platform_count / 5)
        engagement_values = [data.get("engagement_metrics", {}).get("total_engagement", 0) for data in trend_data]
        if engagement_values:
            consistency = 1.0 - (max(engagement_values) - min(engagement_values)) / max(1, max(engagement_values))
            consistency_confidence = max(0.0, consistency)
        else:
            consistency_confidence = 0.5
        return (data_confidence + consistency_confidence) / 2

    def _detect_market_cycles(self, trend_data: list[TrendDataPoint]) -> dict[str, dict[str, Any]]:
        """Detect market cycles in trend data."""
        cycles = {}
        time.time()
        sorted_data = sorted(trend_data, key=lambda x: x.get("timestamp", 0))
        if len(sorted_data) < 20:
            return cycles
        engagement_values = [data.get("engagement_metrics", {}).get("total_engagement", 0) for data in sorted_data]
        peaks = self._find_peaks(engagement_values)
        troughs = self._find_troughs(engagement_values)
        if len(peaks) >= 2 and len(troughs) >= 2:
            cycle_duration = self._calculate_cycle_duration(sorted_data, peaks, troughs)
            current_phase = self._determine_current_cycle_phase(sorted_data, peaks, troughs)
            phase_duration = self._calculate_phase_duration(cycle_duration)
            cycle_amplitude = self._calculate_cycle_amplitude(engagement_values)
            confidence = self._calculate_cycle_confidence(peaks, troughs, engagement_values)
            cycles["market_cycle"] = {
                "cycle_type": "engagement_cycle",
                "cycle_duration": cycle_duration,
                "current_phase": current_phase,
                "phase_duration": phase_duration,
                "cycle_amplitude": cycle_amplitude,
                "confidence": confidence,
            }
        return cycles

    def _find_peaks(self, values: list[float]) -> list[int]:
        """Find peaks in a series of values."""
        peaks = []
        for i in range(1, len(values) - 1):
            if values[i] > values[i - 1] and values[i] > values[i + 1]:
                peaks.append(i)
        return peaks

    def _find_troughs(self, values: list[float]) -> list[int]:
        """Find troughs in a series of values."""
        troughs = []
        for i in range(1, len(values) - 1):
            if values[i] < values[i - 1] and values[i] < values[i + 1]:
                troughs.append(i)
        return troughs

    def _calculate_cycle_duration(
        self, sorted_data: list[TrendDataPoint], peaks: list[int], troughs: list[int]
    ) -> float:
        """Calculate cycle duration in days."""
        if len(peaks) < 2:
            return 7.0
        peak_times = [sorted_data[peak].get("timestamp", 0) for peak in peaks]
        time_diffs = []
        for i in range(1, len(peak_times)):
            diff = peak_times[i] - peak_times[i - 1]
            time_diffs.append(diff / 86400)
        if time_diffs:
            avg_duration = sum(time_diffs) / len(time_diffs)
            return max(1.0, avg_duration)
        return 7.0

    def _determine_current_cycle_phase(
        self, sorted_data: list[TrendDataPoint], peaks: list[int], troughs: list[int]
    ) -> str:
        """Determine current cycle phase."""
        if not peaks or not troughs:
            return "unknown"
        recent_peak = max(peaks) if peaks else 0
        recent_trough = max(troughs) if troughs else 0
        if recent_peak > recent_trough:
            return "expansion"
        else:
            return "contraction"

    def _calculate_phase_duration(self, cycle_duration: float) -> float:
        """Calculate phase duration."""
        return cycle_duration / 2

    def _calculate_cycle_amplitude(self, engagement_values: list[float]) -> float:
        """Calculate cycle amplitude."""
        if len(engagement_values) < 2:
            return 0.0
        max_value = max(engagement_values)
        min_value = min(engagement_values)
        if max_value > 0:
            amplitude = (max_value - min_value) / max_value
            return min(1.0, amplitude)
        return 0.0

    def _calculate_cycle_confidence(
        self, peaks: list[int], troughs: list[int], engagement_values: list[float]
    ) -> float:
        """Calculate confidence in cycle detection."""
        if len(peaks) < 2 or len(troughs) < 2:
            return 0.3
        cycle_count = min(len(peaks), len(troughs))
        cycle_confidence = min(1.0, cycle_count / 5)
        amplitude = self._calculate_cycle_amplitude(engagement_values)
        amplitude_confidence = amplitude
        return (cycle_confidence + amplitude_confidence) / 2

    def _predict_next_phase_transition(self, cycle_data: dict[str, Any]) -> float:
        """Predict next phase transition time."""
        phase_duration = cycle_data.get("phase_duration", 3.5)
        time_to_transition = phase_duration * 0.5
        current_time = time.time()
        return current_time + time_to_transition * 86400

    def _predict_trend_values(self, trend_data: list[TrendDataPoint], forecast_horizon: int) -> list[float]:
        """Predict future trend values."""
        if len(trend_data) < 3:
            return [0.0] * forecast_horizon
        engagement_values = [data.get("engagement_metrics", {}).get("total_engagement", 0) for data in trend_data]
        if len(engagement_values) >= 2:
            x_values = list(range(len(engagement_values)))
            y_values = engagement_values
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum((x * y for x, y in zip(x_values, y_values, strict=False)))
            sum_x2 = sum(x * x for x in x_values)
            if n * sum_x2 - sum_x * sum_x != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                intercept = (sum_y - slope * sum_x) / n
            else:
                slope = 0
                intercept = sum_y / n
            predictions = []
            for i in range(forecast_horizon):
                future_x = len(engagement_values) + i
                predicted_value = slope * future_x + intercept
                predictions.append(max(0.0, predicted_value))
            return predictions
        return [engagement_values[-1] if engagement_values else 0.0] * forecast_horizon

    def _calculate_confidence_intervals(
        self, trend_data: list[TrendDataPoint], predicted_values: list[float]
    ) -> list[dict[str, float]]:
        """Calculate confidence intervals for predictions."""
        if not predicted_values:
            return []
        engagement_values = [data.get("engagement_metrics", {}).get("total_engagement", 0) for data in trend_data]
        if len(engagement_values) < 2:
            return [{"lower": 0.0, "upper": value * 2} for value in predicted_values]
        mean_value = sum(engagement_values) / len(engagement_values)
        variance = sum((x - mean_value) ** 2 for x in engagement_values) / len(engagement_values)
        std_dev = variance**0.5
        confidence_factor = 1.96
        intervals = []
        for value in predicted_values:
            margin_of_error = std_dev * confidence_factor
            intervals.append({"lower": max(0.0, value - margin_of_error), "upper": value + margin_of_error})
        return intervals

    def _determine_trend_direction(self, predicted_values: list[float]) -> str:
        """Determine trend direction from predicted values."""
        if len(predicted_values) < 2:
            return "stable"
        first_value = predicted_values[0]
        last_value = predicted_values[-1]
        if last_value > first_value * 1.1:
            return "increasing"
        elif last_value < first_value * 0.9:
            return "decreasing"
        else:
            return "stable"

    def _predict_volatility(self, trend_data: list[TrendDataPoint]) -> float:
        """Predict future volatility."""
        engagement_values = [data.get("engagement_metrics", {}).get("total_engagement", 0) for data in trend_data]
        if len(engagement_values) < 2:
            return 0.0
        mean_value = sum(engagement_values) / len(engagement_values)
        variance = sum((x - mean_value) ** 2 for x in engagement_values) / len(engagement_values)
        std_dev = variance**0.5
        if mean_value > 0:
            volatility = std_dev / mean_value
            return min(1.0, volatility)
        return 0.0

    def _identify_key_events(
        self, trend_data: list[TrendDataPoint], predicted_values: list[float]
    ) -> list[dict[str, Any]]:
        """Identify key events in trend forecast."""
        events = []
        if not predicted_values:
            return events
        max_value = max(predicted_values)
        max_index = predicted_values.index(max_value)
        events.append(
            {
                "type": "peak",
                "day": max_index + 1,
                "value": max_value,
                "description": f"Predicted peak engagement on day {max_index + 1}",
            }
        )
        for i in range(1, len(predicted_values)):
            change = predicted_values[i] - predicted_values[i - 1]
            change_percent = change / max(1, predicted_values[i - 1]) * 100
            if abs(change_percent) > 20:
                events.append(
                    {
                        "type": "significant_change",
                        "day": i + 1,
                        "value": predicted_values[i],
                        "change_percent": change_percent,
                        "description": f"{('Increase' if change > 0 else 'Decrease')} of {abs(change_percent):.1f}% on day {i + 1}",
                    }
                )
        return events

    def _analyze_forecasting_insights(
        self,
        lifecycle_forecasts: list[TrendLifecycleForecast],
        seasonal_forecasts: list[SeasonalForecast],
        propagation_forecasts: list[PropagationForecast],
    ) -> dict[str, Any]:
        """Analyze insights from forecasting results."""
        insights = {"summary": [], "key_findings": [], "recommendations": []}
        if lifecycle_forecasts:
            growth_trends = [f for f in lifecycle_forecasts if f["current_stage"] == "growth"]
            decline_trends = [f for f in lifecycle_forecasts if f["current_stage"] == "decline"]
            insights["summary"].append(f"Analyzed {len(lifecycle_forecasts)} trend lifecycles")
            if growth_trends:
                insights["key_findings"].append(f"{len(growth_trends)} trends in growth phase")
                insights["recommendations"].append("Consider capitalizing on growing trends")
            if decline_trends:
                insights["key_findings"].append(f"{len(decline_trends)} trends in decline phase")
                insights["recommendations"].append("Monitor declining trends for exit strategies")
        if seasonal_forecasts:
            insights["summary"].append(f"Detected {len(seasonal_forecasts)} seasonal patterns")
            for forecast in seasonal_forecasts:
                if forecast["confidence"] > 0.8:
                    insights["key_findings"].append(f"Strong seasonal pattern in {forecast['pattern_type']}")
                    insights["recommendations"].append(f"Plan content around {forecast['pattern_type']} peaks")
        if propagation_forecasts:
            insights["summary"].append(f"Identified {len(propagation_forecasts)} cross-platform trends")
            for forecast in propagation_forecasts:
                if forecast["propagation_confidence"] > 0.7:
                    insights["key_findings"].append(f"Trend propagating from {forecast['source_platform']}")
                    insights["recommendations"].append(f"Monitor {forecast['target_platforms']} for trend adoption")
        return insights

    def _assess_model_performance(
        self, trend_data: list[TrendDataPoint], historical_data: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Assess forecasting model performance."""
        performance = {"data_quality": "good", "model_confidence": 0.7, "limitations": [], "improvements": []}
        if len(trend_data) < 10:
            performance["data_quality"] = "limited"
            performance["limitations"].append("Insufficient historical data")
            performance["model_confidence"] = 0.4
        engagement_values = [data.get("engagement_metrics", {}).get("total_engagement", 0) for data in trend_data]
        if engagement_values:
            zero_values = sum(1 for v in engagement_values if v == 0)
            if zero_values / len(engagement_values) > 0.3:
                performance["limitations"].append("High proportion of zero engagement values")
                performance["model_confidence"] *= 0.8
        if len(trend_data) < 50:
            performance["improvements"].append("Collect more historical data for better predictions")
        if not historical_data:
            performance["improvements"].append("Include external factors for enhanced forecasting")
        return performance

    def run(
        self,
        trend_data: list[TrendDataPoint],
        historical_data: dict[str, Any] | None = None,
        forecasting_config: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
        forecast_mode: str = "comprehensive",
    ) -> StepResult:
        """Public interface for trend forecasting."""
        return self._run(trend_data, historical_data, forecasting_config, tenant, workspace, forecast_mode)
