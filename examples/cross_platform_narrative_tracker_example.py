#!/usr/bin/env python3
"""Example usage of the Cross-Platform Narrative Tracker.

This script demonstrates how to use the CrossPlatformNarrativeTracker for tracking
how stories evolve across multiple platforms (YouTube, Twitter, Reddit).

Usage:
    python examples/cross_platform_narrative_tracker_example.py

Environment Variables:
    None required - uses rule-based analysis for narrative tracking
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.narrative_tracker.cross_platform_narrative_tracker import get_cross_platform_narrative_tracker


def main() -> int:
    """Main example function."""
    print("🔍 Cross-Platform Narrative Tracker Demo")
    print("=" * 60)

    # Get narrative tracker
    tracker = get_cross_platform_narrative_tracker()

    # Example content items simulating a breaking news story evolution
    content_items = [
        {
            "id": "yt_announcement",
            "platform": "youtube",
            "title": "BREAKING: Major Tech Company Announces Revolutionary AI",
            "text": "In a shocking announcement today, TechCorp revealed their revolutionary new AI technology that promises to change how we interact with computers forever.",
            "timestamp": 1000000000,
            "author": "TechCreator",
            "reach": 50000,
        },
        {
            "id": "tw_reaction_1",
            "platform": "twitter",
            "text": "Just watched the TechCorp AI announcement - this is incredible! The future is here. Can't wait to try it! #AI #TechRevolution",
            "timestamp": 1000000060,
            "author": "TechInfluencer",
            "reach": 15000,
        },
        {
            "id": "rd_discussion",
            "platform": "reddit",
            "title": "TechCorp AI Announcement - What are your thoughts?",
            "text": "The new AI from TechCorp looks amazing, but I'm concerned about privacy implications. Anyone else worried about data collection?",
            "timestamp": 1000000120,
            "author": "PrivacyAdvocate",
            "reach": 8000,
        },
        {
            "id": "tw_reaction_2",
            "platform": "twitter",
            "text": "The privacy concerns about TechCorp's new AI are valid. We need to be careful about how this technology is implemented. #Privacy #AI",
            "timestamp": 1000000180,
            "author": "PrivacyExpert",
            "reach": 12000,
        },
        {
            "id": "yt_followup",
            "platform": "youtube",
            "title": "TechCorp AI Update: Addressing Privacy Concerns",
            "text": "Following up on our AI announcement, we want to address the privacy concerns raised by the community. Here's how we're handling data protection.",
            "timestamp": 1000000240,
            "author": "TechCreator",
            "reach": 35000,
        },
    ]

    print(f"📝 Analyzing {len(content_items)} content items from multiple platforms...")

    # Track narrative evolution
    result = tracker.track_narrative_evolution(
        content_items,
        time_window_hours=1,
        similarity_threshold=0.6,
        max_threads=5,
        model="balanced",
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Narrative tracking failed: {result.error}")
        return 1

    data = result.data

    print("✅ Narrative tracking completed!"    print(f"   Total content analyzed: {data['total_content_analyzed']}")
    print(f"   Cross-platform connections: {data['cross_platform_connections']}")
    print(f"   Tracking confidence: {data.get('tracking_confidence', 0):.2f}")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show narrative threads
    narrative_threads = data.get("narrative_threads", [])
    if narrative_threads:
        print(f"🧵 Narrative Threads ({len(narrative_threads)}):")
        print("-" * 80)

        for i, thread in enumerate(narrative_threads[:3]):  # Show first 3 threads
            thread_id = thread['thread_id']
            title = thread.get('title', 'Untitled Thread')
            summary = thread.get('summary', 'No summary')
            platforms = thread.get('platforms_involved', [])
            reach = thread.get('total_reach', 0)
            evolution = thread.get('evolution_score', 0)

            print(f"   {i+1}. **{title}**")
            print(f"      Platforms: {', '.join(platforms)}")
            print(f"      Total Reach: {reach:,}",")
            print(f"      Evolution Score: {evolution:.2f}")
            print(f"      Summary: {summary}")
            print()

        if len(narrative_threads) > 3:
            print(f"   ... and {len(narrative_threads) - 3} more threads")

    print("-" * 80)

    # Demonstrate contradiction/clarification detection
    print("🔍 Contradiction and Clarification Detection...")

    contradiction_result = tracker.find_contradictions_and_clarifications(
        content_items, similarity_threshold=0.7, model="balanced"
    )

    if contradiction_result.success:
        contradiction_data = contradiction_result.data

        print("✅ Contradiction analysis completed!"        print(f"   Contradictions found: {contradiction_data.get('contradictions_found', 0)}")
        print(f"   Clarifications found: {contradiction_data.get('clarifications_found', 0)}")

        # Show contradictions
        contradictions = contradiction_data.get("contradictions", [])
        if contradictions:
            print("   Contradictions detected:")
            for i, contradiction in enumerate(contradictions[:2]):
                score = contradiction.get("contradiction_score", 0)
                print(f"     {i+1}. Score: {score:.2f}")
                print(f"        Original: {contradiction['item1'].get('title', 'Unknown')}")
                print(f"        Contradiction: {contradiction['item2'].get('title', 'Unknown')}")

        # Show clarifications
        clarifications = contradiction_data.get("clarifications", [])
        if clarifications:
            print("   Clarifications detected:")
            for i, clarification in enumerate(clarifications[:2]):
                score = clarification.get("clarification_score", 0)
                print(f"     {i+1}. Score: {score:.2f}")
                print(f"        Original: {clarification['original_item'].get('title', 'Unknown')}")
                print(f"        Clarification: {clarification['clarifying_item'].get('title', 'Unknown')}")
    else:
        print(f"❌ Contradiction analysis failed: {contradiction_result.error}")

    print()

    # Demonstrate narrative timeline generation
    if narrative_threads:
        print("📅 Narrative Timeline Generation...")

        # Use the first thread for timeline generation
        thread = narrative_threads[0]

        # Convert back to NarrativeThread object for timeline generation
        from features.narrative_tracker.cross_platform_narrative_tracker import NarrativeThread, NarrativeEvent

        # Create a simplified thread for demo
        events = []
        for event_data in thread.get("events", []):
            event = NarrativeEvent(
                event_id=event_data["event_id"],
                primary_content=event_data["primary_content"],
                related_content=event_data.get("related_content", []),
                narrative_type=event_data["narrative_type"],
                evolution_timeline=event_data.get("evolution_timeline", []),
                confidence=event_data["confidence"],
                created_at=event_data["created_at"],
                updated_at=event_data["updated_at"],
            )
            events.append(event)

        demo_thread = NarrativeThread(
            thread_id=thread["thread_id"],
            title=thread["title"],
            summary=thread["summary"],
            events=events,
            platforms_involved=thread["platforms_involved"],
            key_participants=thread["key_participants"],
            total_reach=thread["total_reach"],
            evolution_score=thread["evolution_score"],
            created_at=thread["created_at"],
            updated_at=thread["updated_at"],
        )

        timeline_result = tracker.generate_narrative_timeline(demo_thread)

        if timeline_result.success:
            timeline_data = timeline_result.data

            print("✅ Timeline generated!"            print(f"   Thread ID: {timeline_data['thread_id']}")
            print(f"   Total events: {timeline_data['total_events']}")
            print(f"   Platforms involved: {', '.join(timeline_data['platforms_involved'])}")

            # Show timeline events
            events = timeline_data.get("timeline_events", [])
            if events:
                print("   Timeline events:")
                for i, event in enumerate(events[:3]):
                    timestamp = event.get("timestamp", 0)
                    event_type = event.get("narrative_type", "unknown")
                    platform_count = len(event.get("platform_sequence", []))
                    print(f"     {i+1}. {event_type.title()} at {timestamp} ({platform_count} platforms)")
        else:
            print(f"❌ Timeline generation failed: {timeline_result.error}")

    print()

    # Show cache statistics
    print("💾 Cache Statistics:")
    cache_stats = tracker.get_cache_stats()

    if cache_stats.success:
        stats = cache_stats.data
        print(f"   Total cached: {stats['total_cached']}")
        print(f"   Cache utilization: {stats['utilization']:.1%}")
    else:
        print(f"❌ Failed to get cache stats: {cache_stats.error}")

    print()
    print("=" * 60)
    print("🎉 Cross-Platform Narrative Tracker Demo Complete!")
    print()
    print("💡 Key Features Demonstrated:")
    print("   ✅ Multi-platform content analysis")
    print("   ✅ Narrative evolution tracking")
    print("   ✅ Contradiction and clarification detection")
    print("   ✅ Timeline generation with confidence intervals")
    print("   ✅ Cross-platform connection identification")
    print("   ✅ Evolution scoring and participant tracking")

    return 0


if __name__ == "__main__":
    sys.exit(main())

