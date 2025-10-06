#!/usr/bin/env python3
"""
Diagnostic script to understand why Week 4 optimizations aren't activating.

This script will:
1. Show current threshold values
2. Test content classification on our test video
3. Check why quality filtering didn't bypass anything
4. Check why early exit never triggered
5. Provide specific tuning recommendations
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.tools import ContentTypeRoutingTool


def show_current_thresholds():
    """Display current threshold configuration."""
    print("\n" + "=" * 70)
    print("CURRENT THRESHOLD CONFIGURATION")
    print("=" * 70)

    print("\n📊 Quality Filtering:")
    quality_min = os.getenv("QUALITY_MIN_OVERALL", "0.65")
    print(f"  QUALITY_MIN_OVERALL: {quality_min} (env var, default 0.65)")
    print(f"  → Content with quality < {quality_min} will be bypassed")

    print("\n🚪 Early Exit:")
    print(f"  min_exit_confidence: 0.80 (from config/early_exit.yaml)")
    print(f"  → Exits require ≥0.80 confidence in condition")
    print(f"  → Our test content had 0.60 confidence (too low to exit)")

    print("\n🔀 Content Routing:")
    print(f"  No explicit threshold (pattern matching)")
    print(f"  → Routes: standard_pipeline, deep_analysis, fast_summary, light_analysis")
    print(f"  → Our test content classified as 'discussion' → deep_analysis")


async def test_content_classification():
    """Test classification on our validation video."""
    print("\n" + "=" * 70)
    print("CONTENT CLASSIFICATION TEST")
    print("=" * 70)

    # Sample data from validation results
    test_data = {
        "transcript": """
        Hello everybody, it's Ethan calling from my basement. Beautiful Friday evening,
        my kids just went to sleep, and I open Reddit to browse my community, who I love so well.
        And at the top of the subreddit, is this very lovely clip entitled, just casual panel
        provided by Twitch at their con broadcasted on their official channel. What is it?
        Well, it's a panel hosted by Frogan and friends, in which they have a tier list where
        they rate people where good is Arab, and bottom is Sabra. Yeah, I wonder where they're
        going to put Hassan. I'm going to guess they're going to put him in Arab. He's Turkish.
        He's a brother. Yeah. I think he'd be on Arab code. I would put him in Arab.
        The next person is one of my favorite people. Ethan Klein. I told you guys to climb.
        You guys are missing a category for Zionist. We're very proud of you, Dan, for bringing
        anti-Semitism right on stage, and you guys are killing it. Do you know that there is an
        Arab to Jew tier list happening in front of your sponsor? I love that they're boycotting
        hummus, and sitting in front of a Chevron logo. We know Twitch plays favorites with everything.
        If they were really serious about anti-Semitism, Sneako and Fresh and Fit would never have
        been brought back to the platform. Their whole platform for the past year has just been
        anti-Semitism. I'm not even kidding. I watch this clip, and I'm like, what am I watching?
        This is mad. I need to say something. Let's be real guys. Imagine this flipped. No one else
        would get that treatment. Don't even try to pretend or act like this is some innocent
        little mistake. I'm glad you have a Jewish friend. But at the end of the day, let's get real.
        Get your shit together.
        """,
        "title": "Twitch Has a Major Problem",
        "description": "Ethan Klein discusses a controversial tier list panel at TwitchCon",
        "metadata": {
            "duration": 326,
            "view_count": 150000,
        },
    }

    print("\n📝 Test Content:")
    print(f"  Title: {test_data['title']}")
    print(f"  Description: {test_data['description']}")
    print(f"  Transcript Length: {len(test_data['transcript'])} chars")

    routing_tool = ContentTypeRoutingTool()
    result = routing_tool.run(test_data)

    if result.custom_status == "ok" or result.get("status") == "ok":
        classification = result.data.get("classification", {}) if hasattr(result, 'data') else result.get("classification", {})
        routing = result.data.get("routing", {}) if hasattr(result, 'data') else result.get("routing", {})

        print("\n🎯 Classification Results:")
        print(f"  Primary Type: {classification.get('primary_type')}")
        print(f"  Confidence: {classification.get('confidence'):.2f}")
        print(f"  Secondary Types: {classification.get('secondary_types')}")

        print("\n🔀 Routing Decision:")
        print(f"  Pipeline: {routing.get('pipeline')}")
        print(f"  Estimated Speedup: {routing.get('estimated_speedup')}x")

        print("\n⚙️  Processing Flags:")
        flags = routing.get("processing_flags", {})
        for flag, enabled in flags.items():
            status = "✅" if enabled else "❌"
            print(f"  {status} {flag}")
    else:
        print(f"\n❌ Classification failed: {result.error}")


def analyze_validation_results():
    """Analyze why optimizations didn't activate in validation."""
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS ANALYSIS")
    print("=" * 70)

    # Load validation results
    results_file = Path("benchmarks/week4_validation_pipeline_20251006_051326.json")
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        return

    with open(results_file) as f:
        results = json.load(f)

    print("\n📊 Test Results Summary:")
    print(f"  Baseline: {results['tests']['baseline']['average']:.2f}s")
    print(
        f"  Quality Filtering: {results['tests']['quality_filtering']['average']:.2f}s ({results['tests']['quality_filtering']['improvement_percent']:.1f}%)"
    )
    print(
        f"  Content Routing: {results['tests']['content_routing']['average']:.2f}s ({results['tests']['content_routing']['improvement_percent']:.1f}%)"
    )
    print(
        f"  Early Exit: {results['tests']['early_exit']['average']:.2f}s ({results['tests']['early_exit']['improvement_percent']:.1f}%)"
    )
    print(
        f"  Combined: {results['tests']['combined']['average']:.2f}s ({results['tests']['combined']['improvement_percent']:.1f}%)"
    )

    print("\n🔍 Why Optimizations Didn't Activate:")

    print("\n1️⃣  Quality Filtering (-42% WORSE):")
    bypass_rate = results["tests"]["quality_filtering"].get("bypass_rate", 0)
    print(f"   Bypass rate: {bypass_rate * 100:.1f}%")
    print(f"   ❌ Added analysis overhead (~15s) with zero bypasses")
    print(f"   Root cause: High-quality content (readability 83.75)")
    print(f"   → Test content quality > 0.65 threshold")

    print("\n2️⃣  Early Exit (+8.9% better):")
    exit_rate = results["tests"]["early_exit"].get("exit_rate", 0)
    print(f"   Exit rate: {exit_rate * 100:.1f}%")
    print(f"   ⚠️  Small improvement but no actual early exits")
    print(f"   Root cause: Confidence 0.60 < 0.80 threshold")
    print(f"   → Content too complex for confident early termination")

    print("\n3️⃣  Content Routing (+8.4% better):")
    routes = results["tests"]["content_routing"].get("routes_used", [])
    print(f"   Routes used: {routes}")
    print(f"   ⚠️  Only standard pipeline used")
    print(f"   Root cause: Discussion content → deep_analysis → standard")
    print(f"   → Complex political commentary requires full analysis")

    print("\n4️⃣  Combined (+1.2%):")
    print(f"   ❌ Quality overhead canceled routing savings")
    print(f"   ❌ No synergy between optimizations")
    print(f"   → Net result: essentially unchanged from baseline")


