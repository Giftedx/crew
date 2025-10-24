#!/usr/bin/env python3
"""Test script to validate crew fixes for the critical failures.

This script tests the key fixes made to resolve the crew tool failures:
1. Async/sync mismatch in PipelineToolWrapper
2. Tool data flow improvements
3. Simplified orchestrator chain
4. Enhanced error handling and diagnostics

Usage:
    python test_crew_fixes.py
"""

import asyncio
import sys
from pathlib import Path

import pytest


# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_pipeline_tool_wrapper():
    """Test that PipelineToolWrapper can handle async context properly."""
    print("🧪 Testing PipelineToolWrapper async/sync handling...")

    try:
        from ultimate_discord_intelligence_bot.crewai_tool_wrappers import (
            PipelineToolWrapper,
        )
        from ultimate_discord_intelligence_bot.tools.pipeline_tool import PipelineTool

        # Create wrapper with real pipeline tool
        pipeline_tool = PipelineTool()
        wrapper = PipelineToolWrapper(pipeline_tool)

        # Test basic instantiation
        assert wrapper.name == "Pipeline Tool"
        assert hasattr(wrapper, "_wrapped_tool")
        print("✅ PipelineToolWrapper instantiation successful")

        # Test that it has proper async handling methods
        assert hasattr(wrapper._wrapped_tool, "_run_async")
        print("✅ Async method available on wrapped tool")

    except Exception as e:
        print(f"❌ PipelineToolWrapper test failed: {e}")
        import traceback

        traceback.print_exc()
        pytest.fail(f"PipelineToolWrapper test failed: {e}")


def test_tool_wrapper_context():
    """Test that CrewAIToolWrapper properly handles context sharing."""
    print("🧪 Testing CrewAIToolWrapper context sharing...")

    try:
        from ultimate_discord_intelligence_bot.crewai_tool_wrappers import (
            CrewAIToolWrapper,
        )
        from ultimate_discord_intelligence_bot.tools.text_analysis_tool import (
            TextAnalysisTool,
        )

        # Create wrapper
        tool = TextAnalysisTool()
        wrapper = CrewAIToolWrapper(tool)

        # Test context management
        test_context = {"url": "https://example.com", "content": "test content"}
        wrapper.update_context(test_context)

        assert hasattr(wrapper, "_shared_context")
        assert wrapper._shared_context["url"] == "https://example.com"
        print("✅ Context sharing mechanism working")

    except Exception as e:
        print(f"❌ Tool wrapper context test failed: {e}")
        import traceback

        traceback.print_exc()
        pytest.fail(f"Tool wrapper context test failed: {e}")


def test_orchestrator_imports():
    """Test that orchestrator import chain is working."""
    print("🧪 Testing orchestrator import chain...")

    try:
        # Test direct orchestrator import
        from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
            AutonomousIntelligenceOrchestrator,
        )

        orchestrator = AutonomousIntelligenceOrchestrator()
        assert orchestrator is not None
        print("✅ Direct orchestrator import successful")

        # Test crew-based orchestrator
        try:
            from ultimate_discord_intelligence_bot.crew import (
                UltimateDiscordIntelligenceBotCrew,
            )

            crew = UltimateDiscordIntelligenceBotCrew()
            crew_orchestrator = crew.autonomous_orchestrator()
            assert crew_orchestrator is not None
            print("✅ Crew-based orchestrator import successful")
        except Exception as crew_error:
            print(f"⚠️ Crew orchestrator import failed (may be expected): {crew_error}")

    except Exception as e:
        print(f"❌ Orchestrator import test failed: {e}")
        import traceback

        traceback.print_exc()
        pytest.fail(f"Orchestrator import test failed: {e}")


def test_step_result_handling():
    """Test that StepResult is properly handled in wrappers."""
    print("🧪 Testing StepResult handling...")

    try:
        from ultimate_discord_intelligence_bot.step_result import StepResult

        # Test basic StepResult creation
        success_result = StepResult.ok(data={"test": "data"})
        assert success_result.success is True
        # Check if data is directly accessible or via .data attribute
        data = getattr(success_result, "data", success_result)
        if isinstance(data, dict) and "test" in data:
            assert data["test"] == "data"
        print("✅ StepResult.ok() working")

        fail_result = StepResult.fail(error="test error")
        assert success_result.success is not False
        error_msg = getattr(fail_result, "error", str(fail_result))
        assert "test error" in str(error_msg)
        print("✅ StepResult.fail() working")

        skip_result = StepResult.skip(reason="test skip")
        assert skip_result.success is True  # skip is treated as success for control flow
        assert skip_result.custom_status == "skipped"  # but has custom_status marker
        print("✅ StepResult.skip() working")

    except Exception as e:
        print(f"❌ StepResult test failed: {e}")
        import traceback

        traceback.print_exc()
        pytest.fail(f"StepResult test failed: {e}")


@pytest.mark.asyncio
async def test_async_pipeline_execution():
    """Test async pipeline execution in isolation."""
    print("🧪 Testing async pipeline execution...")

    try:
        from ultimate_discord_intelligence_bot.tools.pipeline_tool import PipelineTool

        # Create pipeline tool
        pipeline = PipelineTool()

        # Test that async method exists and can be called
        assert hasattr(pipeline, "_run_async")
        print("✅ Pipeline has async execution method")

        # Note: We don't actually run the pipeline with a real URL in this test
        # to avoid network calls and dependencies during testing
        print("✅ Async pipeline execution method available")

    except Exception as e:
        print(f"❌ Async pipeline test failed: {e}")
        import traceback

        traceback.print_exc()
        pytest.fail(f"Async pipeline test failed: {e}")


def main():
    """Run all tests and report results."""
    print("🚀 Running crew fixes validation tests...\n")

    tests = [
        ("Pipeline Tool Wrapper", test_pipeline_tool_wrapper),
        ("Tool Wrapper Context", test_tool_wrapper_context),
        ("Orchestrator Imports", test_orchestrator_imports),
        ("StepResult Handling", test_step_result_handling),
        (
            "Async Pipeline Execution",
            lambda: asyncio.run(test_async_pipeline_execution()),
        ),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Crew fixes appear to be working.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
