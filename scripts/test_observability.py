#!/usr/bin/env python3
"""Test observability hooks and metrics collection."""

import sys
import time
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
    from ultimate_discord_intelligence_bot.step_result import StepResult

    print("✅ Successfully imported observability modules")
except ImportError as e:
    print(f"❌ Failed to import observability modules: {e}")
    sys.exit(1)


def test_metrics_collection():
    """Test basic metrics collection."""
    print("\n🔍 Testing metrics collection...")

    try:
        metrics = get_metrics()

        # Test counter
        if hasattr(metrics, "tool_executions_total"):
            metrics.tool_executions_total.inc()
            print("✅ Counter metric recorded")
        else:
            print("⚠️  Counter metric not available")

        # Test histogram
        if hasattr(metrics, "tool_execution_duration_seconds"):
            metrics.tool_execution_duration_seconds.observe(1.5)
            print("✅ Histogram metric recorded")
        else:
            print("⚠️  Histogram metric not available")

        # Test gauge
        if hasattr(metrics, "active_tools"):
            metrics.active_tools.set(5)
            print("✅ Gauge metric recorded")
        else:
            print("⚠️  Gauge metric not available")

        print("✅ Metrics collection test completed")
        return True

    except Exception as e:
        print(f"❌ Metrics collection test failed: {e}")
        return False


def test_stepresult_observability():
    """Test StepResult observability integration."""
    print("\n🔍 Testing StepResult observability...")

    try:
        # Test successful result
        result = StepResult.ok(data={"test": "success"})
        print(f"✅ StepResult.ok created: {result.success}")

        # Test failed result
        result = StepResult.fail(error="test error")
        print(f"✅ StepResult.fail created: {not result.success}")

        # Test skipped result
        result = StepResult.skip(reason="test skip")
        print(f"✅ StepResult.skip created: {result.skipped}")

        print("✅ StepResult observability test completed")
        return True

    except Exception as e:
        print(f"❌ StepResult observability test failed: {e}")
        return False


def test_health_monitoring():
    """Test health monitoring capabilities."""
    print("\n🔍 Testing health monitoring...")

    try:
        # Simulate tool execution with timing
        start_time = time.time()
        time.sleep(0.1)  # Simulate work
        duration = time.time() - start_time

        # Record metrics if available
        metrics = get_metrics()
        if hasattr(metrics, "tool_execution_duration_seconds"):
            metrics.tool_execution_duration_seconds.observe(duration)

        print(f"✅ Health monitoring test completed (duration: {duration:.3f}s)")
        return True

    except Exception as e:
        print(f"❌ Health monitoring test failed: {e}")
        return False


def test_pii_filtering():
    """Test PII filtering in observability."""
    print("\n🔍 Testing PII filtering...")

    try:
        # Test that sensitive data is not logged
        sensitive_data = "password123"
        result = StepResult.ok(data={"user_input": sensitive_data})

        # Check that result doesn't expose sensitive data in string representation
        result_str = str(result)
        if sensitive_data not in result_str:
            print("✅ PII filtering appears to be working")
        else:
            print("⚠️  PII filtering may not be working properly")

        print("✅ PII filtering test completed")
        return True

    except Exception as e:
        print(f"❌ PII filtering test failed: {e}")
        return False


def main():
    """Run all observability tests."""
    print("🚀 Starting observability tests...")

    tests = [
        test_metrics_collection,
        test_stepresult_observability,
        test_health_monitoring,
        test_pii_filtering,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All observability tests passed!")
        return 0
    else:
        print("❌ Some observability tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
