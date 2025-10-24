#!/usr/bin/env python3
"""Test and benchmark lazy loading system.

This script tests the lazy loading functionality and measures performance
improvements compared to eager loading.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ultimate_discord_intelligence_bot.agents.acquisition.acquisition_specialist import AcquisitionSpecialistAgent
from ultimate_discord_intelligence_bot.agents.acquisition.lazy_acquisition_specialist import (
    LazyAcquisitionSpecialistAgent,
)
from ultimate_discord_intelligence_bot.tools.lazy_loader import clear_lazy_cache, get_lazy_loader_stats


def benchmark_agent_creation():
    """Benchmark agent creation with and without lazy loading."""
    print("🚀 Benchmarking Agent Creation Performance")
    print("=" * 50)

    # Test eager loading (original)
    print("\n📊 Testing Eager Loading (Original Agent)")
    eager_times = []

    for i in range(5):
        start_time = time.time()
        try:
            agent = AcquisitionSpecialistAgent()
            # Access tools to trigger full loading
            tools = agent._tools
            end_time = time.time()
            eager_times.append(end_time - start_time)
            print(f"  Run {i + 1}: {end_time - start_time:.4f}s ({len(tools)} tools loaded)")
        except Exception as e:
            print(f"  Run {i + 1}: Failed - {e}")
            eager_times.append(float("inf"))

    # Test lazy loading
    print("\n⚡ Testing Lazy Loading (Lazy Agent)")
    lazy_times = []

    for i in range(5):
        start_time = time.time()
        try:
            agent = LazyAcquisitionSpecialistAgent()
            # Don't access tools yet - just create agent
            end_time = time.time()
            lazy_times.append(end_time - start_time)
            print(f"  Run {i + 1}: {end_time - start_time:.4f}s (agent created, tools not loaded)")
        except Exception as e:
            print(f"  Run {i + 1}: Failed - {e}")
            lazy_times.append(float("inf"))

    # Test lazy loading with tool access
    print("\n🔧 Testing Lazy Loading with Tool Access")
    lazy_access_times = []

    for i in range(5):
        start_time = time.time()
        try:
            agent = LazyAcquisitionSpecialistAgent()
            # Access tools to trigger lazy loading
            tools = agent.tools
            end_time = time.time()
            lazy_access_times.append(end_time - start_time)
            print(f"  Run {i + 1}: {end_time - start_time:.4f}s ({len(tools)} tools loaded)")
        except Exception as e:
            print(f"  Run {i + 1}: Failed - {e}")
            lazy_access_times.append(float("inf"))

    # Calculate averages
    valid_eager = [t for t in eager_times if t != float("inf")]
    valid_lazy = [t for t in lazy_times if t != float("inf")]
    valid_lazy_access = [t for t in lazy_access_times if t != float("inf")]

    avg_eager = sum(valid_eager) / len(valid_eager) if valid_eager else 0
    avg_lazy = sum(valid_lazy) / len(valid_lazy) if valid_lazy else 0
    avg_lazy_access = sum(valid_lazy_access) / len(valid_lazy_access) if valid_lazy_access else 0

    print("\n📈 Performance Summary:")
    print(f"  Eager Loading Average: {avg_eager:.4f}s")
    print(f"  Lazy Loading (Creation): {avg_lazy:.4f}s")
    print(f"  Lazy Loading (With Tools): {avg_lazy_access:.4f}s")

    if avg_eager > 0 and avg_lazy > 0:
        improvement = ((avg_eager - avg_lazy) / avg_eager) * 100
        print(f"  🎯 Startup Improvement: {improvement:.1f}% faster")

    return {
        "eager_times": eager_times,
        "lazy_times": lazy_times,
        "lazy_access_times": lazy_access_times,
        "avg_eager": avg_eager,
        "avg_lazy": avg_lazy,
        "avg_lazy_access": avg_lazy_access,
    }


def test_lazy_tool_loading():
    """Test individual lazy tool loading."""
    print("\n🔧 Testing Individual Lazy Tool Loading")
    print("=" * 50)

    from ultimate_discord_intelligence_bot.tools.lazy_loader import get_lazy_tool

    tool_names = ["MultiPlatformDownloadTool", "TwitchDownloadTool", "DiscordDownloadTool", "DriveUploadTool"]

    for tool_name in tool_names:
        print(f"\n📦 Testing {tool_name}")
        try:
            start_time = time.time()
            tool = get_lazy_tool(tool_name)
            load_time = time.time() - start_time

            print(f"  ✅ Loaded in {load_time:.4f}s")
            print(f"  📝 Tool name: {tool.name}")
            print(f"  📄 Description: {tool.description[:100]}...")

        except Exception as e:
            print(f"  ❌ Failed to load: {e}")


def test_tool_preloading():
    """Test tool preloading functionality."""
    print("\n⚡ Testing Tool Preloading")
    print("=" * 50)

    agent = LazyAcquisitionSpecialistAgent()

    print("📊 Preloading all tools...")
    start_time = time.time()
    results = agent.preload_tools()
    preload_time = time.time() - start_time

    print(f"⏱️  Preload completed in {preload_time:.4f}s")
    print(f"📈 Success rate: {sum(results.values())}/{len(results)} tools")

    for tool_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {tool_name}")

    # Get loading statistics
    stats = agent.get_tool_loading_stats()
    print("\n📊 Loading Statistics:")
    print(f"  Cached tools: {stats.get('total_cached', 0)}")
    print(f"  Import errors: {stats.get('total_errors', 0)}")

    if "loading_times" in stats:
        print(f"  Loading times: {stats['loading_times']}")


def test_memory_usage():
    """Test memory usage with lazy loading."""
    print("\n💾 Testing Memory Usage")
    print("=" * 50)

    try:
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Test eager loading memory
        print("📊 Testing Eager Loading Memory Usage")
        clear_lazy_cache()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        agent_eager = AcquisitionSpecialistAgent()
        tools_eager = agent_eager._tools
        eager_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"  Initial memory: {initial_memory:.1f} MB")
        print(f"  After eager loading: {eager_memory:.1f} MB")
        print(f"  Memory increase: {eager_memory - initial_memory:.1f} MB")

        # Test lazy loading memory
        print("\n⚡ Testing Lazy Loading Memory Usage")
        clear_lazy_cache()
        lazy_initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        agent_lazy = LazyAcquisitionSpecialistAgent()
        lazy_creation_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Access tools to trigger loading
        tools_lazy = agent_lazy.tools
        lazy_final_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"  Initial memory: {lazy_initial_memory:.1f} MB")
        print(f"  After lazy creation: {lazy_creation_memory:.1f} MB")
        print(f"  After tool access: {lazy_final_memory:.1f} MB")
        print(f"  Memory increase (creation): {lazy_creation_memory - lazy_initial_memory:.1f} MB")
        print(f"  Memory increase (total): {lazy_final_memory - lazy_initial_memory:.1f} MB")

        if eager_memory > lazy_creation_memory:
            memory_savings = eager_memory - lazy_creation_memory
            print(f"  🎯 Memory savings (creation): {memory_savings:.1f} MB")

    except ImportError:
        print("⚠️  psutil not available - skipping memory usage test")
    except Exception as e:
        print(f"❌ Memory test failed: {e}")


def main():
    """Main test function."""
    print("🧪 Lazy Loading System Test Suite")
    print("=" * 60)

    try:
        # Run benchmarks
        benchmark_results = benchmark_agent_creation()

        # Test individual tool loading
        test_lazy_tool_loading()

        # Test preloading
        test_tool_preloading()

        # Test memory usage
        test_memory_usage()

        # Get final statistics
        print("\n📊 Final Lazy Loader Statistics")
        print("=" * 50)
        final_stats = get_lazy_loader_stats()
        for key, value in final_stats.items():
            print(f"  {key}: {value}")

        print("\n✅ Lazy loading tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
