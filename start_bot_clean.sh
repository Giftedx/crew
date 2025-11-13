#!/bin/bash
# Start Discord bot with clean environment (no webhook placeholders)

# Unset problematic environment variables
unset DISCORD_WEBHOOK
unset DISCORD_PRIVATE_WEBHOOK

# Start the bot
cd /home/crew
exec /home/crew/venv/bin/python scripts/start_full_bot.py
