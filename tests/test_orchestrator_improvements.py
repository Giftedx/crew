#!/usr/bin/env python3
"""Test script to verify autonomous orchestrator improvements."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


# Mock interaction object for testing
class MockChannel:
    def __init__(self):
        self.name = "test_channel"


class MockInteraction:
    def __init__(self):
        self.guild_id = "test_guild"
        self.channel = MockChannel()

    async def response_defer(self):
        print("✅ Response deferred")

    async def followup_send(self, content, ephemeral=False):
        print(f"📤 Followup: {content}")


async def test_autonomous_orchestrator():
    """Test the autonomous orchestrator with our improvements."""
    try:
        print("🔍 Testing Autonomous Orchestrator...")

        # Import with error handling
        try:
            from ultimate_discord_intelligence_bot.autonomous_orchestrator import AutonomousIntelligenceOrchestrator
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            return False

        # Initialize orchestrator
        print("🚀 Initializing orchestrator...")
        orchestrator = AutonomousIntelligenceOrchestrator()

        # Check system health
        print("🏥 System health check:")
        health = orchestrator.system_health
        print(f"   Healthy: {health['healthy']}")
        print(f"   Available capabilities: {health['available_capabilities']}")
        print(f"   Degraded capabilities: {health['degraded_capabilities']}")
        if health["warnings"]:
            for warning in health["warnings"]:
                print(f"   ⚠️  {warning}")
        if health["errors"]:
            for error in health["errors"]:
                print(f"   ❌ {error}")

        # Test workflow execution (simplified)
        print("🔧 Testing workflow execution...")
        interaction = MockInteraction()

        # This would normally fail due to missing dependencies, but should now degrade gracefully
        try:
            await orchestrator.execute_autonomous_intelligence_workflow(
                interaction=interaction, url="https://www.youtube.com/watch?v=xtFiJ8AVdW0", depth="standard"
            )
            print("✅ Workflow executed successfully (with degradation)")
        except Exception as e:
            print(f"❌ Workflow execution failed: {e}")
            return False

        print("✅ All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Ensure we're using the virtual environment
    if not os.path.exists(".venv"):
        print("❌ Virtual environment not found. Please run from project root.")
        sys.exit(1)

    # Set up environment
    os.environ.setdefault("PYTHONPATH", "/home/crew/src")

    success = asyncio.run(test_autonomous_orchestrator())
    sys.exit(0 if success else 1)
