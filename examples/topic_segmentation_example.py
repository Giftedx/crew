#!/usr/bin/env python3
"""Example usage of the Topic Segmentation service.

This script demonstrates how to use the TopicSegmentationService for analyzing
topics in transcribed content, which is essential for creator intelligence analysis.

Usage:
    python examples/topic_segmentation_example.py "sample transcript text"

Environment Variables:
    None required - uses fallback methods when dependencies unavailable
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis.topic.topic_segmentation_service import get_topic_segmentation_service


def main() -> int:
    """Main example function."""
    if len(sys.argv) < 2:
        print('Usage: python examples/topic_segmentation_example.py "transcript text"')
        print(
            'Example: python examples/topic_segmentation_example.py "This is a long transcript about AI and technology topics that should be segmented into different themes and subjects for analysis."'
        )
        return 1

    text = sys.argv[1]
    if len(text) < 100:
        print(
            "Error: Text too short for meaningful topic analysis (minimum 100 characters)"
        )
        return 1

    print(f"🧠 Analyzing topics in: {len(text)} characters of text")

    # Get topic segmentation service
    topic_service = get_topic_segmentation_service()

    # Segment text into topics
    result = topic_service.segment_text(
        text=text,
        model="balanced",  # Use balanced for good quality/speed balance
        min_topic_size=3,
        max_topics=20,
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Topic segmentation failed: {result.error}")
        return 1

    data = result.data

    print("✅ Topic segmentation completed!")
    print(f"   Model: {data['model']}")
    print(f"   Overall coherence: {data.get('overall_coherence', 0):.2f}")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show topic model information
    topic_model = data.get("topic_model")
    if topic_model:
        print("📊 Topic Model:")
        print(f"   Topics found: {topic_model.get('num_topics', 0)}")
        print(f"   Model coherence: {topic_model.get('coherence_score', 0):.2f}")
        print(f"   Model type: {topic_model.get('model_type', 'unknown')}")
        print()

    # Show topic distribution
    topic_distribution = data.get("topic_distribution", {})
    if topic_distribution:
        print("📈 Topic Distribution:")
        sorted_topics = sorted(
            topic_distribution.items(), key=lambda x: x[1], reverse=True
        )
        for topic_id, frequency in sorted_topics[:5]:  # Show top 5
            print(f"   {topic_id}: {frequency:.1%}")
        if len(topic_distribution) > 5:
            print(f"   ... and {len(topic_distribution) - 5} more topics")
        print()

    # Show segments with topics
    segments = data.get("segments", [])
    if segments:
        print(f"📝 Topic Segments ({len(segments)}):")
        print("-" * 100)

        for i, segment in enumerate(segments[:8]):  # Show first 8 segments
            start_time = segment["start_time"]
            end_time = segment["end_time"]
            duration = end_time - start_time

            # Get dominant topic name
            dominant_topic = segment.get("dominant_topic", "unknown")
            topic_names = segment.get("topic_names", [])

            print(
                f"   {i + 1:2d}. [{start_time:6.1f}s - {end_time:6.1f}s] "
                f"({duration:5.1f}s) Topic: {dominant_topic}"
            )

            # Show topic names if available
            if topic_names:
                print(f"         Topics: {', '.join(topic_names[:3])}")  # Show first 3

            # Show segment text preview
            text_preview = segment["text"][:80]
            if len(segment["text"]) > 80:
                text_preview += "..."
            print(f'         "{text_preview}"')

        if len(segments) > 8:
            print(f"   ... and {len(segments) - 8} more segments")

    print("-" * 100)

    # Show coherence analysis
    if segments:
        coherences = [s.get("coherence_score", 0) for s in segments]
        avg_coherence = sum(coherences) / len(coherences) if coherences else 0

        print("\n📊 Coherence Analysis:")
        print(f"   Average segment coherence: {avg_coherence:.2f}")
        print(
            f"   High coherence segments: {sum(1 for c in coherences if c > 0.7)}/{len(coherences)}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
