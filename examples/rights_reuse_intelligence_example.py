#!/usr/bin/env python3
"""Example usage of the Rights and Reuse Intelligence service.

This script demonstrates how to use the RightsReuseIntelligenceService for analyzing
content rights, assessing fair use risks, and suggesting alternative content.

Usage:
    python examples/rights_reuse_intelligence_example.py

Environment Variables:
    None required - uses rule-based analysis for rights assessment
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.rights_management.rights_reuse_intelligence_service import (
    get_rights_reuse_intelligence_service,
)


def main() -> int:
    """Main example function."""
    print("⚖️ Rights and Reuse Intelligence Demo")
    print("=" * 50)

    # Get rights management service
    rights_service = get_rights_reuse_intelligence_service()

    # Example content segments with different rights scenarios
    content_segments = [
        {
            "start_time": 0.0,
            "end_time": 30.0,
            "description": "Educational content about technology with Creative Commons license",
            "source_url": "https://creativecommons.org/licenses/by/4.0/",
        },
        {
            "start_time": 30.0,
            "end_time": 60.0,
            "description": "Recent viral video with all rights reserved copyright notice",
            "source_url": "https://youtube.com/watch?v=viral_video",
        },
        {
            "start_time": 60.0,
            "end_time": 90.0,
            "description": "Fair use commentary on current events",
            "source_url": "https://news.example.com/analysis",
        },
    ]

    print(
        f"📝 Analyzing {len(content_segments)} content segments for rights compliance..."
    )

    # Analyze content rights
    result = rights_service.analyze_content_rights(
        content_segments=content_segments,
        content_type="video",
        intended_use="educational",
        target_audience_size="medium",
        model="balanced",
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Rights analysis failed: {result.error}")
        return 1

    data = result.data

    print("✅ Rights analysis completed!")
    print(f"   Total segments: {data['total_content_duration']:.0f}s duration")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show content fragments
    content_fragments = data.get("content_fragments", [])
    if content_fragments:
        print("📄 Content Fragments Analysis:")
        print("-" * 80)

        for i, fragment in enumerate(content_fragments[:3]):  # Show first 3 fragments
            fragment_id = fragment["fragment_id"]
            start_time = fragment["start_time"]
            end_time = fragment["end_time"]
            duration = fragment["duration"]
            license_type = fragment["license_info"]["license_type"]
            risk_score = fragment["risk_score"]
            rights_holder = fragment["license_info"]["rights_holder"]

            print(f"   {i + 1}. **{fragment_id}**")
            print(
                f"      Duration: {duration:.1f}s ({start_time:.1f}s - {end_time:.1f}s)"
            )
            print(f"      License: {license_type}")
            print(f"      Rights Holder: {rights_holder}")
            print(f"      Risk Score: {risk_score:.2f}")

            # Show license details
            license_info = fragment["license_info"]
            if license_info["usage_rights"]:
                print(f"      Usage Rights: {', '.join(license_info['usage_rights'])}")
            if license_info["restrictions"]:
                print(f"      Restrictions: {', '.join(license_info['restrictions'])}")

            # Show alternative suggestions
            alternatives = fragment.get("alternative_suggestions", [])
            if alternatives:
                print(f"      Alternatives: {len(alternatives)} suggestions")
                for alt in alternatives[:2]:
                    print(f"        - {alt}")

            print()

        if len(content_fragments) > 3:
            print(f"   ... and {len(content_fragments) - 3} more fragments")

    print("-" * 80)

    # Show reuse analysis
    reuse_analysis = data.get("reuse_analysis", {})
    if reuse_analysis:
        print("♻️  Reuse Analysis:")
        print(f"   Can Reuse: {reuse_analysis.get('can_reuse', False)}")
        print(f"   Risk Level: {reuse_analysis.get('risk_level', 'unknown')}")
        print(f"   Compliance Score: {reuse_analysis.get('compliance_score', 0):.2f}")
        print(f"   Estimated Cost: ${reuse_analysis.get('estimated_cost', 0):.0f}")

        required_actions = reuse_analysis.get("required_actions", [])
        if required_actions:
            print("   Required Actions:")
            for action in required_actions:
                print(f"     - {action}")

        alternative_content = reuse_analysis.get("alternative_content", [])
        if alternative_content:
            print("   Alternative Content:")
            for alt in alternative_content[:3]:
                print(f"     - {alt}")

    print("-" * 80)

    # Show risk assessment
    risk_assessment = data.get("risk_assessment", {})
    if risk_assessment:
        print("⚠️  Risk Assessment:")
        print(f"   Overall Risk: {risk_assessment.get('overall_risk', 0):.2f}")
        print(f"   Max Risk: {risk_assessment.get('max_risk', 0):.2f}")
        print(f"   Min Risk: {risk_assessment.get('min_risk', 0):.2f}")
        print(
            f"   High Risk Fragments: {risk_assessment.get('high_risk_fragments', 0)}"
        )
        print(
            f"   Medium Risk Fragments: {risk_assessment.get('medium_risk_fragments', 0)}"
        )
        print(f"   Low Risk Fragments: {risk_assessment.get('low_risk_fragments', 0)}")

    print("-" * 80)

    # Show recommendations
    recommendations = data.get("recommendations", [])
    if recommendations:
        print("💡 Recommendations:")
        for i, rec in enumerate(recommendations[:5]):
            print(f"   {i + 1}. {rec}")

    print("-" * 80)

    # Demonstrate fair use assessment
    print("⚖️  Fair Use Risk Assessment...")

    fair_use_result = rights_service.assess_fair_use_risk(
        content_description="Brief educational clip for commentary on current events",
        intended_use="educational",
        content_type="news",
        audience_size="medium",
    )

    if fair_use_result.success:
        fair_use_data = fair_use_result.data

        print("✅ Fair use assessment completed!")
        print(f"   Fair Use Score: {fair_use_data['fair_use_score']:.2f}")
        print(f"   Risk Level: {fair_use_data['risk_level']}")

        factors = fair_use_data.get("factors", {})
        if factors:
            print("   Fair Use Factors:")
            for factor, score in factors.items():
                print(f"     {factor}: {score:.2f}")

        recommendations = fair_use_data.get("recommendations", [])
        if recommendations:
            print("   Recommendations:")
            for rec in recommendations:
                print(f"     - {rec}")
    else:
        print(f"❌ Fair use assessment failed: {fair_use_result.error}")

    print("-" * 80)

    # Demonstrate alternative content suggestions
    print("🔄 Alternative Content Suggestions...")

    original_content = {
        "content_type": "video",
        "description": "Recent viral news footage with copyright restrictions",
    }

    alternatives = rights_service.suggest_alternative_content(
        original_content, risk_threshold=0.5
    )

    print("✅ Alternative content suggestions generated!")
    print(f"   Suggestions: {len(alternatives)}")

    for i, alt in enumerate(alternatives[:5]):
        risk_score = rights_service._assess_alternative_risk(alt)
        print(f"   {i + 1}. {alt} (Risk: {risk_score:.2f})")

    print("-" * 80)

    # Show cache statistics
    print("💾 Cache Statistics:")
    cache_stats = rights_service.get_cache_stats()

    if cache_stats.success:
        stats = cache_stats.data
        print(f"   Total cached: {stats['total_cached']}")
        print(f"   Cache utilization: {stats['utilization']:.1%}")
    else:
        print(f"❌ Failed to get cache stats: {cache_stats.error}")

    print()
    print("=" * 50)
    print("🎉 Rights and Reuse Intelligence Demo Complete!")
    print()
    print("💡 Key Features Demonstrated:")
    print("   ✅ Content rights analysis and license detection")
    print("   ✅ Risk assessment for different use cases")
    print("   ✅ Fair use evaluation with factor analysis")
    print("   ✅ Alternative content suggestions")
    print("   ✅ Compliance scoring and recommendations")

    return 0


if __name__ == "__main__":
    sys.exit(main())
