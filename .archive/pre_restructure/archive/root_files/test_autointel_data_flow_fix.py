#!/usr/bin/env python3
"""Quick diagnostic test for /autointel data flow fix.

This script verifies that:
1. Agents are created once and cached
2. Context is populated and persists
3. Tools receive non-empty parameters
"""

import asyncio
import sys
from pathlib import Path


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
    AutonomousIntelligenceOrchestrator,
)


async def test_agent_caching():
    """Test that agents are created once and reused."""
    print("🧪 Testing agent caching mechanism...")

    orchestrator = AutonomousIntelligenceOrchestrator()

    # Get agent first time (should create)
    agent1 = orchestrator._get_or_create_agent("analysis_cartographer")
    print(f"✅ Created agent: {agent1}")

    # Get agent second time (should reuse)
    agent2 = orchestrator._get_or_create_agent("analysis_cartographer")
    print(f"✅ Retrieved agent: {agent2}")

    # Verify they're the same instance
    assert agent1 is agent2, "❌ FAIL: Agents are different instances!"
    print("✅ PASS: Same agent instance reused")

    # Verify it's cached
    assert "analysis_cartographer" in orchestrator.agent_coordinators
    print("✅ PASS: Agent is in coordinators cache")

    return True


async def test_context_population():
    """Test that context is populated and persists on tools."""
    print("\n🧪 Testing context population...")

    orchestrator = AutonomousIntelligenceOrchestrator()

    # Get agent
    agent = orchestrator._get_or_create_agent("analysis_cartographer")

    # Populate context
    test_context = {
        "transcript": "This is a test transcript with actual content",
        "text": "This is a test transcript with actual content",
        "media_info": {"title": "Test Video", "platform": "YouTube"},
    }

    orchestrator._populate_agent_tool_context(agent, test_context)
    print("✅ Populated context on agent")

    # Verify tools have context
    tools_with_context = 0
    for tool in agent.tools:
        if hasattr(tool, "_shared_context") and tool._shared_context:
            tools_with_context += 1
            # Check if transcript is in context
            if "transcript" in tool._shared_context:
                transcript = tool._shared_context["transcript"]
                print(f"✅ Tool {tool.name} has transcript: {len(transcript)} chars")

    assert tools_with_context > 0, "❌ FAIL: No tools have context!"
    print(f"✅ PASS: {tools_with_context} tools have populated context")

    return True


async def test_context_persistence():
    """Test that context persists across multiple agent retrievals."""
    print("\n🧪 Testing context persistence...")

    orchestrator = AutonomousIntelligenceOrchestrator()

    # Get agent and populate context
    agent1 = orchestrator._get_or_create_agent("analysis_cartographer")
    test_context = {"transcript": "Persistent test transcript"}
    orchestrator._populate_agent_tool_context(agent1, test_context)

    # Get agent again (should be same instance with same context)
    agent2 = orchestrator._get_or_create_agent("analysis_cartographer")

    # Verify context is still there
    has_context = False
    for tool in agent2.tools:
        if hasattr(tool, "_shared_context") and "transcript" in tool._shared_context:
            has_context = True
            print(f"✅ Context persisted: {tool._shared_context['transcript']}")
            break

    assert has_context, "❌ FAIL: Context not persisted!"
    print("✅ PASS: Context persisted across agent retrievals")

    return True


async def main():
    """Run all diagnostic tests."""
    print("=" * 60)
    print("🔬 /autointel Data Flow Fix - Diagnostic Tests")
    print("=" * 60)

    try:
        # Test 1: Agent caching
        await test_agent_caching()

        # Test 2: Context population
        await test_context_population()

        # Test 3: Context persistence
        await test_context_persistence()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Data flow fix is working!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
