#!/usr/bin/env python3
"""
Week 4 validation with TUNED thresholds.

Thresholds adjusted based on diagnostic analysis:
- QUALITY_MIN_OVERALL: 0.65 → 0.55
- min_exit_confidence: 0.80 → 0.70

Expected improvement: 45-60% combined (vs 1.2% baseline)
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline


async def run_tuned_validation(url: str):
    """Run validation with tuned thresholds."""
    results = {
        "timestamp": time.time(),
        "url": url,
        "tuning_applied": {
            "quality_min_overall": "0.55 (was 0.65)",
            "min_exit_confidence": "0.70 (was 0.80)",
        },
        "tests": {},
    }

    print(f"\n{'=' * 70}")
    print("Week 4 TUNED Threshold Validation")
    print(f"{'=' * 70}\n")
    print(f"URL: {url}")
    print("\nTuned Thresholds:")
    print("  • QUALITY_MIN_OVERALL: 0.55 (was 0.65)")
    print("  • min_exit_confidence: 0.70 (was 0.80)")
    print(f"\n{'=' * 70}\n")

    # Test 1: Baseline (no optimizations)
    print("1️⃣  Running baseline test (no optimizations)...")
    os.environ["ENABLE_QUALITY_FILTERING"] = "0"
    os.environ["ENABLE_CONTENT_ROUTING"] = "0"
    os.environ["ENABLE_EARLY_EXIT"] = "0"

    start = time.time()
    pipeline = ContentPipeline()
    result = await pipeline.process_video(url=url)
    baseline_time = time.time() - start

    results["tests"]["baseline"] = {"time": baseline_time}
    print(f"   ✅ Baseline: {baseline_time:.2f}s\n")

    # Test 2: Quality filtering (with tuned threshold)
    print("2️⃣  Running quality filtering test (threshold 0.55)...")
    os.environ["ENABLE_QUALITY_FILTERING"] = "1"
    os.environ["QUALITY_MIN_OVERALL"] = "0.55"  # TUNED
    os.environ["ENABLE_CONTENT_ROUTING"] = "0"
    os.environ["ENABLE_EARLY_EXIT"] = "0"

    start = time.time()
    pipeline = ContentPipeline()
    result = await pipeline.process_video(url=url)
    quality_time = time.time() - start

    improvement = ((baseline_time - quality_time) / baseline_time) * 100
    results["tests"]["quality_filtering"] = {
        "time": quality_time,
        "improvement_percent": improvement,
        "threshold": 0.55,
    }
    print(f"   ✅ Quality filtering: {quality_time:.2f}s ({improvement:+.1f}%)\n")

    # Test 3: Early exit (with tuned confidence)
    print("3️⃣  Running early exit test (confidence 0.70)...")
    os.environ["ENABLE_QUALITY_FILTERING"] = "0"
    os.environ["ENABLE_CONTENT_ROUTING"] = "0"
    os.environ["ENABLE_EARLY_EXIT"] = "1"

    start = time.time()
    pipeline = ContentPipeline()
    result = await pipeline.process_video(url=url)
    exit_time = time.time() - start

    improvement = ((baseline_time - exit_time) / baseline_time) * 100
    results["tests"]["early_exit"] = {
        "time": exit_time,
        "improvement_percent": improvement,
        "confidence_threshold": 0.70,
    }
    print(f"   ✅ Early exit: {exit_time:.2f}s ({improvement:+.1f}%)\n")

    # Test 4: Combined optimizations (all tuned)
    print("4️⃣  Running combined test (all optimizations tuned)...")
    os.environ["ENABLE_QUALITY_FILTERING"] = "1"
    os.environ["QUALITY_MIN_OVERALL"] = "0.55"  # TUNED
    os.environ["ENABLE_CONTENT_ROUTING"] = "1"
    os.environ["ENABLE_EARLY_EXIT"] = "1"

    start = time.time()
    pipeline = ContentPipeline()
    result = await pipeline.process_video(url=url)
    combined_time = time.time() - start

    improvement = ((baseline_time - combined_time) / baseline_time) * 100
    results["tests"]["combined"] = {
        "time": combined_time,
        "improvement_percent": improvement,
    }
    print(f"   ✅ Combined: {combined_time:.2f}s ({improvement:+.1f}%)\n")

    # Summary
    print(f"{'=' * 70}")
    print("TUNED VALIDATION RESULTS")
    print(f"{'=' * 70}\n")
    print(f"Baseline:           {baseline_time:.2f}s")
    print(
        f"Quality Filtering:  {quality_time:.2f}s ({results['tests']['quality_filtering']['improvement_percent']:+.1f}%)"
    )
    print(f"Early Exit:         {exit_time:.2f}s ({results['tests']['early_exit']['improvement_percent']:+.1f}%)")
    print(f"Combined:           {combined_time:.2f}s ({improvement:+.1f}%)")
    print(f"\n{'=' * 70}")

    combined_improvement = results["tests"]["combined"]["improvement_percent"]

    if combined_improvement >= 65:
        print("✅ SUCCESS: Combined improvement ≥65% - READY FOR PRODUCTION")
        results["recommendation"] = "deploy_to_production"
    elif combined_improvement >= 50:
        print("⚠️  MARGINAL: 50-65% improvement - Continue tuning recommended")
        results["recommendation"] = "continue_tuning"
    elif combined_improvement >= 30:
        print("⚠️  PARTIAL: 30-50% improvement - Expand test suite or adjust thresholds")
        results["recommendation"] = "expand_test_suite"
    else:
        print("❌ BELOW TARGET: <30% improvement - Investigate further")
        results["recommendation"] = "investigate"

    print(f"{'=' * 70}\n")

    # Save results
    output_file = Path("benchmarks") / f"week4_tuned_validation_{int(time.time())}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"📊 Results saved to: {output_file}\n")

    return results


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        url = "https://www.youtube.com/watch?v=xtFiJ8AVdW0"
        print(f"Using default URL: {url}")
    else:
        url = sys.argv[1]

    results = await run_tuned_validation(url)

    # Exit with appropriate code
    combined_improvement = results["tests"]["combined"]["improvement_percent"]
    sys.exit(0 if combined_improvement >= 50 else 1)


if __name__ == "__main__":
    asyncio.run(main())
