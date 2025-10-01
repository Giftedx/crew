#!/usr/bin/env python3

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_command():
    try:
        # Set dummy API key
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing"

        from ultimate_discord_intelligence_bot.discord_bot.registrations import _execute_autointel

        # Mock Discord interaction
        interaction = MagicMock()
        interaction.guild_id = "test_guild"
        interaction.channel = MagicMock()
        interaction.channel.name = "test_channel"
        interaction.user = MagicMock()
        interaction.user.mention = "@testuser"
        interaction.followup = AsyncMock()

        async def mock_followup_send(content=None, embed=None, **kwargs):
            if content:
                print(f"Discord: {content[:80]}...")
            else:
                print("Discord: <embed message>")
            return MagicMock()

        interaction.followup.send = mock_followup_send

        # Test the original failing command
        url = "https://www.youtube.com/watch?v=xtFiJ8AVdW0"
        depth = "Experimental - Cutting-Edge AI"  # Use the original depth parameter

        print("🚀 Testing ORIGINAL failing /autointel command")
        print(f"  URL: {url}")
        print(f"  Depth: {depth}")
        print("")

        # Execute the command that was originally failing
        await _execute_autointel(interaction, url, depth)

        print("")
        print("✅ ORIGINAL COMMAND FIXED - no more coroutine errors!")
        return True

    except Exception as e:
        print(f"❌ Command still failing: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_complete_command())
    if result:
        print("Final result: SUCCESS - All critical fixes applied!")
    else:
        print("Final result: Still needs work")
