#!/usr/bin/env python3
"""Example usage of the Cross-Platform Deduplication service.

This script demonstrates how to use the CrossPlatformDeduplicationService for
identifying duplicate content across multiple platforms using perceptual and
semantic hashing.

Usage:
    python examples/cross_platform_deduplication_example.py

Environment Variables:
    None required - uses fallback methods when dependencies unavailable
"""

from __future__ import annotations

import sys
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis.deduplication.cross_platform_deduplication_service import (
    get_cross_platform_deduplication_service,
)


def main() -> int:
    """Main example function."""
    print("🔍 Cross-Platform Deduplication Analysis")
    print("=" * 60)

    # Get deduplication service
    deduplication_service = get_cross_platform_deduplication_service()

    # Example text items (simulating cross-platform content)
    text_items = [
        {
            "id": "yt_video_1",
            "platform": "youtube",
            "title": "Amazing Tech Review",
            "text": "This is a comprehensive review of the latest smartphone technology. The camera quality is outstanding and the battery life is impressive.",
        },
        {
            "id": "tw_tweet_1",
            "platform": "twitter",
            "text": "This is a comprehensive review of the latest smartphone technology. The camera quality is outstanding and the battery life is impressive.",  # Duplicate
        },
        {
            "id": "rd_post_1",
            "platform": "reddit",
            "title": "Smartphone Review Discussion",
            "text": "I recently got the new smartphone and I'm really impressed with the camera and battery life. Here's my detailed review.",
        },
        {
            "id": "yt_video_2",
            "platform": "youtube",
            "title": "Cooking Tutorial",
            "text": "Today we're making pasta from scratch. First, mix flour and eggs, then knead the dough for 10 minutes until smooth.",
        },
    ]

    print(f"📝 Analyzing {len(text_items)} content items from multiple platforms...")

    # Find duplicates
    result = deduplication_service.find_duplicates(
        text_items=text_items,
        similarity_threshold=0.8,
        model="balanced",  # Use balanced for good quality/speed balance
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Deduplication failed: {result.error}")
        return 1

    data = result.data

    print("✅ Deduplication analysis completed!")
    print(f"   Total items processed: {data['total_items_processed']}")
    print(f"   Duplicates found: {data['duplicates_found']}")
    print(f"   Unique items: {data['unique_items']}")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show duplicate clusters
    duplicate_clusters = data.get("duplicate_clusters", [])
    if duplicate_clusters:
        print(f"🔗 Duplicate Clusters ({len(duplicate_clusters)}):")
        print("-" * 80)

        for i, cluster in enumerate(duplicate_clusters[:5]):  # Show first 5 clusters
            cluster_id = cluster["cluster_id"]
            confidence = cluster["confidence"]
            platform_items = cluster.get("platform_items", {})

            print(f"   {i + 1}. Cluster '{cluster_id}' (confidence: {confidence:.2f})")
            print(f"      Platforms: {', '.join(platform_items.keys())}")

            for platform, items in platform_items.items():
                print(f"      {platform}: {len(items)} items")
                for item in items[:2]:  # Show first 2 items per platform
                    item_id = item.get("id", "unknown")
                    similarity = cluster.get("similarity_scores", {}).get(item_id, 0)
                    print(f"        - {item_id} (similarity: {similarity:.2f})")

            print()

        if len(duplicate_clusters) > 5:
            print(f"   ... and {len(duplicate_clusters) - 5} more clusters")

    print("-" * 80)

    # Show platform breakdown
    platform_counts = {}
    for item in text_items:
        platform = item.get("platform", "unknown")
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

    print("📊 Platform Distribution:")
    for platform, count in platform_counts.items():
        print(f"   {platform}: {count} items")
    print()

    # Show deduplication effectiveness
    if data["total_items_processed"] > 0:
        deduplication_rate = data["duplicates_found"] / data["total_items_processed"]
        uniqueness_rate = data["unique_items"] / data["total_items_processed"]

        print("📈 Deduplication Effectiveness:")
        print(f"   Duplication rate: {deduplication_rate:.1%}")
        print(f"   Uniqueness rate: {uniqueness_rate:.1%}")

        if deduplication_rate > 0.1:
            print("   💡 High duplication detected - consider content consolidation")
        elif uniqueness_rate > 0.9:
            print("   ✅ Low duplication - content appears mostly unique")
        else:
            print("   📋 Moderate duplication - some content overlap detected")

    print("-" * 80)

    # Demonstrate stream deduplication
    print("🌊 Real-time Stream Deduplication Demo:")
    print("   (Simulating live content processing)")

    # Simulate a stream of content items
    content_stream = [
        {
            "id": "stream_1",
            "content_type": "text",
            "text": "Breaking news: Major tech announcement",
        },
        {
            "id": "stream_2",
            "content_type": "text",
            "text": "Breaking news: Major tech announcement",
        },  # Duplicate
        {
            "id": "stream_3",
            "content_type": "text",
            "text": "Weather update: Sunny day ahead",
        },
        {
            "id": "stream_4",
            "content_type": "text",
            "text": "Breaking news: Major tech announcement",
        },  # Another duplicate
    ]

    stream_result = deduplication_service.deduplicate_content_stream(
        content_stream, similarity_threshold=0.9, model="fast"
    )

    if stream_result.success:
        stream_data = stream_result.data
        print(f"   Stream items processed: {stream_data['total_items_processed']}")
        print(f"   Duplicates detected: {stream_data['duplicates_found']}")
        print(f"   Unique content: {stream_data['unique_items']}")

        # Show which items were marked as duplicates
        processed_items = stream_data["processed_items"]
        for item in processed_items:
            status = "🔄 DUPLICATE" if item.get("is_duplicate") else "✅ UNIQUE"
            item_id = item.get("id", "unknown")
            print(f"   {status}: {item_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