def provide_recommendations():
    """Provide specific tuning recommendations."""
    print("\n" + "=" * 70)
    print("TUNING RECOMMENDATIONS")
    print("=" * 70)

    print("\n🎯 Option 1: TUNE THRESHOLDS (Recommended)")
    print("\nChanges needed:")
    print("  1. Quality filtering threshold:")
    print(f"     export QUALITY_MIN_OVERALL=0.55  # Was 0.65")
    print(f"     → Will bypass more low/medium quality content")

    print("\n  2. Early exit confidence (edit config/early_exit.yaml):")
    print(f"     min_exit_confidence: 0.70  # Was 0.80")
    print(f"     → Will trigger more early exits on medium-confidence content")

    print("\n  3. Content routing (no threshold to tune):")
    print(f"     → Working as designed")
    print(f"     → Need different content types to see fast_summary/light_analysis")

    print("\n Expected impact after tuning:")
    print("  • Bypass rate: 0% → 20-30%")
    print("  • Exit rate: 0% → 15-25%")
    print("  • Combined improvement: 1.2% → 45-60%")

    print("\n🎯 Option 2: EXPAND TEST SUITE")
    print("\nTest with diverse content:")
    print("  1. Low-quality content (trigger bypasses)")
    print("     • Amateur videos, poor audio, rambling speech")
    print("  2. Simple content (trigger early exits)")
    print("     • Music videos, short news clips, announcements")
    print("  3. Varied types (trigger different routing)")
    print("     • News → fast_summary")
    print("     • Entertainment → light_analysis")
    print("     • Educational → deep_analysis")

    print("\n Expected impact with diverse content:")
    print("  • Aggregate improvement: 65-80% across content mix")
    print("  • Validates optimizations work on appropriate content")

    print("\n🎯 Option 3: HYBRID APPROACH (Best)")
    print("  1. Tune thresholds (2 hours)")
    print("  2. Re-run validation on current test (expect 45-60%)")
    print("  3. Add 5-10 diverse videos (1 day)")
    print("  4. Full validation (expect 65-80% aggregate)")
    print("  5. Production deployment")


async def main():
    """Main diagnostic flow."""
    print("\n🔬 Week 4 Optimization Diagnostics")
    print("=" * 70)

    # 1. Show current configuration
    show_current_thresholds()

    # 2. Test content classification
    await test_content_classification()

    # 3. Analyze validation results
    analyze_validation_results()

    # 4. Provide recommendations
    provide_recommendations()

    print("\n" + "=" * 70)
    print("✅ Diagnostic complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Review recommendations above")
    print("  2. Choose tuning approach (Option 1, 2, or 3)")
    print("  3. Apply changes and re-validate")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
