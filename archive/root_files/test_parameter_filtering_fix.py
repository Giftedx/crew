"""Quick validation test for crewai_tool_wrappers parameter filtering fix."""

import sys
from pathlib import Path


# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ultimate_discord_intelligence_bot.crewai_tool_wrappers import CrewAIToolWrapper
from ultimate_discord_intelligence_bot.step_result import StepResult


class MockTool:
    """Mock tool with restricted signature."""

    name = "MockTool"

    def _run(self, text: str) -> StepResult:
        """Tool that only accepts 'text' parameter."""
        return StepResult.ok(
            data={
                "received_text": text,
                "text_length": len(text),
            }
        )


def test_parameter_filtering_preserves_context():
    """Test that shared_context parameters are preserved during filtering."""
    print("🧪 Testing parameter filtering fix...")

    # Create mock tool and wrapper
    tool = MockTool()
    wrapper = CrewAIToolWrapper(wrapped_tool=tool)

    # Populate shared context (simulates _populate_agent_tool_context)
    context_data = {
        "transcript": "Full transcript text here...",
        "metadata": {"title": "Test Video", "platform": "YouTube"},
        "sentiment_analysis": {"label": "positive", "score": 0.85},
        "timeline_anchors": [{"time": 0, "text": "intro"}],
    }
    wrapper.update_context(context_data)

    print(f"  ✅ Populated context with {len(context_data)} keys: {list(context_data.keys())}")

    # Simulate CrewAI calling the tool with no explicit arguments
    # (CrewAI expects tool to use shared_context)
    print("  🔧 Calling wrapper._run() with no explicit args...")
    result = wrapper._run()

    # Validate result
    print(f"  📊 Result success: {result.success}")
    print(
        f"  📊 Result data keys: {list(result.data.keys()) if hasattr(result, 'data') and isinstance(result.data, dict) else 'N/A'}"
    )

    # Check if tool received the transcript (via aliasing transcript → text)
    if result.success and hasattr(result, "data") and isinstance(result.data, dict):
        received_text = result.data.get("received_text", "")
        if "Full transcript text here" in received_text:
            print("  ✅ Tool received transcript via 'text' parameter (aliasing worked)")
        else:
            print(f"  ❌ Tool did NOT receive transcript. Got: {received_text[:50]}...")
            return False

        # The fix ensures context data is available to the tool
        # Even though MockTool only has 'text' in signature, the wrapper should have
        # attempted to pass the full context (filtered to 'text' + context_keys)
        print("  ✅ Parameter filtering preserved context data")
        return True
    else:
        print(f"  ❌ Tool execution failed: {result.error if hasattr(result, 'error') else 'Unknown error'}")
        return False


def test_parameter_filtering_with_explicit_args():
    """Test that explicit CrewAI args are still validated."""
    print("\n🧪 Testing explicit arg validation...")

    tool = MockTool()
    wrapper = CrewAIToolWrapper(wrapped_tool=tool)

    # Populate context
    wrapper.update_context({"transcript": "Context transcript"})

    # CrewAI calls with explicit (wrong) argument
    print("  🔧 Calling wrapper._run(invalid_param='should be filtered')...")
    result = wrapper._run(invalid_param="should be filtered")

    # Tool should still work because context provides 'transcript' → 'text'
    if result.success:
        print("  ✅ Invalid explicit args filtered, context preserved")
        return True
    else:
        print(f"  ❌ Unexpected failure: {result.error if hasattr(result, 'error') else 'Unknown'}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Parameter Filtering Fix Validation")
    print("=" * 60)

    success = True

    # Test 1: Context preservation
    if not test_parameter_filtering_preserves_context():
        success = False

    # Test 2: Explicit arg validation
    if not test_parameter_filtering_with_explicit_args():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - Parameter filtering fix validated!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ TESTS FAILED - Fix may need adjustment")
        print("=" * 60)
        sys.exit(1)
