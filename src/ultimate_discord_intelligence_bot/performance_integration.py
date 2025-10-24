#!/usr/bin/env python3
"""
Agent Performance Monitor    ...self, interaction_id: str, tool_name: str, tool_action: str, success: bool = True, error_details: dict[Any, Any] | None = Noneng Integration

This module provides integration hooks to seamlessly connect the enhanced
performance monitoring system with the existing Discord bot and crew execution.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from core.time import default_utc_now

from .agent_training.performance_monitor import AgentPerformanceMonitor
from .enhanced_performance_monitor import EnhancedPerformanceMonitor


class PerformanceIntegrationManager:
    """Manages integration of performance monitoring into the bot workflow."""

    def __init__(self, enable_enhanced_monitoring: bool = True):
        self.enable_enhanced_monitoring = enable_enhanced_monitoring

        # Initialize monitoring systems
        self.base_monitor = AgentPerformanceMonitor()
        self.enhanced_monitor: EnhancedPerformanceMonitor | None
        if enable_enhanced_monitoring:
            self.enhanced_monitor = EnhancedPerformanceMonitor(self.base_monitor)
        else:
            self.enhanced_monitor = None

        self.logger = logging.getLogger(__name__)
        self.active_interactions: dict[str, dict[str, Any]] = {}  # Track ongoing interactions

    async def start_interaction_tracking(self, agent_name: str, task_type: str, context: dict[str, Any]) -> str:
        """Start tracking a new agent interaction."""
        interaction_id = f"{agent_name}_{default_utc_now().timestamp()}"

        self.active_interactions[interaction_id] = {
            "agent_name": agent_name,
            "task_type": task_type,
            "context": context,
            "start_time": default_utc_now(),
            "tools_used": [],
            "tool_sequence": [],
        }

        self.logger.debug(f"Started tracking interaction {interaction_id} for {agent_name}")
        return interaction_id

    async def record_tool_usage(
        self,
        interaction_id: str,
        tool_name: str,
        tool_action: str,
        success: bool = True,
        error_details: dict[Any, Any] | None = None,
    ):
        """Record tool usage within an interaction."""

        if interaction_id not in self.active_interactions:
            self.logger.warning(f"Tool usage recorded for unknown interaction: {interaction_id}")
            return

        interaction = self.active_interactions[interaction_id]

        # Add to tools used
        if tool_name not in interaction["tools_used"]:
            interaction["tools_used"].append(tool_name)

        # Add to tool sequence
        interaction["tool_sequence"].append(
            {
                "tool": tool_name,
                "action": tool_action,
                "timestamp": default_utc_now().isoformat(),
                "success": success,
                "error_details": error_details or {},
            }
        )

    async def complete_interaction_tracking(
        self,
        interaction_id: str,
        response: str,
        user_feedback: dict[Any, Any] | None = None,
        error_occurred: bool = False,
        error_details: dict[Any, Any] | None = None,
    ) -> dict[str, Any]:
        """Complete interaction tracking and record performance data."""

        if interaction_id not in self.active_interactions:
            self.logger.warning(f"Attempted to complete unknown interaction: {interaction_id}")
            return {}

        interaction = self.active_interactions[interaction_id]
        end_time = default_utc_now()
        response_time = (end_time - interaction["start_time"]).total_seconds()

        # Assess response quality
        quality_score = 0.5  # Default fallback
        if self.enhanced_monitor:
            try:
                quality_score = await self.enhanced_monitor.real_time_quality_assessment(
                    response, interaction["context"]
                )
            except Exception as e:
                self.logger.warning(f"Quality assessment failed: {e}")
                quality_score = 0.5
        else:
            # Basic quality assessment
            quality_score = self._basic_quality_assessment(response, interaction["context"])

        # Record interaction data
        interaction_data = {
            "agent_name": interaction["agent_name"],
            "task_type": interaction["task_type"],
            "tools_used": interaction["tools_used"],
            "tool_sequence": interaction["tool_sequence"],
            "response_quality": quality_score,
            "response_time": response_time,
            "user_feedback": user_feedback or {},
            "error_occurred": error_occurred,
            "error_details": error_details or {},
        }

        # Record with base monitor
        self.base_monitor.record_agent_interaction(**interaction_data)

        # Enhanced monitoring
        real_time_data = {}
        if self.enhanced_monitor:
            try:
                real_time_data = await self.enhanced_monitor.monitor_real_time_performance(
                    interaction["agent_name"], interaction_data
                )
            except Exception as e:
                self.logger.warning(f"Enhanced monitoring failed: {e}")

        # Clean up
        del self.active_interactions[interaction_id]

        return {
            "interaction_id": interaction_id,
            "performance_data": interaction_data,
            "real_time_analysis": real_time_data,
        }

    def _basic_quality_assessment(self, response: str, context: dict[str, Any]) -> float:
        """Basic quality assessment when enhanced monitoring is disabled."""

        score = 0.0

        # Length check
        if 50 <= len(response) <= 2000:
            score += 0.3
        elif len(response) > 50:
            score += 0.2

        # Content indicators
        if any(phrase in response.lower() for phrase in ["analysis", "evidence", "source", "because", "therefore"]):
            score += 0.4

        # Error indicators
        if not any(phrase in response.lower() for phrase in ["error", "failed", "unable", "couldn't"]):
            score += 0.3

        return min(1.0, score)

    async def generate_agent_dashboard_data(self, agent_name: str | None = None) -> dict[str, Any]:
        """Generate dashboard data for one or all agents."""

        if not self.enhanced_monitor:
            return {"error": "Enhanced monitoring not available"}

        try:
            if agent_name:
                # Single agent data
                report = self.base_monitor.generate_performance_report(agent_name)
                dashboard_data = await self.enhanced_monitor.generate_real_time_dashboard_data()

                return {
                    "agent": agent_name,
                    "performance_report": {
                        "overall_score": report.overall_score,
                        "metrics_count": len(report.metrics),
                        "recommendations_count": len(report.recommendations),
                        "reporting_period": report.reporting_period,
                    },
                    "real_time_data": dashboard_data.get("agents", {}).get(agent_name, {}),
                }
            else:
                # All agents dashboard
                return await self.enhanced_monitor.generate_real_time_dashboard_data()

        except Exception as e:
            self.logger.error(f"Dashboard generation failed: {e}")
            return {"error": str(e)}

    async def check_performance_alerts(self) -> list[dict[str, Any]]:
        """Check for performance alerts across all monitored agents."""

        if not self.enhanced_monitor:
            return []

        try:
            dashboard_data = await self.enhanced_monitor.generate_real_time_dashboard_data()
            all_alerts = []

            for agent_name, agent_data in dashboard_data.get("agents", {}).items():
                alerts = agent_data.get("active_alerts", [])
                for alert in alerts:
                    alert["agent_name"] = agent_name
                    all_alerts.append(alert)

            return all_alerts

        except Exception as e:
            self.logger.error(f"Alert checking failed: {e}")
            return []

    async def track_crew_execution(
        self,
        execution_id: str,
        agents_used: list[str],
        tools_used: list[str],
        quality_score: float,
        execution_time: float,
        result: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist a consolidated record for a complete crew execution run."""

        metadata = metadata or {}
        context = {
            "execution_id": execution_id,
            "agents_used": agents_used,
            "tools_used": tools_used,
            "result_digest": str(result)[:512] if result is not None else "",
            "user_feedback": metadata.get("user_feedback"),
            "tool_sequence": metadata.get("tool_sequence", []),
            "error_details": metadata.get("error_details"),
            "error_occurred": metadata.get("error_occurred", False),
            "task_type": metadata.get("task_type", "crew_execution"),
        }

        if self.enhanced_monitor:
            try:
                await self.enhanced_monitor.record_interaction_async(
                    agent_name="crew_orchestrator",
                    interaction_type=context["task_type"],
                    quality_score=quality_score,
                    response_time=execution_time,
                    context=context,
                    tools_used=tools_used,
                    error_occurred=context.get("error_occurred", False),
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                self.logger.debug("Enhanced monitor failed to capture crew execution: %s", exc)

        per_agent_time = execution_time / max(len(agents_used) or 1, 1)
        for agent in agents_used or ["crew_orchestrator"]:
            try:
                self.base_monitor.record_agent_interaction(
                    agent_name=agent,
                    task_type=context["task_type"],
                    tools_used=tools_used,
                    tool_sequence=context.get("tool_sequence", []),
                    response_quality=quality_score,
                    response_time=per_agent_time,
                    user_feedback=context.get("user_feedback"),
                    error_occurred=context.get("error_occurred", False),
                    error_details={"execution_id": execution_id},
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                self.logger.debug("Base monitor failed to log interaction for %s: %s", agent, exc)

        self.logger.info(
            "Recorded crew execution %s (agents=%d, tools=%d, quality=%.2f)",
            execution_id,
            len(agents_used),
            len(tools_used),
            quality_score,
        )

    async def generate_weekly_report(self, agent_names: list[str] | None = None) -> dict[str, Any]:
        """Generate comprehensive weekly performance report."""

        try:
            # Get all agent names if not specified
            if agent_names is None:
                if self.enhanced_monitor:
                    agent_names = list(self.enhanced_monitor.real_time_metrics.keys())
                else:
                    agent_names = list(self.base_monitor.performance_history.keys())

            if not agent_names:
                return {"error": "No agents found for reporting"}

            # Generate individual reports
            agent_reports = {}
            for agent_name in agent_names:
                try:
                    report = self.base_monitor.generate_performance_report(agent_name, days=7)
                    agent_reports[agent_name] = report
                except Exception as e:
                    self.logger.warning(f"Could not generate report for {agent_name}: {e}")

            # Comparative analysis
            comparative_data = {}
            if self.enhanced_monitor and agent_reports:
                comparative_data = self.enhanced_monitor.generate_comparative_analysis(
                    list(agent_reports.keys()), days=7
                )

            # Generate summary
            if agent_reports:
                all_scores = [report.overall_score for report in agent_reports.values()]
                total_recommendations = sum(len(report.recommendations) for report in agent_reports.values())

                summary = {
                    "reporting_period": "Last 7 days",
                    "agents_analyzed": len(agent_reports),
                    "average_performance": sum(all_scores) / len(all_scores),
                    "best_performer": max(agent_reports.items(), key=lambda x: x[1].overall_score)[0],
                    "total_recommendations": total_recommendations,
                    "performance_distribution": {
                        "excellent": len([s for s in all_scores if s >= 0.9]),
                        "good": len([s for s in all_scores if 0.7 <= s < 0.9]),
                        "needs_attention": len([s for s in all_scores if s < 0.7]),
                    },
                }
            else:
                summary = {"error": "No performance data available"}

            return {
                "summary": summary,
                "agent_reports": {
                    name: {
                        "overall_score": report.overall_score,
                        "metrics_count": len(report.metrics),
                        "recommendations": report.recommendations[:3],  # Top 3 recommendations
                        "top_tools": [p.tool_name for p in report.tool_usage[:3]],  # Top 3 tools
                    }
                    for name, report in agent_reports.items()
                },
                "comparative_analysis": comparative_data,
                "generation_timestamp": default_utc_now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Weekly report generation failed: {e}")
            return {"error": str(e)}

    def save_performance_snapshot(self) -> Path:
        """Save a snapshot of current performance state."""

        snapshot_dir = Path("data/agent_performance/snapshots")
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = default_utc_now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = snapshot_dir / f"performance_snapshot_{timestamp}.json"

        snapshot_data = {
            "timestamp": default_utc_now().isoformat(),
            "active_interactions": len(self.active_interactions),
            "monitored_agents": list(self.base_monitor.performance_history.keys()),
            "enhanced_monitoring_enabled": self.enable_enhanced_monitoring,
        }

        if self.enhanced_monitor:
            snapshot_data["real_time_metrics"] = {
                agent: {
                    "recent_interactions_count": len(metrics["recent_interactions"]),
                    "session_stats": metrics["current_session_stats"],
                }
                for agent, metrics in self.enhanced_monitor.real_time_metrics.items()
            }

        with open(snapshot_file, "w") as f:
            import json

            json.dump(snapshot_data, f, indent=2)

        self.logger.info(f"Performance snapshot saved: {snapshot_file}")
        return snapshot_file


# Convenience functions for easy integration

_integration_manager = None


def get_performance_manager(
    enable_enhanced: bool = True,
) -> PerformanceIntegrationManager:
    """Get the global performance integration manager instance."""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = PerformanceIntegrationManager(enable_enhanced)
    return _integration_manager


async def track_agent_interaction(agent_name: str, task_type: str, context: dict[str, Any]):
    """Convenient context manager for tracking agent interactions."""
    manager = get_performance_manager()
    return await manager.start_interaction_tracking(agent_name, task_type, context)


async def record_tool_use(interaction_id: str, tool_name: str, action: str, success: bool = True):
    """Convenient function to record tool usage."""
    manager = get_performance_manager()
    await manager.record_tool_usage(interaction_id, tool_name, action, success)


async def complete_interaction(
    interaction_id: str,
    response: str,
    user_feedback: dict[Any, Any] | None = None,
    error_occurred: bool = False,
    error_details: dict[Any, Any] | None = None,
):
    """Convenient function to complete interaction tracking."""
    manager = get_performance_manager()
    return await manager.complete_interaction_tracking(
        interaction_id, response, user_feedback, error_occurred, error_details
    )


async def get_dashboard_data(agent_name: str | None = None):
    """Convenient function to get dashboard data."""
    manager = get_performance_manager()
    return await manager.generate_agent_dashboard_data(agent_name)


async def check_alerts():
    """Convenient function to check performance alerts."""
    manager = get_performance_manager()
    return await manager.check_performance_alerts()


# Example usage for Discord bot integration
class PerformanceAwareDiscordBot:
    """Example Discord bot integration with performance monitoring."""

    def __init__(self):
        self.performance_manager = get_performance_manager()

    async def handle_command(self, ctx, agent_name: str, user_input: str):
        """Example command handler with performance tracking."""

        # Start tracking
        interaction_id = await track_agent_interaction(
            agent_name=agent_name,
            task_type="discord_command",
            context={
                "user_id": str(ctx.author.id),
                "channel_type": "discord",
                "command_input": user_input,
            },
        )

        try:
            # Simulate agent processing with tool usage
            await record_tool_use(interaction_id, "text_analyzer", "analyze", True)
            await record_tool_use(interaction_id, "response_generator", "generate", True)

            # Simulate response generation
            response = f"Agent {agent_name} processed: {user_input}"

            # Complete tracking
            result = await complete_interaction(
                interaction_id,
                response,
                user_feedback={"user_id": str(ctx.author.id), "channel": "discord"},
            )

            return response, result

        except Exception as e:
            # Record error and complete tracking
            await complete_interaction(
                interaction_id,
                "Error occurred during processing",
                error_occurred=True,
                error_details={"error": str(e)},
            )
            raise


async def main():
    """Example usage of the performance integration system."""

    print("🚀 Initializing Enhanced Agent Performance Monitoring")

    # Get performance manager
    manager = get_performance_manager(enable_enhanced=True)

    # Simulate agent interaction
    interaction_id = await track_agent_interaction(
        agent_name="enhanced_fact_checker",
        task_type="fact_verification",
        context={"user_id": "test_user", "priority": "high"},
    )

    await record_tool_use(interaction_id, "claim_extractor", "extract_claims", True)
    await record_tool_use(interaction_id, "fact_checker", "verify_claims", True)

    result = await complete_interaction(
        interaction_id,
        "Claims verified with 95% confidence based on 3 reliable sources.",
        user_feedback={"satisfaction": 0.9},
    )

    print(f"✅ Interaction completed: Quality {result['performance_data']['response_quality']:.2f}")

    # Check alerts
    alerts = await check_alerts()
    if alerts:
        print(f"⚠️  {len(alerts)} performance alerts found")
    else:
        print("✅ No performance alerts")

    # Get dashboard data
    dashboard = await get_dashboard_data()
    print(f"📊 Monitoring {dashboard['system_overview']['total_agents_monitored']} agents")

    # Generate weekly report
    weekly_report = await manager.generate_weekly_report()
    if "summary" in weekly_report:
        print(f"📈 Weekly Summary: {weekly_report['summary']['agents_analyzed']} agents analyzed")
        print(f"   Average Performance: {weekly_report['summary']['average_performance']:.2f}")

    print("🎯 Enhanced Agent Performance Monitoring Demonstration Complete")


if __name__ == "__main__":
    asyncio.run(main())
