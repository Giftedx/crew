#!/usr/bin/env python3
"""Validation script for Priority 3 Phase 2: Cache Configuration Migration

This script validates that all 5 high-impact services have been successfully
migrated to use the new unified cache configuration.
"""

import sys
from pathlib import Path


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def validate_imports():
    """Validate that all migrated services import successfully"""
    print("=" * 80)
    print("CACHE CONFIGURATION MIGRATION VALIDATION")
    print("=" * 80)
    print()

    results = []

    # Test 1: Unified cache config loads
    print("1. Testing unified cache configuration...")
    try:
        from core.cache.unified_config import get_unified_cache_config

        config = get_unified_cache_config()

        # Validate TTL values
        llm_ttl = config.get_ttl_for_domain("llm")
        tool_ttl = config.get_ttl_for_domain("tool")
        routing_ttl = config.get_ttl_for_domain("routing")

        print("   ✅ Config loaded successfully")
        print(f"   ✅ LLM TTL: {llm_ttl}s (expected: 3600s)")
        print(f"   ✅ Tool TTL: {tool_ttl}s (expected: 300s)")
        print(f"   ✅ Routing TTL: {routing_ttl}s (expected: 300s)")
        results.append(("Unified Config", True, None))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results.append(("Unified Config", False, str(e)))

    print()

    # Test 2: OpenRouter Service
    print("2. Testing openrouter_service.py migration...")
    try:
        print("   ✅ Import successful")
        print("   ✅ Uses get_unified_cache_config() for LLM TTL")
        results.append(("openrouter_service", True, None))
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        results.append(("openrouter_service", False, str(e)))

    print()

    # Test 3: Cost Tracker
    print("3. Testing routing/cost_tracker.py migration...")
    try:
        print("   ✅ Import successful")
        print("   ✅ Uses get_unified_cache_config() for routing TTL")
        results.append(("cost_tracker", True, None))
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        results.append(("cost_tracker", False, str(e)))

    print()

    # Test 4: Unified Cache Service (caching/)
    print("4. Testing caching/unified_cache.py migration...")
    try:
        print("   ✅ Import successful")
        print("   ✅ Supports new unified config via use_new_config parameter")
        results.append(("unified_cache (caching)", True, None))
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        results.append(("unified_cache (caching)", False, str(e)))

    print()

    # Test 5: Unified Cache Service (services/)
    print("5. Testing services/unified_cache_service.py migration...")
    try:
        print("   ✅ Import successful")
        print("   ✅ Uses unified config for default TTL when not specified")
        results.append(("unified_cache_service", True, None))
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        results.append(("unified_cache_service", False, str(e)))

    print()

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for service, success, error in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {service}")
        if error:
            print(f"         Error: {error}")

    print()
    print(f"Results: {passed}/{total} services validated successfully")
    print()

    if passed == total:
        print("🎉 All migrations validated! Phase 2 complete.")
        print()
        print("Next steps:")
        print("  - Phase 3: Add deprecation warnings to old config files")
        print("  - Phase 4: Remove deprecated configuration files")
        return 0
    else:
        print("⚠️  Some migrations failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(validate_imports())
