#!/usr/bin/env python3
"""Example usage of the Safety and Brand Suitability Analysis service.

This script demonstrates how to use the SafetyBrandSuitabilityService for analyzing
content safety, brand suitability, and policy compliance.

Usage:
    python examples/safety_brand_suitability_example.py "content to analyze"

Environment Variables:
    None required - uses rule-based analysis when transformers unavailable
"""

from __future__ import annotations

import sys
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis.safety.safety_brand_suitability_service import (
    get_safety_brand_suitability_service,
)


def main() -> int:
    """Main example function."""
    if len(sys.argv) < 2:
        print('Usage: python examples/safety_brand_suitability_example.py "content to analyze"')
        print("Example:")
        print(
            'python examples/safety_brand_suitability_example.py "This is professional content about technology and education. It contains no inappropriate material and is suitable for all audiences."'
        )
        return 1

    content = sys.argv[1]
    if len(content) < 20:
        print("Error: Content too short for meaningful analysis (minimum 20 characters)")
        return 1

    print(f"🛡️  Analyzing safety and brand suitability in: {len(content)} characters of content")

    # Get safety analysis service
    safety_service = get_safety_brand_suitability_service()

    # Analyze content
    result = safety_service.analyze_content(
        content=content,
        model="balanced",  # Use balanced for good quality/speed balance
        use_cache=True,
    )

    if not result.success:
        print(f"❌ Analysis failed: {result.error}")
        return 1

    data = result.data

    print("✅ Analysis completed!")
    print(f"   Analysis confidence: {data.get('analysis_confidence', 0):.2f}")
    print(f"   Cache hit: {data['cache_hit']}")
    print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
    print()

    # Show safety analysis
    safety = data.get("safety", {})
    if safety:
        print("🛡️  Safety Analysis:")
        print(f"   Safety Level: {safety.get('safety_level', 'unknown')}")
        print(f"   Confidence: {safety.get('confidence', 0):.2f}")
        print(f"   Compliance Score: {safety.get('compliance_score', 0):.2f}")

        risk_factors = safety.get("risk_factors", [])
        if risk_factors:
            print(f"   Risk Factors: {', '.join(risk_factors)}")
        else:
            print("   Risk Factors: None detected")
        print()

    # Show brand suitability analysis
    brand = data.get("brand_suitability", {})
    if brand:
        print("🏢 Brand Suitability Analysis:")
        print(f"   Suitability Score: {brand.get('suitability_score', 0):.2f}")
        print(f"   Brand Alignment: {brand.get('brand_alignment', 'unknown')}")
        print(f"   Target Audience: {brand.get('target_audience', 'unknown')}")
        print(f"   Sponsorship Ready: {brand.get('sponsorship_readiness', False)}")

        content_warnings = brand.get("content_warnings", [])
        if content_warnings:
            print(f"   Content Warnings: {len(content_warnings)}")
            for warning in content_warnings:
                print(f"     - {warning}")
        else:
            print("   Content Warnings: None required")
        print()

    # Show policy compliance analysis
    policy = data.get("policy_compliance", {})
    if policy:
        print("📋 Policy Compliance Analysis:")
        print(f"   Compliance Score: {policy.get('compliance_score', 0):.2f}")

        violated_policies = policy.get("violated_policies", [])
        if violated_policies:
            print(f"   Violated Policies: {len(violated_policies)}")
            for policy_name in violated_policies:
                print(f"     - {policy_name}")
        else:
            print("   Violated Policies: None")

        compliance_flags = policy.get("compliance_flags", [])
        if compliance_flags:
            print(f"   Compliance Flags: {len(compliance_flags)}")
            for flag in compliance_flags[:2]:  # Show first 2
                print(f"     - {flag}")

        recommendations = policy.get("recommendations", [])
        if recommendations:
            print(f"   Recommendations: {len(recommendations)}")
            for rec in recommendations[:2]:  # Show first 2
                print(f"     - {rec}")
        print()

    # Show content metadata
    print("📄 Content Metadata:")
    print(f"   Speaker: {data.get('speaker', 'Unknown')}")
    print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
    print()

    # Show original content
    print("📝 Original Content:")
    print("-" * 60)
    print(data.get("content_segment", content))
    print("-" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
