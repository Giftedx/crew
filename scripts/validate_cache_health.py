#!/usr/bin/env python3
"""Validate cache health and configuration.

This script checks the cache configuration, environment variables,
and runs integration tests to validate cache functionality.

Usage:
    python scripts/validate_cache_health.py
    python scripts/validate_cache_health.py --run-tests
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def check_environment() -> dict[str, str | bool]:
    """Check cache-related environment variables.

    Returns:
        Dict with environment variable status
    """
    required_vars = {
        "REDIS_URL": os.getenv("REDIS_URL"),
        "ENABLE_TOOL_RESULT_CACHING": os.getenv("ENABLE_TOOL_RESULT_CACHING", "true"),
        "CACHE_MEMORY_SIZE": os.getenv("CACHE_MEMORY_SIZE", "1000"),
    }

    return required_vars


def check_redis_connectivity() -> bool:
    """Check if Redis is available.

    Returns:
        True if Redis is reachable, False otherwise
    """
    try:
        result = subprocess.run(
            ["redis-cli", "PING"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and "PONG" in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_integration_tests() -> bool:
    """Run cache integration tests.

    Returns:
        True if tests passed, False otherwise
    """
    test_file = Path(__file__).parent.parent / "test_cache_integration.py"

    if not test_file.exists():
        print(f"  ⚠️  Test file not found: {test_file}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("  ✅ Integration tests PASSED")
            # Show summary lines
            for line in result.stdout.splitlines():
                if "PASSED" in line or "Summary" in line or "Tested Tools" in line or "✅" in line:
                    print(f"     {line}")
            return True
        else:
            print("  ❌ Integration tests FAILED")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("  ❌ Integration tests TIMED OUT")
        return False
    except Exception as e:
        print(f"  ❌ Failed to run integration tests: {e}")
        return False


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate cache health and configuration")
    parser.add_argument("--run-tests", action="store_true", help="Run integration tests")
    args = parser.parse_args()

    print("=" * 70)
    print("CACHE HEALTH CHECK")
    print("=" * 70)
    print()

    # Check environment
    print("🔍 Environment Configuration:")
    print("-" * 70)
    env_vars = check_environment()
    for var, value in env_vars.items():
        status = "✅" if value else "❌"
        display_value = value if value else "(not set)"
        print(f"  {status} {var}: {display_value}")
    print()

    # Check Redis connectivity
    print("📡 Redis Connectivity:")
    print("-" * 70)
    redis_ok = check_redis_connectivity()
    if redis_ok:
        print("  ✅ Redis is reachable (PING → PONG)")
    else:
        print("  ⚠️  Redis is not reachable (cache will use memory-only mode)")
    print()

    # Check cache implementation files
    print("📁 Cache Implementation:")
    print("-" * 70)
    cache_files = [
        "src/platform/cache/multi_level_cache.py",
        "src/platform/cache/tool_cache_decorator.py",
    ]

    all_files_exist = True
    for cache_file in cache_files:
        file_path = Path(__file__).parent.parent / cache_file
        if file_path.exists():
            print(f"  ✅ {cache_file}")
        else:
            print(f"  ❌ {cache_file} (missing)")
            all_files_exist = False
    print()

    # Check cached tools
    print("🛠️  Cached Tools:")
    print("-" * 70)
    cached_tools = [
        ("Tier 1", "SentimentTool", "src/domains/intelligence/analysis/sentiment_tool.py"),
        ("Tier 1", "EnhancedAnalysisTool", "src/domains/intelligence/analysis/enhanced_analysis_tool.py"),
        ("Tier 1", "TextAnalysisTool", "src/domains/intelligence/analysis/text_analysis_tool.py"),
        ("Tier 2", "EmbeddingService", "src/domains/memory/embedding_service.py"),
        ("Tier 2", "TranscriptIndexTool", "src/domains/ingestion/providers/transcript_index_tool.py"),
        ("Tier 2", "VectorSearchTool", "src/domains/memory/vector/vector_search_tool.py"),
    ]

    for tier, tool_name, tool_file in cached_tools:
        file_path = Path(__file__).parent.parent / tool_file
        if file_path.exists():
            # Check if file contains cache decorator
            with open(file_path) as f:
                content = f.read()
                has_cache = "@cache_tool_result" in content or "MultiLevelCache" in content
                status = "✅" if has_cache else "⚠️ "
                cache_status = "cached" if has_cache else "not cached"
                print(f"  {status} [{tier}] {tool_name} - {cache_status}")
        else:
            print(f"  ❌ [{tier}] {tool_name} - file not found")
    print()

    # Run integration tests if requested
    if args.run_tests:
        print("🧪 Running Integration Tests:")
        print("-" * 70)
        tests_passed = run_integration_tests()
        print()
    else:
        tests_passed = None

    # Summary
    print("=" * 70)
    cache_enabled = env_vars.get("ENABLE_TOOL_RESULT_CACHING", "true").lower() == "true"
    redis_status = "connected" if redis_ok else "disconnected (memory-only)"

    if cache_enabled and all_files_exist:
        print(f"✅ Cache system is CONFIGURED and ENABLED")
        print(f"   Redis: {redis_status}")
        print(f"   Memory cache size: {env_vars.get('CACHE_MEMORY_SIZE', '1000')}")

        if tests_passed is not None:
            if tests_passed:
                print("   Integration tests: ✅ PASSED")
            else:
                print("   Integration tests: ❌ FAILED")
        else:
            print("   Run with --run-tests to validate functionality")
    elif not cache_enabled:
        print("⚠️  Cache system is DISABLED")
        print("   Set ENABLE_TOOL_RESULT_CACHING=true to enable")
    else:
        print("❌ Cache system is INCOMPLETE")
        print("   Missing required files or configuration")

    print("=" * 70)


if __name__ == "__main__":
    main()
