"""
Discord Bot Event Handler for Artifact Publishing.

This module provides event handlers for the Discord bot to automatically
publish artifacts and handle crew workflow integration.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from ..services.artifact_publisher import ArtifactMetadata, ArtifactPublisher, DiscordConfig
from ..step_result import StepResult


if TYPE_CHECKING:
    from discord.ext import commands


logger = logging.getLogger(__name__)


class ArtifactHandler:
    """Discord bot event handler for artifact publishing."""

    def __init__(self, bot: commands.Bot, publisher: ArtifactPublisher | None = None):
        """Initialize artifact handler.

        Args:
            bot: Discord bot instance
            publisher: Artifact publisher instance
        """
        self.bot = bot
        self.publisher = publisher or ArtifactPublisher()
        self.crew_system = None  # Will be set by crew integration

        # Register event handlers
        self._register_events()

        logger.info("Initialized ArtifactHandler for Discord bot")

    def _register_events(self):
        """Register Discord bot event handlers."""
        self.bot.add_listener(self.on_ready, "on_ready")
        self.bot.add_listener(self.on_crew_completion, "on_crew_completion")

    async def on_ready(self):
        """Handle bot ready event."""
        logger.info(f"Discord bot ready: {self.bot.user}")

    async def on_crew_completion(self, crew_result: dict[str, Any]):
        """Handle crew completion event.

        Args:
            crew_result: Result from crew execution
        """
        try:
            logger.info("Processing crew completion for artifact publishing")

            # Extract artifacts from crew result
            artifacts = self._extract_artifacts_from_crew_result(crew_result)

            if not artifacts:
                logger.info("No artifacts found in crew result")
                return

            # Publish each artifact
            for artifact_data, metadata in artifacts:
                result = await self.publisher.publish_artifact(
                    artifact_data=artifact_data,
                    metadata=metadata,
                )

                if result.success:
                    logger.info("Published artifact: %s", metadata.artifact_id)
                else:
                    logger.error("Failed to publish artifact %s: %s", metadata.artifact_id, result.error)

        except Exception as e:
            logger.error("Error handling crew completion: %s", str(e))

    def _extract_artifacts_from_crew_result(
        self, crew_result: dict[str, Any]
    ) -> list[tuple[dict[str, Any], ArtifactMetadata]]:
        """Extract artifacts from crew execution result.

        Args:
            crew_result: Crew execution result

        Returns:
            List of (artifact_data, metadata) tuples
        """
        artifacts = []

        try:
            # Extract analysis artifacts
            if "analysis" in crew_result:
                analysis_data = crew_result["analysis"]
                metadata = ArtifactMetadata(
                    artifact_id=f"analysis_{int(time.time())}",
                    title="Content Analysis",
                    description="Comprehensive analysis of the provided content",
                    content_type="analysis",
                    tenant=crew_result.get("tenant", ""),
                    workspace=crew_result.get("workspace", ""),
                    created_at=time.time(),
                    source_url=crew_result.get("source_url"),
                    tags=["analysis", "content"],
                )
                artifacts.append((analysis_data, metadata))

            # Extract transcript artifacts
            if "transcript" in crew_result:
                transcript_data = crew_result["transcript"]
                metadata = ArtifactMetadata(
                    artifact_id=f"transcript_{int(time.time())}",
                    title="Content Transcript",
                    description="Transcribed content from the source",
                    content_type="transcript",
                    tenant=crew_result.get("tenant", ""),
                    workspace=crew_result.get("workspace", ""),
                    created_at=time.time(),
                    source_url=crew_result.get("source_url"),
                    tags=["transcript", "content"],
                )
                artifacts.append((transcript_data, metadata))

            # Extract verification artifacts
            if "verification" in crew_result:
                verification_data = crew_result["verification"]
                metadata = ArtifactMetadata(
                    artifact_id=f"verification_{int(time.time())}",
                    title="Fact Verification",
                    description="Fact-checking and verification results",
                    content_type="verification",
                    tenant=crew_result.get("tenant", ""),
                    workspace=crew_result.get("workspace", ""),
                    created_at=time.time(),
                    source_url=crew_result.get("source_url"),
                    tags=["verification", "fact-check"],
                )
                artifacts.append((verification_data, metadata))

            # Extract summary artifacts
            if "summary" in crew_result:
                summary_data = crew_result["summary"]
                metadata = ArtifactMetadata(
                    artifact_id=f"summary_{int(time.time())}",
                    title="Content Summary",
                    description="Summarized content and key findings",
                    content_type="summary",
                    tenant=crew_result.get("tenant", ""),
                    workspace=crew_result.get("workspace", ""),
                    created_at=time.time(),
                    source_url=crew_result.get("source_url"),
                    tags=["summary", "content"],
                )
                artifacts.append((summary_data, metadata))

        except Exception as e:
            logger.error("Error extracting artifacts from crew result: %s", str(e))

        return artifacts

    def set_crew_system(self, crew_system):
        """Set the crew system for integration.

        Args:
            crew_system: Crew system instance
        """
        self.crew_system = crew_system
        logger.info("Crew system integrated with ArtifactHandler")

    async def publish_manual_artifact(
        self,
        artifact_data: dict[str, Any],
        title: str,
        description: str,
        content_type: str = "analysis",
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """Manually publish an artifact.

        Args:
            artifact_data: Artifact content
            title: Artifact title
            description: Artifact description
            content_type: Type of content
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with publishing result
        """
        try:
            metadata = ArtifactMetadata(
                artifact_id=f"manual_{int(time.time())}",
                title=title,
                description=description,
                content_type=content_type,
                tenant=tenant,
                workspace=workspace,
                created_at=time.time(),
            )

            result = await self.publisher.publish_artifact(
                artifact_data=artifact_data,
                metadata=metadata,
                tenant=tenant,
                workspace=workspace,
            )

            return result

        except Exception as e:
            logger.error("Manual artifact publishing failed: %s", str(e))
            return StepResult.fail(f"Manual artifact publishing failed: {e!s}")

    async def get_publishing_status(self) -> StepResult:
        """Get current publishing status.

        Returns:
            StepResult with publishing status
        """
        try:
            stats_result = self.publisher.get_publishing_stats()
            if stats_result.success:
                return StepResult.ok(
                    data={
                        "publisher_stats": stats_result.data,
                        "bot_ready": self.bot.is_ready(),
                        "crew_integrated": self.crew_system is not None,
                    }
                )
            else:
                return StepResult.fail(f"Failed to get publisher stats: {stats_result.error}")

        except Exception as e:
            logger.error("Failed to get publishing status: %s", str(e))
            return StepResult.fail(f"Failed to get publishing status: {e!s}")


def create_artifact_handler(bot: commands.Bot, discord_config: DiscordConfig | None = None) -> ArtifactHandler:
    """Create an artifact handler for a Discord bot.

    Args:
        bot: Discord bot instance
        discord_config: Discord configuration

    Returns:
        Configured ArtifactHandler
    """
    publisher = ArtifactPublisher(discord_config)
    return ArtifactHandler(bot, publisher)
