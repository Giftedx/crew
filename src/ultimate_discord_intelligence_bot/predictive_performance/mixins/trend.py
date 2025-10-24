from __future__ import annotations

import logging
import statistics
from typing import TYPE_CHECKING

from ..models import PredictionConfidence


if TYPE_CHECKING:
    from collections import deque


logger = logging.getLogger(__name__)


class TrendAnalysisMixin:
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
                        factors.append(f"Frequent use of tools: {', '.join(common_tools)}")
            elif "response_time" in metric_name:
                avg_complexity = statistics.mean([d["context"].get("complexity", 0) for d in recent_data])
                if avg_complexity > 3:
                    factors.append("High task complexity increasing response time")
                success_rate = sum(1 for d in recent_data if d["context"].get("success", True)) / len(recent_data)
                if success_rate < 0.9:
                    factors.append("Error handling overhead affecting response time")
        except Exception as e:  # pragma: no cover - defensive logging
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
        except Exception as e:  # pragma: no cover
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
        except Exception:  # pragma: no cover
            return 0.0
