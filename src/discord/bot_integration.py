"""Discord bot integration service for conversational pipeline.

This module bridges Discord bot message handlers with the ConversationalPipeline,
handling message format conversion, tenant resolution, and service initialization.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry


if TYPE_CHECKING:
    from collections.abc import Sequence

    from core.learning_engine import LearningEngine

    from ultimate_discord_intelligence_bot.services.memory_service import MemoryService
    from ultimate_discord_intelligence_bot.services.openrouter_service.adaptive_routing import AdaptiveRoutingManager
    from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine

    from .conversational_pipeline import ConversationalPipeline


logger = logging.getLogger(__name__)


class DiscordPipelineService:
    """Service for integrating Discord bot with ConversationalPipeline."""

    def __init__(self):
        """Initialize the Discord pipeline service with all dependencies."""
        self._pipeline_per_guild: dict[str, ConversationalPipeline] = {}
        self._tenant_registry: TenantRegistry | None = None
        self._initialized = False

    async def initialize(self) -> StepResult:
        """Initialize all service dependencies."""
        try:
            # Initialize tenant registry
            from pathlib import Path as PathLib

            tenants_dir = PathLib("tenants")
            if not tenants_dir.exists():
                # Fallback to project root
                tenants_dir = PathLib(__file__).parent.parent.parent.parent / "tenants"
            if tenants_dir.exists():
                self._tenant_registry = TenantRegistry(tenants_dir)
                self._tenant_registry.load()
                logger.info(f"Loaded {len(self._tenant_registry._cache)} tenants")
            else:
                logger.warning(f"Tenants directory not found at {tenants_dir}, proceeding without tenant registry")

            # Initialize services (lazy initialization per guild)
            self._initialized = True
            return StepResult.ok(data={"initialized": True, "tenants_loaded": self._tenant_registry is not None})

        except Exception as e:
            logger.error(f"Failed to initialize DiscordPipelineService: {e}", exc_info=True)
            return StepResult.fail(f"Initialization failed: {e!s}")

    def _get_or_create_pipeline(self, guild_id: str, tenant_ctx: TenantContext | None = None) -> ConversationalPipeline:
        """Get or create pipeline instance for a guild."""
        if guild_id in self._pipeline_per_guild:
            return self._pipeline_per_guild[guild_id]

        # Initialize services for this guild
        from core.learning_engine import LearningEngine
        from ultimate_discord_intelligence_bot.services.memory_service import MemoryService
        from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
        from ultimate_discord_intelligence_bot.services.openrouter_service.adaptive_routing import AdaptiveRoutingManager
        from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine

        # Create LearningEngine
        learning_engine = LearningEngine()

        # Create PromptEngine
        prompt_engine = PromptEngine()

        # Create MemoryService
        memory_service = MemoryService()

        # Create OpenRouterService with tenant registry
        openrouter_service = OpenRouterService(
            learning_engine=learning_engine,
            tenant_registry=self._tenant_registry,
        )

        # Create AdaptiveRoutingManager
        routing_manager_base = AdaptiveRoutingManager(enabled=True)
        
        # Create adapter layer to bridge interface gaps
        from .routing_adapter import RoutingAdapter, PromptEngineAdapter
        
        # Create routing adapter that provides suggest_model() and estimate_cost()
        routing_manager = RoutingAdapter(routing_manager_base, openrouter_service)
        
        # Wrap prompt_engine to provide generate_response() method
        prompt_engine_wrapped = PromptEngineAdapter(prompt_engine, openrouter_service)

        # Create ConversationalPipeline
        from .conversational_pipeline import ConversationalPipeline, PipelineConfig

        pipeline = ConversationalPipeline(
            routing_manager=routing_manager,  # Using adapter
            prompt_engine=prompt_engine_wrapped,  # Using adapter
            memory_service=memory_service,
            learning_engine=learning_engine,
            config=PipelineConfig(),
        )

        # Cache per guild
        self._pipeline_per_guild[guild_id] = pipeline

        logger.info(f"Created ConversationalPipeline for guild {guild_id}")
        return pipeline

    def _resolve_tenant_context(self, guild_id: int | str | None) -> TenantContext | None:
        """Resolve tenant context from Discord guild ID."""
        if not self._tenant_registry:
            # Fallback: create default tenant context
            if guild_id:
                return TenantContext(tenant_id=f"guild_{guild_id}", workspace_id="main")
            return None

        if guild_id is None:
            return None

        # Convert to int for registry lookup
        guild_id_int = int(guild_id) if isinstance(guild_id, str) else guild_id

        # Resolve from registry
        tenant_ctx = self._tenant_registry.resolve_discord_guild(guild_id_int)
        if tenant_ctx:
            logger.debug(f"Resolved guild {guild_id_int} to tenant {tenant_ctx.tenant_id}/{tenant_ctx.workspace_id}")
            return tenant_ctx

        # Fallback: create default tenant context
        logger.debug(f"No tenant config found for guild {guild_id_int}, using default")
        return TenantContext(tenant_id=f"guild_{guild_id_int}", workspace_id="main")

    def _convert_discord_message(self, discord_message: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Convert Discord message object to pipeline format."""
        try:
            # Extract basic message data
            message_data = {
                "id": str(getattr(discord_message, "id", "")),
                "content": getattr(discord_message, "content", ""),
                "author": {
                    "id": str(getattr(discord_message.author, "id", "")),
                    "username": str(getattr(discord_message.author, "username", "")),
                    "bot": getattr(discord_message.author, "bot", False),
                },
                "guild_id": str(getattr(discord_message.guild, "id", "")) if hasattr(discord_message, "guild") and discord_message.guild else None,
                "channel_id": str(getattr(discord_message.channel, "id", "")) if hasattr(discord_message, "channel") else None,
                "created_at": getattr(discord_message, "created_at", None),
                "mentions": [str(m.id) for m in getattr(discord_message, "mentions", [])],
            }

            # Get recent messages from channel (simplified - would need actual Discord API call in real implementation)
            recent_messages: list[dict[str, Any]] = []

            # Note: Recent message history would require async Discord API calls
            # For now, we rely on the pipeline's context window management
            # Future enhancement: implement async history fetching in process_discord_message

            return message_data, recent_messages

        except Exception as e:
            logger.error(f"Failed to convert Discord message: {e}", exc_info=True)
            # Return minimal message data
            return (
                {
                    "id": "",
                    "content": str(getattr(discord_message, "content", "")),
                    "author": {"id": "", "username": "", "bot": False},
                    "guild_id": None,
                    "channel_id": None,
                },
                [],
            )

    async def process_discord_message(self, discord_message: Any) -> StepResult:
        """Process a Discord message through the conversational pipeline."""
        try:
            if not self._initialized:
                init_result = await self.initialize()
                if not init_result.success:
                    return StepResult.fail("Pipeline service not initialized")

            # Skip bot messages
            if getattr(discord_message.author, "bot", False):
                return StepResult.ok(data={"action": "skipped", "reason": "bot_message"})

            # Resolve tenant context from guild
            guild_id = getattr(discord_message.guild, "id", None) if hasattr(discord_message, "guild") and discord_message.guild else None
            tenant_ctx = self._resolve_tenant_context(guild_id)

            # Convert Discord message to pipeline format
            message_data, recent_messages = self._convert_discord_message(discord_message)

            guild_id_str = str(guild_id) if guild_id else "dm"

            # Get or create pipeline for this guild
            pipeline = self._get_or_create_pipeline(guild_id_str, tenant_ctx)

            # Process message with tenant context
            if tenant_ctx:
                with with_tenant(tenant_ctx):
                    result = await pipeline.process_message(message_data, recent_messages)
            else:
                result = await pipeline.process_message(message_data, recent_messages)

            return result

        except Exception as e:
            logger.error(f"Failed to process Discord message: {e}", exc_info=True)
            return StepResult.fail(f"Message processing failed: {e!s}")


# Global singleton instance
_pipeline_service: DiscordPipelineService | None = None


def get_pipeline_service() -> DiscordPipelineService:
    """Get or create the global Discord pipeline service instance."""
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = DiscordPipelineService()
    return _pipeline_service

