#!/usr/bin/env python3
"""Test and benchmark result caching system.

This script tests the result caching functionality and measures performance
improvements from caching expensive operations.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ultimate_discord_intelligence_bot.caching import (
    analyze_cache_performance,
    auto_optimize_cache,
    cache_result,
    get_cache_recommendations,
    get_cache_stats,
    smart_cache_tool_result,
)
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class ExpensiveAnalysisTool(BaseTool):
    """Mock tool that simulates expensive analysis operations."""

    def __init__(self):
        super().__init__()
        self.name = "ExpensiveAnalysisTool"
        self.description = "Tool that performs expensive analysis operations"

    def _run(self, content: str, analysis_type: str = "basic") -> StepResult:
        """Simulate expensive analysis operation."""
        # Simulate processing time based on content length and analysis type
        base_time = len(content) * 0.001  # 1ms per character
        if analysis_type == "advanced":
            base_time *= 3
        elif analysis_type == "deep":
            base_time *= 5

        time.sleep(base_time)  # Simulate processing

        return StepResult.ok(
            data={
                "content": content,
                "analysis_type": analysis_type,
                "processed_at": time.time(),
                "result": f"Analysis of {len(content)} characters completed",
            }
        )


class CachedAnalysisTool(BaseTool):
    """Analysis tool with result caching."""

    def __init__(self):
        super().__init__()
        self.name = "CachedAnalysisTool"
        self.description = "Analysis tool with intelligent result caching"

    @smart_cache_tool_result(ttl=300, priority=8)  # 5 minutes, high priority
    def _run(self, content: str, analysis_type: str = "basic") -> StepResult:
        """Cached analysis operation."""
        # Simulate expensive processing
        base_time = len(content) * 0.001
        if analysis_type == "advanced":
            base_time *= 3
        elif analysis_type == "deep":
            base_time *= 5

        time.sleep(base_time)

        return StepResult.ok(
            data={
                "content": content,
                "analysis_type": analysis_type,
                "processed_at": time.time(),
                "result": f"Cached analysis of {len(content)} characters completed",
            }
        )


@cache_result(ttl=600)  # 10 minutes
def expensive_computation(data: str, complexity: int = 1) -> dict:
    """Simulate expensive computation with caching."""
    # Simulate processing time
    time.sleep(complexity * 0.1)

    return {
        "data": data,
        "complexity": complexity,
        "result": f"Computed result for {data} with complexity {complexity}",
        "timestamp": time.time(),
    }


def benchmark_caching_performance():
    """Benchmark caching performance improvements."""
    print("🚀 Benchmarking Caching Performance")
    print("=" * 50)

    # Test data
    test_content = "This is a test content for analysis. " * 100  # 3600 characters

    # Test without caching
    print("\n📊 Testing Without Caching")
    no_cache_times = []

    tool = ExpensiveAnalysisTool()
    for i in range(5):
        start_time = time.time()
        tool._run(test_content, "advanced")
        end_time = time.time()
        no_cache_times.append(end_time - start_time)
        print(f"  Run {i + 1}: {end_time - start_time:.4f}s")

    # Test with caching
    print("\n⚡ Testing With Smart Caching")
    cache_times = []

    cached_tool = CachedAnalysisTool()
    for i in range(5):
        start_time = time.time()
        cached_tool._run(test_content, "advanced")
        end_time = time.time()
        cache_times.append(end_time - start_time)
        print(f"  Run {i + 1}: {end_time - start_time:.4f}s")

    # Calculate improvements
    avg_no_cache = sum(no_cache_times) / len(no_cache_times)
    avg_cache = sum(cache_times) / len(cache_times)

    if avg_no_cache > 0:
        improvement = ((avg_no_cache - avg_cache) / avg_no_cache) * 100
        print("\n📈 Performance Summary:")
        print(f"  Without Caching: {avg_no_cache:.4f}s average")
        print(f"  With Caching: {avg_cache:.4f}s average")
        print(f"  🎯 Performance Improvement: {improvement:.1f}% faster")

    return {
        "no_cache_times": no_cache_times,
        "cache_times": cache_times,
        "avg_no_cache": avg_no_cache,
        "avg_cache": avg_cache,
        "improvement": improvement if avg_no_cache > 0 else 0,
    }


def test_cache_hit_rates():
    """Test cache hit rates with repeated operations."""
    print("\n🎯 Testing Cache Hit Rates")
    print("=" * 50)

    tool = CachedAnalysisTool()
    test_data = [
        ("Short content", "basic"),
        ("Medium content for analysis", "advanced"),
        ("Long content for deep analysis with multiple parameters", "deep"),
        ("Short content", "basic"),  # Repeat for cache hit
        ("Medium content for analysis", "advanced"),  # Repeat for cache hit
    ]

    print("📝 Test Operations:")
    for i, (content, analysis_type) in enumerate(test_data):
        start_time = time.time()
        tool._run(content, analysis_type)
        end_time = time.time()

        status = "🔄 Cache Miss" if end_time - start_time > 0.01 else "⚡ Cache Hit"
        print(f"  {i + 1}. {status} - {content[:30]}... ({analysis_type}) - {end_time - start_time:.4f}s")

    # Get cache statistics
    stats = get_cache_stats()
    print("\n📊 Cache Statistics:")
    print(f"  Cache Size: {stats['size']}")
    print(f"  Hit Rate: {stats['hit_rate']:.1f}%")
    print(f"  Total Hits: {stats['hits']}")
    print(f"  Total Misses: {stats['misses']}")


def test_smart_cache_analysis():
    """Test smart cache analysis and recommendations."""
    print("\n🧠 Testing Smart Cache Analysis")
    print("=" * 50)

    # Generate some usage patterns
    tool = CachedAnalysisTool()
    test_scenarios = [
        ("Content 1", "basic"),
        ("Content 2", "advanced"),
        ("Content 1", "basic"),  # Repeat for cache hit
        ("Content 3", "deep"),
        ("Content 2", "advanced"),  # Repeat for cache hit
        ("Content 4", "basic"),
        ("Content 1", "basic"),  # Another repeat
    ]

    print("📊 Generating Usage Patterns:")
    for i, (content, analysis_type) in enumerate(test_scenarios):
        tool._run(content, analysis_type)
        print(f"  {i + 1}. Processed: {content} ({analysis_type})")

    # Analyze performance
    print("\n🔍 Smart Cache Analysis:")
    analysis = analyze_cache_performance()

    print(f"  Total Tools: {analysis['smart_cache']['total_tools']}")
    print(f"  Cached Tools: {analysis['smart_cache']['cached_tools']}")
    print(f"  Cache Coverage: {analysis['smart_cache']['cache_coverage']:.1f}%")
    print(f"  Average Hit Rate: {analysis['smart_cache']['avg_hit_rate']:.1f}%")

    # Get recommendations
    print("\n💡 Cache Recommendations:")
    recommendations = get_cache_recommendations()

    for tool_name, rec in recommendations.items():
        print(f"  {tool_name}:")
        print(f"    Should Cache: {rec['should_cache']}")
        print(f"    Optimal TTL: {rec['optimal_ttl']}s")
        print(f"    Priority: {rec['priority']}")
        if rec["recommendations"]:
            print(f"    Recommendations: {', '.join(rec['recommendations'])}")


def test_function_caching():
    """Test function-level caching."""
    print("\n🔧 Testing Function-Level Caching")
    print("=" * 50)

    test_data = [
        ("dataset1", 1),
        ("dataset2", 2),
        ("dataset1", 1),  # Repeat for cache hit
        ("dataset3", 3),
        ("dataset2", 2),  # Repeat for cache hit
    ]

    print("📝 Function Cache Tests:")
    for i, (data, complexity) in enumerate(test_data):
        start_time = time.time()
        expensive_computation(data, complexity)
        end_time = time.time()

        status = "🔄 Cache Miss" if end_time - start_time > 0.05 else "⚡ Cache Hit"
        print(f"  {i + 1}. {status} - {data} (complexity {complexity}) - {end_time - start_time:.4f}s")

    # Get cache stats
    stats = get_cache_stats()
    print("\n📊 Function Cache Statistics:")
    print(f"  Hit Rate: {stats['hit_rate']:.1f}%")
    print(f"  Cache Size: {stats['size']}")


def test_cache_optimization():
    """Test automatic cache optimization."""
    print("\n⚙️ Testing Cache Optimization")
    print("=" * 50)

    # Run auto-optimization
    print("🔄 Running automatic cache optimization...")
    auto_optimize_cache()

    # Get updated analysis
    analysis = analyze_cache_performance()
    print("📊 Post-Optimization Analysis:")
    print(f"  Cache Coverage: {analysis['smart_cache']['cache_coverage']:.1f}%")
    print(f"  Average Hit Rate: {analysis['smart_cache']['avg_hit_rate']:.1f}%")

    # Show strategy updates
    strategies = analysis.get("strategies", {})
    if strategies:
        print("\n🎯 Updated Caching Strategies:")
        for tool_name, strategy in strategies.items():
            print(f"  {tool_name}:")
            print(f"    Enabled: {strategy['enabled']}")
            print(f"    TTL: {strategy['ttl']}s")
            print(f"    Priority: {strategy['priority']}")


def main():
    """Main test function."""
    print("🧪 Result Caching System Test Suite")
    print("=" * 60)

    try:
        # Run benchmarks
        benchmark_caching_performance()

        # Test cache hit rates
        test_cache_hit_rates()

        # Test smart cache analysis
        test_smart_cache_analysis()

        # Test function caching
        test_function_caching()

        # Test cache optimization
        test_cache_optimization()

        print("\n✅ Result caching tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
