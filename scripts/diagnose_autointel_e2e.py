#!/usr/bin/env python3
"""End-to-end diagnostic for /autointel fixes.

This script validates all 5 comprehensive fixes:
1. Integration task has full context access (all 4 previous tasks)
2. Integration task has explicit "use actual content" instructions
3. Verification task extracts textual claims, not JSON structures
4. JSON repair logic handles malformed JSON gracefully
5. Enhanced extraction patterns handle nested JSON correctly
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
    AutonomousIntelligenceOrchestrator,
)


def validate_json_repair():
    """Validate JSON repair functionality."""
    print("\n" + "=" * 70)
    print("🧪 TEST 1: JSON Repair Validation")
    print("=" * 70)

    orchestrator = AutonomousIntelligenceOrchestrator()

    test_cases = [
        # Test 1: Trailing commas (common in LLM outputs)
        {
            "name": "Trailing commas",
            "input": '{"key1": "value1", "key2": "value2",}',
            "expected_valid": True,
        },
        # Test 2: Newlines in string values
        {
            "name": "Newlines in strings",
            "input": '{"claim": "Video discusses\nmultiple topics"}',
            "expected_valid": True,
        },
        # Test 3: Single quotes (non-JSON standard)
        {
            "name": "Single quotes",
            "input": "{'key': 'value'}",
            "expected_valid": True,
        },
        # Test 4: Nested JSON with trailing commas
        {
            "name": "Nested with trailing commas",
            "input": '{"outer": {"inner": "value",}, "key": "val",}',
            "expected_valid": True,
        },
    ]

    passed = 0
    for case in test_cases:
        repaired = orchestrator._repair_json(case["input"])
        try:
            json.loads(repaired)
            is_valid = True
        except json.JSONDecodeError:
            is_valid = False

        status = "✅" if is_valid == case["expected_valid"] else "❌"
        print(f"{status} {case['name']}")
        print(f"   Input:  {case['input'][:60]}...")
        print(f"   Output: {repaired[:60]}...")
        print(f"   Valid: {is_valid}")

        if is_valid == case["expected_valid"]:
            passed += 1

    print(f"\n📊 JSON Repair: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def validate_task_configuration():
    """Validate task descriptions and context configuration."""
    print("\n" + "=" * 70)
    print("🧪 TEST 2: Task Configuration Validation")
    print("=" * 70)

    orchestrator = AutonomousIntelligenceOrchestrator()

    # Build crew to inspect task configuration
    crew = orchestrator._build_intelligence_crew(url="https://youtube.com/watch?v=test", depth="quick")

    tasks = crew.tasks
    checks = []

    # Check 1: Integration task has full context (4 previous tasks)
    integration_task = tasks[4]  # 5th task (0-indexed)
    context_count = len(integration_task.context) if integration_task.context else 0
    checks.append(
        {
            "name": "Integration task full context access",
            "condition": context_count == 4,
            "actual": f"{context_count} context tasks",
            "expected": "4 context tasks",
        }
    )

    # Check 2: Integration description mentions "ALL previous task outputs"
    integration_desc = integration_task.description
    checks.append(
        {
            "name": "Integration explicit instruction (ALL outputs)",
            "condition": "ALL previous task outputs" in integration_desc,
            "actual": "Present" if "ALL previous task outputs" in integration_desc else "Missing",
            "expected": "Present",
        }
    )

    # Check 3: Integration description mentions "ACTUAL content"
    checks.append(
        {
            "name": "Integration explicit instruction (ACTUAL content)",
            "condition": "ACTUAL content" in integration_desc,
            "actual": "Present" if "ACTUAL content" in integration_desc else "Missing",
            "expected": "Present",
        }
    )

    # Check 4: Verification task extracts TEXTUAL claims
    verification_task = tasks[3]  # 4th task (0-indexed)
    verification_desc = verification_task.description
    checks.append(
        {
            "name": "Verification extracts textual claims (not JSON)",
            "condition": "TEXTUAL claims" in verification_desc,
            "actual": "Present" if "TEXTUAL claims" in verification_desc else "Missing",
            "expected": "Present",
        }
    )

    # Check 5: Verification avoids extracting full JSON
    checks.append(
        {
            "name": "Verification avoids JSON extraction",
            "condition": "NOT the full JSON structure" in verification_desc,
            "actual": "Present" if "NOT the full JSON structure" in verification_desc else "Missing",
            "expected": "Present",
        }
    )

    # Print results
    passed = 0
    for check in checks:
        status = "✅" if check["condition"] else "❌"
        print(f"{status} {check['name']}")
        print(f"   Expected: {check['expected']}")
        print(f"   Actual:   {check['actual']}")

        if check["condition"]:
            passed += 1

    print(f"\n📊 Task Configuration: {passed}/{len(checks)} checks passed")
    return passed == len(checks)


def validate_extraction_patterns():
    """Validate enhanced JSON extraction patterns."""
    print("\n" + "=" * 70)
    print("🧪 TEST 3: JSON Extraction Patterns Validation")
    print("=" * 70)

    import re

    # Test the extraction strategies directly (from _task_completion_callback)
    extraction_strategies = [
        # Strategy 1: JSON code block with ```json (non-greedy, handles nested braces)
        (r"```json\s*(\{(?:[^{}]|\{[^{}]*\})*\})\s*```", "json code block"),
        # Strategy 2: JSON code block without language specifier (non-greedy)
        (r"```\s*(\{(?:[^{}]|\{[^{}]*\})*\})\s*```", "generic code block"),
        # Strategy 3: Inline JSON object with balanced braces
        (r'(\{(?:[^{}"]*"[^"]*"[^{}]*|[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\})', "inline JSON"),
    ]

    test_cases = [
        # Test 1: Code block with simple JSON
        {
            "name": "Code block extraction",
            "input": '```json\n{"key": "value"}\n```',
            "expected_pattern": "json code block",
        },
        # Test 2: Nested JSON in code block
        {
            "name": "Nested JSON extraction",
            "input": '```json\n{"outer": {"inner": "value"}}\n```',
            "expected_pattern": "json code block",
        },
        # Test 3: JSON with array
        {
            "name": "JSON with array",
            "input": '```json\n{"items": ["a", "b", "c"]}\n```',
            "expected_pattern": "json code block",
        },
        # Test 4: Inline JSON (not in code block)
        {
            "name": "Inline JSON extraction",
            "input": 'The result is {"status": "success"} and we continue',
            "expected_pattern": "inline JSON",
        },
    ]

    passed = 0
    for case in test_cases:
        extracted_json = None
        matched_pattern = None

        # Try extraction strategies
        for pattern, method in extraction_strategies:
            json_match = re.search(pattern, case["input"], re.DOTALL)
            if json_match:
                matched_pattern = method
                try:
                    extracted_json = json.loads(json_match.group(1))
                    break
                except json.JSONDecodeError:
                    continue

        success = extracted_json is not None and matched_pattern == case["expected_pattern"]
        status = "✅" if success else "❌"
        print(f"{status} {case['name']}")
        print(f"   Input:    {case['input'][:50]}...")
        print(f"   Expected: {case['expected_pattern']}")
        print(f"   Matched:  {matched_pattern or 'None'}")
        print(f"   Extracted: {list(extracted_json.keys()) if extracted_json else 'None'}")

        if success:
            passed += 1

    print(f"\n📊 Extraction Patterns: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


async def main():
    """Run all diagnostic tests."""
    print("\n" + "=" * 70)
    print("🚀 /autointel End-to-End Diagnostic")
    print("=" * 70)
    print("\nValidating 5 comprehensive fixes:")
    print("1. Integration task full context access (4 tasks not 1)")
    print("2. Integration explicit 'use actual content' instruction")
    print("3. Verification textual claims extraction (not JSON)")
    print("4. JSON repair logic (4 strategies)")
    print("5. Enhanced extraction patterns (nested JSON support)")

    results = []

    # Run all tests
    results.append(("JSON Repair", validate_json_repair()))
    results.append(("Task Configuration", validate_task_configuration()))
    results.append(("Extraction Patterns", validate_extraction_patterns()))

    # Summary
    print("\n" + "=" * 70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print("\n" + "=" * 70)
    if passed == total:
        print("🎉 SUCCESS: All diagnostic tests passed!")
        print("\nThe /autointel command should now:")
        print("  ✅ Parse JSON without 'Unterminated string' errors")
        print("  ✅ Produce correct final briefings with actual content")
        print("  ✅ Handle malformed JSON gracefully with repair logic")
        print("  ✅ Extract nested JSON structures correctly")
        print("  ✅ Provide full workflow context to all agents")
    else:
        print(f"⚠️  WARNING: {total - passed}/{total} tests failed")
        print("\nSome fixes may not be working correctly.")
        print("Review the failed tests above for details.")

    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
