#!/usr/bin/env python3
"""Example usage of the Sponsor and Compliance Assistant.

This script demonstrates how to use the SponsorComplianceAssistant for analyzing
content compliance and generating sponsor-safe cut lists and scripts.

Usage:
    python examples/sponsor_compliance_assistant_example.py

Environment Variables:
    None required - uses rule-based analysis for compliance checking
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.sponsor_assistant.sponsor_compliance_service import (
    BrandGuidelines,
    get_sponsor_compliance_assistant,
)


def main() -> int:
    """Main example function."""
    print("🏢 Sponsor and Compliance Assistant Demo")
    print("=" * 60)

    # Get sponsor compliance assistant
    assistant = get_sponsor_compliance_assistant()

    # Example 1: Analyze content compliance
    print("🔍 Content Compliance Analysis...")

    content_segments = [
        {
            "start_time": 0.0,
            "end_time": 30.0,
            "text": "Welcome to our educational technology discussion. Today we'll explore the latest innovations in AI.",
            "speaker": "Host",
        },
        {
            "start_time": 30.0,
            "end_time": 60.0,
            "text": "This damn technology is frustrating! I hate when it doesn't work properly.",
            "speaker": "Guest",
        },
        {
            "start_time": 60.0,
            "end_time": 90.0,
            "text": "Let's move on to the positive aspects and best practices for implementation.",
            "speaker": "Host",
        },
    ]

    # Define brand guidelines for family-friendly content
    brand_guidelines = BrandGuidelines(
        brand_name="TechCorp",
        target_audience="family",
        allowed_topics=["education", "technology", "innovation"],
        prohibited_topics=["profanity", "frustration", "negative_emotions"],
        tone_requirements=["professional", "positive", "educational"],
        content_warnings=["mild_technical_discussion"],
        sponsorship_format="integrated",
    )

    compliance_result = assistant.analyze_compliance(
        content_segments,
        brand_guidelines=brand_guidelines,
        policy_pack="family_friendly",
    )

    if compliance_result.success:
        compliance_report = compliance_result.data["compliance_report"]

        print("✅ Compliance analysis completed!"        print(f"   Overall compliance score: {compliance_report.overall_compliance_score:.1%}")
        print(f"   Brand suitability score: {compliance_report.brand_suitability_score:.1%}")
        print(f"   Safe content percentage: {compliance_report.safe_content_percentage:.1%}")

        if compliance_report.policy_violations:
            print(f"   Policy violations: {len(compliance_report.policy_violations)}")
            for violation in compliance_report.policy_violations:
                print(f"     - {violation}")

        if compliance_report.recommendations:
            print(f"   Recommendations: {len(compliance_report.recommendations)}")
            for rec in compliance_report.recommendations[:2]:
                print(f"     - {rec}")
    else:
        print(f"❌ Compliance analysis failed: {compliance_result.error}")
        return 1

    print()

    # Example 2: Generate sponsor-safe cut list
    print("✂️  Generating Sponsor-Safe Cut List...")

    cut_list_result = assistant.generate_compliant_cut_list(
        content_segments,
        brand_guidelines,
        max_video_duration=120.0,  # 2-minute max for demo
    )

    if cut_list_result.success:
        cut_list = cut_list_result.data["cut_list"]

        print("✅ Cut list generated!"        print(f"   Total duration: {cut_list.total_duration:.1f}s")
        print(f"   Safe segments: {len(cut_list.safe_segments)}")
        print(f"   Unsafe segments: {len(cut_list.unsafe_segments)}")
        print(f"   Sponsor placements: {len(cut_list.sponsor_placements)}")

        # Show safe segments
        if cut_list.safe_segments:
            print("   Safe segments:")
            for i, segment in enumerate(cut_list.safe_segments[:3]):
                print(f"     {i+1}. [{segment.start_time:.1f}s - {segment.end_time:.1f}s] "
                      f"({segment.duration:.1f}s) - {segment.content_type}")

        # Show unsafe segments
        if cut_list.unsafe_segments:
            print("   Unsafe segments (to be removed):")
            for i, segment in enumerate(cut_list.unsafe_segments[:2]):
                print(f"     {i+1}. [{segment.start_time:.1f}s - {segment.end_time:.1f}s] "
                      f"- Risk factors: {', '.join(segment.risk_factors)}")
    else:
        print(f"❌ Cut list generation failed: {cut_list_result.error}")

    print()

    # Example 3: Generate sponsor script
    print("📝 Generating Sponsor Script...")

    sponsor_script_result = assistant.generate_sponsor_script(
        content_segments,
        brand_guidelines,
        sponsor_product="Premium AI Software",
        sponsor_message="It revolutionizes workflow efficiency for professionals",
    )

    if sponsor_script_result.success:
        sponsor_script = sponsor_script_result.data["sponsor_script"]

        print("✅ Sponsor script generated!"        print(f"   Total script duration: {sponsor_script.total_script_duration:.1f}s")
        print(f"   Script segments: {len(sponsor_script.script_segments)}")
        print(f"   Brand guidelines applied: {len(sponsor_script.brand_guidelines_applied)}")
        print(f"   Sponsor integration points: {len(sponsor_script.sponsor_integration_points)}")

        # Show brand guidelines
        print("   Brand guidelines applied:")
        for guideline in sponsor_script.brand_guidelines_applied:
            print(f"     - {guideline}")

        # Show script segments
        print("   Script segments:")
        for i, segment in enumerate(sponsor_script.script_segments[:3]):
            print(f"     {i+1}. {segment['segment_type']}: {segment['content'][:50]}{'...' if len(segment['content']) > 50 else ''}")
    else:
        print(f"❌ Sponsor script generation failed: {sponsor_script_result.error}")

    print()

    # Example 4: Different brand guidelines comparison
    print("🏢 Brand Guidelines Comparison...")

    # Family-friendly guidelines
    family_guidelines = BrandGuidelines(
        brand_name="FamilyCorp",
        target_audience="family",
        allowed_topics=["education", "entertainment"],
        prohibited_topics=["profanity", "violence", "adult_content"],
        tone_requirements=["positive", "educational"],
    )

    # Professional guidelines
    professional_guidelines = BrandGuidelines(
        brand_name="ProCorp",
        target_audience="professional",
        allowed_topics=["business", "technology", "productivity"],
        prohibited_topics=["controversial_politics", "profanity"],
        tone_requirements=["professional", "informative"],
    )

    # Analyze same content with different guidelines
    family_result = assistant.analyze_compliance(
        content_segments, family_guidelines, policy_pack="family_friendly"
    )

    professional_result = assistant.analyze_compliance(
        content_segments, professional_guidelines, policy_pack="professional"
    )

    if family_result.success and professional_result.success:
        family_report = family_result.data["compliance_report"]
        professional_report = professional_result.data["compliance_report"]

        print("✅ Brand comparison completed!"        print("   Family-friendly compliance:"        print(f"     Score: {family_report.overall_compliance_score:.1%}")
        print(f"     Violations: {len(family_report.policy_violations)}")

        print("   Professional compliance:"        print(f"     Score: {professional_report.overall_compliance_score:.1%}")
        print(f"     Violations: {len(professional_report.policy_violations)}")

        # Show the difference in compliance scores
        score_diff = abs(family_report.overall_compliance_score - professional_report.overall_compliance_score)
        stricter_brand = "Family" if family_report.overall_compliance_score < professional_report.overall_compliance_score else "Professional"
        print(f"   {stricter_brand} guidelines are stricter (difference: {score_diff:.1%})")

    print()

    # Example 5: Cache statistics
    print("💾 Cache Statistics:")
    cache_stats = assistant.get_cache_stats()

    if cache_stats.success:
        stats = cache_stats.data
        print(f"   Total cached: {stats['total_cached']}")
        print(f"   Cache utilization: {stats['utilization']:.1%}")
    else:
        print(f"❌ Failed to get cache stats: {cache_stats.error}")

    print()
    print("=" * 60)
    print("🎉 Sponsor and Compliance Assistant Demo Complete!")
    print()
    print("💡 Key Features Demonstrated:")
    print("   ✅ Content compliance analysis with policy packs")
    print("   ✅ Brand suitability assessment")
    print("   ✅ Sponsor-safe cut list generation")
    print("   ✅ Sponsor script generation with brand integration")
    print("   ✅ Multi-brand guidelines comparison")
    print("   ✅ Compliance scoring and recommendations")

    return 0


if __name__ == "__main__":
    sys.exit(main())

