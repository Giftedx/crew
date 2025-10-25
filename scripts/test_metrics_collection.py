#!/usr/bin/env python3
"""Test Metrics Collection System.

This script tests the metrics collection and observability infrastructure
by simulating tool usage and generating sample metrics.
"""

from __future__ import annotations

import random
import sys
import time
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.observability.metrics_collector import (
    generate_metrics_report,
    get_metrics_collector,
    record_tool_usage,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


def simulate_tool_usage(tool_name: str, num_calls: int = 10):
    """Simulate tool usage for testing metrics collection."""
    print(f"🔧 Simulating {num_calls} calls to {tool_name}...")

    for i in range(num_calls):
        # Simulate execution time
        execution_time = random.uniform(0.1, 2.0)
        time.sleep(execution_time * 0.1)  # Scale down for testing

        # Simulate success/failure
        success = random.random() > 0.1  # 90% success rate

        if success:
            result = StepResult.ok(message=f"Tool {tool_name} executed successfully")
        else:
            result = StepResult.fail(error=f"Tool {tool_name} failed with error")

        # Record metrics
        record_tool_usage(tool_name, execution_time, result)

        if i % 5 == 0:
            print(f"  📊 Completed {i + 1}/{num_calls} calls")


def test_metrics_collection():
    """Test the metrics collection system."""
    print("🚀 Testing Metrics Collection System")
    print("=" * 50)

    # Get metrics collector
    collector = get_metrics_collector()

    # Simulate usage for different tools
    tools_to_test = [
        ("AudioTranscriptionTool", 15),
        ("MultiPlatformDownloadTool", 20),
        ("UnifiedMemoryTool", 12),
        ("ContentQualityAssessmentTool", 18),
        ("FactCheckTool", 25),
        ("DebateAnalysisTool", 10),
        ("TimelineAnalysisTool", 8),
        ("NarrativeAnalysisTool", 6),
    ]

    print("📊 Simulating tool usage...")
    for tool_name, num_calls in tools_to_test:
        simulate_tool_usage(tool_name, num_calls)

    print("\n📈 Generating metrics report...")

    # Generate comprehensive report
    report = generate_metrics_report()

    print(f"📊 Report generated at: {report['timestamp']}")
    print(f"📊 Total tool calls: {report['total_tool_calls']:,}")
    print(f"📊 Active tools: {report['active_tools']}")
    print(f"📊 Average execution time: {report['average_execution_time']:.4f}s")

    # Display top tools
    print("\n🏆 Top Tools by Usage:")
    for i, tool in enumerate(report["top_tools"], 1):
        print(f"  {i}. {tool['tool_name']}: {tool['total_calls']} calls, {tool['success_rate'] * 100:.1f}% success")

    # Display slowest tools
    print("\n🐌 Slowest Tools:")
    for i, tool in enumerate(report["slowest_tools"], 1):
        print(f"  {i}. {tool['tool_name']}: {tool['average_execution_time']:.4f}s avg")

    # Display error-prone tools
    print("\n❌ Error-Prone Tools:")
    for i, tool in enumerate(report["error_prone_tools"], 1):
        error_rate = tool["failed_calls"] / tool["total_calls"] if tool["total_calls"] > 0 else 0
        print(f"  {i}. {tool['tool_name']}: {error_rate * 100:.1f}% error rate")

    # Export metrics
    export_file = f"test_metrics_{int(time.time())}.json"
    if collector.export_metrics(export_file):
        print(f"\n💾 Metrics exported to: {export_file}")
    else:
        print("\n❌ Failed to export metrics")

    print("\n✅ Metrics collection test completed")


def test_metrics_api():
    """Test the metrics API endpoints."""
    print("\n🌐 Testing Metrics API...")

    try:
        from ultimate_discord_intelligence_bot.observability.metrics_api import create_metrics_api

        # Create API instance
        create_metrics_api()
        print("✅ Metrics API created successfully")

        # Test API routes (without actually running the server)
        print("📊 Available API endpoints:")
        print("  • GET  /api/metrics/health - Health check")
        print("  • GET  /api/metrics/system - System metrics")
        print("  • GET  /api/metrics/tools - All tool metrics")
        print("  • GET  /api/metrics/tools/<name> - Specific tool metrics")
        print("  • GET  /api/metrics/top-tools - Top tools by usage")
        print("  • GET  /api/metrics/slowest-tools - Slowest tools")
        print("  • GET  /api/metrics/error-prone-tools - Error-prone tools")
        print("  • GET  /api/metrics/report - Comprehensive report")
        print("  • GET  /api/metrics/export - Export metrics")
        print("  • POST /api/metrics/reset - Reset metrics")

        print("✅ Metrics API test completed")

    except ImportError as e:
        print(f"⚠️  Metrics API not available: {e}")
        print("💡 Install Flask to enable metrics API: pip install flask")


def test_metrics_dashboard():
    """Test the metrics dashboard."""
    print("\n📊 Testing Metrics Dashboard...")

    try:
        from ultimate_discord_intelligence_bot.observability.metrics_collector import get_all_tool_metrics

        # Test dashboard functionality
        all_metrics = get_all_tool_metrics()
        print(f"📊 Found {len(all_metrics)} tools with metrics")

        if all_metrics:
            # Display sample metrics
            sample_tool = next(iter(all_metrics.values()))
            print("📊 Sample tool metrics:")
            print(f"  • Tool: {sample_tool.tool_name}")
            print(f"  • Total calls: {sample_tool.total_calls}")
            print(f"  • Success rate: {sample_tool.success_rate * 100:.1f}%")
            print(f"  • Average time: {sample_tool.average_execution_time:.4f}s")

        print("✅ Metrics dashboard test completed")

    except Exception as e:
        print(f"❌ Metrics dashboard test failed: {e}")


def main():
    """Main test function."""
    print("🧪 Metrics Collection System Test Suite")
    print("=" * 60)

    try:
        # Test metrics collection
        test_metrics_collection()

        # Test metrics API
        test_metrics_api()

        # Test metrics dashboard
        test_metrics_dashboard()

        print("\n🎉 All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
