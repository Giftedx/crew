#!/usr/bin/env python3
"""Cache performance benchmarking script.

Measures actual performance improvements from cache implementation,
including latency reduction and hit rate analysis.

Usage:
    python benchmarks/cache_performance_benchmark.py
    python benchmarks/cache_performance_benchmark.py --iterations 50
    python benchmarks/cache_performance_benchmark.py --save-results
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domains.intelligence.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from domains.intelligence.analysis.sentiment_tool import SentimentTool
from domains.intelligence.analysis.text_analysis_tool import TextAnalysisTool


@dataclass
class CacheBenchmarkResult:
    """Results from a cache performance benchmark."""

    tool_name: str
    iteration: int
    cache_hit: bool
    duration_ms: float
    operation: str
    timestamp: str


@dataclass
class CachePerformanceStats:
    """Aggregated cache performance statistics."""

    tool_name: str
    total_calls: int
    cache_hits: int
    cache_misses: int
    hit_rate_pct: float
    avg_cached_latency_ms: float
    avg_uncached_latency_ms: float
    p50_cached_ms: float
    p50_uncached_ms: float
    p95_cached_ms: float
    p95_uncached_ms: float
    latency_reduction_pct: float
    estimated_time_saved_ms: float


def flush_redis():
    """Flush Redis cache before benchmarks."""
    try:
        subprocess.run(["redis-cli", "FLUSHDB"], check=True, capture_output=True)
        print("🧹 Redis cache flushed")
    except Exception as e:
        print(f"⚠️  Failed to flush Redis: {e}")


def percentile(data: list[float], p: float) -> float:
    """Calculate percentile of data."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = (p / 100) * (len(sorted_data) - 1)
    if index == int(index):
        return sorted_data[int(index)]
    lower = sorted_data[int(index)]
    upper = sorted_data[int(index) + 1]
    return lower + (upper - lower) * (index - int(index))


