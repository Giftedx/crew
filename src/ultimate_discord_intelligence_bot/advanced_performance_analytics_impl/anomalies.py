from __future__ import annotations

import logging
import statistics
from datetime import timedelta

from core.time import default_utc_now

from .models import PerformanceAnomaly

logger = logging.getLogger(__name__)


def detect_performance_anomalies(engine, lookback_hours: int) -> list[PerformanceAnomaly]:
    anomalies: list[PerformanceAnomaly] = []
    try:
        if hasattr(engine.enhanced_monitor, "real_time_metrics"):
            for agent_name, agent_data in engine.enhanced_monitor.real_time_metrics.items():
                recent_interactions = agent_data.get("recent_interactions", [])
                if len(recent_interactions) >= 10:
                    quality_values = [i.get("response_quality", 0) for i in recent_interactions]
                    anomalies.extend(_detect_anomalies_in_series(engine, quality_values, f"{agent_name}_quality"))
                    time_values = [i.get("response_time", 0) for i in recent_interactions]
                    anomalies.extend(_detect_anomalies_in_series(engine, time_values, f"{agent_name}_response_time"))
    except Exception as e:
        logger.debug(f"Anomaly detection error: {e}")
    return anomalies


def _detect_anomalies_in_series(engine, values: list[float], metric_name: str) -> list[PerformanceAnomaly]:
    if len(values) < 10:
        return []
    anomalies: list[PerformanceAnomaly] = []
    try:
        window_size = min(10, len(values) // 2)
        for i in range(window_size, len(values)):
            window = values[i - window_size : i]
            current_value = values[i]
            try:
                mean_val = statistics.mean(window)
                std_val = statistics.stdev(window) if len(window) > 1 else 0
            except statistics.StatisticsError:
                mean_val, std_val = (0.0, 0.0)
            if std_val > 0:
                z_score = abs(current_value - mean_val) / std_val
                if z_score > engine.anomaly_sensitivity:
                    anomaly_type = "spike" if current_value > mean_val else "drop"
                    if z_score > 4:
                        severity = "critical"
                    elif z_score > 3:
                        severity = "high"
                    elif z_score > 2.5:
                        severity = "medium"
                    else:
                        severity = "low"
                    anomalies.append(
                        PerformanceAnomaly(
                            timestamp=default_utc_now() - timedelta(minutes=(len(values) - i) * 5),
                            metric_name=metric_name,
                            expected_value=mean_val,
                            actual_value=current_value,
                            severity=severity,
                            anomaly_type=anomaly_type,
                            context={"z_score": z_score, "window_mean": mean_val, "window_std": std_val, "i": i},
                        )
                    )
    except Exception as e:
        logger.debug(f"Anomaly detection failed for {metric_name}: {e}")
    return anomalies
