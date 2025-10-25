#!/usr/bin/env python3
"""Test and benchmark memory optimization system.

This script tests the memory optimization functionality and measures
performance improvements from memory pooling and optimization strategies.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ultimate_discord_intelligence_bot.optimization.memory_optimizer import (
    analyze_memory_usage,
    get_memory_optimizer,
    get_memory_stats,
    optimize_memory,
)
from ultimate_discord_intelligence_bot.optimization.memory_pool import (
    get_memory_stats as get_pool_stats,
)
from ultimate_discord_intelligence_bot.optimization.memory_pool import (
    register_resource_type,
    with_pooled_resource,
)


class ExpensiveResource:
    """Mock expensive resource for testing."""

    def __init__(self, resource_id: str, size_mb: int = 10):
        """Initialize the expensive resource."""
        self.resource_id = resource_id
        self.size_mb = size_mb
        # Simulate memory allocation
        self.data = [0] * (size_mb * 1024 * 1024 // 8)  # Approximate MB
        self.created_at = time.time()
        self.use_count = 0

    def use(self):
        """Use the resource."""
        self.use_count += 1
        # Simulate some work
        return sum(self.data[:1000])  # Use a small portion

    def cleanup(self):
        """Clean up the resource."""
        self.data.clear()
        self.data = None


def create_expensive_resource(resource_id: str = "default") -> ExpensiveResource:
    """Factory function for creating expensive resources."""
    return ExpensiveResource(resource_id, size_mb=5)


def benchmark_memory_pooling():
    """Benchmark memory pooling performance."""
    print("🚀 Benchmarking Memory Pooling Performance")
    print("=" * 50)

    # Register resource type
    register_resource_type("expensive_resource", create_expensive_resource)

    # Test without pooling
    print("\n📊 Testing Without Pooling")
    no_pool_times = []
    no_pool_memory = []

    for i in range(5):
        start_time = time.time()
        start_memory = get_memory_stats()["current_memory_mb"]

        # Create and use resources without pooling
        resources = []
        for j in range(10):
            resource = ExpensiveResource(f"resource_{i}_{j}", size_mb=2)
            resource.use()
            resources.append(resource)

        # Clean up manually
        for resource in resources:
            resource.cleanup()

        end_time = time.time()
        end_memory = get_memory_stats()["current_memory_mb"]

        no_pool_times.append(end_time - start_time)
        no_pool_memory.append(end_memory - start_memory)
        print(f"  Run {i + 1}: {end_time - start_time:.4f}s, {end_memory - start_memory:.1f}MB")

    # Test with pooling
    print("\n⚡ Testing With Memory Pooling")
    pool_times = []
    pool_memory = []

    for i in range(5):
        start_time = time.time()
        start_memory = get_memory_stats()["current_memory_mb"]

        # Use pooled resources
        with with_pooled_resource("expensive_resource", f"pooled_{i}") as resource:
            resource.use()

        end_time = time.time()
        end_memory = get_memory_stats()["current_memory_mb"]

        pool_times.append(end_time - start_time)
        pool_memory.append(end_memory - start_memory)
        print(f"  Run {i + 1}: {end_time - start_time:.4f}s, {end_memory - start_memory:.1f}MB")

    # Calculate improvements
    avg_no_pool_time = sum(no_pool_times) / len(no_pool_times)
    avg_pool_time = sum(pool_times) / len(pool_times)
    avg_no_pool_memory = sum(no_pool_memory) / len(no_pool_memory)
    avg_pool_memory = sum(pool_memory) / len(pool_memory)

    print("\n📈 Performance Summary:")
    print(f"  Without Pooling: {avg_no_pool_time:.4f}s average, {avg_no_pool_memory:.1f}MB average")
    print(f"  With Pooling: {avg_pool_time:.4f}s average, {avg_pool_memory:.1f}MB average")

    if avg_no_pool_time > 0:
        time_improvement = ((avg_no_pool_time - avg_pool_time) / avg_no_pool_time) * 100
        print(f"  🎯 Time Improvement: {time_improvement:.1f}% faster")

    if avg_no_pool_memory > 0:
        memory_improvement = ((avg_no_pool_memory - avg_pool_memory) / avg_no_pool_memory) * 100
        print(f"  🎯 Memory Improvement: {memory_improvement:.1f}% less memory usage")

    return {
        "no_pool_times": no_pool_times,
        "pool_times": pool_times,
        "no_pool_memory": no_pool_memory,
        "pool_memory": pool_memory,
        "time_improvement": time_improvement if avg_no_pool_time > 0 else 0,
        "memory_improvement": memory_improvement if avg_no_pool_memory > 0 else 0,
    }


def test_memory_analysis():
    """Test memory usage analysis."""
    print("\n🧠 Testing Memory Usage Analysis")
    print("=" * 50)

    # Create some memory pressure
    print("📊 Creating Memory Pressure...")
    large_objects = []
    for _i in range(20):
        obj = [0] * (1024 * 1024)  # 1MB object
        large_objects.append(obj)

    # Analyze memory usage
    analysis = analyze_memory_usage()

    print(f"  Current Memory: {analysis['current_profile']['current_memory_mb']:.1f}MB")
    print(f"  Memory Growth: {analysis['current_profile']['memory_growth_mb']:.1f}MB")
    print(f"  Object Count: {analysis['current_profile']['object_count']}")
    print(f"  Memory Trend: {analysis['memory_trend']}")
    print(f"  Growth Rate: {analysis['growth_rate_mb_per_minute']:.2f}MB/min")

    if analysis["issues"]:
        print("\n⚠️  Memory Issues:")
        for issue in analysis["issues"]:
            print(f"    - {issue}")

    if analysis["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in analysis["recommendations"]:
            print(f"    - {rec}")

    # Clean up
    large_objects.clear()

    return analysis


def test_optimization_strategies():
    """Test individual optimization strategies."""
    print("\n⚙️ Testing Optimization Strategies")
    print("=" * 50)

    optimizer = get_memory_optimizer()

    # Test each strategy
    strategies = ["gc_optimization", "object_pooling", "memory_compaction", "lazy_loading", "resource_cleanup"]

    for strategy_name in strategies:
        print(f"\n🔧 Testing {strategy_name}...")
        result = optimizer.apply_optimization_strategy(strategy_name)

        if result.get("success", False):
            print(f"  ✅ Success: {result.get('memory_saved_mb', 0):.1f}MB saved")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")


def test_comprehensive_optimization():
    """Test comprehensive memory optimization."""
    print("\n🚀 Testing Comprehensive Memory Optimization")
    print("=" * 50)

    # Create initial memory pressure
    print("📊 Creating Initial Memory Pressure...")
    initial_objects = []
    for _i in range(30):
        obj = [0] * (512 * 1024)  # 512KB object
        initial_objects.append(obj)

    # Get initial stats
    initial_stats = get_memory_stats()
    print(f"  Initial Memory: {initial_stats['current_memory_mb']:.1f}MB")

    # Run comprehensive optimization
    print("\n⚡ Running Comprehensive Optimization...")
    optimization_result = optimize_memory()

    print(f"  Initial Memory: {optimization_result['initial_memory_mb']:.1f}MB")
    print(f"  Final Memory: {optimization_result['final_memory_mb']:.1f}MB")
    print(f"  Total Memory Saved: {optimization_result['total_memory_saved_mb']:.1f}MB")

    # Show strategy results
    print("\n📊 Strategy Results:")
    for strategy, result in optimization_result["optimization_results"].items():
        if result.get("success", False):
            saved = result.get("memory_saved_mb", 0)
            print(f"  ✅ {strategy}: {saved:.1f}MB saved")
        else:
            print(f"  ❌ {strategy}: {result.get('error', 'Failed')}")

    # Clean up
    initial_objects.clear()

    return optimization_result


def test_memory_pool_stats():
    """Test memory pool statistics."""
    print("\n📊 Testing Memory Pool Statistics")
    print("=" * 50)

    # Get pool stats
    pool_stats = get_pool_stats()

    print(f"  Pool Utilization: {pool_stats['pool_utilization']:.1f}%")
    print(f"  Total Pooled Resources: {pool_stats['total_pooled_resources']}")
    print(f"  Total Active Resources: {pool_stats['total_active_resources']}")

    if pool_stats["resource_types"]:
        print("  Resource Types:")
        for resource_type, count in pool_stats["resource_types"].items():
            print(f"    - {resource_type}: {count}")

    if pool_stats["memory_stats"]:
        memory_stats = pool_stats["memory_stats"]
        print("  Memory Stats:")
        print(f"    - Current: {memory_stats['current_memory_mb']:.1f}MB")
        print(f"    - Peak: {memory_stats['peak_memory_mb']:.1f}MB")
        print(f"    - Usage: {memory_stats['memory_usage_percent']:.1f}%")


def main():
    """Main test function."""
    print("🧪 Memory Optimization System Test Suite")
    print("=" * 60)

    try:
        # Run benchmarks
        benchmark_memory_pooling()

        # Test memory analysis
        test_memory_analysis()

        # Test optimization strategies
        test_optimization_strategies()

        # Test comprehensive optimization
        test_comprehensive_optimization()

        # Test memory pool stats
        test_memory_pool_stats()

        print("\n✅ Memory optimization tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
