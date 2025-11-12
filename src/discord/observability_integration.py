"""
Integration of observability system with Discord AI chatbot pipeline.

This module provides integration between the observability system and the
conversational pipeline, ensuring comprehensive monitoring and analytics.
"""

from __future__ import annotations

import time
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult

from .observability import ObservabilityManager, create_observability_manager


class DiscordObservabilityIntegration:
    """
    Integration layer for Discord AI chatbot observability.

    This class integrates the observability system with the conversational
    pipeline to provide comprehensive monitoring and analytics.
    """

    def __init__(self, observability_manager: ObservabilityManager | None = None):
        self.observability_manager = observability_manager or create_observability_manager()
        self._initialized = False

    async def initialize(self) -> StepResult:
        """Initialize the observability integration."""
        try:
            result = await self.observability_manager.initialize()
            if result.success:
                self._initialized = True
            return result
        except Exception as e:
            return StepResult.fail(f"Failed to initialize observability integration: {e!s}")

    async def start_conversation_monitoring(
        self,
        conversation_id: str,
        user_id: str,
        guild_id: str,
        channel_id: str,
        initial_context: dict[str, Any] | None = None,
    ) -> StepResult:
        """Start monitoring a conversation."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        return await self.observability_manager.start_conversation_observation(
            conversation_id, user_id, guild_id, channel_id, initial_context
        )

    async def end_conversation_monitoring(
        self,
        conversation_id: str,
        satisfaction_score: float | None = None,
        topics_discussed: list[str] | None = None,
        summary: str | None = None,
    ) -> StepResult:
        """End monitoring a conversation."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        return await self.observability_manager.end_conversation_observation(
            conversation_id, satisfaction_score, topics_discussed, summary
        )

    async def track_message_evaluation(
        self, conversation_id: str, message_content: str, evaluation_result: dict[str, Any], processing_time_ms: float
    ) -> StepResult:
        """Track message evaluation step."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        return await self.observability_manager.record_conversation_step(
            conversation_id=conversation_id,
            step_type="message_evaluation",
            content=message_content,
            metadata={"evaluation_result": evaluation_result, "processing_time_ms": processing_time_ms},
        )

    async def track_personality_adaptation(
        self, conversation_id: str, trait_name: str, old_value: float, new_value: float, adaptation_reason: str
    ) -> StepResult:
        """Track personality trait adaptation."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        step_result = await self.observability_manager.record_conversation_step(
            conversation_id=conversation_id,
            step_type="personality_adaptation",
            content=f"Adapted {trait_name} from {old_value:.3f} to {new_value:.3f}",
            metadata={
                "trait_name": trait_name,
                "old_value": old_value,
                "new_value": new_value,
                "adaptation_reason": adaptation_reason,
            },
        )
        if step_result.success:
            await self.observability_manager.record_personality_snapshot(
                trait_name=trait_name,
                value=new_value,
                confidence=0.8,
                context={"adaptation_reason": adaptation_reason, "conversation_id": conversation_id},
            )
        return step_result

    async def track_reward_computation(
        self, conversation_id: str, user_id: str, reward_signals: dict[str, float], final_reward: float
    ) -> StepResult:
        """Track reward computation and user feedback."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        step_result = await self.observability_manager.record_conversation_step(
            conversation_id=conversation_id,
            step_type="reward_computation",
            content=f"Computed reward: {final_reward:.3f}",
            metadata={"reward_signals": reward_signals, "final_reward": final_reward, "user_id": user_id},
        )
        for trait_name, reward_value in reward_signals.items():
            await self.observability_manager.record_user_feedback(
                user_id=user_id,
                trait_name=trait_name,
                feedback_value=reward_value,
                context={"conversation_id": conversation_id, "computation_timestamp": time.time()},
            )
        return step_result

    async def track_mcp_server_interaction(
        self,
        conversation_id: str,
        server_name: str,
        operation: str,
        request_data: dict[str, Any],
        response_data: dict[str, Any],
        processing_time_ms: float,
    ) -> StepResult:
        """Track MCP server interactions."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        return await self.observability_manager.record_conversation_step(
            conversation_id=conversation_id,
            step_type="mcp_server_interaction",
            content=f"MCP {server_name}: {operation}",
            metadata={
                "server_name": server_name,
                "operation": operation,
                "request_data": request_data,
                "response_data": response_data,
                "processing_time_ms": processing_time_ms,
            },
        )

    async def track_memory_operation(
        self, conversation_id: str, operation_type: str, operation_details: dict[str, Any], processing_time_ms: float
    ) -> StepResult:
        """Track memory service operations."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        return await self.observability_manager.record_conversation_step(
            conversation_id=conversation_id,
            step_type="memory_operation",
            content=f"Memory: {operation_type}",
            metadata={
                "operation_type": operation_type,
                "operation_details": operation_details,
                "processing_time_ms": processing_time_ms,
            },
        )

    async def track_error(
        self, conversation_id: str, error_type: str, error_message: str, error_context: dict[str, Any] | None = None
    ) -> StepResult:
        """Track errors in the conversation flow."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        return await self.observability_manager.record_conversation_step(
            conversation_id=conversation_id,
            step_type="error",
            content=f"Error: {error_message}",
            metadata={
                "error_type": error_type,
                "error_message": error_message,
                "error_context": error_context or {},
                "timestamp": time.time(),
            },
        )

    async def get_conversation_analytics(self, conversation_id: str) -> StepResult:
        """Get comprehensive analytics for a conversation."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        return await self.observability_manager.get_conversation_insights(conversation_id)

    async def get_user_analytics(self, user_id: str) -> StepResult:
        """Get comprehensive analytics for a user."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        return await self.observability_manager.get_user_insights(user_id)

    async def get_system_analytics(self) -> StepResult:
        """Get comprehensive system analytics."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        return await self.observability_manager.get_system_insights()

    async def export_analytics_data(self, fmt: str = "json") -> StepResult:
        """Export all analytics data."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        return await self.observability_manager.export_observability_data(fmt)

    async def cleanup_analytics_data(self, max_age_hours: int = 168) -> StepResult:
        """Clean up old analytics data."""
        if not self._initialized:
            return StepResult.fail("Observability integration not initialized")
        return await self.observability_manager.cleanup_old_data(max_age_hours)


def create_discord_observability_integration(
    observability_manager: ObservabilityManager | None = None,
) -> DiscordObservabilityIntegration:
    """Create a Discord observability integration instance."""
    return DiscordObservabilityIntegration(observability_manager)
