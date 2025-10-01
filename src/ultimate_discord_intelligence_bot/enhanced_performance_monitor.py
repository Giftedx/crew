#!/usr/bin/env python3
"""
Enhanced Agent Performance Monitoring System

This module extends the existing AgentPerformanceMonitor with:
1. Real-time performance dashboards
2. Automated alerting for performance degradation
3. Enhanced integration with Discord bot
4. Predictive performance analysis
5. Comparative agent analysis
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from core.time import default_utc_now
from ultimate_discord_intelligence_bot.agent_training.performance_monitor import AgentPerformanceMonitor


class EnhancedPerformanceMonitor:
    """Enhanced performance monitoring with real-time capabilities and alerting."""

    def __init__(self, base_monitor: AgentPerformanceMonitor = None):
        self.base_monitor = base_monitor or AgentPerformanceMonitor()
        self.alerts_enabled = True
        self.real_time_metrics: dict[str, Any] = {}
        self.performance_thresholds = {
            "critical_accuracy_drop": 0.15,  # 15% drop triggers alert
            "response_time_spike": 2.0,  # 2x normal response time
            "error_rate_spike": 0.20,  # 20% error rate
            "tool_failure_rate": 0.30,  # 30% tool failure rate
        }

        self.logger = logging.getLogger(__name__)

    async def real_time_quality_assessment(self, response: str, context: dict[str, Any]) -> float:
        """Enhanced real-time quality assessment with context awareness."""
        quality_score = 0.0

        # 1. Content Quality (40% weight)
        content_score = self._assess_content_quality(response, context)
        quality_score += content_score * 0.4

        # 2. Factual Accuracy (30% weight)
        accuracy_score = await self._assess_factual_accuracy(response, context)
        quality_score += accuracy_score * 0.3

        # 3. Reasoning Quality (20% weight)
        reasoning_score = self._assess_reasoning_quality(response)
        quality_score += reasoning_score * 0.2

        # 4. User Experience (10% weight)
        ux_score = self._assess_user_experience(response, context)
        quality_score += ux_score * 0.1

        return min(1.0, quality_score)

    def _assess_content_quality(self, response: str, context: dict[str, Any]) -> float:
        """Assess content quality with context awareness."""
        score = 0.0

        # Length appropriateness based on task type
        task_type = context.get("task_type", "general")
        if task_type == "summary":
            target_length = (100, 500)
        elif task_type == "analysis":
            target_length = (300, 1500)
        elif task_type == "fact_check":
            target_length = (150, 800)
        else:
            target_length = (50, 1000)

        response_length = len(response)
        if target_length[0] <= response_length <= target_length[1]:
            score += 0.3
        elif response_length > target_length[1] * 0.8:  # 80% of max is still good
            score += 0.2

        # Content structure
        if any(marker in response for marker in ["1.", "2.", "•", "-", "*"]):
            score += 0.2  # Well-structured

        # Evidence and sources
        if any(phrase in response.lower() for phrase in ["source:", "according to", "verified by", "evidence shows"]):
            score += 0.3

        # Professional language
        if not any(phrase in response.lower() for phrase in ["i think", "maybe", "probably", "i guess"]):
            score += 0.2

        return min(1.0, score)

    async def _assess_factual_accuracy(self, response: str, context: dict[str, Any]) -> float:
        """Assess factual accuracy using various signals."""
        score = 0.0

        # Check for uncertainty indicators (good for accuracy)
        uncertainty_phrases = ["according to", "appears to", "suggests that", "evidence indicates"]
        if any(phrase in response.lower() for phrase in uncertainty_phrases):
            score += 0.3

        # Check for specific citations or references
        if any(phrase in response.lower() for phrase in ["source", "study", "research", "report", "data shows"]):
            score += 0.4

        # Check for absence of absolute claims without evidence
        absolute_phrases = ["definitely", "certainly", "absolutely", "always", "never"]
        absolute_count = sum(1 for phrase in absolute_phrases if phrase in response.lower())
        if absolute_count == 0:
            score += 0.3
        elif absolute_count <= 2:
            score += 0.1

        return min(1.0, score)

    def _assess_reasoning_quality(self, response: str) -> float:
        """Assess quality of reasoning and logical flow."""
        score = 0.0

        # Logical connectors
        connectors = [
            "because",
            "therefore",
            "however",
            "moreover",
            "furthermore",
            "consequently",
            "as a result",
            "due to",
            "given that",
        ]
        connector_count = sum(1 for conn in connectors if conn in response.lower())
        if connector_count >= 2:
            score += 0.4
        elif connector_count >= 1:
            score += 0.2

        # Evidence-based reasoning
        evidence_phrases = ["analysis shows", "data indicates", "research suggests", "evidence supports", "based on"]
        if any(phrase in response.lower() for phrase in evidence_phrases):
            score += 0.3

        # Multiple perspectives or balanced view
        balance_phrases = ["on the other hand", "alternatively", "however", "while", "although"]
        if any(phrase in response.lower() for phrase in balance_phrases):
            score += 0.3

        return min(1.0, score)

    def _assess_user_experience(self, response: str, context: dict[str, Any]) -> float:
        """Assess user experience factors."""
        score = 0.0

        # Clear formatting
        if "\n\n" in response or response.count("\n") >= 2:
            score += 0.3  # Good paragraph breaks

        # Appropriate tone for context
        if context.get("channel_type") == "professional":
            if not any(phrase in response.lower() for phrase in ["lol", "omg", "wtf"]):
                score += 0.2

        # Actionable information
        action_phrases = ["you can", "try", "consider", "recommend", "suggest"]
        if any(phrase in response.lower() for phrase in action_phrases):
            score += 0.3

        # No error indicators
        if not any(
            phrase in response.lower() for phrase in ["error", "failed", "unable to", "couldn't", "can't process"]
        ):
            score += 0.2

        return min(1.0, score)

    async def monitor_real_time_performance(self, agent_name: str, interaction_data: dict[str, Any]) -> dict[str, Any]:
        """Monitor performance in real-time and trigger alerts if needed."""

        # Update real-time metrics
        if agent_name not in self.real_time_metrics:
            self.real_time_metrics[agent_name] = {
                "recent_interactions": [],
                "current_session_stats": {
                    "total_requests": 0,
                    "avg_quality": 0.0,
                    "avg_response_time": 0.0,
                    "error_count": 0,
                    "session_start": default_utc_now().isoformat(),
                },
            }

        # Add to recent interactions (keep last 50)
        agent_metrics = self.real_time_metrics[agent_name]
        agent_metrics["recent_interactions"].append({**interaction_data, "timestamp": default_utc_now().isoformat()})

        if len(agent_metrics["recent_interactions"]) > 50:
            agent_metrics["recent_interactions"] = agent_metrics["recent_interactions"][-50:]

        # Update session stats
        session_stats = agent_metrics["current_session_stats"]
        session_stats["total_requests"] += 1

        # Calculate rolling averages
        recent = agent_metrics["recent_interactions"][-10:]  # Last 10 interactions
        if recent:
            session_stats["avg_quality"] = sum(i.get("response_quality", 0) for i in recent) / len(recent)
            session_stats["avg_response_time"] = sum(i.get("response_time", 0) for i in recent) / len(recent)
            session_stats["error_count"] = sum(1 for i in recent if i.get("error_occurred", False))

        # Check for performance alerts
        alerts = await self._check_performance_alerts(agent_name, recent)

        return {
            "agent_name": agent_name,
            "current_performance": session_stats,
            "alerts": alerts,
            "recent_trend": self._calculate_recent_trend(recent),
        }

    async def record_interaction_async(
        self,
        agent_name: str,
        interaction_type: str,
        quality_score: float,
        response_time: float,
        context: dict[str, Any] | None = None,
        tools_used: list[str] | None = None,
        error_occurred: bool = False,
    ) -> dict[str, Any]:
        """Asynchronously persist interaction details and refresh monitoring state."""

        context = context or {}
        interaction_payload = {
            "task_type": interaction_type,
            "tools_used": tools_used or context.get("tools_used", []),
            "tool_sequence": context.get("tool_sequence", []),
            "response_quality": quality_score,
            "response_time": response_time,
            "user_feedback": context.get("user_feedback", {}),
            "error_occurred": error_occurred or context.get("error_occurred", False),
            "error_details": context.get("error_details", {}),
        }
        # Merge any custom context values for downstream analytics
        interaction_payload.update({k: v for k, v in context.items() if k not in interaction_payload})

        # Update real-time dashboard first so alerts reflect this interaction
        dashboard_state = await self.monitor_real_time_performance(agent_name, interaction_payload)

        try:
            self.base_monitor.record_agent_interaction(
                agent_name=agent_name,
                task_type=interaction_type,
                tools_used=interaction_payload.get("tools_used", []),
                tool_sequence=interaction_payload.get("tool_sequence", []),
                response_quality=quality_score,
                response_time=response_time,
                user_feedback=interaction_payload.get("user_feedback"),
                error_occurred=interaction_payload.get("error_occurred", False),
                error_details=interaction_payload.get("error_details"),
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.debug("Failed to persist interaction via base monitor: %s", exc)

        return dashboard_state

    async def _check_performance_alerts(self, agent_name: str, recent_interactions: list[dict]) -> list[dict[str, Any]]:
        """Check for performance issues that require alerts."""
        alerts: list[dict[str, Any]] = []

        if len(recent_interactions) < 5:
            return alerts  # Need minimum data for reliable alerts

        # 1. Quality degradation alert
        recent_quality = [i.get("response_quality", 0) for i in recent_interactions[-5:]]
        earlier_quality = [i.get("response_quality", 0) for i in recent_interactions[-10:-5]]

        if recent_quality and earlier_quality:
            recent_avg = sum(recent_quality) / len(recent_quality)
            earlier_avg = sum(earlier_quality) / len(earlier_quality)

            if earlier_avg - recent_avg > self.performance_thresholds["critical_accuracy_drop"]:
                alerts.append(
                    {
                        "type": "quality_degradation",
                        "severity": "high",
                        "message": f"Agent {agent_name} quality dropped by {(earlier_avg - recent_avg) * 100:.1f}%",
                        "current_avg": recent_avg,
                        "previous_avg": earlier_avg,
                        "threshold": self.performance_thresholds["critical_accuracy_drop"],
                    }
                )

        # 2. Response time spike alert
        recent_times = [i.get("response_time", 0) for i in recent_interactions[-5:]]
        earlier_times = [i.get("response_time", 0) for i in recent_interactions[-10:-5]]

        if recent_times and earlier_times:
            recent_avg_time = sum(recent_times) / len(recent_times)
            earlier_avg_time = sum(earlier_times) / len(earlier_times)

            if recent_avg_time > earlier_avg_time * self.performance_thresholds["response_time_spike"]:
                alerts.append(
                    {
                        "type": "response_time_spike",
                        "severity": "medium",
                        "message": f"Agent {agent_name} response time increased significantly",
                        "current_avg": recent_avg_time,
                        "previous_avg": earlier_avg_time,
                        "spike_factor": recent_avg_time / earlier_avg_time if earlier_avg_time > 0 else "undefined",
                    }
                )

        # 3. Error rate spike alert
        recent_errors = sum(1 for i in recent_interactions[-5:] if i.get("error_occurred", False))
        error_rate = recent_errors / len(recent_interactions[-5:])

        if error_rate > self.performance_thresholds["error_rate_spike"]:
            alerts.append(
                {
                    "type": "error_rate_spike",
                    "severity": "high",
                    "message": f"Agent {agent_name} error rate: {error_rate * 100:.1f}%",
                    "error_rate": error_rate,
                    "threshold": self.performance_thresholds["error_rate_spike"],
                    "recent_errors": recent_errors,
                }
            )

        return alerts

    def _calculate_recent_trend(self, recent_interactions: list[dict]) -> str:
        """Calculate trend from recent interactions."""
        if len(recent_interactions) < 6:
            return "insufficient_data"

        # Split into two halves
        mid = len(recent_interactions) // 2
        first_half = recent_interactions[:mid]
        second_half = recent_interactions[mid:]

        first_avg_quality = sum(i.get("response_quality", 0) for i in first_half) / len(first_half)
        second_avg_quality = sum(i.get("response_quality", 0) for i in second_half) / len(second_half)

        diff = second_avg_quality - first_avg_quality

        if abs(diff) < 0.05:
            return "stable"
        elif diff > 0:
            return "improving"
        else:
            return "declining"

    def generate_comparative_analysis(self, agent_names: list[str], days: int = 7) -> dict[str, Any]:
        """Generate comparative analysis across multiple agents."""

        agent_reports = {}
        for agent_name in agent_names:
            try:
                report = self.base_monitor.generate_performance_report(agent_name, days)
                agent_reports[agent_name] = report
            except Exception as e:
                self.logger.warning(f"Could not generate report for {agent_name}: {e}")
                continue

        if not agent_reports:
            return {"error": "No agent reports could be generated"}

        # Comparative metrics
        comparative_analysis: dict[str, Any] = {
            "reporting_period": {"days_analyzed": days, "end_date": default_utc_now().isoformat()},
            "agent_rankings": {},
            "performance_summary": {},
            "recommendations": {"top_performers": [], "needs_attention": [], "improvement_opportunities": []},
        }

        # Calculate rankings
        agents_by_score = sorted(agent_reports.items(), key=lambda x: x[1].overall_score, reverse=True)

        for rank, (agent_name, report) in enumerate(agents_by_score, 1):
            comparative_analysis["agent_rankings"][agent_name] = {
                "rank": rank,
                "overall_score": report.overall_score,
                "score_percentile": 100 * (len(agents_by_score) - rank) / len(agents_by_score),
            }

        # Performance summary
        all_scores = [report.overall_score for report in agent_reports.values()]
        comparative_analysis["performance_summary"] = {
            "average_score": sum(all_scores) / len(all_scores),
            "best_score": max(all_scores),
            "worst_score": min(all_scores),
            "score_variance": self._calculate_variance(all_scores),
            "total_agents_analyzed": len(agent_reports),
        }

        # Generate recommendations
        top_performers = [name for name, _ in agents_by_score[: max(1, len(agents_by_score) // 3)]]
        needs_attention = [name for name, report in agent_reports.items() if report.overall_score < 0.7]

        comparative_analysis["recommendations"]["top_performers"] = [
            f"{agent}: {agent_reports[agent].overall_score:.2f} score" for agent in top_performers
        ]

        comparative_analysis["recommendations"]["needs_attention"] = [
            f"{agent}: {agent_reports[agent].overall_score:.2f} score - {len(agent_reports[agent].recommendations)} issues identified"
            for agent in needs_attention
        ]

        # Cross-agent improvement opportunities
        all_recommendations = []
        for report in agent_reports.values():
            all_recommendations.extend(report.recommendations)

        # Find common issues
        common_issues = self._find_common_patterns(all_recommendations)
        comparative_analysis["recommendations"]["improvement_opportunities"] = common_issues[:5]

        return comparative_analysis

    def _calculate_variance(self, values: list[float]) -> float:
        """Calculate variance of a list of values."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _find_common_patterns(self, recommendations: list[str]) -> list[str]:
        """Find common patterns in recommendations across agents."""

        # Simple pattern matching for common issues
        patterns = {
            "tool efficiency": ["tool", "efficiency", "selection"],
            "response time": ["response time", "timeout", "optimization"],
            "accuracy": ["accuracy", "quality", "verification"],
            "error handling": ["error", "failure", "exception"],
        }

        pattern_counts = {}
        for pattern_name, keywords in patterns.items():
            count = sum(1 for rec in recommendations if any(keyword in rec.lower() for keyword in keywords))
            if count > 1:  # Found in multiple agents
                pattern_counts[pattern_name] = count

        # Sort by frequency and return
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
        return [f"{pattern}: affects {count} agents" for pattern, count in sorted_patterns]

    async def generate_real_time_dashboard_data(self) -> dict[str, Any]:
        """Generate data for real-time performance dashboard."""

        dashboard_data: dict[str, Any] = {
            "timestamp": default_utc_now().isoformat(),
            "agents": {},
            "system_overview": {
                "total_agents_monitored": len(self.real_time_metrics),
                "alerts_count": 0,
                "avg_system_performance": 0.0,
            },
        }

        total_performance = 0.0
        total_alerts = 0

        for agent_name, metrics in self.real_time_metrics.items():
            recent_interactions = metrics["recent_interactions"][-10:]
            session_stats = metrics["current_session_stats"]

            # Check for recent alerts
            alerts = await self._check_performance_alerts(agent_name, recent_interactions)
            total_alerts += len(alerts)

            agent_dashboard_data = {
                "current_performance": session_stats,
                "recent_trend": self._calculate_recent_trend(recent_interactions),
                "active_alerts": alerts,
                "interaction_count_last_hour": len(
                    [
                        i
                        for i in recent_interactions
                        if datetime.fromisoformat(i["timestamp"]) > (default_utc_now() - timedelta(hours=1))
                    ]
                ),
                "performance_status": self._get_performance_status(session_stats, alerts),
            }

            dashboard_data["agents"][agent_name] = agent_dashboard_data
            total_performance += session_stats.get("avg_quality", 0)

        # System overview
        if dashboard_data["agents"]:
            dashboard_data["system_overview"]["avg_system_performance"] = total_performance / len(
                dashboard_data["agents"]
            )

        dashboard_data["system_overview"]["alerts_count"] = total_alerts

        return dashboard_data

    def _get_performance_status(self, session_stats: dict, alerts: list[dict]) -> str:
        """Determine overall performance status for an agent."""

        if any(alert["severity"] == "high" for alert in alerts):
            return "critical"
        elif any(alert["severity"] == "medium" for alert in alerts):
            return "warning"
        elif session_stats.get("avg_quality", 0) > 0.85:
            return "excellent"
        elif session_stats.get("avg_quality", 0) > 0.70:
            return "good"
        else:
            return "needs_attention"

    def save_enhanced_report(
        self,
        agent_name: str,
        comparative_data: dict[str, Any] | None = None,
        dashboard_data: dict[str, Any] | None = None,
    ) -> Path:
        """Save enhanced performance report with additional analytics."""

        # Generate base report
        base_report = self.base_monitor.generate_performance_report(agent_name)

        # Create enhanced report
        enhanced_report = {
            "base_performance_report": {
                "agent_name": base_report.agent_name,
                "reporting_period": base_report.reporting_period,
                "overall_score": base_report.overall_score,
                "metrics": [
                    {
                        "metric_name": m.metric_name,
                        "target_value": m.target_value,
                        "actual_value": m.actual_value,
                        "trend": m.trend,
                        "confidence": m.confidence,
                        "last_updated": m.last_updated,
                    }
                    for m in base_report.metrics
                ],
                "tool_usage": [
                    {
                        "tool_name": p.tool_name,
                        "usage_frequency": p.usage_frequency,
                        "success_rate": p.success_rate,
                        "average_quality_score": p.average_quality_score,
                        "common_sequences": p.common_sequences,
                        "error_patterns": p.error_patterns,
                    }
                    for p in base_report.tool_usage
                ],
                "quality_trends": base_report.quality_trends,
                "recommendations": base_report.recommendations,
                "training_suggestions": base_report.training_suggestions,
            },
            "enhanced_analytics": {
                "real_time_performance": self.real_time_metrics.get(agent_name, {}),
                "comparative_analysis": comparative_data,
                "dashboard_snapshot": dashboard_data,
                "enhancement_timestamp": default_utc_now().isoformat(),
            },
        }

        # Save enhanced report
        output_dir = self.base_monitor.data_dir / "enhanced_reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = default_utc_now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"{agent_name}_enhanced_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(enhanced_report, f, indent=2)

        self.logger.info(f"Enhanced performance report saved: {report_file}")
        return report_file


