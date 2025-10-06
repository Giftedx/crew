#!/usr/bin/env python3
"""
Week 4 Production Validation Script

Runs direct validation of Phase 2 optimizations using the autonomous orchestrator.
Validates quality filtering, content routing, early exit, and combined optimizations.
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

from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
    AutonomousIntelligenceOrchestrator,
)


class Week4Validator:
    """Week 4 validation test runner."""

    def __init__(self, url: str, iterations: int = 3):
        self.url = url
        self.iterations = iterations
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "iterations": iterations,
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
            orchestrator = AutonomousIntelligenceOrchestrator()
            start = time.time()
            try:
                result = await orchestrator.execute_autonomous_intelligence_workflow(self.url, "experimental")
                duration = time.time() - start
                times.append(duration)
                success = result.success if hasattr(result, "success") else True
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
        for i in range(self.iterations):
            print(f"  Iteration {i + 1}/{self.iterations}...")
            orchestrator = AutonomousIntelligenceOrchestrator()
            start = time.time()
            try:
                result = await orchestrator.execute_autonomous_intelligence_workflow(self.url, "experimental")
                duration = time.time() - start
                times.append(duration)
                success = result.success if hasattr(result, "success") else True
                print(f"    ✅ {duration:.2f}s (success: {success})")
            except Exception as e:
                print(f"    ❌ Error: {e}")
                times.append(0)

        avg_time = sum(times) / len(times) if times else 0
        print(f"  📊 Quality filtering average: {avg_time:.2f}s ({avg_time / 60:.2f} min)\n")

        return {"times": times, "average": avg_time, "iterations": self.iterations}

    async def run_content_routing_test(self) -> dict:
        """Run content routing test."""
        print("📊 Testing content routing...")

        os.environ["ENABLE_QUALITY_FILTERING"] = "0"
        os.environ["ENABLE_CONTENT_ROUTING"] = "1"
        os.environ["ENABLE_EARLY_EXIT"] = "0"

        times = []
        for i in range(self.iterations):
            print(f"  Iteration {i + 1}/{self.iterations}...")
            orchestrator = AutonomousIntelligenceOrchestrator()
            start = time.time()
            try:
                result = await orchestrator.execute_autonomous_intelligence_workflow(self.url, "experimental")
                duration = time.time() - start
                times.append(duration)
                success = result.success if hasattr(result, "success") else True
                print(f"    ✅ {duration:.2f}s (success: {success})")
            except Exception as e:
                print(f"    ❌ Error: {e}")
                times.append(0)

        avg_time = sum(times) / len(times) if times else 0
        print(f"  📊 Content routing average: {avg_time:.2f}s ({avg_time / 60:.2f} min)\n")

        return {"times": times, "average": avg_time, "iterations": self.iterations}

    async def run_early_exit_test(self) -> dict:
        """Run early exit test."""
        print("📊 Testing early exit conditions...")

        os.environ["ENABLE_QUALITY_FILTERING"] = "0"
        os.environ["ENABLE_CONTENT_ROUTING"] = "0"
        os.environ["ENABLE_EARLY_EXIT"] = "1"

        times = []
        for i in range(self.iterations):
            print(f"  Iteration {i + 1}/{self.iterations}...")
            orchestrator = AutonomousIntelligenceOrchestrator()
            start = time.time()
            try:
                result = await orchestrator.execute_autonomous_intelligence_workflow(self.url, "experimental")
                duration = time.time() - start
                times.append(duration)
                success = result.success if hasattr(result, "success") else True
                print(f"    ✅ {duration:.2f}s (success: {success})")
            except Exception as e:
                print(f"    ❌ Error: {e}")
                times.append(0)

        avg_time = sum(times) / len(times) if times else 0
        print(f"  📊 Early exit average: {avg_time:.2f}s ({avg_time / 60:.2f} min)\n")

        return {"times": times, "average": avg_time, "iterations": self.iterations}

    async def run_combined_test(self) -> dict:
        """Run combined optimization test."""
        print("📊 Testing combined optimizations...")

        os.environ["ENABLE_QUALITY_FILTERING"] = "1"
        os.environ["ENABLE_CONTENT_ROUTING"] = "1"
        os.environ["ENABLE_EARLY_EXIT"] = "1"

        times = []
        for i in range(self.iterations):
            print(f"  Iteration {i + 1}/{self.iterations}...")
            orchestrator = AutonomousIntelligenceOrchestrator()
            start = time.time()
            try:
                result = await orchestrator.execute_autonomous_intelligence_workflow(self.url, "experimental")
                duration = time.time() - start
                times.append(duration)
                success = result.success if hasattr(result, "success") else True
                print(f"    ✅ {duration:.2f}s (success: {success})")
            except Exception as e:
                print(f"    ❌ Error: {e}")
                times.append(0)

        avg_time = sum(times) / len(times) if times else 0
        print(f"  📊 Combined average: {avg_time:.2f}s ({avg_time / 60:.2f} min)\n")

        return {"times": times, "average": avg_time, "iterations": self.iterations}

    async def run_all_tests(self):
        """Run all validation tests."""
        print("=" * 80)
        print("Week 4 Production Validation Suite")
        print("=" * 80)
        print(f"URL: {self.url}")
        print(f"Iterations per test: {self.iterations}")
        print("")

        # Run tests
        self.results["tests"]["baseline"] = await self.run_baseline_test()
        self.results["tests"]["quality_filtering"] = await self.run_quality_filtering_test()
        self.results["tests"]["content_routing"] = await self.run_content_routing_test()
        self.results["tests"]["early_exit"] = await self.run_early_exit_test()
        self.results["tests"]["combined"] = await self.run_combined_test()

        # Calculate improvements
        baseline_avg = self.results["tests"]["baseline"]["average"]
        self.results["improvements"] = {}

        for test_name, test_data in self.results["tests"].items():
            if test_name == "baseline":
                continue
            test_avg = test_data["average"]
            if baseline_avg > 0:
                improvement = ((baseline_avg - test_avg) / baseline_avg) * 100
                self.results["improvements"][test_name] = {
                    "absolute_seconds": baseline_avg - test_avg,
                    "percent": improvement,
                }

        # Print summary
        self.print_summary()

        # Save results
        self.save_results()

    def print_summary(self):
        """Print test summary."""
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("")

        baseline_avg = self.results["tests"]["baseline"]["average"]
        print(f"Baseline: {baseline_avg:.2f}s ({baseline_avg / 60:.2f} min)")
        print("")

        print("Improvements:")
        for test_name, improvement in self.results["improvements"].items():
            pct = improvement["percent"]
            secs = improvement["absolute_seconds"]
            status = "✅" if pct > 0 else "❌"
            print(f"  {status} {test_name}: {pct:+.1f}% ({secs:+.1f}s)")

        print("")

        # Combined impact analysis
        if "combined" in self.results["improvements"]:
            combined_pct = self.results["improvements"]["combined"]["percent"]
            target_pct = 65
            if combined_pct >= target_pct:
                print(f"🎯 TARGET ACHIEVED: {combined_pct:.1f}% (target: {target_pct}%)")
            else:
                print(f"⚠️  Below target: {combined_pct:.1f}% (target: {target_pct}%)")

    def save_results(self):
        """Save results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(f"benchmarks/week4_validation_{timestamp}.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📁 Results saved: {output_file}")


async def main():
    """Main entry point."""
    # Default test URL
    url = "https://www.youtube.com/watch?v=xtFiJ8AVdW0"

    # Allow override from command line
    if len(sys.argv) > 1:
        url = sys.argv[1]

    iterations = 3
    if len(sys.argv) > 2:
        iterations = int(sys.argv[2])

    validator = Week4Validator(url, iterations)
    await validator.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
