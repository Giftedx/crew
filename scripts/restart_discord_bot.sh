#!/bin/bash
# Restart Discord bot with telemetry properly disabled
# Created: 2025-10-06

set -euo pipefail

echo "🛑 Stopping existing Discord bot processes..."
pkill -f "ultimate_discord_intelligence_bot" || echo "   No existing processes found"
sleep 2

echo "🔧 Loading environment variables from .env..."
set -a
source /home/crew/.env
set +a

echo "✅ Telemetry flags:"
echo "   CREWAI_DISABLE_TELEMETRY=$CREWAI_DISABLE_TELEMETRY"
echo "   TELEMETRY_OPT_OUT=$TELEMETRY_OPT_OUT"
echo "   OTEL_SDK_DISABLED=$OTEL_SDK_DISABLED"
echo "   DO_NOT_TRACK=$DO_NOT_TRACK"

echo ""
echo "🚀 Starting Discord bot..."
cd /home/crew
python -m ultimate_discord_intelligence_bot.setup_cli run discord