class CachePerformanceBenchmarker:
    """Benchmark cache performance across tools."""

    def __init__(self, iterations: int = 20):
        self.iterations = iterations
        self.results: list[CacheBenchmarkResult] = []

    def benchmark_tool(self, tool: Any, tool_name: str, test_inputs: list[str]) -> list[CacheBenchmarkResult]:
        """Benchmark a single tool with cache behavior."""
        results = []

        # Pattern: test same input multiple times to trigger cache hits
        for i in range(self.iterations):
            # Use different inputs to create realistic cache miss/hit pattern
            input_idx = i % len(test_inputs)
            test_input = test_inputs[input_idx]

            # Measure execution time
            start_time = time.perf_counter()
            result = tool._run(test_input)
            end_time = time.perf_counter()

            duration_ms = (end_time - start_time) * 1000
            cache_hit = result.metadata.get("cache_hit", False)

            benchmark_result = CacheBenchmarkResult(
                tool_name=tool_name,
                iteration=i + 1,
                cache_hit=cache_hit,
                duration_ms=duration_ms,
                operation=f"input_{input_idx}",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            )
            results.append(benchmark_result)

        return results

    def analyze_results(self, tool_results: list[CacheBenchmarkResult]) -> CachePerformanceStats:
        """Analyze benchmark results for a tool."""
        if not tool_results:
            raise ValueError("No results to analyze")

        tool_name = tool_results[0].tool_name
        total_calls = len(tool_results)
        cache_hits = sum(1 for r in tool_results if r.cache_hit)
        cache_misses = total_calls - cache_hits
        hit_rate_pct = (cache_hits / total_calls * 100) if total_calls > 0 else 0

        cached_latencies = [r.duration_ms for r in tool_results if r.cache_hit]
        uncached_latencies = [r.duration_ms for r in tool_results if not r.cache_hit]

        avg_cached = statistics.mean(cached_latencies) if cached_latencies else 0
        avg_uncached = statistics.mean(uncached_latencies) if uncached_latencies else 0

        p50_cached = percentile(cached_latencies, 50) if cached_latencies else 0
        p50_uncached = percentile(uncached_latencies, 50) if uncached_latencies else 0
        p95_cached = percentile(cached_latencies, 95) if cached_latencies else 0
        p95_uncached = percentile(uncached_latencies, 95) if uncached_latencies else 0

        if avg_uncached > 0:
            latency_reduction_pct = ((avg_uncached - avg_cached) / avg_uncached) * 100
        else:
            latency_reduction_pct = 0

        # Estimate time saved (cached calls use cached latency instead of uncached)
        estimated_time_saved_ms = cache_hits * (avg_uncached - avg_cached) if avg_uncached > avg_cached else 0

        return CachePerformanceStats(
            tool_name=tool_name,
            total_calls=total_calls,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate_pct=hit_rate_pct,
            avg_cached_latency_ms=avg_cached,
            avg_uncached_latency_ms=avg_uncached,
            p50_cached_ms=p50_cached,
            p50_uncached_ms=p50_uncached,
            p95_cached_ms=p95_cached,
            p95_uncached_ms=p95_uncached,
            latency_reduction_pct=latency_reduction_pct,
            estimated_time_saved_ms=estimated_time_saved_ms,
        )

    def run_all_benchmarks(self) -> dict[str, CachePerformanceStats]:
        """Run benchmarks for all cached tools."""
        all_stats = {}

        # Benchmark SentimentTool
        print("🧪 Benchmarking SentimentTool...")
        sentiment_tool = SentimentTool()
        sentiment_inputs = [
            "This is an amazing and wonderful experience!",
            "I'm feeling quite frustrated and disappointed.",
            "The weather is nice today.",
            "This is terrible and unacceptable behavior.",
            "Everything is going well and I'm very happy.",
        ]
        sentiment_results = self.benchmark_tool(sentiment_tool, "SentimentTool", sentiment_inputs)
        self.results.extend(sentiment_results)
        all_stats["SentimentTool"] = self.analyze_results(sentiment_results)
        print(f"  ✅ Completed {len(sentiment_results)} iterations")

        # Benchmark EnhancedAnalysisTool
        print("🧪 Benchmarking EnhancedAnalysisTool...")
        enhanced_tool = EnhancedAnalysisTool()
        enhanced_inputs = [
            "The new healthcare policy proposal includes comprehensive reforms.",
            "Technology companies are investing heavily in artificial intelligence.",
            "Climate change is affecting global weather patterns significantly.",
            "Economic indicators suggest potential growth in the next quarter.",
            "Educational institutions are adapting to hybrid learning models.",
        ]
        enhanced_results = self.benchmark_tool(enhanced_tool, "EnhancedAnalysisTool", enhanced_inputs)
        self.results.extend(enhanced_results)
        all_stats["EnhancedAnalysisTool"] = self.analyze_results(enhanced_results)
        print(f"  ✅ Completed {len(enhanced_results)} iterations")

        # Benchmark TextAnalysisTool
        print("🧪 Benchmarking TextAnalysisTool...")
        text_tool = TextAnalysisTool()
        text_inputs = [
            "The quick brown fox jumps over the lazy dog.",
            "Artificial intelligence is transforming modern society rapidly.",
            "Renewable energy sources are becoming more cost-effective.",
            "Data privacy concerns continue to grow in the digital age.",
            "Remote work has fundamentally changed workplace dynamics.",
        ]
        text_results = self.benchmark_tool(text_tool, "TextAnalysisTool", text_inputs)
        self.results.extend(text_results)
        all_stats["TextAnalysisTool"] = self.analyze_results(text_results)
        print(f"  ✅ Completed {len(text_results)} iterations")

        return all_stats

    def print_summary(self, all_stats: dict[str, CachePerformanceStats]) -> None:
        """Print benchmark summary."""
        print()
        print("=" * 80)
        print("CACHE PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)
        print()

        for tool_name, stats in all_stats.items():
            print(f"📊 {tool_name}")
            print("-" * 80)
            print("  Cache Performance:")
            print(f"    Total Calls:     {stats.total_calls}")
            print(f"    Cache Hits:      {stats.cache_hits}")
            print(f"    Cache Misses:    {stats.cache_misses}")
            print(f"    Hit Rate:        {stats.hit_rate_pct:.1f}%")
            print()
            print("  Latency (Cached):")
            print(f"    Average:         {stats.avg_cached_latency_ms:.2f}ms")
            print(f"    P50:             {stats.p50_cached_ms:.2f}ms")
            print(f"    P95:             {stats.p95_cached_ms:.2f}ms")
            print()
            print("  Latency (Uncached):")
            print(f"    Average:         {stats.avg_uncached_latency_ms:.2f}ms")
            print(f"    P50:             {stats.p50_uncached_ms:.2f}ms")
            print(f"    P95:             {stats.p95_uncached_ms:.2f}ms")
            print()
            print("  Performance Improvement:")
            print(f"    Latency Reduction: {stats.latency_reduction_pct:.1f}%")
            print(
                f"    Time Saved:        {stats.estimated_time_saved_ms:.2f}ms (total across {stats.cache_hits} cached calls)"
            )
            print()

        # Overall statistics
        total_calls = sum(s.total_calls for s in all_stats.values())
        total_hits = sum(s.cache_hits for s in all_stats.values())
        total_time_saved = sum(s.estimated_time_saved_ms for s in all_stats.values())
        overall_hit_rate = (total_hits / total_calls * 100) if total_calls > 0 else 0

        print("=" * 80)
        print("OVERALL SUMMARY")
        print("=" * 80)
        print(f"  Total Calls:       {total_calls}")
        print(f"  Total Cache Hits:  {total_hits}")
        print(f"  Overall Hit Rate:  {overall_hit_rate:.1f}%")
        print(f"  Total Time Saved:  {total_time_saved:.2f}ms ({total_time_saved / 1000:.2f}s)")
        print()

        # Expected cost savings (rough estimate based on LLM API calls)
        # Assume ~$0.002 per 1K tokens, average 500 tokens per call
        estimated_api_calls_saved = total_hits  # Cached calls don't hit API
        estimated_cost_saved = estimated_api_calls_saved * 0.001  # $0.001 per cached call (rough estimate)

        print("  Estimated Cost Savings:")
        print(f"    API Calls Saved:   {estimated_api_calls_saved}")
        print(f"    Cost Saved:        ~${estimated_cost_saved:.3f} (for this benchmark)")
        print(f"    Annual Projection: ~${estimated_cost_saved * 365 * 10:.2f} (assuming 10x traffic daily)")
        print("=" * 80)

    def save_results(self, filename: str = "cache_benchmark_results.json") -> None:
        """Save benchmark results to file."""
        output_path = Path("benchmarks/results") / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "iterations": self.iterations,
            "results": [asdict(r) for r in self.results],
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"💾 Results saved to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark cache performance across tools")
    parser.add_argument("--iterations", type=int, default=20, help="Number of iterations per tool (default: 20)")
    parser.add_argument("--save-results", action="store_true", help="Save results to JSON file")
    parser.add_argument("--no-flush", action="store_true", help="Skip Redis flush (use existing cache state)")
    args = parser.parse_args()

    print("=" * 80)
    print("CACHE PERFORMANCE BENCHMARK")
    print("=" * 80)
    print(f"Iterations per tool: {args.iterations}")
    print(f"Test pattern: 5 unique inputs, repeated {args.iterations // 5} times each")
    print()

    # Flush Redis unless --no-flush specified
    if not args.no_flush:
        flush_redis()
        print()

    # Run benchmarks
    benchmarker = CachePerformanceBenchmarker(iterations=args.iterations)
    all_stats = benchmarker.run_all_benchmarks()

    # Print summary
    benchmarker.print_summary(all_stats)

    # Save results if requested
    if args.save_results:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        benchmarker.save_results(f"cache_benchmark_{timestamp}.json")


if __name__ == "__main__":
    main()
