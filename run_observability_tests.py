#!/usr/bin/env python3
"""
Test runner for Discord AI observability system.

This script runs comprehensive tests for all observability components
including metrics collection, conversation tracing, personality dashboard,
and integration.
"""

import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_observability_tests() -> int:
    """Run all observability tests."""
    print("🧪 Running Discord AI Observability Tests")
    print("=" * 50)

    # Test file paths
    test_files = ["tests/test_discord_observability.py"]

    # Run tests with verbose output
    args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker handling
        "--disable-warnings",  # Disable warnings for cleaner output
    ]

    # Add test files
    args.extend(test_files)

    print(f"Running tests: {', '.join(test_files)}")
    print()

    # Run pytest
    exit_code = pytest.main(args)

    if exit_code == 0:
        print("\n✅ All observability tests passed!")
        print("\n📊 Test Summary:")
        print("- DiscordMetricsCollector: ✓")
        print("- ConversationTracer: ✓")
        print("- PersonalityDashboard: ✓")
        print("- ObservabilityIntegration: ✓")
        print("- Integration Tests: ✓")
    else:
        print(f"\n❌ Some tests failed (exit code: {exit_code})")
        print("\n🔍 Check the output above for details on failed tests.")

    return int(exit_code)


def main() -> None:
    """Main entry point."""
    try:
        exit_code = run_observability_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
