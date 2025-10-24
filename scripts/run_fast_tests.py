#!/usr/bin/env python3
"""Run fast test suite to ensure <5 second execution time."""

import subprocess
import sys
import time
from pathlib import Path


def run_fast_tests():
    """Run the fast test suite and measure execution time."""
    print("🚀 Running fast test suite...")
    print("Target: <5 seconds execution time")
    print("-" * 50)

    start_time = time.time()

    try:
        # Run fast tests
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/fast/test_minimal.py",
                "-v",
                "--tb=short",
                "--disable-warnings",
                "--maxfail=5",
                "-m",
                "fast",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        end_time = time.time()
        execution_time = end_time - start_time

        print(f"⏱️  Execution time: {execution_time:.2f} seconds")

        if execution_time < 5.0:
            print("✅ Fast test suite passed performance target!")
        else:
            print("❌ Fast test suite exceeded 5-second target")
            return False

        if result.returncode == 0:
            print("✅ All fast tests passed!")
            return True
        else:
            print("❌ Some fast tests failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("❌ Fast test suite timed out (>10 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error running fast tests: {e}")
        return False


def main():
    """Main function."""
    print("Fast Test Suite Runner")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("tests/fast").exists():
        print("❌ tests/fast directory not found")
        print("Please run this script from the project root")
        sys.exit(1)

    # Run fast tests
    success = run_fast_tests()

    if success:
        print("\n🎉 Fast test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Fast test suite failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
