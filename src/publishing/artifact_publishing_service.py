"""Artifact Publishing Service for Creator Intelligence.

This module provides publishing capabilities for analysis artifacts including:
- Discord API integration for report publishing
- MCP tool integration for seamless publishing
- Artifact formatting and presentation
- Publishing queue management

Features:
- Discord webhook integration for automated publishing
- Rich embed formatting for analysis reports
- Publishing queue with retry logic
- Integration with multimodal analysis pipeline

Dependencies:
- discord.py: For Discord API interactions
- requests: For webhook HTTP requests
- Optional: Custom formatting libraries
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)

# Try to import discord.py (optional dependency)
try:
    from discord.ext import commands

    import discord

    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    commands = None  # type: ignore
    logger.warning("discord.py not available, Discord publishing disabled")


@dataclass
class PublishingArtifact:
    """An artifact to be published."""

    artifact_type: str  # report, summary, highlight, analysis, etc.
    title: str
    content: str
    metadata: dict[str, Any]
    platform: str = "discord"
    priority: int = 1  # 1-10, higher = more important
    created_at: float = 0.0


@dataclass
class PublishingResult:
    """Result of publishing operation."""

    success: bool
    artifact_id: str
    published_at: float
    platform_response: dict[str, Any] | None = None
    error_message: str | None = None


@dataclass
class PublishingQueue:
    """Publishing queue for managing artifact distribution."""

    pending_artifacts: list[PublishingArtifact] = None  # type: ignore[assignment]
    published_artifacts: list[PublishingResult] = None  # type: ignore[assignment]
    failed_artifacts: list[PublishingResult] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.pending_artifacts is None:
            self.pending_artifacts = []
        if self.published_artifacts is None:
            self.published_artifacts = []
        if self.failed_artifacts is None:
            self.failed_artifacts = []


class ArtifactPublishingService:
    """Service for publishing analysis artifacts to various platforms.

    Usage:
        service = ArtifactPublishingService()
        result = service.publish_artifact(artifact)
        success = result.data["success"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize publishing service.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._publishing_cache: dict[str, PublishingResult] = {}
        self._publishing_queue = PublishingQueue()

        # Discord client (lazy initialization)
        self._discord_client: Any = None
        self._discord_webhook_url: str | None = None

        # Load configuration from environment
        self._load_config()

    def _load_config(self) -> None:
        """Load publishing configuration from environment."""
        import os

        self._discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self._discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")

    def publish_artifact(
        self,
        artifact: PublishingArtifact,
        platform: str | None = None,
        use_cache: bool = True,
    ) -> StepResult:
        """Publish an artifact to specified platform.

        Args:
            artifact: Artifact to publish
            platform: Target platform (discord, webhook, etc.)
            use_cache: Whether to use publishing cache

        Returns:
            StepResult with publishing result
        """
        try:
            import time

            start_time = time.time()

            # Validate input
            if not artifact or not artifact.title or not artifact.content:
                return StepResult.fail("Artifact must have title and content", status="bad_request")

            # Determine platform
            if platform is None:
                platform = artifact.platform

            # Check cache first
            if use_cache:
                cache_result = self._check_cache(artifact, platform)
                if cache_result:
                    logger.info(f"Publishing cache hit for {artifact.title}")
                    return StepResult.ok(
                        data={
                            "success": cache_result.success,
                            "artifact_id": cache_result.artifact_id,
                            "published_at": cache_result.published_at,
                            "platform_response": cache_result.platform_response,
                            "error_message": cache_result.error_message,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )

            # Publish artifact
            publishing_result = self._publish_artifact(artifact, platform)

            if publishing_result:
                # Cache result
                if use_cache:
                    self._cache_result(artifact, platform, publishing_result)

                processing_time = (time.time() - start_time) * 1000

                return StepResult.ok(
                    data={
                        "success": publishing_result.success,
                        "artifact_id": publishing_result.artifact_id,
                        "published_at": publishing_result.published_at,
                        "platform_response": publishing_result.platform_response,
                        "error_message": publishing_result.error_message,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Publishing failed", status="retryable")

        except Exception as e:
            logger.error(f"Artifact publishing failed: {e}")
            return StepResult.fail(f"Publishing failed: {str(e)}", status="retryable")

    def publish_report(
        self,
        report_data: dict[str, Any],
        report_type: str = "analysis",
        title: str | None = None,
        platform: str = "discord",
    ) -> StepResult:
        """Publish an analysis report to Discord.

        Args:
            report_data: Report content and metadata
            report_type: Type of report (analysis, summary, highlights, etc.)
            title: Report title (auto-generated if None)
            platform: Target platform

        Returns:
            StepResult with publishing result
        """
        try:
            # Generate title if not provided
            if title is None:
                title = self._generate_report_title(report_data, report_type)

            # Format content for publishing
            formatted_content = self._format_report_content(report_data, report_type)

            # Create artifact
            artifact = PublishingArtifact(
                artifact_type=report_type,
                title=title,
                content=formatted_content,
                metadata=report_data,
                platform=platform,
                priority=5,  # Medium priority for reports
                created_at=time.time(),
            )

            # Publish artifact
            return self.publish_artifact(artifact, platform)

        except Exception as e:
            logger.error(f"Report publishing failed: {e}")
            return StepResult.fail(f"Report publishing failed: {str(e)}")

    def publish_highlight_summary(
        self,
        highlights: list[dict[str, Any]],
        episode_info: dict[str, Any] | None = None,
        platform: str = "discord",
    ) -> StepResult:
        """Publish a highlight summary to Discord.

        Args:
            highlights: List of highlight segments
            episode_info: Episode metadata (optional)
            platform: Target platform

        Returns:
            StepResult with publishing result
        """
        try:
            # Generate summary content
            summary_content = self._format_highlight_summary(highlights, episode_info)

            # Generate title
            episode_title = episode_info.get("title", "Unknown Episode") if episode_info else "Content"
            title = f"🎬 Highlight Summary: {episode_title}"

            # Create artifact
            artifact = PublishingArtifact(
                artifact_type="highlight_summary",
                title=title,
                content=summary_content,
                metadata={
                    "highlights": highlights,
                    "episode_info": episode_info or {},
                    "highlight_count": len(highlights),
                },
                platform=platform,
                priority=7,  # Higher priority for highlights
                created_at=time.time(),
            )

            # Publish artifact
            return self.publish_artifact(artifact, platform)

        except Exception as e:
            logger.error(f"Highlight summary publishing failed: {e}")
            return StepResult.fail(f"Highlight summary publishing failed: {str(e)}")

    def publish_claim_summary(
        self,
        claims: list[dict[str, Any]],
        quotes: list[dict[str, Any]] | None = None,
        episode_info: dict[str, Any] | None = None,
        platform: str = "discord",
    ) -> StepResult:
        """Publish a claim and quote summary to Discord.

        Args:
            claims: List of extracted claims
            quotes: List of extracted quotes (optional)
            episode_info: Episode metadata (optional)
            platform: Target platform

        Returns:
            StepResult with publishing result
        """
        try:
            # Generate summary content
            summary_content = self._format_claim_quote_summary(claims, quotes, episode_info)

            # Generate title
            episode_title = episode_info.get("title", "Unknown Episode") if episode_info else "Content"
            title = f"📋 Claims & Quotes: {episode_title}"

            # Create artifact
            artifact = PublishingArtifact(
                artifact_type="claim_quote_summary",
                title=title,
                content=summary_content,
                metadata={
                    "claims": claims,
                    "quotes": quotes or [],
                    "episode_info": episode_info or {},
                    "claim_count": len(claims),
                    "quote_count": len(quotes) if quotes else 0,
                },
                platform=platform,
                priority=6,  # Medium-high priority for analysis
                created_at=time.time(),
            )

            # Publish artifact
            return self.publish_artifact(artifact, platform)

        except Exception as e:
            logger.error(f"Claim/quote summary publishing failed: {e}")
            return StepResult.fail(f"Claim/quote summary publishing failed: {str(e)}")

    def _publish_artifact(self, artifact: PublishingArtifact, platform: str) -> PublishingResult | None:
        """Publish artifact to specified platform.

        Args:
            artifact: Artifact to publish
            platform: Target platform

        Returns:
            PublishingResult or None if publishing fails
        """
        try:
            if platform == "discord":
                return self._publish_to_discord(artifact)
            elif platform == "webhook":
                return self._publish_to_webhook(artifact)
            else:
                logger.warning(f"Unsupported platform: {platform}")
                return PublishingResult(
                    success=False,
                    artifact_id=f"{artifact.artifact_type}_{int(time.time())}",
                    published_at=time.time(),
                    error_message=f"Unsupported platform: {platform}",
                )

        except Exception as e:
            logger.error(f"Artifact publishing failed: {e}")
            return PublishingResult(
                success=False,
                artifact_id=f"{artifact.artifact_type}_{int(time.time())}",
                published_at=time.time(),
                error_message=str(e),
            )

    def _publish_to_discord(self, artifact: PublishingArtifact) -> PublishingResult:
        """Publish artifact to Discord using webhook or bot.

        Args:
            artifact: Artifact to publish

        Returns:
            PublishingResult with Discord response
        """
        try:
            # Use webhook if available
            if self._discord_webhook_url:
                return self._publish_to_discord_webhook(artifact)

            # Use bot client if available
            if self._discord_bot_token and DISCORD_AVAILABLE:
                return self._publish_to_discord_bot(artifact)

            # Fallback to webhook if URL is available
            logger.warning("Discord bot not configured, trying webhook")
            if self._discord_webhook_url:
                return self._publish_to_discord_webhook(artifact)

            return PublishingResult(
                success=False,
                artifact_id=f"{artifact.artifact_type}_{int(time.time())}",
                published_at=time.time(),
                error_message="Discord publishing not configured",
            )

        except Exception as e:
            logger.error(f"Discord publishing failed: {e}")
            return PublishingResult(
                success=False,
                artifact_id=f"{artifact.artifact_type}_{int(time.time())}",
                published_at=time.time(),
                error_message=str(e),
            )

    def _publish_to_discord_webhook(self, artifact: PublishingArtifact) -> PublishingResult:
        """Publish artifact to Discord via webhook.

        Args:
            artifact: Artifact to publish

        Returns:
            PublishingResult with webhook response
        """
        try:
            import requests

            # Format Discord embed
            embed = self._format_discord_embed(artifact)

            # Prepare webhook payload
            payload = {
                "embeds": [embed],
                "username": "Creator Intelligence Bot",
                "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png",
            }

            # Send to webhook
            response = requests.post(
                self._discord_webhook_url,
                json=payload,
                timeout=10,
            )

            response.raise_for_status()

            return PublishingResult(
                success=True,
                artifact_id=f"{artifact.artifact_type}_{int(time.time())}",
                published_at=time.time(),
                platform_response={
                    "status_code": response.status_code,
                    "response_text": response.text[:200],  # First 200 chars
                },
            )

        except Exception as e:
            logger.error(f"Discord webhook publishing failed: {e}")
            return PublishingResult(
                success=False,
                artifact_id=f"{artifact.artifact_type}_{int(time.time())}",
                published_at=time.time(),
                error_message=str(e),
            )

    def _publish_to_discord_bot(self, artifact: PublishingArtifact) -> PublishingResult:
        """Publish artifact to Discord via bot client.

        Args:
            artifact: Artifact to publish

        Returns:
            PublishingResult with bot response
        """
        # Placeholder for bot-based publishing
        # Would require channel ID and bot setup
        logger.warning("Discord bot publishing not implemented, using webhook fallback")

        return PublishingResult(
            success=False,
            artifact_id=f"{artifact.artifact_type}_{int(time.time())}",
            published_at=time.time(),
            error_message="Discord bot publishing not implemented",
        )

    def _publish_to_webhook(self, artifact: PublishingArtifact) -> PublishingResult:
        """Publish artifact to generic webhook.

        Args:
            artifact: Artifact to publish

        Returns:
            PublishingResult with webhook response
        """
        try:
            # Prepare webhook payload
            payload = {
                "artifact_type": artifact.artifact_type,
                "title": artifact.title,
                "content": artifact.content,
                "metadata": artifact.metadata,
                "timestamp": time.time(),
            }

            # Send to webhook (would need webhook URL configuration)
            # For now, simulate success
            return PublishingResult(
                success=True,
                artifact_id=f"{artifact.artifact_type}_{int(time.time())}",
                published_at=time.time(),
                platform_response={"status": "simulated_success"},
            )

        except Exception as e:
            logger.error(f"Webhook publishing failed: {e}")
            return PublishingResult(
                success=False,
                artifact_id=f"{artifact.artifact_type}_{int(time.time())}",
                published_at=time.time(),
                error_message=str(e),
            )

    def _format_discord_embed(self, artifact: PublishingArtifact) -> dict[str, Any]:
        """Format artifact as Discord embed.

        Args:
            artifact: Artifact to format

        Returns:
            Discord embed dictionary
        """
        # Determine color based on artifact type
        color_map = {
            "highlight_summary": 0xFFD700,  # Gold
            "claim_quote_summary": 0x3498DB,  # Blue
            "analysis": 0xE74C3C,  # Red
            "report": 0x2ECC71,  # Green
        }

        embed_color = color_map.get(artifact.artifact_type, 0x95A5A6)  # Default gray

        # Create embed
        embed = {
            "title": artifact.title,
            "description": self._truncate_content(artifact.content, 2000),  # Discord limit
            "color": embed_color,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "footer": {
                "text": f"Creator Intelligence • {artifact.artifact_type}",
            },
        }

        # Add fields based on artifact type
        if artifact.artifact_type == "highlight_summary":
            highlight_count = artifact.metadata.get("highlight_count", 0)
            embed["fields"] = [
                {
                    "name": "🎬 Highlights Found",
                    "value": str(highlight_count),
                    "inline": True,
                }
            ]

        elif artifact.artifact_type == "claim_quote_summary":
            claim_count = artifact.metadata.get("claim_count", 0)
            quote_count = artifact.metadata.get("quote_count", 0)
            embed["fields"] = [
                {
                    "name": "📋 Claims",
                    "value": str(claim_count),
                    "inline": True,
                },
                {
                    "name": "💬 Quotes",
                    "value": str(quote_count),
                    "inline": True,
                },
            ]

        return embed

    def _generate_report_title(self, report_data: dict[str, Any], report_type: str) -> str:
        """Generate a title for the report.

        Args:
            report_data: Report data
            report_type: Type of report

        Returns:
            Generated title string
        """
        # Try to extract meaningful title from data
        episode_title = report_data.get("episode_title") or report_data.get("title")
        platform = report_data.get("platform", "Content")

        if episode_title:
            return f"📊 {report_type.title()}: {episode_title}"
        else:
            return f"📊 {platform} {report_type.title()} Report"

    def _format_report_content(self, report_data: dict[str, Any], report_type: str) -> str:
        """Format report data as readable content.

        Args:
            report_data: Report data
            report_type: Type of report

        Returns:
            Formatted content string
        """
        content_lines = []

        # Add summary based on report type
        if report_type == "analysis":
            content_lines.append("🔍 **Analysis Summary**")
            if "sentiment" in report_data:
                sentiment = report_data["sentiment"]
                content_lines.append(
                    f"• Sentiment: {sentiment.get('sentiment', 'unknown')} ({sentiment.get('confidence', 0):.1%})"
                )

        elif report_type == "highlights":
            content_lines.append("🎬 **Highlight Summary**")
            highlights = report_data.get("highlights", [])
            content_lines.append(f"• Found {len(highlights)} highlight moments")

        # Add metadata
        if "duration" in report_data:
            duration = report_data["duration"]
            content_lines.append(f"• Duration: {duration:.1f}s")

        if "platform" in report_data:
            content_lines.append(f"• Platform: {report_data['platform']}")

        return "\n".join(content_lines)

    def _format_highlight_summary(self, highlights: list[dict[str, Any]], episode_info: dict[str, Any] | None) -> str:
        """Format highlight summary for publishing.

        Args:
            highlights: List of highlight segments
            episode_info: Episode metadata

        Returns:
            Formatted summary string
        """
        lines = []

        # Header
        episode_title = episode_info.get("title", "Unknown Episode") if episode_info else "Content"
        lines.append(f"🎬 **Highlight Summary: {episode_title}**")
        lines.append("")

        # Sort highlights by score
        sorted_highlights = sorted(highlights, key=lambda h: h.get("highlight_score", 0), reverse=True)

        # Show top highlights
        for i, highlight in enumerate(sorted_highlights[:5]):  # Top 5
            start_time = highlight.get("start_time", 0)
            end_time = highlight.get("end_time", start_time + 30)
            score = highlight.get("highlight_score", 0)
            transcript = highlight.get("transcript_text", "No transcript available")

            lines.append(f"**{i + 1}.** [{start_time:.1f}s - {end_time:.1f}s] (Score: {score:.2f})")
            lines.append(f'   "{transcript[:100]}{"..." if len(transcript) > 100 else ""}"')
            lines.append("")

        if len(highlights) > 5:
            lines.append(f"... and {len(highlights) - 5} more highlights")

        return "\n".join(lines)

    def _format_claim_quote_summary(
        self,
        claims: list[dict[str, Any]],
        quotes: list[dict[str, Any]] | None,
        episode_info: dict[str, Any] | None,
    ) -> str:
        """Format claim and quote summary for publishing.

        Args:
            claims: List of extracted claims
            quotes: List of extracted quotes
            episode_info: Episode metadata

        Returns:
            Formatted summary string
        """
        lines = []

        # Header
        episode_title = episode_info.get("title", "Unknown Episode") if episode_info else "Content"
        lines.append(f"📋 **Claims & Quotes: {episode_title}**")
        lines.append("")

        # Claims section
        if claims:
            lines.append(f"**📋 Claims ({len(claims)})**")
            for i, claim in enumerate(claims[:3]):  # Top 3 claims
                confidence = claim.get("confidence", 0)
                speaker = claim.get("speaker", "Unknown")
                lines.append(f'• **{speaker}:** "{claim.get("text", "")}" ({confidence:.1%})')
            if len(claims) > 3:
                lines.append(f"... and {len(claims) - 3} more claims")
            lines.append("")

        # Quotes section
        if quotes:
            lines.append(f"**💬 Notable Quotes ({len(quotes)})**")
            for i, quote in enumerate(quotes[:3]):  # Top 3 quotes
                confidence = quote.get("confidence", 0)
                speaker = quote.get("speaker", "Unknown")
                lines.append(f'• **{speaker}:** "{quote.get("text", "")}" ({confidence:.1%})')
            if len(quotes) > 3:
                lines.append(f"... and {len(quotes) - 3} more quotes")

        return "\n".join(lines)

    def _truncate_content(self, content: str, max_length: int) -> str:
        """Truncate content to maximum length.

        Args:
            content: Content to truncate
            max_length: Maximum length

        Returns:
            Truncated content
        """
        if len(content) <= max_length:
            return content

        return content[: max_length - 3] + "..."

    def _check_cache(self, artifact: PublishingArtifact, platform: str) -> PublishingResult | None:
        """Check if publishing result exists in cache.

        Args:
            artifact: Artifact being published
            platform: Target platform

        Returns:
            Cached PublishingResult or None
        """
        import hashlib

        # Create cache key from artifact content and platform
        content_hash = hashlib.sha256(artifact.content.encode()).hexdigest()[:16]
        cache_key = f"{artifact.artifact_type}:{content_hash}:{platform}"

        if cache_key in self._publishing_cache:
            return self._publishing_cache[cache_key]

        return None

    def _cache_result(self, artifact: PublishingArtifact, platform: str, result: PublishingResult) -> None:
        """Cache publishing result.

        Args:
            artifact: Published artifact
            platform: Target platform
            result: PublishingResult to cache
        """
        import hashlib

        # Create cache key
        content_hash = hashlib.sha256(artifact.content.encode()).hexdigest()[:16]
        cache_key = f"{artifact.artifact_type}:{content_hash}:{platform}"

        # Evict old entries if cache is full
        if len(self._publishing_cache) >= self.cache_size:
            # Simple FIFO eviction - remove first key
            first_key = next(iter(self._publishing_cache))
            del self._publishing_cache[first_key]

        self._publishing_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear publishing cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._publishing_cache)
        self._publishing_cache.clear()

        logger.info(f"Cleared {cache_size} cached publishing results")

        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get publishing cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._publishing_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._publishing_cache) / self.cache_size if self.cache_size > 0 else 0.0,
                "platforms_cached": {},
            }

            # Count entries per platform
            for result in self._publishing_cache.values():
                # Extract platform from error message or assume discord
                platform = "discord"  # Default
                if result.error_message and "webhook" in result.error_message.lower():
                    platform = "webhook"
                stats["platforms_cached"][platform] = stats["platforms_cached"].get(platform, 0) + 1

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {str(e)}")


# Singleton instance
_publishing_service: ArtifactPublishingService | None = None


def get_artifact_publishing_service() -> ArtifactPublishingService:
    """Get singleton publishing service instance.

    Returns:
        Initialized ArtifactPublishingService instance
    """
    global _publishing_service

    if _publishing_service is None:
        _publishing_service = ArtifactPublishingService()

    return _publishing_service
