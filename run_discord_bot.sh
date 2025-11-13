#!/bin/bash
cd /home/crew
source venv/bin/activate

# Trap signals to ensure clean shutdown
trap 'kill $PID; wait $PID' SIGTERM SIGINT

# Run bot in background and capture PID
python3 -m ultimate_discord_intelligence_bot.discord_bot.scoped &
PID=$!

# Wait for the bot process to finish
wait $PID
