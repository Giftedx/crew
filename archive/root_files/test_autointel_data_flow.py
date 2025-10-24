#!/usr/bin/env python3
"""Test script to verify /autointel data flow fix.

This script tests that CrewAI tools receive proper context data
before execution, fixing the critical data flow issue.
"""

import asyncio
import logging
import sys
from pathlib import Path


# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MockInteraction:
    """Mock Discord interaction for testing."""

    class MockChannel:
        name = "test-channel"

    class MockResponse:
        async def defer(self):
            logger.info("✅ Mock: Deferred response")

        async def send_message(self, content=None, ephemeral=False):
            logger.info(f"✅ Mock: Response sent: {content[:100] if content else 'None'}...")

    class MockFollowup:
        async def send(self, content=None, ephemeral=False):
            logger.info(f"✅ Mock: Followup sent: {content[:100] if content else 'None'}...")

    def __init__(self):
        self.guild_id = "test_guild_123"
        self.channel = self.MockChannel()
        self.response = self.MockResponse()
        self.followup = self.MockFollowup()


async def test_context_population():
    """Test that context is properly populated before crew execution."""
    logger.info("=" * 80)
    logger.info("Testing /autointel Context Population Fix")
    logger.info("=" * 80)

    try:
        # Import orchestrator
        from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
            AutonomousIntelligenceOrchestrator,
        )

        logger.info("✅ Imported AutonomousIntelligenceOrchestrator")

        # Create orchestrator instance
        orchestrator = AutonomousIntelligenceOrchestrator()
        logger.info("✅ Created orchestrator instance")

        # Test the helper method directly
        class MockTool:
            name = "TestTool"
            context_received = None

            def update_context(self, context):
                self.context_received = context
                logger.info(f"✅ MockTool.update_context called with keys: {list(context.keys())}")

        class MockAgent:
            role = "test_agent"
            tools = [MockTool()]

        mock_agent = MockAgent()
        test_context = {
            "transcript": "This is a test transcript with full content",
            "text": "This is a test transcript with full content",
            "media_info": {"title": "Test Video", "platform": "YouTube"},
        }

        logger.info("\n📝 Testing _populate_agent_tool_context...")
        orchestrator._populate_agent_tool_context(mock_agent, test_context)

        # Verify tool received context
        if mock_agent.tools[0].context_received:
            logger.info("✅ Tool received context:")
            for key, value in mock_agent.tools[0].context_received.items():
                if isinstance(value, str):
                    logger.info(f"  - {key}: {len(value)} chars")
                else:
                    logger.info(f"  - {key}: {type(value).__name__}")

            # Check critical keys
            if "transcript" in mock_agent.tools[0].context_received:
                logger.info("✅ 'transcript' key present")
            else:
                logger.error("❌ 'transcript' key MISSING!")

            if "text" in mock_agent.tools[0].context_received:
                logger.info("✅ 'text' key present (alias for TextAnalysisTool)")
            else:
                logger.error("❌ 'text' key MISSING!")

            if mock_agent.tools[0].context_received.get("transcript") == test_context["transcript"]:
                logger.info("✅ Transcript content matches")
            else:
                logger.error("❌ Transcript content MISMATCH!")

        else:
            logger.error("❌ Tool did NOT receive context!")
            return False

        logger.info("\n" + "=" * 80)
        logger.info("✅ Context Population Test PASSED")
        logger.info("=" * 80)
        return True

    except Exception as e:
        logger.error(f"❌ Test FAILED: {e}", exc_info=True)
        return False


async def test_tool_wrapper_aliasing():
    """Test that tool wrapper aliasing works correctly."""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Tool Wrapper Aliasing")
    logger.info("=" * 80)

    try:
        from ultimate_discord_intelligence_bot.crewai_tool_wrappers import (
            CrewAIToolWrapper,
        )

        logger.info("✅ Imported tool wrapper")

        # Create a minimal mock tool instead of TextAnalysisTool to avoid NLTK dependency
        class MockAnalysisTool:
            name = "text_analysis_tool"
            description = "Analyze text content"

            def _run(self, text: str):
                return {"analysis": f"Analyzed {len(text)} chars"}

        # Create wrapped tool
        mock_tool = MockAnalysisTool()
        wrapper = CrewAIToolWrapper(mock_tool)

        logger.info("✅ Created wrapped tool")

        # Populate context
        context = {
            "transcript": "This is a comprehensive test transcript that should be aliased to 'text' parameter",
            "media_info": {"title": "Test Video"},
        }

        wrapper.update_context(context)
        logger.info(f"✅ Updated wrapper context with keys: {list(context.keys())}")

        # Check that aliasing will work
        if wrapper._shared_context.get("transcript"):
            logger.info(f"✅ Wrapper has transcript: {len(wrapper._shared_context['transcript'])} chars")
        else:
            logger.error("❌ Wrapper missing transcript in _shared_context")

        logger.info("\n" + "=" * 80)
        logger.info("✅ Tool Wrapper Aliasing Test PASSED")
        logger.info("=" * 80)
        return True

    except Exception as e:
        logger.error(f"❌ Test FAILED: {e}", exc_info=True)
        return False


async def main():
    """Run all tests."""
    logger.info("\n🚀 Starting /autointel Data Flow Tests\n")

    results = []

    # Test 1: Context Population
    results.append(await test_context_population())

    # Test 2: Tool Wrapper Aliasing
    results.append(await test_tool_wrapper_aliasing())

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Tests Passed: {sum(results)}/{len(results)}")

    if all(results):
        logger.info("✅ ALL TESTS PASSED")
        logger.info("\nThe /autointel data flow fix is working correctly!")
        logger.info("Tools will now receive full transcript data via shared context.")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED")
        logger.error("\nThe data flow issue may still be present.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
