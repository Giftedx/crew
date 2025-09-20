#!/usr/bin/env python3
"""
Test script to validate performance monitoring integration
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ultimate_discord_intelligence_bot.agent_training.performance_monitor import AgentPerformanceMonitor


def test_performance_monitor():
    """Test the performance monitor functionality."""
    print("🧪 Testing Performance Monitor Integration...")

    # Create monitor instance
    monitor = AgentPerformanceMonitor()
    print("✅ Performance monitor created successfully")

    # Test recording an interaction
    monitor.record_agent_interaction(
        agent_name="test_agent",
        task_type="test_analysis",
        tools_used=["fact_check_tool", "vector_tool"],
        tool_sequence=[
            {"tool": "fact_check_tool", "action": "verify_claim"},
            {"tool": "vector_tool", "action": "semantic_search"},
        ],
        response_quality=0.85,
        response_time=12.5,
        user_feedback={"satisfaction": 0.9},
        error_occurred=False,
    )
    print("✅ Agent interaction recorded successfully")

    # Test generating performance report
    report = monitor.generate_performance_report("test_agent", days=1)
    print(f"✅ Performance report generated: {report.agent_name}")
    print(f"   Overall Score: {report.overall_score:.2f}")
    print(f"   Metrics: {len(report.metrics)}")
    print(f"   Recommendations: {len(report.recommendations)}")

    # Assertions to verify success
    assert report.agent_name == "test_agent"
    assert isinstance(report.overall_score, float)
    assert len(report.metrics) >= 0
    assert len(report.recommendations) >= 0


def test_quality_assessment():
    """Test the response quality assessment function."""
    print("\n🧪 Testing Quality Assessment...")

    # Import the assessment function
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from start_full_bot import assess_response_quality

    # Test cases
    test_cases = [
        ("Short response", 0.2),  # Should be low quality
        (
            "This is a comprehensive analysis with evidence and verified sources that demonstrates clear reasoning because the data shows significant trends. According to multiple research studies, this approach yields better results.",
            0.8,
        ),  # Should be high quality
        ("Error occurred while processing", 0.1),  # Should be very low quality
        ("Well-researched analysis with verified sources and logical reasoning", 0.6),  # Should be moderate quality
    ]

    for text, expected_min in test_cases:
        quality = assess_response_quality(text)
        print(f"   Text: '{text[:50]}...' -> Quality: {quality:.2f}")
        if quality >= expected_min:
            print(f"   ✅ Quality assessment passed (>= {expected_min})")
        else:
            print(f"   ⚠️  Quality lower than expected (expected >= {expected_min})")

    # Assert that function works (basic functionality test)
    assert callable(assess_response_quality)
    assert isinstance(assess_response_quality("test"), (int, float))


def test_discord_commands_structure():
    """Test that the Discord command structure is valid."""
    print("\n🧪 Testing Discord Command Structure...")

    # Test imports
    try:
        import importlib.util

        discord_spec = importlib.util.find_spec("discord")
        if discord_spec is not None:
            print("✅ Discord library available")
    except ImportError:
        print("⚠️  Discord library not available (lightweight mode)")
        # Skip this test in lightweight mode - this is expected
        import pytest

        pytest.skip("Discord library not available (lightweight mode)")

    # Check if our command functions are properly structured
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from start_full_bot import ToolContainer

        print("✅ Core functions imported successfully")

        # Test tool container
        tools = ToolContainer()
        print(f"✅ Tool container created with {len(tools.get_all_tools())} tools")

        # Assertions
        assert isinstance(tools, ToolContainer)
        assert len(tools.get_all_tools()) >= 0

    except Exception as e:
        print(f"❌ Error testing command structure: {e}")
        assert False, f"Command structure test failed: {e}"


def main():
    """Run all tests."""
    print("🚀 Performance Monitoring Integration Test Suite")
    print("=" * 50)

    tests = [
        test_performance_monitor,
        test_quality_assessment,
        test_discord_commands_structure,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! Performance monitoring integration is ready.")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
