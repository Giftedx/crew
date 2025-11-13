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
        try:
            import sys

            sys.stdout.write(f"🤖 Scoped Discord Bot logged in as {bot.user}\n")
            sys.stdout.flush()
            sys.stdout.write(f"📊 Connected to {len(bot.guilds)} guilds\n")
            sys.stdout.flush()
            try:
                synced = await bot.tree.sync()
                sys.stdout.write(f"✅ Synced {len(synced)} scoped slash commands\n")
                sys.stdout.flush()
            except Exception as e:
                sys.stdout.write(f"⚠️ Could not sync slash commands: {e}\n")
                sys.stdout.flush()
            sys.stdout.write("✅ Scoped Discord Intelligence Bot ready!\n")
            sys.stdout.write("📋 Available command families: /system-*, !ops-*, !dev-*, !analytics-*\n")
            sys.stdout.flush()
        except Exception as e:
            print(f"❌ Error in on_ready: {e}")
            import traceback

            traceback.print_exc()

    @bot.event
    async def on_command_error(ctx, error):
        try:
            if isinstance(error, commands.CommandNotFound):
                return  # silently ignore unknown commands to preserve read-only posture
            await ctx.send(f"❌ Error: {error}")
            print(f"Command error: {error}")
        except Exception as e:
            print(f"❌ Error in on_command_error: {e}")

    @bot.event
    async def on_error(event, *_args, **_kwargs):
        """Catch-all error handler to prevent bot crashes."""
        import traceback

        print(f"❌ Error in event '{event}':")
        traceback.print_exc()

    @bot.event
    async def on_message(message):
        try:
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
        except Exception as e:
            print(f"❌ Error in on_message: {e}")
            import traceback

            traceback.print_exc()


__all__ = ["register_events"]
