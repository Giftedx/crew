from __future__ import annotations

import logging
from typing import Any

from .models import OptimizationRecommendation, PerformanceAnomaly


logger = logging.getLogger(__name__)


def generate_recommendations(
    trends: list[dict[str, Any]],
    anomalies: list[PerformanceAnomaly],
    dashboard_data: dict[str, Any],
) -> list[OptimizationRecommendation]:
    recommendations: list[OptimizationRecommendation] = []
    try:
        for trend_data in trends:
            if trend_data.get("trend_direction") == "declining" and trend_data.get("confidence_score", 0) > 0.5:
                metric_name = trend_data.get("metric_name", "")
                if "quality" in metric_name:
                    recommendations.append(
                        OptimizationRecommendation(
                            category="quality",
                            priority="high",
                            title=f"Address Quality Decline in {metric_name.split('_')[0]}",
                            description=(
                                f"Quality metrics show declining trend with {trend_data.get('change_rate', 0):.1f}%"
                                " negative change rate"
                            ),
                            expected_impact="10-20% quality improvement",
                            implementation_effort="medium",
                            confidence_score=trend_data.get("confidence_score", 0),
                            supporting_data=trend_data,
                            action_items=[
                                "Review agent configuration and prompts",
                                "Analyze tool usage patterns",
                                "Consider model fine-tuning",
                                "Implement additional quality gates",
                            ],
                        )
                    )
                elif "response_time" in metric_name:
                    recommendations.append(
                        OptimizationRecommendation(
                            category="performance",
                            priority="medium",
                            title=f"Optimize Response Time for {metric_name.split('_')[0]}",
                            description=(
                                f"Response time increasing by {trend_data.get('change_rate', 0):.1f}% per interaction"
                            ),
                            expected_impact="15-30% latency reduction",
                            implementation_effort="low",
                            confidence_score=trend_data.get("confidence_score", 0),
                            supporting_data=trend_data,
                            action_items=[
                                "Profile agent execution pipeline",
                                "Optimize tool selection logic",
                                "Implement response caching",
                                "Review timeout configurations",
                            ],
                        )
                    )
        critical_anomalies = [a for a in anomalies if a.severity in ["critical", "high"]]
        if len(critical_anomalies) > 3:
            recommendations.append(
                OptimizationRecommendation(
                    category="reliability",
                    priority="critical",
                    title="Address Frequent Performance Anomalies",
                    description=f"Detected {len(critical_anomalies)} critical/high severity anomalies",
                    expected_impact="50-80% reduction in performance instability",
                    implementation_effort="high",
                    confidence_score=0.9,
                    supporting_data={"anomaly_count": len(critical_anomalies)},
                    action_items=[
                        "Implement automated anomaly alerting",
                        "Add circuit breaker patterns",
                        "Review resource allocation",
                        "Enhance monitoring granularity",
                    ],
                )
            )
        health = dashboard_data.get("system_health", {})
        health_status = health.get("overall_status", "unknown")
        if health_status in ["degraded", "critical"]:
            recommendations.append(
                OptimizationRecommendation(
                    category="system",
                    priority="critical",
                    title="System Health Optimization Required",
                    description=f"Overall system health is {health_status}",
                    expected_impact="Restore system to healthy state",
                    implementation_effort="high",
                    confidence_score=0.95,
                    supporting_data=health,
                    action_items=[
                        "Immediate system health assessment",
                        "Review resource utilization",
                        "Check for cascading failures",
                        "Implement emergency scaling procedures",
                    ],
                )
            )
        recommendations.append(
            OptimizationRecommendation(
                category="cost",
                priority="medium",
                title="Implement Cost-Aware Agent Routing",
                description="Optimize model selection based on task complexity and cost",
                expected_impact="20-40% cost reduction",
                implementation_effort="medium",
                confidence_score=0.7,
                supporting_data={},
                action_items=[
                    "Implement task complexity scoring",
                    "Add cost-aware model selection",
                    "Monitor cost per interaction",
                    "Set up cost alerting thresholds",
                ],
            )
        )
    except Exception as e:
        logger.debug(f"Recommendation generation error: {e}")
    return recommendations
