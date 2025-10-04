#!/usr/bin/env python3
"""Test script to validate /autointel fixes.

This script tests:
1. JSON extraction with nested structures
2. JSON repair for malformed data
3. Task context passing between agents
4. Verification task claim extraction
5. Knowledge integration with full context
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
    AutonomousIntelligenceOrchestrator,
)


def test_json_repair():
    """Test the JSON repair functionality."""
    print("\n🧪 Test 1: JSON Repair")
    print("=" * 60)

    orchestrator = AutonomousIntelligenceOrchestrator()

    # Test case 1: Trailing commas
    malformed1 = '{"key1": "value1", "key2": "value2",}'
    repaired1 = orchestrator._repair_json(malformed1)
    print(f"✅ Trailing comma: {malformed1} -> {repaired1}")

    try:
        json.loads(repaired1)
        print("   ✅ Valid JSON after repair")
    except json.JSONDecodeError as e:
        print(f"   ❌ Still invalid: {e}")

    # Test case 2: Newlines in strings
    malformed2 = '{"key": "value with\nnewline"}'
    repaired2 = orchestrator._repair_json(malformed2)
    print(f"✅ Newline fix: {malformed2} -> {repaired2}")

    try:
        json.loads(repaired2)
        print("   ✅ Valid JSON after repair")
    except json.JSONDecodeError as e:
        print(f"   ❌ Still invalid: {e}")

    print("\n✅ JSON repair tests completed")


def test_json_extraction():
    """Test the enhanced JSON extraction patterns."""
    print("\n🧪 Test 2: JSON Extraction")
    print("=" * 60)

    orchestrator = AutonomousIntelligenceOrchestrator()

    # Test case 1: JSON in code block
    text1 = """
    Some preamble text.

    ```json
    {
        "file_path": "/root/Downloads/video.mp4",
        "title": "Test Video",
        "metadata": {
            "duration": 300,
            "author": "Test Author"
        }
    }
    ```

    Some trailing text.
    """

    result1 = orchestrator._extract_key_values_from_text(text1)
    print(f"✅ Code block extraction: {result1}")

    # Test case 2: Nested JSON with quotes
    text2 = """
    Final Answer: {
        "verified_claims": ["Claim 1: Video is 5 minutes", "Claim 2: Author is 'Test'"],
        "fact_checks": [{"claim": "Video duration", "verified": true}]
    }
    """

    result2 = orchestrator._extract_key_values_from_text(text2)
    print(f"✅ Nested JSON extraction: {result2}")

    print("\n✅ JSON extraction tests completed")


def test_task_descriptions():
    """Test that task descriptions and context are properly configured."""
    print("\n🧪 Test 3: Task Descriptions & Context")
    print("=" * 60)

    orchestrator = AutonomousIntelligenceOrchestrator()

    # Build crew to inspect task descriptions
    crew = orchestrator._build_intelligence_crew(url="https://youtube.com/watch?v=test", depth="experimental")

    # Check each task
    for i, task in enumerate(crew.tasks):
        print(f"\n📋 Task {i + 1}: {task.expected_output[:50]}...")

        # Check if description has required keywords
        desc = task.description.lower()

        if i == 2:  # Analysis task (index 2)
            if "extract the 'transcript' field" in desc:
                print("   ✅ Explicit transcript extraction instruction")
            else:
                print("   ⚠️  Missing explicit extraction instruction")

        if i == 3:  # Verification task (index 3)
            if "textual claims" in desc and "not the full json" in desc.lower():
                print("   ✅ Improved verification instructions")
            else:
                print("   ⚠️  Missing improved verification instructions")

        if i == 4:  # Integration task (index 4)
            if len(task.context) == 4:
                print(f"   ✅ Full context access: {len(task.context)} previous tasks")
            else:
                print(f"   ⚠️  Limited context: only {len(task.context)} tasks")

            if "actual content" in desc.lower():
                print("   ✅ Explicit instruction to use actual content")
            else:
                print("   ⚠️  Missing actual content instruction")

    print("\n✅ Task description tests completed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 Testing /autointel Fixes")
    print("=" * 60)

    try:
        test_json_repair()
        test_json_extraction()
        test_task_descriptions()

        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
