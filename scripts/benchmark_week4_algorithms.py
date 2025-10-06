#!/usr/bin/env python3
"""Week 4 Benchmark: Algorithmic Optimization Testing.

This script tests Week 4 algorithmic optimization strategies:
- Quality Threshold Filtering
- Content Type Routing
- Early Exit Conditions

USAGE:
    # Run all Week 4 tests
    python scripts/benchmark_week4_algorithms.py --url "https://youtube.com/..." --iterations 3

    # Run specific optimization test
    python scripts/benchmark_week4_algorithms.py --url "..." --test quality_filtering

    # Quick test with single iteration
    python scripts/benchmark_week4_algorithms.py --url "..." --iterations 1 --test all

OUTPUT:
    - JSON results: benchmarks/week4_results_{timestamp}.json
    - Summary report: benchmarks/week4_summary_{timestamp}.md
    - Individual logs: benchmarks/week4_logs/test_{name}_iter_{N}.log
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
    AutonomousIntelligenceOrchestrator,
)

# ============================================================================
# WEEK 4 TEST CONFIGURATIONS
# ============================================================================

WEEK4_TESTS = {
    "baseline": {
        "name": "baseline",
        "description": "Sequential baseline (no optimizations)",
        "flags": {
            "ENABLE_QUALITY_THRESHOLD_FILTERING": "0",
            "ENABLE_CONTENT_TYPE_ROUTING": "0",
            "ENABLE_EARLY_EXIT_CONDITIONS": "0",
        },
        "expected_improvement": 0.0,
        "target_time_min": 2.84,  # Original baseline
    },
    "quality_filtering": {
        "name": "quality_filtering",
        "description": "Quality threshold filtering (skip low-quality content)",
        "flags": {
            "ENABLE_QUALITY_THRESHOLD_FILTERING": "1",
            "ENABLE_CONTENT_TYPE_ROUTING": "0",
            "ENABLE_EARLY_EXIT_CONDITIONS": "0",
            # Quality thresholds
            "QUALITY_MIN_WORD_COUNT": "500",
            "QUALITY_MIN_SENTENCE_COUNT": "10",
            "QUALITY_MIN_COHERENCE": "0.6",
            "QUALITY_MIN_OVERALL": "0.65",
        },
        "expected_improvement": 0.20,  # 20% improvement
        "target_time_min": 2.27,  # 2.84 * 0.8
    },
    "content_routing": {
        "name": "content_routing",
        "description": "Content type routing (specialized pipelines)",
        "flags": {
            "ENABLE_QUALITY_THRESHOLD_FILTERING": "0",
            "ENABLE_CONTENT_TYPE_ROUTING": "1",
            "ENABLE_EARLY_EXIT_CONDITIONS": "0",
        },
        "expected_improvement": 0.25,  # 25% improvement
        "target_time_min": 2.13,  # 2.84 * 0.75
    },
    "early_exit": {
        "name": "early_exit",
        "description": "Early exit conditions (stop on confidence thresholds)",
        "flags": {
            "ENABLE_QUALITY_THRESHOLD_FILTERING": "0",
            "ENABLE_CONTENT_TYPE_ROUTING": "0",
            "ENABLE_EARLY_EXIT_CONDITIONS": "1",
            # Confidence thresholds
            "EARLY_EXIT_CONFIDENCE_THRESHOLD": "0.85",
            "EARLY_EXIT_MIN_ANALYSIS_TASKS": "3",
        },
        "expected_improvement": 0.15,  # 15% improvement
        "target_time_min": 2.41,  # 2.84 * 0.85
    },
    "combined_optimizations": {
        "name": "combined_optimizations",
        "description": "All algorithmic optimizations enabled",
        "flags": {
            "ENABLE_QUALITY_THRESHOLD_FILTERING": "1",
            "ENABLE_CONTENT_TYPE_ROUTING": "1",
            "ENABLE_EARLY_EXIT_CONDITIONS": "1",
            # Quality thresholds
            "QUALITY_MIN_WORD_COUNT": "500",
            "QUALITY_MIN_SENTENCE_COUNT": "10",
            "QUALITY_MIN_COHERENCE": "0.6",
            "QUALITY_MIN_OVERALL": "0.65",
            # Confidence thresholds
            "EARLY_EXIT_CONFIDENCE_THRESHOLD": "0.85",
            "EARLY_EXIT_MIN_ANALYSIS_TASKS": "3",
        },
        "expected_improvement": 0.45,  # 45% improvement (combined)
        "target_time_min": 1.56,  # 2.84 * 0.55
    },
}

# Week 4 specific flags to capture in results
WEEK4_FLAG_NAMES = [
    "ENABLE_QUALITY_THRESHOLD_FILTERING",
    "ENABLE_CONTENT_TYPE_ROUTING",
    "ENABLE_EARLY_EXIT_CONDITIONS",
    "QUALITY_MIN_WORD_COUNT",
    "QUALITY_MIN_SENTENCE_COUNT",
    "QUALITY_MIN_COHERENCE",
    "QUALITY_MIN_OVERALL",
    "EARLY_EXIT_CONFIDENCE_THRESHOLD",
    "EARLY_EXIT_MIN_ANALYSIS_TASKS",
]

# ============================================================================
# BENCHMARK EXECUTION
# ============================================================================


class Week4BenchmarkRunner:
    """Handles Week 4 algorithmic optimization benchmarking."""

    def __init__(self, url: str, depth: str = "experimental"):
        self.url = url
        self.depth = depth
        self.results: dict[str, Any] = {}
        self.orchestrator = AutonomousIntelligenceOrchestrator()

    async def run_single_test(self, test_name: str, iteration: int, log_dir: Path) -> dict[str, Any]:
        """Run a single test iteration."""
        test_config = WEEK4_TESTS[test_name]

        print(f"🧪 Running {test_name} (iteration {iteration})...")
        print(f"   Description: {test_config['description']}")

        # Set up environment
        env_backup = {}
        for flag_name, flag_value in test_config["flags"].items():
            env_backup[flag_name] = os.environ.get(flag_name)
            os.environ[flag_name] = flag_value

        # Set up logging
        log_file = log_dir / f"test_{test_name}_iter_{iteration}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Run the test
        start_time = time.time()

        try:
            # Execute the workflow
            result = await self.orchestrator.execute_autonomous_intelligence_workflow(self.url, self.depth)

            end_time = time.time()
            duration = end_time - start_time

            # Determine success
            success = getattr(result, "success", True)

            # Collect results
            iteration_result = {
                "test_name": test_name,
                "iteration": iteration,
                "duration_seconds": duration,
                "duration_minutes": duration / 60,
                "success": success,
                "timestamp": datetime.now().isoformat(),
                "flags": test_config["flags"].copy(),
                "expected_improvement": test_config["expected_improvement"],
                "target_time_min": test_config["target_time_min"],
                "log_file": str(log_file),
            }

            print(f"   ✅ Completed in {duration:.2f}s ({duration / 60:.2f} min)")

            return iteration_result

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            print(f"   ❌ Failed after {duration:.2f}s: {str(e)}")

            return {
                "test_name": test_name,
                "iteration": iteration,
                "duration_seconds": duration,
                "duration_minutes": duration / 60,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "flags": test_config["flags"].copy(),
                "log_file": str(log_file),
            }

        finally:
            # Restore environment
            for flag_name, original_value in env_backup.items():
                if original_value is None:
                    os.environ.pop(flag_name, None)
                else:
                    os.environ[flag_name] = original_value

    async def run_test_suite(self, test_names: list[str], iterations: int, output_dir: Path) -> dict[str, Any]:
        """Run complete test suite."""
        start_time = datetime.now()

        print("🚀 Starting Week 4 Algorithmic Optimization Benchmark")
        print(f"   URL: {self.url}")
        print(f"   Tests: {', '.join(test_names)}")
        print(f"   Iterations per test: {iterations}")
        print(f"   Total runs: {len(test_names) * iterations}")
        print()

        # Create output directories
        log_dir = output_dir / "week4_logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Run all test iterations
        all_results = []

        for test_name in test_names:
            for iteration in range(1, iterations + 1):
                result = await self.run_single_test(test_name, iteration, log_dir)
                all_results.append(result)

        # Calculate statistics
        test_stats = self._calculate_statistics(all_results)

        # Prepare final results
        final_results = {
            "benchmark_info": {
                "suite": "week4_algorithmic_optimization",
                "url": self.url,
                "depth": self.depth,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_minutes": (datetime.now() - start_time).total_seconds() / 60,
                "tests_run": test_names,
                "iterations_per_test": iterations,
                "total_iterations": len(all_results),
            },
            "week4_flags_snapshot": {flag: os.environ.get(flag, "not_set") for flag in WEEK4_FLAG_NAMES},
            "individual_results": all_results,
            "test_statistics": test_stats,
            "baseline_comparison": self._compare_to_baseline(test_stats),
        }

        return final_results

    def _calculate_statistics(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate statistical summaries for each test."""
        stats = {}

        # Group results by test name
        by_test = {}
        for result in results:
            test_name = result["test_name"]
            if test_name not in by_test:
                by_test[test_name] = []
            by_test[test_name].append(result)

        # Calculate stats for each test
        for test_name, test_results in by_test.items():
            successful_results = [r for r in test_results if r["success"]]

            if not successful_results:
                stats[test_name] = {
                    "name": test_name,
                    "description": WEEK4_TESTS[test_name]["description"],
                    "iterations": len(test_results),
                    "success_rate": 0.0,
                    "all_failed": True,
                }
                continue

            durations = [r["duration_seconds"] for r in successful_results]
            durations_min = [d / 60 for d in durations]

            # Basic statistics
            mean_duration = sum(durations) / len(durations)
            mean_duration_min = mean_duration / 60
            median_duration = sorted(durations)[len(durations) // 2]
            median_duration_min = median_duration / 60
            min_duration = min(durations)
            max_duration = max(durations)

            # Standard deviation
            if len(durations) > 1:
                variance = sum((d - mean_duration) ** 2 for d in durations) / len(durations)
                std_dev = variance**0.5
            else:
                std_dev = 0.0

            # Expected performance
            test_config = WEEK4_TESTS[test_name]
            expected_improvement = test_config.get("expected_improvement", 0.0)
            target_time_min = test_config.get("target_time_min", 2.84)

            stats[test_name] = {
                "name": test_name,
                "description": test_config["description"],
                "iterations": len(test_results),
                "successful_iterations": len(successful_results),
                "success_rate": len(successful_results) / len(test_results),
                "mean_seconds": mean_duration,
                "mean_minutes": mean_duration_min,
                "median_seconds": median_duration,
                "median_minutes": median_duration_min,
                "min_seconds": min_duration,
                "max_seconds": max_duration,
                "std_dev_seconds": std_dev,
                "expected_improvement": expected_improvement,
                "target_time_min": target_time_min,
                "flags": test_config["flags"],
            }

        return stats

    def _compare_to_baseline(self, test_stats: dict[str, Any]) -> dict[str, Any]:
        """Compare test results to baseline performance."""
        baseline_time = 2.84  # Original baseline from Week 3

        if "baseline" in test_stats:
            baseline_time = test_stats["baseline"]["mean_minutes"]

        comparisons = {}

        for test_name, stats in test_stats.items():
            if stats.get("all_failed"):
                comparisons[test_name] = {
                    "status": "FAILED",
                    "vs_baseline_minutes": None,
                    "vs_baseline_percent": None,
                    "met_expectations": False,
                }
                continue

            mean_time = stats["mean_minutes"]
            time_diff = mean_time - baseline_time
            percent_change = (time_diff / baseline_time) * 100

            # Determine if expectations were met
            expected_improvement = stats.get("expected_improvement", 0.0)
            expected_time = baseline_time * (1 - expected_improvement)
            met_expectations = mean_time <= expected_time * 1.1  # 10% tolerance

            # Status determination
            if percent_change <= -20:  # 20%+ improvement
                status = "EXCELLENT"
            elif percent_change <= -10:  # 10%+ improvement
                status = "GOOD"
            elif percent_change <= 10:  # Within 10%
                status = "NEUTRAL"
            elif percent_change <= 25:  # 25% slower
                status = "POOR"
            else:
                status = "FAILED"

            comparisons[test_name] = {
                "status": status,
                "vs_baseline_minutes": time_diff,
                "vs_baseline_percent": percent_change,
                "met_expectations": met_expectations,
                "expected_improvement_percent": expected_improvement * 100,
                "expected_time_min": expected_time,
                "actual_time_min": mean_time,
            }

        return comparisons


# ============================================================================
# OUTPUT GENERATION
# ============================================================================


def save_results(results: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    """Save benchmark results to JSON and markdown files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON results file
    json_file = output_dir / f"week4_results_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Markdown summary
    md_file = output_dir / f"week4_summary_{timestamp}.md"
    with open(md_file, "w") as f:
        f.write(generate_markdown_summary(results))

    return json_file, md_file


def generate_markdown_summary(results: dict[str, Any]) -> str:
    """Generate markdown summary report."""
    benchmark_info = results["benchmark_info"]
    test_stats = results["test_statistics"]
    baseline_comparison = results["baseline_comparison"]

    # Find baseline for reference
    baseline_time = 2.84
    if "baseline" in test_stats:
        baseline_time = test_stats["baseline"]["mean_minutes"]

    md_content = f"""# Week 4 Algorithmic Optimization Results

**Generated:** {datetime.now().isoformat()}
**Benchmark Suite:** {benchmark_info["suite"]}
**Total Duration:** {benchmark_info["duration_minutes"]:.1f} minutes

---

## Executive Summary

Week 4 tested algorithmic optimization strategies to improve performance through:
- Quality threshold filtering (skip low-quality content)
- Content type routing (specialized pipelines)
- Early exit conditions (confidence-based termination)

**Baseline Reference:** {baseline_time:.2f} minutes

---

## Test Results Summary

| Test | Status | Mean Time | vs Baseline | Expected | Met Target |
|------|--------|-----------|-------------|----------|------------|
"""

    for test_name in test_stats.keys():
        stats = test_stats[test_name]
        comparison = baseline_comparison[test_name]

        if stats.get("all_failed"):
            md_content += f"| {test_name} | ❌ FAILED | N/A | N/A | N/A | ❌ |\n"
            continue

        status_emoji = {"EXCELLENT": "🟢", "GOOD": "✅", "NEUTRAL": "⚠️", "POOR": "🔶", "FAILED": "❌"}.get(
            comparison["status"], "❓"
        )

        mean_time = stats["mean_minutes"]
        vs_baseline = comparison["vs_baseline_percent"]
        expected = comparison["expected_improvement_percent"]
        met_target = "✅" if comparison["met_expectations"] else "❌"

        md_content += f"| {test_name} | {status_emoji} {comparison['status']} | {mean_time:.2f} min | {vs_baseline:+.1f}% | {expected:.0f}% | {met_target} |\n"

    md_content += "\n---\n\n## Detailed Statistics\n\n"

    for test_name, stats in test_stats.items():
        if stats.get("all_failed"):
            md_content += f"### {test_name}: FAILED\n\n**Description:** {stats['description']}\n\nAll {stats['iterations']} iterations failed.\n\n"
            continue

        comparison = baseline_comparison[test_name]

        md_content += f"""### {test_name}

**Description:** {stats["description"]}

**Performance:**
- Iterations: {stats["successful_iterations"]}/{stats["iterations"]} successful
- Mean: {stats["mean_seconds"]:.1f}s ({stats["mean_minutes"]:.2f} min)
- Median: {stats["median_seconds"]:.1f}s ({stats["median_minutes"]:.2f} min)
- Range: {stats["min_seconds"]:.1f}s - {stats["max_seconds"]:.1f}s
- Std Dev: {stats["std_dev_seconds"]:.1f}s

**vs Baseline:**
- Performance: {comparison["vs_baseline_percent"]:+.1f}% ({comparison["vs_baseline_minutes"]:+.2f} min)
- Expected: {comparison["expected_improvement_percent"]:.0f}% improvement
- Target Time: {comparison["expected_time_min"]:.2f} min
- Met Expectations: {"✅ Yes" if comparison["met_expectations"] else "❌ No"}

**Configuration:**
"""

        for flag, value in stats["flags"].items():
            md_content += f"- {flag}: {value}\n"

        md_content += "\n"

    md_content += """
---

## Production Recommendations

### Successful Optimizations
Deploy the following optimizations based on test results:

"""

    successful_tests = [
        name
        for name, comp in baseline_comparison.items()
        if comp["status"] in ["EXCELLENT", "GOOD"] and comp["met_expectations"]
    ]

    if successful_tests:
        for test_name in successful_tests:
            stats = test_stats[test_name]
            comparison = baseline_comparison[test_name]
            md_content += f"- **{test_name}**: {comparison['vs_baseline_percent']:+.1f}% improvement\n"
    else:
        md_content += "- No optimizations met performance expectations\n"

    md_content += """
### Failed Optimizations
Investigate or disable the following:

"""

    failed_tests = [
        name
        for name, comp in baseline_comparison.items()
        if comp["status"] in ["POOR", "FAILED"] or not comp["met_expectations"]
    ]

    if failed_tests:
        for test_name in failed_tests:
            comparison = baseline_comparison[test_name]
            md_content += f"- **{test_name}**: {comparison['vs_baseline_percent']:+.1f}% change (expected {comparison['expected_improvement_percent']:.0f}% improvement)\n"
    else:
        md_content += "- All tests met or exceeded expectations\n"

    md_content += """

---

**Next Steps:** Based on these results, proceed with Week 4 Phase 2 or Week 5 planning.
"""

    return md_content


# ============================================================================
# MAIN EXECUTION
# ============================================================================


async def main():
    """Main benchmark execution function."""
    parser = argparse.ArgumentParser(
        description="Week 4 Algorithmic Optimization Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--url", required=True, help="YouTube URL to analyze")

    parser.add_argument("--depth", default="experimental", help="Analysis depth (default: experimental)")

    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations per test (default: 3)")

    parser.add_argument(
        "--test", choices=list(WEEK4_TESTS.keys()) + ["all"], default="all", help="Specific test to run (default: all)"
    )

    parser.add_argument(
        "--output-dir", type=Path, default=Path("benchmarks"), help="Output directory for results (default: benchmarks)"
    )

    args = parser.parse_args()

    # Determine which tests to run
    if args.test == "all":
        test_names = list(WEEK4_TESTS.keys())
    else:
        test_names = [args.test]

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Run benchmark
    runner = Week4BenchmarkRunner(args.url, args.depth)
    results = await runner.run_test_suite(test_names, args.iterations, args.output_dir)

    # Save results
    json_file, md_file = save_results(results, args.output_dir)

    print()
    print("================================================================================")
    print("Week 4 Benchmark Complete!")
    print("================================================================================")
    print(f"JSON Results: {json_file}")
    print(f"Summary Report: {md_file}")
    print()

    # Print quick summary
    baseline_comparison = results["baseline_comparison"]
    successful_count = sum(
        1
        for comp in baseline_comparison.values()
        if comp["status"] in ["EXCELLENT", "GOOD"] and comp.get("met_expectations", False)
    )

    print(f"Tests Meeting Expectations: {successful_count}/{len(test_names)}")

    if successful_count > 0:
        print("🎉 Some optimizations succeeded! Check the detailed report.")
    else:
        print("⚠️  No optimizations met expectations. Review strategies for Week 4 Phase 2.")


if __name__ == "__main__":
    asyncio.run(main())
