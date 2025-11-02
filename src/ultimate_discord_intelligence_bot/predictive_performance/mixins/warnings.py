from __future__ import annotations

import logging
import statistics
from datetime import timedelta
from platform.time import default_utc_now
from typing import TYPE_CHECKING

from ..models import AlertSeverity, EarlyWarningAlert, PredictionConfidence


if TYPE_CHECKING:
    from collections import deque
logger = logging.getLogger(__name__)


class WarningDetectionMixin:
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
                    alert_id=f"quality_degradation_{agent_name}_{default_utc_now().strftime('%Y%m%d_%H%M%S')}",
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
                    alert_id=f"performance_degradation_{agent_name}_{default_utc_now().strftime('%Y%m%d_%H%M%S')}",
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
            if hasattr(self, "enhanced_monitor") and hasattr(self.enhanced_monitor, "real_time_metrics"):
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
                                    alert_id=f"capacity_imbalance_{default_utc_now().strftime('%Y%m%d_%H%M%S')}",
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
