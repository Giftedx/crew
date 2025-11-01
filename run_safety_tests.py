#!/usr/bin/env python3
"""Test runner for Discord AI safety and moderation system tests."""

import sys
from pathlib import Path

import pytest


SRC_PATH = Path(__file__).parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def run_safety_tests():
    """Run all safety-related tests."""
    print("🧪 Running Discord AI Safety System Tests")
    print("=" * 50)

    # Test file paths
    test_files = [
        "tests/test_discord_safety.py",
    ]

    # Run pytest with verbose output
    args = [
        "-v",  # Verbose output
        "-s",  # Don't capture output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "-x",  # Stop on first failure
    ]

    # Add test files
    args.extend(test_files)

    print(f"Running tests: {', '.join(test_files)}")
    print(f"Pytest arguments: {' '.join(args)}")
    print()

    # Run the tests
    exit_code = pytest.main(args)

    if exit_code == 0:
        print("\n✅ All safety tests passed!")
    else:
        print(f"\n❌ Some safety tests failed (exit code: {exit_code})")

    return exit_code


def run_quick_safety_tests():
    """Run quick safety tests (unit tests only)."""
    print("⚡ Running Quick Safety Tests (Unit Tests Only)")
    print("=" * 50)

    # Run only unit tests, skip integration tests
    args = [
        "-v",
        "-s",
        "--tb=short",
        "-x",
        "-m",
        "not integration",  # Skip integration tests
        "tests/test_discord_safety.py",
    ]

    print(f"Running quick tests with args: {' '.join(args)}")
    print()

    exit_code = pytest.main(args)

    if exit_code == 0:
        print("\n✅ All quick safety tests passed!")
    else:
        print(f"\n❌ Some quick safety tests failed (exit code: {exit_code})")

    return exit_code


def run_integration_tests():
    """Run integration tests only."""
    print("🔗 Running Safety Integration Tests")
    print("=" * 50)

    args = [
        "-v",
        "-s",
        "--tb=short",
        "-x",
        "-m",
        "integration",  # Only integration tests
        "tests/test_discord_safety.py",
    ]

    print(f"Running integration tests with args: {' '.join(args)}")
    print()

    exit_code = pytest.main(args)

    if exit_code == 0:
        print("\n✅ All safety integration tests passed!")
    else:
        print(f"\n❌ Some safety integration tests failed (exit code: {exit_code})")

    return exit_code


def run_specific_test_class(test_class: str):
    """Run tests for a specific test class."""
    print(f"🎯 Running {test_class} Tests")
    print("=" * 50)

    args = [
        "-v",
        "-s",
        "--tb=short",
        "-x",
        f"tests/test_discord_safety.py::{test_class}",
    ]

    print(f"Running {test_class} tests with args: {' '.join(args)}")
    print()

    exit_code = pytest.main(args)

    if exit_code == 0:
        print(f"\n✅ All {test_class} tests passed!")
    else:
        print(f"\n❌ Some {test_class} tests failed (exit code: {exit_code})")

    return exit_code


def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "quick":
            return run_quick_safety_tests()
        elif command == "integration":
            return run_integration_tests()
        elif command in ["content_filter", "rate_limiter", "moderation_alerts", "safety_manager"]:
            return run_specific_test_class(f"Test{command.replace('_', '').title()}")
        elif command == "help":
            print("Discord AI Safety Test Runner")
            print("=" * 30)
            print("Usage: python run_safety_tests.py [command]")
            print()
            print("Commands:")
            print("  (no args)     - Run all safety tests")
            print("  quick         - Run unit tests only (skip integration)")
            print("  integration   - Run integration tests only")
            print("  content_filter - Run content filter tests")
            print("  rate_limiter   - Run rate limiter tests")
            print("  moderation_alerts - Run moderation alerts tests")
            print("  safety_manager - Run safety manager tests")
            print("  help          - Show this help message")
            return 0
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' to see available commands")
            return 1
    else:
        return run_safety_tests()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
