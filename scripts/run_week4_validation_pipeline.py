#!/usr/bin/env python3
"""
Week 4 Production Validation Script - ContentPipeline Version

Uses ContentPipeline instead of AutonomousOrchestrator to validate Phase 2 optimizations.
This bypasses the CrewAI task architecture issue while still testing the core optimizations:
- Quality filtering (ENABLE_QUALITY_FILTERING)
- Content routing (ENABLE_CONTENT_ROUTING)
- Early exit conditions (ENABLE_EARLY_EXIT)

This is the RECOMMENDED approach to unblock Week 4 validation.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline


class Week4PipelineValidator:
    """Week 4 validation test runner using ContentPipeline."""

    def __init__(self, url: str, iterations: int = 3):
        self.url = url
        self.iterations = iterations
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "iterations": iterations,
            "validation_method": "ContentPipeline",
            "tests": {},
        }

    async def run_baseline_test(self) -> dict:
        """Run baseline test (no optimizations)."""
        print("🎯 Running baseline test (no optimizations)...")

        # Disable all optimizations
        os.environ["ENABLE_QUALITY_FILTERING"] = "0"
        os.environ["ENABLE_CONTENT_ROUTING"] = "0"
        os.environ["ENABLE_EARLY_EXIT"] = "0"

        times = []
        for i in range(self.iterations):
            print(f"  Iteration {i + 1}/{self.iterations}...")
            pipeline = ContentPipeline()
            start = time.time()
            try:
                result = await pipeline.process_video(url=self.url)
                duration = time.time() - start
                times.append(duration)
                success = result.get("success", True) if isinstance(result, dict) else True
                print(f"    ✅ {duration:.2f}s (success: {success})")
            except Exception as e:
                print(f"    ❌ Error: {e}")
                times.append(0)

        avg_time = sum(times) / len(times) if times else 0
        print(f"  📊 Baseline average: {avg_time:.2f}s ({avg_time / 60:.2f} min)\n")

        return {"times": times, "average": avg_time, "iterations": self.iterations}

    async def run_quality_filtering_test(self) -> dict:
        """Run quality filtering test."""
        print("📊 Testing quality filtering...")

        os.environ["ENABLE_QUALITY_FILTERING"] = "1"
        os.environ["ENABLE_CONTENT_ROUTING"] = "0"
        os.environ["ENABLE_EARLY_EXIT"] = "0"

        times = []
        bypass_count = 0

        for i in range(self.iterations):
            print(f"  Iteration {i + 1}/{self.iterations}...")
            pipeline = ContentPipeline()
            start = time.time()
            try:
                result = await pipeline.process_video(url=self.url)
                duration = time.time() - start
                times.append(duration)

                # Check if quality filtering bypassed
                if isinstance(result, dict) and result.get("bypassed_by_quality_filter"):
                    bypass_count += 1
                    print(f"    ⏭️  {duration:.2f}s (bypassed by quality filter)")
                else:
                    print(f"    ✅ {duration:.2f}s (passed quality filter)")
            except Exception as e:
                print(f"    ❌ Error: {e}")
                times.append(0)

        avg_time = sum(times) / len(times) if times else 0
        bypass_rate = bypass_count / self.iterations if self.iterations > 0 else 0
        print(f"  📊 Quality filtering average: {avg_time:.2f}s ({avg_time / 60:.2f} min)")
        print(f"  ⏭️  Bypass rate: {bypass_rate * 100:.1f}%\n")

        return {
            "times": times,
            "average": avg_time,
            "iterations": self.iterations,
            "bypass_count": bypass_count,
            "bypass_rate": bypass_rate,
        }

    async def run_content_routing_test(self) -> dict:
        """Run content routing test."""
        print("🔀 Testing content routing...")

        os.environ["ENABLE_QUALITY_FILTERING"] = "0"
        os.environ["ENABLE_CONTENT_ROUTING"] = "1"
        os.environ["ENABLE_EARLY_EXIT"] = "0"

        times = []
        routes_used = []

        for i in range(self.iterations):
            print(f"  Iteration {i + 1}/{self.iterations}...")
            pipeline = ContentPipeline()
            start = time.time()
            try:
                result = await pipeline.process_video(url=self.url)
                duration = time.time() - start
                times.append(duration)

                # Track routing decision
                route = "unknown"
                if isinstance(result, dict):
                    route = result.get("content_route", "standard")
                routes_used.append(route)

                print(f"    ✅ {duration:.2f}s (route: {route})")
            except Exception as e:
                print(f"    ❌ Error: {e}")
                times.append(0)
                routes_used.append("error")

        avg_time = sum(times) / len(times) if times else 0
        print(f"  📊 Content routing average: {avg_time:.2f}s ({avg_time / 60:.2f} min)")
        print(f"  🔀 Routes used: {dict((r, routes_used.count(r)) for r in set(routes_used))}\n")

        return {
            "times": times,
            "average": avg_time,
            "iterations": self.iterations,
            "routes_used": routes_used,
        }

    async def run_early_exit_test(self) -> dict:
        """Run early exit test."""
        print("🚪 Testing early exit conditions...")

        os.environ["ENABLE_QUALITY_FILTERING"] = "0"
        os.environ["ENABLE_CONTENT_ROUTING"] = "0"
        os.environ["ENABLE_EARLY_EXIT"] = "1"

        times = []
        exit_count = 0

        for i in range(self.iterations):
            print(f"  Iteration {i + 1}/{self.iterations}...")
            pipeline = ContentPipeline()
            start = time.time()
            try:
                result = await pipeline.process_video(url=self.url)
                duration = time.time() - start
                times.append(duration)

                # Check if early exit triggered
                if isinstance(result, dict) and result.get("early_exit_triggered"):
                    exit_count += 1
                    confidence = result.get("early_exit_confidence", 0)
                    print(f"    🚪 {duration:.2f}s (early exit at confidence {confidence:.2f})")
                else:
                    print(f"    ✅ {duration:.2f}s (completed full analysis)")
            except Exception as e:
                print(f"    ❌ Error: {e}")
                times.append(0)

        avg_time = sum(times) / len(times) if times else 0
        exit_rate = exit_count / self.iterations if self.iterations > 0 else 0
        print(f"  📊 Early exit average: {avg_time:.2f}s ({avg_time / 60:.2f} min)")
        print(f"  🚪 Exit rate: {exit_rate * 100:.1f}%\n")

        return {
            "times": times,
            "average": avg_time,
            "iterations": self.iterations,
            "exit_count": exit_count,
            "exit_rate": exit_rate,
        }

    async def run_combined_test(self) -> dict:
        """Run combined test (all optimizations)."""
        print("🎯 Testing combined optimizations...")

        os.environ["ENABLE_QUALITY_FILTERING"] = "1"
        os.environ["ENABLE_CONTENT_ROUTING"] = "1"
        os.environ["ENABLE_EARLY_EXIT"] = "1"

        times = []
        bypass_count = 0
        exit_count = 0
        routes_used = []

        for i in range(self.iterations):
            print(f"  Iteration {i + 1}/{self.iterations}...")
            pipeline = ContentPipeline()
            start = time.time()
            try:
                result = await pipeline.process_video(url=self.url)
                duration = time.time() - start
                times.append(duration)

                # Track all optimization effects
                optimizations = []
                if isinstance(result, dict):
                    if result.get("bypassed_by_quality_filter"):
                        bypass_count += 1
                        optimizations.append("bypassed")
                    if result.get("early_exit_triggered"):
                        exit_count += 1
                        optimizations.append(f"early_exit@{result.get('early_exit_confidence', 0):.2f}")
                    route = result.get("content_route", "standard")
                    routes_used.append(route)
                    optimizations.append(f"route:{route}")

                opt_str = ", ".join(optimizations) if optimizations else "none"
                print(f"    ✅ {duration:.2f}s ({opt_str})")
            except Exception as e:
                print(f"    ❌ Error: {e}")
                times.append(0)

        avg_time = sum(times) / len(times) if times else 0
        bypass_rate = bypass_count / self.iterations if self.iterations > 0 else 0
        exit_rate = exit_count / self.iterations if self.iterations > 0 else 0

        print(f"  📊 Combined average: {avg_time:.2f}s ({avg_time / 60:.2f} min)")
        print(f"  ⏭️  Bypass rate: {bypass_rate * 100:.1f}%")
        print(f"  🚪 Exit rate: {exit_rate * 100:.1f}%")
        print(f"  🔀 Routes: {dict((r, routes_used.count(r)) for r in set(routes_used))}\n")

        return {
            "times": times,
            "average": avg_time,
            "iterations": self.iterations,
            "bypass_count": bypass_count,
            "bypass_rate": bypass_rate,
            "exit_count": exit_count,
            "exit_rate": exit_rate,
            "routes_used": routes_used,
        }

    async def run_all_tests(self):
        """Run all validation tests."""
        print(f"{'=' * 70}")
        print("Week 4 Validation Suite - ContentPipeline Method")
        print(f"URL: {self.url}")
        print(f"Iterations: {self.iterations}")
        print(f"{'=' * 70}\n")

        # Run all tests
        self.results["tests"]["baseline"] = await self.run_baseline_test()
        self.results["tests"]["quality_filtering"] = await self.run_quality_filtering_test()
        self.results["tests"]["content_routing"] = await self.run_content_routing_test()
        self.results["tests"]["early_exit"] = await self.run_early_exit_test()
        self.results["tests"]["combined"] = await self.run_combined_test()

        # Calculate improvements
        baseline_avg = self.results["tests"]["baseline"]["average"]
        if baseline_avg > 0:
            for test_name, test_data in self.results["tests"].items():
                if test_name != "baseline":
                    test_avg = test_data["average"]
                    improvement = ((baseline_avg - test_avg) / baseline_avg) * 100
                    self.results["tests"][test_name]["improvement_percent"] = improvement

        # Calculate combined improvement
        combined_avg = self.results["tests"]["combined"]["average"]
        if baseline_avg > 0:
            combined_improvement = ((baseline_avg - combined_avg) / baseline_avg) * 100
            self.results["combined_improvement"] = combined_improvement
        else:
            self.results["combined_improvement"] = 0

        # Summary
        print(f"\n{'=' * 70}")
        print("Summary of Results")
        print(f"{'=' * 70}")
        print(f"Baseline:          {baseline_avg:.2f}s")
        print(
            f"Quality Filtering: {self.results['tests']['quality_filtering']['average']:.2f}s "
            f"({self.results['tests']['quality_filtering'].get('improvement_percent', 0):.1f}% improvement)"
        )
        print(
            f"Content Routing:   {self.results['tests']['content_routing']['average']:.2f}s "
            f"({self.results['tests']['content_routing'].get('improvement_percent', 0):.1f}% improvement)"
        )
        print(
            f"Early Exit:        {self.results['tests']['early_exit']['average']:.2f}s "
            f"({self.results['tests']['early_exit'].get('improvement_percent', 0):.1f}% improvement)"
        )
        print(f"Combined:          {combined_avg:.2f}s ({self.results['combined_improvement']:.1f}% improvement)")
        print(f"{'=' * 70}\n")

        # Decision recommendation
        combined_improvement = self.results["combined_improvement"]
        if combined_improvement >= 65:
            print("✅ RECOMMENDATION: DEPLOY TO PRODUCTION")
            print(f"   Combined improvement ({combined_improvement:.1f}%) meets 65% target")
        elif combined_improvement >= 50:
            print("⚙️  RECOMMENDATION: TUNE THRESHOLDS")
            print(f"   Combined improvement ({combined_improvement:.1f}%) below target, tune and retest")
        else:
            print("🔍 RECOMMENDATION: INVESTIGATE")
            print(f"   Combined improvement ({combined_improvement:.1f}%) significantly below target")

        # Save results
        output_file = f"benchmarks/week4_validation_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}\n")

        return self.results


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Week 4 validation using ContentPipeline")
    parser.add_argument(
        "url",
        nargs="?",
        default="https://www.youtube.com/watch?v=xtFiJ8AVdW0",
        help="URL to test (default: YouTube test video)",
    )
    parser.add_argument("-i", "--iterations", type=int, default=3, help="Number of iterations per test (default: 3)")
    args = parser.parse_args()

    validator = Week4PipelineValidator(url=args.url, iterations=args.iterations)
    await validator.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
