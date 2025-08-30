#!/usr/bin/env python3
"""
Discord Bot Startup Script for Ultimate Discord Intelligence Bot

This script provides a simple way to start the Discord bot with proper
environment configuration and error handling.
"""

import asyncio
import os
import sys
from pathlib import Path

from discord.ext import commands
from dotenv import load_dotenv

import discord

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("💡 Make sure to activate your virtual environment and install dependencies:")
    print("   source venv/bin/activate && pip install -e .")
    sys.exit(1)


def check_environment() -> bool:
    """Check if required environment variables are set."""
    load_dotenv()

    required_vars = {
        "DISCORD_BOT_TOKEN": "Discord bot token",
        "OPENAI_API_KEY": "OpenAI API key (or OPENROUTER_API_KEY)",
        "QDRANT_URL": "Qdrant vector database URL",
    }

    missing = []
    for var, description in required_vars.items():
        if var == "OPENAI_API_KEY":
            # Check if either OpenAI or OpenRouter key exists
            if not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")):
                missing.append(f"{var} (or OPENROUTER_API_KEY): {description}")
        elif not os.getenv(var):
            missing.append(f"{var}: {description}")

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Create a .env file with the required variables:")
        print("   cp .env.template .env")
        print("   # Then edit .env with your actual keys")
        return False

    return True


async def create_bot():
    """Create and configure the Discord bot."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True

    bot = commands.Bot(
        command_prefix="!",
        intents=intents,
        description="Ultimate Discord Intelligence Bot - Debate Analysis & Fact Checking"
    )

    # Initialize the CrewAI system
    crew_system = UltimateDiscordIntelligenceBotCrew()

    @bot.event
    async def on_ready():
        print(f"🤖 Bot logged in as {bot.user}")
        print(f"📊 Connected to {len(bot.guilds)} guilds")
        print("✅ Ultimate Discord Intelligence Bot is ready!")

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❓ Command not found. Use `!help` for available commands.")
        else:
            await ctx.send(f"❌ Error: {error}")
            print(f"Command error: {error}")

    @bot.command(name="analyze")
    async def analyze_content(ctx, *, url: str):
        """Analyze a video URL for debate content and fact-check claims."""
        await ctx.send(f"🔍 Starting analysis of: {url}")
        try:
            # Run the crew analysis
            inputs = {"url": url}
            crew_system.crew().kickoff(inputs=inputs)
            await ctx.send("✅ Analysis complete! Check results in processing logs.")
        except Exception as e:
            await ctx.send(f"❌ Analysis failed: {e}")

    @bot.command(name="status")
    async def bot_status(ctx):
        """Check bot status and system health."""
        await ctx.send("🟢 Bot is online and operational!")

    @bot.command(name="help_bot")
    async def help_command(ctx):
        """Show available commands."""
        embed = discord.Embed(
            title="🤖 Ultimate Discord Intelligence Bot",
            description="Debate analysis and fact-checking commands",
            color=0x00ff00
        )
        embed.add_field(
            name="Commands",
            value="""
`!analyze <url>` - Analyze video content
`!status` - Check bot status
`!help_bot` - Show this help message
            """,
            inline=False
        )
        await ctx.send(embed=embed)

    return bot


async def main():
    """Main entry point for the Discord bot."""
    print("🚀 Starting Ultimate Discord Intelligence Bot...")

    if not check_environment():
        sys.exit(1)

    print("✅ Environment variables validated")

    try:
        bot = await create_bot()
        token = os.getenv("DISCORD_BOT_TOKEN")
        await bot.start(token)
    except discord.LoginFailure:
        print("❌ Invalid Discord bot token")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)
