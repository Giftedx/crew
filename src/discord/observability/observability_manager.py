"""
Unified observability manager for Discord AI chatbot.

This module provides a centralized observability system that coordinates
metrics collection, conversation tracing, and personality dashboard analytics.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult

from .conversation_tracer import create_conversation_tracer
from .metrics_collector import create_discord_metrics_collector
from .personality_dashboard import create_personality_dashboard


class ObservabilityManager:
    """
    Unified observability manager for Discord AI chatbot.

    This manager coordinates all observability components including metrics
    collection, conversation tracing, and personality analytics.
    """

    def __init__(self, max_traces: int = 1000, max_history_size: int = 10000, max_steps_per_trace: int = 100):
        # Initialize observability components
        self.metrics_collector = create_discord_metrics_collector(max_history_size)
        self.conversation_tracer = create_conversation_tracer(max_traces, max_steps_per_trace)
        self.personality_dashboard = create_personality_dashboard(max_history_size)

        # Integration state
        self._initialized = False

        # Thread safety
        self._lock = asyncio.Lock()

        # Statistics
        self._stats = {
            "total_observations": 0,
            "active_conversations": 0,
            "traces_created": 0,
            "metrics_recorded": 0,
            "personality_snapshots": 0,
        }

    async def initialize(self) -> StepResult:
        """Initialize the observability system."""
        try:
            async with self._lock:
                self._initialized = True

                return StepResult.ok(data={"action": "observability_system_initialized"})

        except Exception as e:
            return StepResult.fail(f"Failed to initialize observability system: {e!s}")

    async def start_conversation_observation(
        self,
        conversation_id: str,
        user_id: str,
        guild_id: str,
        channel_id: str,
        initial_context: dict[str, Any] | None = None,
    ) -> StepResult:
        """Start observing a new conversation."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # Start conversation tracking in metrics collector
            metrics_result = await self.metrics_collector.start_conversation(
                conversation_id, user_id, guild_id, channel_id, initial_context
            )

            if not metrics_result.success:
                return metrics_result

            # Start conversation tracing
            trace_result = await self.conversation_tracer.start_trace(
                conversation_id, user_id, guild_id, channel_id, initial_context
            )

            if not trace_result.success:
                return trace_result

            async with self._lock:
                self._stats["active_conversations"] += 1
                self._stats["traces_created"] += 1

            return StepResult.ok(
                data={
                    "conversation_id": conversation_id,
                    "trace_id": trace_result.data["trace_id"],
                    "action": "conversation_observation_started",
                }
            )

        except Exception as e:
            return StepResult.fail(f"Failed to start conversation observation: {e!s}")

    async def end_conversation_observation(
        self,
        conversation_id: str,
        satisfaction_score: float | None = None,
        topics_discussed: list[str] | None = None,
        summary: str | None = None,
    ) -> StepResult:
        """End observing a conversation."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # End conversation tracking in metrics collector
            metrics_result = await self.metrics_collector.end_conversation(
                conversation_id, satisfaction_score, topics_discussed
            )

            # Get trace ID for this conversation
            traces_result = await self.conversation_tracer.get_conversation_traces(conversation_id)

            trace_id = None
            if traces_result.success and traces_result.data["traces"]:
                # Get the most recent trace
                latest_trace = traces_result.data["traces"][-1]
                trace_id = latest_trace["trace"].trace_id

            # End conversation tracing
            if trace_id:
                trace_result = await self.conversation_tracer.end_trace(trace_id, summary)

                if not trace_result.success:
                    return trace_result

            async with self._lock:
                self._stats["active_conversations"] = max(0, self._stats["active_conversations"] - 1)
                self._stats["total_observations"] += 1

            return StepResult.ok(data={"conversation_id": conversation_id, "action": "conversation_observation_ended"})

        except Exception as e:
            return StepResult.fail(f"Failed to end conversation observation: {e!s}")

    async def record_conversation_step(
        self,
        conversation_id: str,
        step_type: str,
        content: str,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        start_time: float | None = None,
    ) -> StepResult:
        """Record a step in conversation observation."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # Get trace ID for this conversation
            traces_result = await self.conversation_tracer.get_conversation_traces(conversation_id)

            if not traces_result.success or not traces_result.data["traces"]:
                return StepResult.fail(f"No active trace found for conversation {conversation_id}")

            # Get the most recent trace
            latest_trace = traces_result.data["traces"][-1]
            trace_id = latest_trace["trace"].trace_id

            # Add step to trace
            step_result = await self.conversation_tracer.add_step(
                trace_id, step_type, content, metadata, None, start_time
            )

            if not step_result.success:
                return step_result

            # Record message in metrics collector if user_id provided
            if user_id:
                message_type = "user" if step_type == "user_message" else "bot"
                response_time_ms = None
                if start_time and step_type == "bot_response":
                    response_time_ms = (time.time() - start_time) * 1000

                await self.metrics_collector.record_message(conversation_id, user_id, message_type, response_time_ms)

            async with self._lock:
                self._stats["metrics_recorded"] += 1

            return StepResult.ok(
                data={"conversation_id": conversation_id, "step_id": step_result.data["step_id"], "step_recorded": True}
            )

        except Exception as e:
            return StepResult.fail(f"Failed to record conversation step: {e!s}")

    async def end_conversation_step(
        self,
        conversation_id: str,
        step_id: str,
        success: bool = True,
        final_content: str | None = None,
        error_message: str | None = None,
    ) -> StepResult:
        """End a conversation step."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # Get trace ID for this conversation
            traces_result = await self.conversation_tracer.get_conversation_traces(conversation_id)

            if not traces_result.success or not traces_result.data["traces"]:
                return StepResult.fail(f"No active trace found for conversation {conversation_id}")

            # Get the most recent trace
            latest_trace = traces_result.data["traces"][-1]
            trace_id = latest_trace["trace"].trace_id

            # End step in trace
            step_result = await self.conversation_tracer.end_step(
                trace_id, step_id, success, final_content, error_message
            )

            return step_result

        except Exception as e:
            return StepResult.fail(f"Failed to end conversation step: {e!s}")

    async def record_personality_snapshot(
        self,
        trait_name: str,
        value: float,
        confidence: float = 1.0,
        user_feedback: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> StepResult:
        """Record a personality trait snapshot."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # Record in personality dashboard
            result = await self.personality_dashboard.record_trait_snapshot(
                trait_name, value, confidence, user_feedback, context
            )

            if result.success:
                async with self._lock:
                    self._stats["personality_snapshots"] += 1

            return result

        except Exception as e:
            return StepResult.fail(f"Failed to record personality snapshot: {e!s}")

    async def record_user_feedback(
        self, user_id: str, trait_name: str, feedback_value: float, context: dict[str, Any] | None = None
    ) -> StepResult:
        """Record user feedback on personality traits."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # Record in personality dashboard
            result = await self.personality_dashboard.record_user_feedback(user_id, trait_name, feedback_value, context)

            return result

        except Exception as e:
            return StepResult.fail(f"Failed to record user feedback: {e!s}")

    async def get_conversation_insights(self, conversation_id: str) -> StepResult:
        """Get comprehensive insights for a conversation."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # Get conversation metrics
            metrics_result = await self.metrics_collector.get_conversation_metrics(conversation_id)

            # Get conversation traces
            traces_result = await self.conversation_tracer.get_conversation_traces(conversation_id)

            # Get flow analysis if traces exist
            flow_analysis = None
            if traces_result.success and traces_result.data["traces"]:
                latest_trace = traces_result.data["traces"][-1]
                flow_result = await self.conversation_tracer.analyze_conversation_flow(latest_trace["trace"].trace_id)
                if flow_result.success:
                    flow_analysis = flow_result.data["flow_analysis"]

            insights = {
                "conversation_metrics": metrics_result.data if metrics_result.success else None,
                "conversation_traces": traces_result.data if traces_result.success else None,
                "flow_analysis": flow_analysis,
            }

            return StepResult.ok(data={"conversation_insights": insights})

        except Exception as e:
            return StepResult.fail(f"Failed to get conversation insights: {e!s}")

    async def get_user_insights(self, user_id: str) -> StepResult:
        """Get comprehensive insights for a user."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # Get user metrics
            metrics_result = await self.metrics_collector.get_user_metrics(user_id)

            # Get user personality profile
            profile_result = await self.personality_dashboard.get_user_personality_profile(user_id)

            insights = {
                "user_metrics": metrics_result.data if metrics_result.success else None,
                "personality_profile": profile_result.data if profile_result.success else None,
            }

            return StepResult.ok(data={"user_insights": insights})

        except Exception as e:
            return StepResult.fail(f"Failed to get user insights: {e!s}")

    async def get_guild_insights(self, guild_id: str) -> StepResult:
        """Get comprehensive insights for a guild."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # Get guild metrics
            metrics_result = await self.metrics_collector.get_guild_metrics(guild_id)

            insights = {"guild_metrics": metrics_result.data if metrics_result.success else None}

            return StepResult.ok(data={"guild_insights": insights})

        except Exception as e:
            return StepResult.fail(f"Failed to get guild insights: {e!s}")

    async def get_system_insights(self) -> StepResult:
        """Get comprehensive system insights."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # Get comprehensive stats from all components
            metrics_stats = await self.metrics_collector.get_comprehensive_stats()
            tracer_stats = await self.conversation_tracer.get_tracer_stats()
            dashboard_stats = await self.personality_dashboard.get_dashboard_summary()
            performance_insights = await self.conversation_tracer.get_performance_insights()
            personality_analytics = await self.personality_dashboard.get_personality_analytics()

            system_insights = {
                "metrics_stats": metrics_stats.data if metrics_stats.success else {},
                "tracer_stats": tracer_stats.data if tracer_stats.success else {},
                "dashboard_stats": dashboard_stats.data if dashboard_stats.success else {},
                "performance_insights": performance_insights.data if performance_insights.success else {},
                "personality_analytics": personality_analytics.data if personality_analytics.success else {},
                "observability_stats": self._stats,
            }

            return StepResult.ok(data={"system_insights": system_insights})

        except Exception as e:
            return StepResult.fail(f"Failed to get system insights: {e!s}")

    async def export_observability_data(self, format: str = "json") -> StepResult:
        """Export all observability data."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # Export data from all components
            personality_export = await self.personality_dashboard.export_personality_data(format)

            # Get comprehensive system data
            system_insights = await self.get_system_insights()

            export_data = {
                "export_timestamp": time.time(),
                "personality_data": personality_export.data if personality_export.success else {},
                "system_insights": system_insights.data if system_insights.success else {},
                "format": format,
            }

            return StepResult.ok(data={"export_data": export_data})

        except Exception as e:
            return StepResult.fail(f"Failed to export observability data: {e!s}")

    async def cleanup_old_data(self, max_age_hours: int = 168) -> StepResult:  # Default 1 week
        """Clean up old observability data."""
        try:
            if not self._initialized:
                return StepResult.fail("Observability system not initialized")

            # Cleanup metrics collector
            metrics_cleanup = await self.metrics_collector.cleanup_old_data(max_age_hours)

            cleanup_results = {
                "metrics_cleanup": metrics_cleanup.data if metrics_cleanup.success else {},
                "cleanup_timestamp": time.time(),
            }

            return StepResult.ok(data=cleanup_results)

        except Exception as e:
            return StepResult.fail(f"Failed to cleanup old data: {e!s}")

    async def get_observability_stats(self) -> StepResult:
        """Get observability system statistics."""
        try:
            async with self._lock:
                return StepResult.ok(
                    data={
                        "observability_stats": self._stats,
                        "initialized": self._initialized,
                        "components": {
                            "metrics_collector": "active",
                            "conversation_tracer": "active",
                            "personality_dashboard": "active",
                        },
                    }
                )

        except Exception as e:
            return StepResult.fail(f"Failed to get observability stats: {e!s}")


# Factory function for creating observability managers
def create_observability_manager(
    max_traces: int = 1000, max_history_size: int = 10000, max_steps_per_trace: int = 100
) -> ObservabilityManager:
    """Create an observability manager with the specified configuration."""
    return ObservabilityManager(max_traces, max_history_size, max_steps_per_trace)
