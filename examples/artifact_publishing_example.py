#!/usr/bin/env python3
"""Example usage of the Artifact Publishing service.

This script demonstrates how to use the ArtifactPublishingService for publishing
analysis reports and artifacts to Discord via webhooks.

Usage:
    python examples/artifact_publishing_example.py

Environment Variables:
    DISCORD_WEBHOOK_URL: Discord webhook URL for publishing
    DISCORD_BOT_TOKEN: Discord bot token (optional)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from publishing.artifact_publishing_service import get_artifact_publishing_service


def main() -> int:
    """Main example function."""
    print("📢 Artifact Publishing Demo")
    print("=" * 50)

    # Check for Discord webhook configuration
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️  Discord webhook not configured (set DISCORD_WEBHOOK_URL)")
        print("   Publishing will use fallback mode")
        print()

    # Get publishing service
    publishing_service = get_artifact_publishing_service()

    # Example 1: Publish highlight summary
    print("🎬 Publishing Highlight Summary...")

    highlights = [
        {
            "start_time": 0.0,
            "end_time": 30.0,
            "highlight_score": 0.9,
            "transcript_text": "This is an incredibly exciting moment in the discussion!",
        },
        {
            "start_time": 60.0,
            "end_time": 90.0,
            "highlight_score": 0.8,
            "transcript_text": "The guest makes an excellent point about technology.",
        },
        {
            "start_time": 120.0,
            "end_time": 150.0,
            "highlight_score": 0.85,
            "transcript_text": "Amazing conclusion with key takeaways.",
        },
    ]

    episode_info = {
        "title": "Tech Talk Episode #42",
        "platform": "youtube",
        "duration": 1800.0,
    }

    highlight_result = publishing_service.publish_highlight_summary(highlights, episode_info)

    if highlight_result.success:
        print("✅ Highlight summary published successfully!")
        print(f"   Artifact ID: {highlight_result.data['artifact_id']}")
        print(f"   Published at: {highlight_result.data['published_at']}")
        if highlight_result.data.get("platform_response"):
            print(f"   Platform response: {highlight_result.data['platform_response']['status_code']}")
    else:
        print(f"❌ Highlight summary publishing failed: {highlight_result.error}")

    print()

    # Example 2: Publish claims and quotes summary
    print("📋 Publishing Claims & Quotes Summary...")

    claims = [
        {
            "text": "According to research, AI will transform 80% of jobs by 2030",
            "speaker": "Host",
            "confidence": 0.85,
            "claim_type": "prediction",
        },
        {
            "text": "The data clearly shows improved performance metrics",
            "speaker": "Guest",
            "confidence": 0.9,
            "claim_type": "fact",
        },
    ]

    quotes = [
        {
            "text": "This technology is absolutely revolutionary",
            "speaker": "Guest",
            "confidence": 0.95,
            "quote_type": "insightful",
        },
        {
            "text": "I couldn't agree more with that perspective",
            "speaker": "Host",
            "confidence": 0.8,
            "quote_type": "agreement",
        },
    ]

    claim_quote_result = publishing_service.publish_claim_summary(claims, quotes, episode_info)

    if claim_quote_result.success:
        print("✅ Claims & quotes summary published successfully!")
        print(f"   Artifact ID: {claim_quote_result.data['artifact_id']}")
        print(f"   Published at: {claim_quote_result.data['published_at']}")
    else:
        print(f"❌ Claims & quotes summary publishing failed: {claim_quote_result.error}")

    print()

    # Example 3: Publish analysis report
    print("📊 Publishing Analysis Report...")

    analysis_data = {
        "episode_title": "Tech Talk Episode #42",
        "platform": "youtube",
        "duration": 1800.0,
        "sentiment": {
            "sentiment": "positive",
            "confidence": 0.85,
            "intensity": 0.7,
        },
        "emotion": {
            "primary_emotion": "joy",
            "confidence": 0.8,
        },
        "stance": {
            "stance": "agree",
            "confidence": 0.75,
        },
        "safety": {
            "safety_level": "safe",
            "compliance_score": 0.95,
        },
    }

    analysis_result = publishing_service.publish_report(analysis_data, report_type="analysis")

    if analysis_result.success:
        print("✅ Analysis report published successfully!")
        print(f"   Artifact ID: {analysis_result.data['artifact_id']}")
        print(f"   Published at: {analysis_result.data['published_at']}")
    else:
        print(f"❌ Analysis report publishing failed: {analysis_result.error}")

    print()

    # Example 4: Show cache statistics
    print("💾 Publishing Cache Statistics:")
    cache_stats = publishing_service.get_cache_stats()

    if cache_stats.success:
        stats = cache_stats.data
        print(f"   Total cached: {stats['total_cached']}")
        print(f"   Cache utilization: {stats['utilization']:.1%}")
        print(f"   Platforms: {', '.join(stats['platforms_cached'].keys())}")

        for platform, count in stats["platforms_cached"].items():
            print(f"     {platform}: {count} cached items")
    else:
        print(f"❌ Failed to get cache stats: {cache_stats.error}")

    print()

    # Example 5: Demonstrate artifact creation
    print("📦 Artifact Creation Demo:")

    from publishing.artifact_publishing_service import PublishingArtifact

    # Create custom artifact
    custom_artifact = PublishingArtifact(
        artifact_type="custom_report",
        title="Custom Analysis Report",
        content="This is a custom report with detailed analysis of the content.",
        metadata={
            "analysis_type": "comprehensive",
            "confidence": 0.9,
            "custom_field": "custom_value",
        },
        platform="discord",
        priority=8,  # High priority
    )

    print(f"   Created artifact: {custom_artifact.title}")
    print(f"   Type: {custom_artifact.artifact_type}")
    print(f"   Priority: {custom_artifact.priority}")
    print(f"   Content length: {len(custom_artifact.content)} characters")

    # Publish custom artifact
    custom_result = publishing_service.publish_artifact(custom_artifact)

    if custom_result.success:
        print("✅ Custom artifact published successfully!")
        print(f"   Artifact ID: {custom_result.data['artifact_id']}")
    else:
        print(f"❌ Custom artifact publishing failed: {custom_result.error}")

    print()
    print("=" * 50)
    print("🎉 Artifact Publishing Demo Complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())

