#!/usr/bin/env python3
"""Discord artifact publisher with tenant isolation and feature flag support.

This script publishes analysis artifacts and summaries to Discord channels
with proper tenant isolation and feature flag controls.
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import requests


class DiscordPublisher:
    """Discord publisher with tenant isolation and feature flag support."""

    def __init__(self, webhook_url: str | None = None, dry_run: bool = False):
        """Initialize Discord publisher.

        Args:
            webhook_url: Discord webhook URL. If None, uses DISCORD_PRIVATE_WEBHOOK env var.
            dry_run: If True, only log messages without actually posting.
        """
        self.webhook_url = webhook_url or os.getenv("DISCORD_PRIVATE_WEBHOOK")
        self.dry_run = dry_run or os.getenv("DISCORD_DRY_RUN", "false").lower() == "true"
        self.enabled = os.getenv("ENABLE_DISCORD_PUBLISHING", "false").lower() == "true"

        if not self.enabled:
            print("📢 Discord publishing is disabled via ENABLE_DISCORD_PUBLISHING flag")

    def publish_artifact(
        self,
        artifact_type: str,
        title: str,
        content: str,
        tenant: str = "default",
        workspace: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Publish an artifact to Discord.

        Args:
            artifact_type: Type of artifact (analysis, summary, report, etc.)
            title: Title of the artifact
            content: Content to publish
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier for organization
            metadata: Additional metadata

        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.enabled:
            print(f"📢 Discord publishing disabled - would publish {artifact_type}: {title}")
            return True

        if not self.webhook_url:
            print("❌ No Discord webhook URL configured")
            return False

        # Create Discord message
        message = self._create_message(artifact_type, title, content, tenant, workspace, metadata)

        if self.dry_run:
            print("🔍 DRY RUN - Would post to Discord:")
            print(f"   Type: {artifact_type}")
            print(f"   Title: {title}")
            print(f"   Tenant: {tenant}")
            print(f"   Workspace: {workspace}")
            print(f"   Content length: {len(content)} characters")
            return True

        try:
            response = requests.post(self.webhook_url, json=message, timeout=30)
            response.raise_for_status()
            print(f"✅ Successfully published {artifact_type} to Discord")
            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to publish to Discord: {e}")
            return False

    def _create_message(
        self,
        artifact_type: str,
        title: str,
        content: str,
        tenant: str,
        workspace: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create Discord message with proper formatting.

        Args:
            artifact_type: Type of artifact
            title: Title of the artifact
            content: Content to publish
            tenant: Tenant identifier
            workspace: Workspace identifier
            metadata: Additional metadata

        Returns:
            dict: Discord message payload
        """
        # Truncate content if too long (Discord has 2000 char limit)
        if len(content) > 1900:
            content = content[:1900] + "..."

        # Create embed
        embed = {
            "title": f"🤖 {title}",
            "description": content,
            "color": self._get_color_for_type(artifact_type),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {"text": f"Tenant: {tenant} | Workspace: {workspace}"},
            "fields": [
                {"name": "Type", "value": artifact_type, "inline": True},
                {
                    "name": "Timestamp",
                    "value": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "inline": True,
                },
            ],
        }

        # Add metadata fields if provided
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    embed["fields"].append({"name": key.replace("_", " ").title(), "value": str(value), "inline": True})

        return {"embeds": [embed]}

    def _get_color_for_type(self, artifact_type: str) -> int:
        """Get Discord embed color for artifact type.

        Args:
            artifact_type: Type of artifact

        Returns:
            int: Discord embed color (hex as int)
        """
        color_map = {
            "analysis": 0x00FF00,  # Green
            "summary": 0x0099FF,  # Blue
            "report": 0xFF9900,  # Orange
            "error": 0xFF0000,  # Red
            "warning": 0xFFFF00,  # Yellow
            "info": 0x00FFFF,  # Cyan
        }
        return color_map.get(artifact_type.lower(), 0x666666)  # Default gray

    def publish_analysis_summary(
        self, url: str, analysis_results: dict[str, Any], tenant: str = "default", workspace: str = "default"
    ) -> bool:
        """Publish analysis summary to Discord.

        Args:
            url: Source URL that was analyzed
            analysis_results: Analysis results dictionary
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            bool: True if published successfully
        """
        title = f"Analysis Complete: {url}"
        content = self._format_analysis_content(analysis_results)

        metadata = {
            "source_url": url,
            "analysis_type": analysis_results.get("type", "unknown"),
            "confidence": analysis_results.get("confidence", 0.0),
            "processing_time": analysis_results.get("processing_time", 0.0),
        }

        return self.publish_artifact("analysis", title, content, tenant, workspace, metadata)

    def _format_analysis_content(self, analysis_results: dict[str, Any]) -> str:
        """Format analysis results for Discord display.

        Args:
            analysis_results: Analysis results dictionary

        Returns:
            str: Formatted content for Discord
        """
        content_parts = []

        # Add summary
        if "summary" in analysis_results:
            content_parts.append(f"**Summary:** {analysis_results['summary']}")

        # Add key findings
        if "key_findings" in analysis_results:
            content_parts.append(f"**Key Findings:** {analysis_results['key_findings']}")

        # Add sentiment if available
        if "sentiment" in analysis_results:
            sentiment = analysis_results["sentiment"]
            if isinstance(sentiment, dict):
                label = sentiment.get("label", "unknown")
                score = sentiment.get("score", 0.0)
                content_parts.append(f"**Sentiment:** {label} (confidence: {score:.2f})")
            else:
                content_parts.append(f"**Sentiment:** {sentiment}")

        # Add quality score if available
        if "quality_score" in analysis_results:
            score = analysis_results["quality_score"]
            content_parts.append(f"**Quality Score:** {score:.2f}")

        # Add processing info
        if "processing_time" in analysis_results:
            time_taken = analysis_results["processing_time"]
            content_parts.append(f"**Processing Time:** {time_taken:.2f}s")

        return "\n\n".join(content_parts) if content_parts else "Analysis completed successfully."


def main():
    """Main function for testing Discord publisher."""
    if len(sys.argv) < 2:
        print("Usage: post_to_discord.py <command> [args...]")
        print("Commands:")
        print("  test - Test Discord publishing")
        print("  publish <type> <title> <content> - Publish artifact")
        print("  summary <url> <results_json> - Publish analysis summary")
        sys.exit(1)

    command = sys.argv[1]
    publisher = DiscordPublisher()

    if command == "test":
        print("🧪 Testing Discord publisher...")

        # Test basic publishing
        success = publisher.publish_artifact(
            "info",
            "Test Message",
            "This is a test message from the Discord publisher.",
            "test_tenant",
            "test_workspace",
        )

        if success:
            print("✅ Discord publisher test completed successfully")
        else:
            print("❌ Discord publisher test failed")
            sys.exit(1)

    elif command == "publish":
        if len(sys.argv) < 5:
            print("Usage: post_to_discord.py publish <type> <title> <content>")
            sys.exit(1)

        artifact_type = sys.argv[2]
        title = sys.argv[3]
        content = sys.argv[4]

        success = publisher.publish_artifact(artifact_type, title, content)
        sys.exit(0 if success else 1)

    elif command == "summary":
        if len(sys.argv) < 4:
            print("Usage: post_to_discord.py summary <url> <results_json>")
            sys.exit(1)

        url = sys.argv[2]
        results_json = sys.argv[3]

        try:
            results = json.loads(results_json)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            sys.exit(1)

        success = publisher.publish_analysis_summary(url, results)
        sys.exit(0 if success else 1)

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
