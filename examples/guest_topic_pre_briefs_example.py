#!/usr/bin/env python3
"""Example usage of the Guest/Topic Pre-Briefs service.

This script demonstrates how to use the GuestTopicPreBriefsService for generating
comprehensive pre-interview briefings with opponent-process analysis.

Usage:
    python examples/guest_topic_pre_briefs_example.py

Environment Variables:
    None required - uses rule-based analysis for brief generation
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.guest_preparation.guest_topic_pre_briefs_service import get_guest_topic_pre_briefs_service


def main() -> int:
    """Main example function."""
    print("🎙️ Guest/Topic Pre-Briefs Demo")
    print("=" * 50)

    # Get guest preparation service
    service = get_guest_topic_pre_briefs_service()

    # Example guest content (previous statements/interviews)
    guest_content = [
        {
            "text": "According to extensive research and data analysis, artificial intelligence has the potential to transform 80% of jobs by 2030, which is both exciting and concerning.",
            "timestamp": 1000000000,
        },
        {
            "text": "I believe the key to responsible AI development is implementing strict safety measures and ethical guidelines from the very beginning of the development process.",
            "timestamp": 1000000060,
        },
        {
            "text": "In my opinion, over-regulation could potentially stifle innovation, but we absolutely cannot compromise on safety when it comes to AI systems that could impact human lives.",
            "timestamp": 1000000120,
        },
        {
            "text": "The evidence clearly shows that without proper safeguards and testing protocols, AI systems can perpetuate biases and cause unintended harm to vulnerable populations.",
            "timestamp": 1000000180,
        },
    ]

    print(f"📝 Analyzing content from: {len(guest_content)} previous statements")

    # Generate interview brief
    result = service.generate_interview_brief(
        guest_content=guest_content,
        guest_name="Dr. AI Ethics Expert",
        interview_style="educational",
        model="balanced",
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Interview brief generation failed: {result.error}")
        return 1

    data = result.data

    print("✅ Interview brief generated!"    print(f"   Guest: {data['interview_brief']['guest_name']}")
    print(f"   Topic overview: {data['interview_brief']['topic_overview']}")
    print(f"   Confidence score: {data['interview_brief']['confidence_score']:.2f}")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show opponent-process summary
    opponent_summary = data["interview_brief"]["opponent_process_summary"]
    print("🎯 Opponent-Process Summary:")
    print(f"   Guest Position: {opponent_summary['guest_position_summary']}")

    key_arguments = opponent_summary.get("key_arguments", [])
    if key_arguments:
        print(f"   Key Arguments ({len(key_arguments)}):")
        for i, arg in enumerate(key_arguments[:3]):
            strength = arg.get("strength_category", "unknown")
            evidence = arg.get("evidence_quality", 0)
            print(f"     {i+1}. {arg['argument_text'][:60]}...")
            print(f"        Strength: {strength} | Evidence: {evidence:.2f}")

    print()

    # Show potential weaknesses
    weaknesses = opponent_summary.get("potential_weaknesses", [])
    if weaknesses:
        print("⚠️  Potential Weaknesses:")
        for weakness in weaknesses:
            print(f"   - {weakness}")
    print()

    # Show audience hooks
    audience_hooks = opponent_summary.get("audience_hooks", [])
    if audience_hooks:
        print("🎣 Audience Hooks:")
        for hook in audience_hooks:
            print(f"   - {hook}")
    print()

    # Show fact-check priorities
    fact_checks = opponent_summary.get("fact_check_priorities", [])
    if fact_checks:
        print("🔍 Fact-Check Priorities:")
        for fact_check in fact_checks:
            print(f"   - {fact_check}")
    print()

    # Show audience reaction prediction
    audience_prediction = data["interview_brief"]["audience_reaction_prediction"]
    print("👥 Audience Reaction Prediction:")
    print(f"   Primary Reaction: {audience_prediction['primary_reaction']}")
    print(f"   Confidence: {audience_prediction['confidence']:.2f}")
    print(f"   Engagement Potential: {audience_prediction['engagement_potential']:.2f}")
    print(f"   Controversy Risk: {audience_prediction['controversy_risk']:.2f}")

    likely_questions = audience_prediction.get("likely_questions", [])
    if likely_questions:
        print("   Likely Questions:")
        for question in likely_questions[:3]:
            print(f"     - {question}")

    print()

    # Show interview strategy
    strategy = data["interview_brief"]["interview_strategy"]
    print("📋 Interview Strategy:")
    for item in strategy:
        print(f"   - {item}")
    print()

    # Show key questions to ask
    key_questions = data["interview_brief"]["key_questions_to_ask"]
    print("❓ Key Questions to Ask:")
    for i, question in enumerate(key_questions[:5]):
        print(f"   {i+1}. {question}")
    print()

    # Show live fact-check prompts
    fact_check_prompts = data["interview_brief"]["live_fact_check_prompts"]
    print("🔍 Live Fact-Check Prompts:")
    for i, prompt in enumerate(fact_check_prompts[:3]):
        print(f"   {i+1}. {prompt}")
    print()

    # Demonstrate audience reaction prediction
    print("🎭 Audience Reaction Prediction Demo:")
    content_topics = ["artificial_intelligence", "job_displacement", "ethics"]

    prediction = service.predict_audience_reactions(content_topics)

    print("✅ Audience reaction prediction completed!"    print(f"   Primary Reaction: {prediction.primary_reaction}")
    print(f"   Engagement Potential: {prediction.engagement_potential:.1%}")
    print(f"   Controversy Risk: {prediction.controversy_risk:.1%}")

    print("   Likely Questions:")
    for question in prediction.likely_questions[:3]:
        print(f"     - {question}")

    print()

    # Show cache statistics
    print("💾 Cache Statistics:")
    cache_stats = service.get_cache_stats()

    if cache_stats.success:
        stats = cache_stats.data
        print(f"   Total cached: {stats['total_cached']}")
        print(f"   Cache utilization: {stats['utilization']:.1%}")
    else:
        print(f"❌ Failed to get cache stats: {cache_stats.error}")

    print()
    print("=" * 50)
    print("🎉 Guest/Topic Pre-Briefs Demo Complete!")
    print()
    print("💡 Key Features Demonstrated:")
    print("   ✅ Opponent-process analysis of guest arguments")
    print("   ✅ Argument strength and evidence quality assessment")
    print("   ✅ Audience reaction prediction")
    print("   ✅ Live fact-checking prompt generation")
    print("   ✅ Interview strategy recommendations")
    print("   ✅ Key question generation for interviews")

    return 0


if __name__ == "__main__":
    sys.exit(main())

