from __future__ import annotations

import contextlib

try:
    from discord.ext import commands  # type: ignore
except Exception:  # pragma: no cover
    commands = None  # type: ignore


def register_events(bot_owner) -> None:
    bot = bot_owner.bot
    if not bot or commands is None:
        return

    @bot.event
    async def on_ready():
        print(f"🤖 Scoped Discord Bot logged in as {bot.user}")
        print(f"📊 Connected to {len(bot.guilds)} guilds")
        try:
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} scoped slash commands")
        except Exception as e:
            print(f"⚠️ Could not sync slash commands: {e}")
        print("✅ Scoped Discord Intelligence Bot ready!")
        print("📋 Available command families: /system-*, !ops-*, !dev-*, !analytics-*")

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return  # silently ignore unknown commands to preserve read-only posture
        await ctx.send(f"❌ Error: {error}")
        print(f"Command error: {error}")

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
        
        # Try to process through conversational pipeline (if enabled)
        try:
            from discord.bot_integration import get_pipeline_service
            
            # Only process if not a command
            content = getattr(message, "content", "") or ""
            if not content.startswith(("!", "/", "?")):  # Skip command prefixes
                pipeline_service = get_pipeline_service()
                result = await pipeline_service.process_discord_message(message)
                
                # If pipeline decided to respond, send the response
                if result.success and result.data and result.data.should_respond and result.data.response_content:
                    with contextlib.suppress(Exception):
                        await message.channel.send(result.data.response_content)
        except ImportError:
            # Pipeline service not available, skip
            pass
        except Exception as e:
            # Log error but don't break command processing
            print(f"⚠️ Conversational pipeline error: {e}")
        
        # Always process commands
        await bot.process_commands(message)


__all__ = ["register_events"]
