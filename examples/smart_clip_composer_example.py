#!/usr/bin/env python3
"""Example usage of the Smart Clip Composer.

This script demonstrates how to use the SmartClipComposerService for generating
AI-suggested video clips with titles, thumbnails, and A/B testing variants.

Usage:
    python examples/smart_clip_composer_example.py

Environment Variables:
    None required - uses rule-based analysis for clip generation
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.smart_clip_composer.smart_clip_composer_service import (
    get_smart_clip_composer_service,
)


def main() -> int:
    """Main example function."""
    print("🎬 Smart Clip Composer Demo")
    print("=" * 50)

    # Get smart clip composer
    composer = get_smart_clip_composer_service()

    # Example content analysis (simulating multimodal analysis results)
    content_analysis = {
        "duration": 3600.0,  # 1 hour
        "segments": [
            {
                "start_time": 0.0,
                "end_time": 30.0,
                "text": "Welcome to our technology discussion. Today we're exploring the latest innovations in artificial intelligence.",
            },
            {
                "start_time": 30.0,
                "end_time": 60.0,
                "text": "The most exciting development is the new natural language processing capabilities that can understand context much better.",
            },
            {
                "start_time": 60.0,
                "end_time": 90.0,
                "text": "This breakthrough will revolutionize how we interact with technology and make AI more accessible to everyone.",
            },
        ],
        "highlights": [
            {
                "start_time": 60.0,
                "end_time": 90.0,
                "highlight_score": 0.9,
                "transcript_text": "This breakthrough will revolutionize how we interact with technology and make AI more accessible to everyone.",
            },
            {
                "start_time": 30.0,
                "end_time": 60.0,
                "highlight_score": 0.8,
                "transcript_text": "The most exciting development is the new natural language processing capabilities that can understand context much better.",
            },
        ],
        "topic_segments": [
            {
                "start_time": 0.0,
                "end_time": 90.0,
                "transcript_text": "Welcome to our technology discussion. Today we're exploring the latest innovations in artificial intelligence. The most exciting development is the new natural language processing capabilities that can understand context much better. This breakthrough will revolutionize how we interact with technology and make AI more accessible to everyone.",
                "topics": ["artificial_intelligence", "technology", "innovation"],
                "coherence_score": 0.85,
            },
        ],
    }

    print(f"📝 Analyzing content: {content_analysis['duration']:.0f}s duration")
    print(f"   Segments: {len(content_analysis['segments'])}")
    print(f"   Highlights: {len(content_analysis['highlights'])}")
    print(f"   Topics: {len(content_analysis['topic_segments'])}")

    # Generate clip suggestions
    result = composer.generate_clip_suggestions(
        content_analysis=content_analysis,
        max_clips=5,
        min_clip_duration=15.0,
        max_clip_duration=60.0,
        target_platforms=["youtube_shorts", "tiktok", "instagram_reels"],
        model="balanced",
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Clip generation failed: {result.error}")
        return 1

    data = result.data

    print("✅ Clip suggestions generated!")
    print(f"   Total suggestions: {len(data['suggestions'])}")
    print(f"   Content duration: {data['total_content_duration']:.0f}s")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show clip suggestions
    suggestions = data.get("suggestions", [])
    if suggestions:
        print("🎬 Top Clip Suggestions:")
        print("-" * 100)

        for i, suggestion in enumerate(suggestions[:5]):  # Show top 5
            start_time = suggestion["start_time"]
            end_time = suggestion["end_time"]
            duration = suggestion["duration"]
            title = suggestion["title"]
            confidence = suggestion["confidence_score"]
            platforms = suggestion.get("suggested_platforms", [])

            print(f"   {i + 1}. **{title}**")
            print(
                f"      Duration: {duration:.1f}s ({start_time:.1f}s - {end_time:.1f}s)"
            )
            print(f"      Confidence: {confidence:.2f}")
            print(f"      Platforms: {', '.join(platforms)}")

            # Show signal scores
            signal_scores = suggestion.get("signal_scores", {})
            if signal_scores:
                print("      Signal Scores:")
                for signal, score in signal_scores.items():
                    print(f"        {signal}: {score:.2f}")

            # Show description preview
            description = suggestion.get("description", "")
            if description:
                desc_preview = (
                    description[:80] + "..." if len(description) > 80 else description
                )
                print(f'      Description: "{desc_preview}"')

            print()

        if len(suggestions) > 5:
            print(f"   ... and {len(suggestions) - 5} more suggestions")

    print("-" * 100)

    # Show A/B testing variants
    variants = data.get("variants", [])
    if variants and suggestions:
        print("🔬 A/B Testing Variants (for top suggestion):")

        # Use first suggestion for variant generation
        base_suggestion = suggestions[0]
        print(f"   Base: {base_suggestion['title']}")

        # Generate variants
        variant_objects = composer.generate_clip_variants(
            base_suggestion, num_variants=2
        )

        for i, variant in enumerate(variant_objects[:3]):
            expected_perf = variant.expected_performance
            print(f"   Variant {i + 1}: {variant.title}")
            print(f"     Description: {variant.description[:50]}...")
            print(f"     Expected Performance: {expected_perf:.1%}")
            print()

    print("-" * 100)

    # Show cache statistics
    print("💾 Cache Statistics:")
    cache_stats = composer.get_cache_stats()

    if cache_stats.success:
        stats = cache_stats.data
        print(f"   Total cached: {stats['total_cached']}")
        print(f"   Cache utilization: {stats['utilization']:.1%}")
    else:
        print(f"❌ Failed to get cache stats: {cache_stats.error}")

    print()

    # Demonstrate clip extraction (simulated)
    print("✂️  Clip Extraction Demo:")
    if suggestions:
        first_suggestion = suggestions[0]

        # Simulate clip extraction
        extraction_result = composer.extract_clip(
            video_path="/path/to/source/video.mp4",
            suggestion=first_suggestion,
            output_path="/path/to/output/clip.mp4",
            include_audio=True,
        )

        if extraction_result.success:
            extraction_data = extraction_result.data
            print("✅ Clip extraction simulated successfully!")
            print(f"   Source: {extraction_data['source_video']}")
            print(f"   Output: {extraction_data['output_clip']}")
            print(f"   Duration: {extraction_data['duration']:.1f}s")
        else:
            print(f"❌ Clip extraction failed: {extraction_result.error}")

    print()

    # Demonstrate thumbnail generation (simulated)
    print("🖼️  Thumbnail Generation Demo:")
    if suggestions:
        first_suggestion = suggestions[0]

        thumbnail_result = composer.generate_thumbnail(
            video_path="/path/to/source/video.mp4",
            timestamp=first_suggestion["start_time"] + 5,  # 5 seconds into clip
            thumbnail_text=first_suggestion["thumbnail_text"],
            output_path="/path/to/output/thumbnail.jpg",
        )

        if thumbnail_result.success:
            thumbnail_data = thumbnail_result.data
            print("✅ Thumbnail generation simulated successfully!")
            print(f"   Source: {thumbnail_data['source_video']}")
            print(f"   Output: {thumbnail_data['output_thumbnail']}")
            print(f"   Timestamp: {thumbnail_data['timestamp']:.1f}s")
            print(f"   Text: {thumbnail_data['thumbnail_text']}")
        else:
            print(f"❌ Thumbnail generation failed: {thumbnail_result.error}")

    print()
    print("=" * 50)
    print("🎉 Smart Clip Composer Demo Complete!")
    print()
    print("💡 Key Features Demonstrated:")
    print("   ✅ Multi-source clip suggestion generation")
    print("   ✅ Signal-based scoring and ranking")
    print("   ✅ Platform-specific optimization")
    print("   ✅ A/B testing variant generation")
    print("   ✅ Clip extraction and thumbnail generation")
    print("   ✅ Cache management for performance")

    return 0


if __name__ == "__main__":
    sys.exit(main())
