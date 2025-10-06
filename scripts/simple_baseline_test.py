#!/usr/bin/env python3
"""
Simple baseline test for Week 4 validation.
Tests baseline pipeline performance without any optimizations.
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


async def run_baseline_test(url: str):
    """Run a single baseline test."""
    print(f"\n{'=' * 70}")
    print("Week 4 Baseline Test - ContentPipeline")
    print(f"URL: {url}")
    print(f"{'=' * 70}\n")

    # Ensure optimizations are OFF
    os.environ["ENABLE_QUALITY_FILTERING"] = "0"
    os.environ["ENABLE_CONTENT_ROUTING"] = "0"
    os.environ["ENABLE_EARLY_EXIT"] = "0"

    print("🎯 Running baseline test (no optimizations)...")
    start_time = time.time()

    try:
        # Create pipeline
        pipeline = ContentPipeline()

        # Run pipeline
        result = await pipeline.process_video(url=url)

        elapsed = time.time() - start_time

        # Check result
        if isinstance(result, dict) and result.get("status") == "ok":
            print(f"✅ Baseline test completed successfully in {elapsed:.2f}s")

            # Save result
            output = {
                "test": "baseline",
                "timestamp": time.time(),
                "elapsed_seconds": elapsed,
                "url": url,
                "result": result,
            }

            output_file = Path("benchmarks") / f"baseline_test_{int(time.time())}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w") as f:
                json.dump(output, f, indent=2)

            print(f"📊 Results saved to: {output_file}")
            print(f"\n{'=' * 70}")
            print(f"⏱️  Total time: {elapsed:.2f}s")
            print(f"{'=' * 70}\n")

            return True
        else:
            print(f"❌ Baseline test failed: {result}")
            return False

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Baseline test error after {elapsed:.2f}s: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python simple_baseline_test.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    success = await run_baseline_test(url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
