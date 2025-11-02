"""
Artifact Publisher for Discord integration.

This module provides services for publishing finalized artifacts
and analysis results to Discord channels.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import aiohttp

from ..step_result import StepResult
from ..tenancy.helpers import require_tenant


logger = logging.getLogger(__name__)


@dataclass
class ArtifactMetadata:
    """Metadata for published artifacts."""

    artifact_id: str
    title: str
    description: str
    content_type: str  # 'analysis', 'transcript', 'summary', 'verification'
    tenant: str
    workspace: str
    created_at: float
    source_url: str | None = None
    tags: list[str] | None = None


@dataclass
class DiscordConfig:
    """Configuration for Discord publishing."""

    webhook_url: str | None = None
    bot_token: str | None = None
    channel_id: str | None = None
    enable_embeds: bool = True
    max_message_length: int = 2000
    enable_file_uploads: bool = True
    max_file_size_mb: int = 8


class ArtifactPublisher:
    """Service for publishing artifacts to Discord."""

    def __init__(self, config: DiscordConfig | None = None):
        """Initialize artifact publisher.

        Args:
            config: Discord configuration
        """
        self.config = config or DiscordConfig()
        self.published_artifacts: list[ArtifactMetadata] = []
        self.publish_count = 0
        self.total_publish_time = 0.0

        logger.info("Initialized ArtifactPublisher with webhook: %s", bool(self.config.webhook_url))

    @require_tenant(strict_flag_enabled=False)
    async def publish_artifact(
        self,
        artifact_data: dict[str, Any],
        metadata: ArtifactMetadata,
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """Publish an artifact to Discord.

        Args:
            artifact_data: The artifact content to publish
            metadata: Artifact metadata
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with publishing result
        """
        try:
            start_time = time.time()

            # Validate configuration
            if not self.config.webhook_url and not self.config.bot_token:
                return StepResult.fail("No Discord webhook URL or bot token configured")

            # Format the artifact for Discord
            formatted_content = self._format_artifact_for_discord(artifact_data, metadata)

            # Publish to Discord
            if self.config.webhook_url:
                result = await self._publish_via_webhook(formatted_content, metadata)
            else:
                result = await self._publish_via_bot(formatted_content, metadata)

            if result.success:
                # Track publishing metrics
                publish_time = (time.time() - start_time) * 1000
                self.publish_count += 1
                self.total_publish_time += publish_time
                self.published_artifacts.append(metadata)

                logger.debug(
                    "Published artifact %s to Discord (time: %.1fms)",
                    metadata.artifact_id,
                    publish_time,
                )

                return StepResult.ok(
                    data={
                        "artifact_id": metadata.artifact_id,
                        "published": True,
                        "publish_time_ms": publish_time,
                        "discord_message_id": result.data.get("message_id"),
                    }
                )
            else:
                logger.error("Failed to publish artifact %s: %s", metadata.artifact_id, result.error)
                return StepResult.fail(f"Failed to publish artifact: {result.error}")

        except Exception as e:
            logger.error("Artifact publishing failed: %s", str(e))
            return StepResult.fail(f"Artifact publishing failed: {e!s}")

    def _format_artifact_for_discord(self, artifact_data: dict[str, Any], metadata: ArtifactMetadata) -> dict[str, Any]:
        """Format artifact data for Discord publishing.

        Args:
            artifact_data: Raw artifact data
            metadata: Artifact metadata

        Returns:
            Formatted content for Discord
        """
        # Create Discord embed if enabled
        if self.config.enable_embeds:
            embed = {
                "title": metadata.title,
                "description": metadata.description,
                "color": self._get_color_for_content_type(metadata.content_type),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(metadata.created_at)),
                "fields": [],
            }
            fields = embed["fields"]

            # Add content fields
            if "summary" in artifact_data:
                fields.append(
                    {
                        "name": "Summary",
                        "value": self._truncate_text(artifact_data["summary"], 1000),
                        "inline": False,
                    }
                )

            if "key_findings" in artifact_data:
                fields.append(
                    {
                        "name": "Key Findings",
                        "value": self._truncate_text(artifact_data["key_findings"], 1000),
                        "inline": False,
                    }
                )

            if "confidence_score" in artifact_data:
                fields.append(
                    {
                        "name": "Confidence Score",
                        "value": f"{artifact_data['confidence_score']:.2f}",
                        "inline": True,
                    }
                )

            if "source_url" in artifact_data or metadata.source_url:
                fields.append(
                    {
                        "name": "Source",
                        "value": artifact_data.get("source_url", metadata.source_url),
                        "inline": True,
                    }
                )

            # Add tags if available
            if metadata.tags:
                fields.append(
                    {
                        "name": "Tags",
                        "value": ", ".join(metadata.tags),
                        "inline": True,
                    }
                )

            return {
                "content": f"📊 **{metadata.content_type.title()} Analysis Complete**",
                "embeds": [embed],
            }
        else:
            # Simple text format
            content = f"**{metadata.title}**\n\n{metadata.description}\n\n"

            if "summary" in artifact_data:
                content += f"**Summary:**\n{self._truncate_text(artifact_data['summary'], 1500)}\n\n"

            if "key_findings" in artifact_data:
                content += f"**Key Findings:**\n{self._truncate_text(artifact_data['key_findings'], 1500)}\n\n"

            if "source_url" in artifact_data or metadata.source_url:
                content += f"**Source:** {artifact_data.get('source_url', metadata.source_url)}\n"

            return {"content": self._truncate_text(content, self.config.max_message_length)}

    def _get_color_for_content_type(self, content_type: str) -> int:
        """Get Discord embed color for content type.

        Args:
            content_type: Type of content

        Returns:
            Discord embed color (integer)
        """
        color_map = {
            "analysis": 0x3498DB,  # Blue
            "transcript": 0x2ECC71,  # Green
            "summary": 0xF39C12,  # Orange
            "verification": 0xE74C3C,  # Red
            "fact_check": 0x9B59B6,  # Purple
        }
        return color_map.get(content_type, 0x95A5A6)  # Default gray

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    async def _publish_via_webhook(self, content: dict[str, Any], metadata: ArtifactMetadata) -> StepResult:
        """Publish artifact via Discord webhook.

        Args:
            content: Formatted content
            metadata: Artifact metadata

        Returns:
            StepResult with publishing result
        """
        try:
            if not self.config.webhook_url:
                return StepResult.fail("No webhook URL configured")

            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    self.config.webhook_url,
                    json=content,
                    headers={"Content-Type": "application/json"},
                ) as response,
            ):
                if response.status == 200:
                    response_data = await response.json()
                    return StepResult.ok(data={"message_id": response_data.get("id")})
                else:
                    error_text = await response.text()
                    return StepResult.fail(f"Webhook failed: {response.status} - {error_text}")

        except Exception as e:
            logger.error("Webhook publishing failed: %s", str(e))
            return StepResult.fail(f"Webhook publishing failed: {e!s}")

    async def _publish_via_bot(self, content: dict[str, Any], metadata: ArtifactMetadata) -> StepResult:
        """Publish artifact via Discord bot.

        Args:
            content: Formatted content
            metadata: Artifact metadata

        Returns:
            StepResult with publishing result
        """
        try:
            # This would require Discord.py integration
            # For now, return a placeholder implementation
            logger.warning("Bot publishing not yet implemented, using webhook fallback")
            return StepResult.fail("Bot publishing not implemented")

        except Exception as e:
            logger.error("Bot publishing failed: %s", str(e))
            return StepResult.fail(f"Bot publishing failed: {e!s}")

    async def publish_batch(
        self,
        artifacts: list[tuple[dict[str, Any], ArtifactMetadata]],
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """Publish multiple artifacts in batch.

        Args:
            artifacts: List of (artifact_data, metadata) tuples
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with batch publishing results
        """
        try:
            results = []
            successful_publishes = 0
            failed_publishes = 0

            for artifact_data, metadata in artifacts:
                result = await self.publish_artifact(
                    artifact_data=artifact_data,
                    metadata=metadata,
                    tenant=tenant,
                    workspace=workspace,
                )

                if result.success:
                    successful_publishes += 1
                    results.append(
                        {
                            "artifact_id": metadata.artifact_id,
                            "success": True,
                            "publish_time_ms": result.data.get("publish_time_ms", 0),
                        }
                    )
                else:
                    failed_publishes += 1
                    results.append(
                        {
                            "artifact_id": metadata.artifact_id,
                            "success": False,
                            "error": result.error,
                        }
                    )

            return StepResult.ok(
                data={
                    "total_artifacts": len(artifacts),
                    "successful_publishes": successful_publishes,
                    "failed_publishes": failed_publishes,
                    "results": results,
                }
            )

        except Exception as e:
            logger.error("Batch publishing failed: %s", str(e))
            return StepResult.fail(f"Batch publishing failed: {e!s}")

    def get_publishing_stats(self) -> StepResult:
        """Get publishing statistics.

        Returns:
            StepResult with publishing statistics
        """
        try:
            avg_publish_time = self.total_publish_time / self.publish_count if self.publish_count > 0 else 0.0

            stats = {
                "total_published": self.publish_count,
                "average_publish_time_ms": avg_publish_time,
                "total_publish_time_ms": self.total_publish_time,
                "published_artifacts": len(self.published_artifacts),
                "config": {
                    "webhook_configured": bool(self.config.webhook_url),
                    "bot_configured": bool(self.config.bot_token),
                    "embeds_enabled": self.config.enable_embeds,
                    "file_uploads_enabled": self.config.enable_file_uploads,
                },
            }

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error("Failed to get publishing stats: %s", str(e))
            return StepResult.fail(f"Failed to get publishing stats: {e!s}")

    def reset_publishing_history(self) -> StepResult:
        """Reset publishing history.

        Returns:
            StepResult indicating success/failure
        """
        try:
            self.published_artifacts.clear()
            self.publish_count = 0
            self.total_publish_time = 0.0
            logger.info("Reset publishing history")
            return StepResult.ok(data={"reset": True})

        except Exception as e:
            logger.error("Failed to reset publishing history: %s", str(e))
            return StepResult.fail(f"Failed to reset publishing history: {e!s}")

    def update_config(self, new_config: DiscordConfig) -> StepResult:
        """Update Discord configuration.

        Args:
            new_config: New Discord configuration

        Returns:
            StepResult indicating success/failure
        """
        try:
            self.config = new_config
            logger.info("Updated Discord configuration")
            return StepResult.ok(data={"config_updated": True})

        except Exception as e:
            logger.error("Failed to update Discord config: %s", str(e))
            return StepResult.fail(f"Failed to update Discord config: {e!s}")
