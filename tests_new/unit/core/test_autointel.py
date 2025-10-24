#!/usr/bin/env python3
"""Test script to debug /autointel command issues."""

import asyncio
import logging
import os
import sys

import pytest


# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

logging.basicConfig(level=logging.DEBUG)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_autointel_workflow():
    """Test the autonomous intelligence workflow without Discord."""
    try:
        print("🔬 Testing autonomous intelligence workflow...")

        # Import dependencies
        from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
            AutonomousIntelligenceOrchestrator,
        )
        from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant

        print("✅ Imports successful")

        # Create tenant context
        tenant_ctx = TenantContext(tenant_id="test_guild", workspace_id="test_channel")
        print("✅ TenantContext created")

        # Test URL
        test_url = "https://www.youtube.com/watch?v=xtFiJ8AVdW0"

        # Create mock interaction object
        class MockInteraction:
            def __init__(self):
                self.messages = []

            async def followup_send(self, content=None, ephemeral=False, **kwargs):
                embeds = kwargs.get("embeds")
                if embeds is not None and not content:
                    summary = f"[Embeds x{len(embeds)}]"
                    print(f"📢 MOCK: {summary}")
                    self.messages.append({"embeds": embeds, "ephemeral": ephemeral})
                else:
                    message = content or str(kwargs)
                    print(f"📢 MOCK: {message}")
                    self.messages.append(message)
                return self

            async def edit_original_response(self, content):
                print(f"✏️  EDIT: {content}")
                return self

        mock_interaction = MockInteraction()
        # Add the methods the orchestrator expects
        mock_interaction.followup = type("obj", (object,), {"send": mock_interaction.followup_send})()

        # Execute workflow with tenant context
        with with_tenant(tenant_ctx):
            orchestrator = AutonomousIntelligenceOrchestrator()
            print("✅ AutonomousIntelligenceOrchestrator created")

            print("🚀 Starting workflow execution...")
            # Use a timeout to prevent hanging
            await asyncio.wait_for(
                orchestrator.execute_autonomous_intelligence_workflow(mock_interaction, test_url, "standard"),
                timeout=120.0,  # allow longer pipeline completion time for multi-agent analysis
            )
            print("✅ Workflow completed successfully!")

    except TimeoutError:
        print("⏰ Workflow timed out - this suggests a hanging operation")
        return False
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_autointel_workflow())
    sys.exit(0 if success else 1)
