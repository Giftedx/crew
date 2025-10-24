from __future__ import annotations


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
        await bot.process_commands(message)


__all__ = ["register_events"]
