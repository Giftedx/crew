from __future__ import annotations

import contextlib
import logging
import statistics
from typing import Any


logger = logging.getLogger(__name__)


def calculate_system_health_score(
    engine,
    trends: list[dict[str, Any]],
    anomalies: list[Any],
    dashboard_data: dict[str, Any],
) -> float:
    try:
        health_factors: list[tuple[str, float, float]] = []
        declining_trends = len([t for t in trends if t.get("trend_direction") == "declining"])
        total_trends = len(trends) if trends else 1
        trend_health = max(0.0, 1.0 - (declining_trends / total_trends))
        health_factors.append(("trend_health", trend_health, 0.3))
        critical_anomalies = len([a for a in anomalies if getattr(a, "severity", "") in ["critical", "high"]])
        anomaly_health = max(0.0, 1.0 - (critical_anomalies / 10))
        health_factors.append(("anomaly_health", anomaly_health, 0.25))
        avg_quality = 0.75
        if hasattr(engine.enhanced_monitor, "real_time_metrics"):
            quality_scores: list[float] = []
            for agent_data in engine.enhanced_monitor.real_time_metrics.values():
                recent = agent_data.get("recent_interactions", [])
                if recent:
                    scores = [i.get("response_quality", 0) for i in recent[-5:]]
                    with contextlib.suppress(statistics.StatisticsError):
                        quality_scores.append(statistics.mean(scores))
            if quality_scores:
                try:
                    avg_quality = statistics.mean(quality_scores)
                except statistics.StatisticsError:
                    avg_quality = 0.75
        health_factors.append(("performance_health", avg_quality, 0.25))
        stability_score = 0.8
        if hasattr(engine.enhanced_monitor, "real_time_metrics"):
            variance_scores: list[float] = []
            for agent_data in engine.enhanced_monitor.real_time_metrics.values():
                recent = agent_data.get("recent_interactions", [])
                if len(recent) > 5:
                    values = [i.get("response_quality", 0) for i in recent[-10:]]
                    try:
                        variance = statistics.variance(values)
                        stability = max(0.0, 1.0 - variance)
                        variance_scores.append(stability)
                    except statistics.StatisticsError:
                        pass
            if variance_scores:
                try:
                    stability_score = statistics.mean(variance_scores)
                except statistics.StatisticsError:
                    stability_score = 0.8
        health_factors.append(("stability_health", stability_score, 0.2))
        total_weighted_score = sum(score * weight for _name, score, weight in health_factors)
        return max(0.0, min(1.0, total_weighted_score))
    except Exception as e:
        logger.debug(f"Health score calculation error: {e}")
        return 0.5


def get_health_status(health_score: float) -> str:
    if health_score >= 0.9:
        return "excellent"
    elif health_score >= 0.8:
        return "good"
    elif health_score >= 0.7:
        return "fair"
    elif health_score >= 0.5:
        return "degraded"
    return "critical"


def get_key_health_indicators(engine) -> dict[str, Any]:
    try:
        if hasattr(engine.enhanced_monitor, "real_time_metrics"):
            total_agents = len(engine.enhanced_monitor.real_time_metrics)
            active_agents = len(
                [
                    agent
                    for agent, data in engine.enhanced_monitor.real_time_metrics.items()
                    if data.get("recent_interactions", [])
                ]
            )
            return {
                "total_agents_monitored": total_agents,
                "active_agents": active_agents,
                "monitoring_coverage": active_agents / total_agents if total_agents > 0 else 0,
                "recent_alerts": len(getattr(engine, "detected_anomalies", [])),
                "active_recommendations": len(getattr(engine, "active_recommendations", [])),
            }
        else:
            return {
                "total_agents_monitored": 0,
                "active_agents": 0,
                "monitoring_coverage": 0,
                "recent_alerts": 0,
                "active_recommendations": 0,
            }
    except Exception:
        return {}


def perform_comparative_analysis(engine) -> dict[str, Any]:
    try:
        if not hasattr(engine.enhanced_monitor, "real_time_metrics"):
            return {"error": "No monitoring data available"}
        import statistics as _st

        agent_performances: dict[str, dict[str, float]] = {}
        for agent_name, agent_data in engine.enhanced_monitor.real_time_metrics.items():
            recent_interactions = agent_data.get("recent_interactions", [])
            if len(recent_interactions) >= 5:
                quality_scores = [i.get("response_quality", 0) for i in recent_interactions[-10:]]
                response_times = [i.get("response_time", 0) for i in recent_interactions[-10:]]
                agent_performances[agent_name] = {
                    "avg_quality": _st.mean(quality_scores) if quality_scores else 0.0,
                    "quality_consistency": 1.0 - (_st.variance(quality_scores) if len(quality_scores) > 1 else 0.0),
                    "avg_response_time": _st.mean(response_times) if response_times else 0.0,
                    "time_consistency": 1.0
                    - (
                        (_st.variance(response_times) / max(_st.mean(response_times), 1))
                        if len(response_times) > 1
                        else 0.0
                    ),
                    "total_interactions": len(recent_interactions),
                }
        if not agent_performances:
            return {"message": "Insufficient data for comparative analysis"}
        best_quality = max(agent_performances.items(), key=lambda x: x[1]["avg_quality"])
        worst_quality = min(agent_performances.items(), key=lambda x: x[1]["avg_quality"])
        fastest_agent = min(agent_performances.items(), key=lambda x: x[1]["avg_response_time"])
        return {
            "total_agents_compared": len(agent_performances),
            "best_performers": {
                "highest_quality": {
                    "agent": best_quality[0],
                    "quality": best_quality[1]["avg_quality"],
                    "consistency": best_quality[1]["quality_consistency"],
                },
                "fastest_response": {
                    "agent": fastest_agent[0],
                    "avg_time": fastest_agent[1]["avg_response_time"],
                    "consistency": fastest_agent[1]["time_consistency"],
                },
            },
            "needs_attention": {
                "lowest_quality": {
                    "agent": worst_quality[0],
                    "quality": worst_quality[1]["avg_quality"],
                    "gap_from_best": best_quality[1]["avg_quality"] - worst_quality[1]["avg_quality"],
                }
            },
            "performance_distribution": {agent: perf["avg_quality"] for agent, perf in agent_performances.items()},
        }
    except Exception as e:
        logger.debug(f"Comparative analysis error: {e}")
        return {"error": str(e)}