async def main():
    """Example usage of enhanced performance monitoring."""

    # Initialize enhanced monitor
    enhanced_monitor = EnhancedPerformanceMonitor()

    # Example: Monitor real-time performance
    interaction_data = {
        "task_type": "fact_verification",
        "tools_used": ["claim_extractor_tool", "fact_check_tool"],
        "response_quality": 0.87,
        "response_time": 8.5,
        "error_occurred": False,
    }

    real_time_data = await enhanced_monitor.monitor_real_time_performance("enhanced_fact_checker", interaction_data)

    print("Real-time Performance:")
    print(f"Current Score: {real_time_data['current_performance']['avg_quality']:.2f}")
    print(f"Alerts: {len(real_time_data['alerts'])}")
    print(f"Trend: {real_time_data['recent_trend']}")

    # Generate comparative analysis
    agent_names = ["enhanced_fact_checker", "content_manager", "cross_platform_intelligence_gatherer"]
    comparative_analysis = enhanced_monitor.generate_comparative_analysis(agent_names)

    print("\nComparative Analysis:")
    print(f"Average System Score: {comparative_analysis['performance_summary']['average_score']:.2f}")
    print(f"Top Performers: {comparative_analysis['recommendations']['top_performers']}")

    # Generate dashboard data
    dashboard_data = await enhanced_monitor.generate_real_time_dashboard_data()
    print("\nSystem Overview:")
    print(f"Total Agents: {dashboard_data['system_overview']['total_agents_monitored']}")
    print(f"Active Alerts: {dashboard_data['system_overview']['alerts_count']}")


if __name__ == "__main__":
    asyncio.run(main())
