from __future__ import annotations

import logging
from datetime import timedelta
from platform.time import default_utc_now
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class CapacityForecastingMixin:
    def _get_interaction_volume_trend(self) -> list[float]:
        try:
            volume_data: list[float] = []
            if hasattr(self, "enhanced_monitor") and hasattr(self.enhanced_monitor, "real_time_metrics"):
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
            try:
                from sklearn.linear_model import LinearRegression
            except Exception:
                from ..engine import LinearRegression
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
