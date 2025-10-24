from __future__ import annotations

import logging
import math
import statistics
from typing import Any

from scipy import stats  # type: ignore[import-untyped]

from .models import PerformanceForecast


logger = logging.getLogger(__name__)


def generate_performance_forecasts(engine) -> dict[str, dict[str, Any]]:
    forecasts: dict[str, dict[str, Any]] = {}
    try:
        if hasattr(engine.enhanced_monitor, "real_time_metrics"):
            for (
                agent_name,
                agent_data,
            ) in engine.enhanced_monitor.real_time_metrics.items():
                recent_interactions = agent_data.get("recent_interactions", [])
                if len(recent_interactions) >= 15:
                    quality_values = [i.get("response_quality", 0) for i in recent_interactions]
                    quality_forecast = _generate_simple_forecast(engine, quality_values, f"{agent_name}_quality")
                    time_values = [i.get("response_time", 0) for i in recent_interactions]
                    time_forecast = _generate_simple_forecast(engine, time_values, f"{agent_name}_response_time")
                    forecasts[agent_name] = {
                        "quality_forecast": forecast_to_dict(quality_forecast),
                        "response_time_forecast": forecast_to_dict(time_forecast),
                    }
    except Exception as e:
        logger.debug(f"Forecast generation error: {e}")
    return forecasts


def _generate_simple_forecast(engine, values: list[float], metric_name: str) -> PerformanceForecast:
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
        slope, intercept, r_value, _p_value, std_err = stats.linregress(x, y)
        forecast_points: list[float] = []
        confidence_intervals: list[tuple[float, float]] = []
        for i in range(1, engine.forecast_horizon + 1):
            next_x = len(values) + i
            predicted_y = slope * next_x + intercept
            try:
                x_mean = statistics.mean(x)
                var_sum = sum((xi - x_mean) ** 2 for xi in x)
            except statistics.StatisticsError:
                x_mean, var_sum = (0.0, 1.0)
            margin = 1.96 * std_err * math.sqrt(1 + 1 / len(values) + (next_x - x_mean) ** 2 / max(var_sum, 1e-9))
            forecast_points.append(predicted_y)
            confidence_intervals.append((predicted_y - margin, predicted_y + margin))
        return PerformanceForecast(
            metric_name=metric_name,
            forecast_horizon=engine.forecast_horizon,
            predicted_values=forecast_points,
            confidence_intervals=confidence_intervals,
            forecast_accuracy=abs(r_value),
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


def forecast_to_dict(forecast: PerformanceForecast) -> dict[str, Any]:
    return {
        "metric_name": forecast.metric_name,
        "forecast_horizon": forecast.forecast_horizon,
        "predicted_values": forecast.predicted_values,
        "confidence_intervals": forecast.confidence_intervals,
        "forecast_accuracy": forecast.forecast_accuracy,
        "model_type": forecast.model_type,
    }
