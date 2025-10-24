#!/usr/bin/env python3
"""
Test runner for Discord AI integration tests.

This script runs all tests for the Discord AI components including unit tests,
integration tests, and performance tests.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=False, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ {description} failed with error: {e}")
        return False


def setup_test_environment():
    """Set up test environment."""
    print("🔧 Setting up test environment...")

    # Add src to Python path
    src_path = Path(__file__).parent / "performance_optimization" / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Set environment variables for testing
    os.environ["ENABLE_DISCORD_AI_RESPONSES"] = "true"
    os.environ["ENABLE_DISCORD_PERSONALITY_RL"] = "true"
    os.environ["ENABLE_DISCORD_MESSAGE_EVALUATION"] = "true"
    os.environ["ENABLE_DISCORD_OPT_IN_SYSTEM"] = "true"
    os.environ["ENABLE_DISCORD_CONVERSATIONAL_PIPELINE"] = "true"
    os.environ["ENABLE_PERSONALITY_ADAPTATION"] = "true"
    os.environ["ENABLE_REWARD_COMPUTATION"] = "true"
    os.environ["ENABLE_PERSONALITY_MEMORY"] = "true"
    os.environ["ENABLE_MCP_MEMORY"] = "true"
    os.environ["ENABLE_MCP_KG"] = "true"
    os.environ["ENABLE_MCP_CREWAI"] = "true"
    os.environ["ENABLE_MCP_ROUTER"] = "true"
    os.environ["ENABLE_MCP_CREATOR_INTELLIGENCE"] = "true"
    os.environ["ENABLE_MCP_OBS"] = "true"
    os.environ["ENABLE_MCP_INGEST"] = "true"
    os.environ["ENABLE_MCP_HTTP"] = "true"
    os.environ["ENABLE_MCP_A2A"] = "true"

    print("✅ Test environment setup complete")


def run_unit_tests():
    """Run unit tests."""
    return run_command("python -m pytest tests/unit/ -v --tb=short", "Unit Tests")


def run_integration_tests():
    """Run integration tests."""
    return run_command("python -m pytest tests/integration/ -v --tb=short", "Integration Tests")


def run_discord_ai_tests():
    """Run Discord AI specific tests."""
    return run_command(
        "python -m pytest tests/test_discord_ai_integration.py -v --tb=short", "Discord AI Integration Tests"
    )


def run_all_tests():
    """Run all tests."""
    return run_command("python -m pytest tests/ -v --tb=short", "All Tests")


def run_coverage_tests():
    """Run tests with coverage."""
    return run_command(
        "python -m pytest tests/ --cov=performance_optimization.src.discord --cov-report=html --cov-report=term-missing -v",
        "Coverage Tests",
    )


def run_performance_tests():
    """Run performance tests."""
    return run_command("python -m pytest tests/ -m performance -v --tb=short", "Performance Tests")


def run_specific_test(test_path):
    """Run a specific test file or test function."""
    return run_command(f"python -m pytest {test_path} -v --tb=short", f"Specific Test: {test_path}")


def lint_code():
    """Run code linting."""
    return run_command("python -m ruff check performance_optimization/src/discord/ tests/ --fix", "Code Linting")


def format_code():
    """Format code."""
    return run_command("python -m ruff format performance_optimization/src/discord/ tests/", "Code Formatting")


def type_check():
    """Run type checking."""
    return run_command("python -m mypy performance_optimization/src/discord/ --ignore-missing-imports", "Type Checking")


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Discord AI Test Runner")
    parser.add_argument(
        "test_type",
        nargs="?",
        choices=[
            "unit",
            "integration",
            "discord-ai",
            "all",
            "coverage",
            "performance",
            "lint",
            "format",
            "type",
            "specific",
        ],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument("--test-path", help="Path to specific test file or function (for 'specific' test type)")
    parser.add_argument("--setup-only", action="store_true", help="Only set up test environment without running tests")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    print("🤖 Discord AI Test Runner")
    print("=" * 60)

    # Set up test environment
    setup_test_environment()

    if args.setup_only:
        print("✅ Test environment setup complete. Exiting.")
        return 0

    # Run tests based on type
    success = True

    if args.test_type == "unit":
        success = run_unit_tests()
    elif args.test_type == "integration":
        success = run_integration_tests()
    elif args.test_type == "discord-ai":
        success = run_discord_ai_tests()
    elif args.test_type == "all":
        success = run_all_tests()
    elif args.test_type == "coverage":
        success = run_coverage_tests()
    elif args.test_type == "performance":
        success = run_performance_tests()
    elif args.test_type == "lint":
        success = lint_code()
    elif args.test_type == "format":
        success = format_code()
    elif args.test_type == "type":
        success = type_check()
    elif args.test_type == "specific":
        if not args.test_path:
            print("❌ --test-path is required for 'specific' test type")
            return 1
        success = run_specific_test(args.test_path)

    # Print summary
    print(f"\n{'=' * 60}")
    if success:
        print("✅ All tests completed successfully!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
