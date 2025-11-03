from __future__ import annotations

import contextlib
import logging
import statistics
from datetime import datetime, timedelta
from typing import Any

from core.time import default_utc_now  # type: ignore[import-not-found]
from scipy import stats  # type: ignore[import-untyped]

from .models import PerformanceTrend


logger = logging.getLogger(__name__)


def _filter_recent(interactions: list[dict[str, Any]], lookback_hours: int) -> list[dict[str, Any]]:
    if lookback_hours <= 0:
        return interactions

    cutoff = default_utc_now() - timedelta(hours=lookback_hours)
    filtered: list[dict[str, Any]] = []
    for interaction in interactions:
        ts = interaction.get("timestamp")
        candidate: datetime | None
        if ts is None:
            filtered.append(interaction)
            continue
        if isinstance(ts, datetime):
            candidate = ts
        elif isinstance(ts, (int, float)):
            candidate = datetime.fromtimestamp(ts, tz=cutoff.tzinfo)
        elif isinstance(ts, str):
            candidate = None
            with contextlib.suppress(ValueError):
                candidate = datetime.fromisoformat(ts)
        else:
            candidate = None
        if candidate is None or candidate >= cutoff:
            filtered.append(interaction)
    return filtered


def analyze_performance_trends(engine, lookback_hours: int) -> list[dict[str, Any]]:
    trends: list[dict[str, Any]] = []
    try:
        if hasattr(engine.enhanced_monitor, "real_time_metrics"):
            for (
                agent_name,
                agent_data,
            ) in engine.enhanced_monitor.real_time_metrics.items():
                recent_interactions = agent_data.get("recent_interactions", [])
                filtered_interactions = _filter_recent(recent_interactions, lookback_hours)
                if len(filtered_interactions) >= 10:
                    quality_trend = analyze_metric_trend(
                        [i.get("response_quality", 0) for i in filtered_interactions],
                        f"{agent_name}_quality",
                    )
                    trends.append(trend_to_dict(quality_trend, lookback_hours=lookback_hours))
                    time_trend = analyze_metric_trend(
                        [i.get("response_time", 0) for i in filtered_interactions],
                        f"{agent_name}_response_time",
                    )
                    trends.append(trend_to_dict(time_trend, lookback_hours=lookback_hours))
                    error_rates: list[float] = []
                    window_size = 5
                    for i in range(window_size, len(filtered_interactions)):
                        window = filtered_interactions[i - window_size : i]
                        error_rate = sum(1 for w in window if w.get("error_occurred", False)) / window_size
                        error_rates.append(error_rate)
                    if error_rates:
                        error_trend = analyze_metric_trend(error_rates, f"{agent_name}_error_rate")
                        trends.append(trend_to_dict(error_trend, lookback_hours=lookback_hours))
    except Exception as e:
        logger.debug(f"Trend analysis error: {e}")
    return trends


def analyze_metric_trend(values: list[float], metric_name: str) -> PerformanceTrend:
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
    x = list(range(len(values)))
    y = values
    try:
        slope, intercept, r_value, _p_value, _std_err = stats.linregress(x, y)
        if abs(slope) < 0.001:
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "improving" if "quality" in metric_name else "declining"
        else:
            trend_direction = "declining" if "quality" in metric_name else "improving"
        change_rate = (slope * len(values)) / values[0] * 100 if len(values) > 1 and values[0] != 0 else 0.0
        forecast_next_period = slope * len(values) + intercept
        predicted = [slope * i + intercept for i in x]
        residuals = [actual - pred for actual, pred in zip(y, predicted, strict=False)]
        try:
            base_var = statistics.variance(y)
        except statistics.StatisticsError:
            base_var = 0.001
        trend_stability = max(0.0, 1.0 - (statistics.variance(residuals) / max(base_var, 0.001)))
        return PerformanceTrend(
            metric_name=metric_name,
            time_period=f"last_{len(values)}_interactions",
            trend_direction=trend_direction,
            change_rate=change_rate,
            confidence_score=abs(r_value),
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


def trend_to_dict(trend: PerformanceTrend, *, lookback_hours: int | None = None) -> dict[str, Any]:
    data = {
        "metric_name": trend.metric_name,
        "time_period": trend.time_period,
        "trend_direction": trend.trend_direction,
        "change_rate": trend.change_rate,
        "confidence_score": trend.confidence_score,
        "forecast_next_period": trend.forecast_next_period,
        "trend_stability": trend.trend_stability,
        "data_points_count": len(trend.data_points),
    }
    if lookback_hours is not None:
        data["lookback_hours"] = lookback_hours
    return data
