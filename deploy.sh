#!/bin/bash

# Ultimate Discord Intelligence Bot - Deployment Script
# This script sets up and starts the bot with proper environment validation

set -e  # Exit on any error

echo "🚀 Ultimate Discord Intelligence Bot - Deployment Script"
echo "======================================================="

# Check if we're in the project directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Please create it first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -e ."
    exit 1
fi

source venv/bin/activate
echo "✅ Virtual environment activated"

# Check if dependencies are installed
echo "📋 Checking dependencies..."
if ! python -c "import crewai, discord, qdrant_client" 2>/dev/null; then
    echo "⚠️  Installing dependencies..."
    pip install -e .
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already satisfied"
fi

# Check environment file
echo "🔑 Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Checking for .env.template..."
    if [ -f ".env.template" ]; then
        echo "💡 Please copy .env.template to .env and configure your API keys:"
        echo "   cp .env.template .env"
        echo "   nano .env  # Add your API keys"
    else
        echo "❌ No environment template found. Please create .env with required variables."
    fi
    exit 1
fi

# Check required environment variables
echo "🔍 Validating environment variables..."
source .env

MISSING_VARS=()
if [ -z "$DISCORD_BOT_TOKEN" ]; then
    MISSING_VARS+=("DISCORD_BOT_TOKEN")
fi
if [ -z "$OPENAI_API_KEY" ] && [ -z "$OPENROUTER_API_KEY" ]; then
    MISSING_VARS+=("OPENAI_API_KEY or OPENROUTER_API_KEY")
fi
if [ -z "$QDRANT_URL" ]; then
    MISSING_VARS+=("QDRANT_URL")
fi

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '   - %s\n' "${MISSING_VARS[@]}"
    echo ""
    echo "💡 Please edit your .env file and add the missing variables."
    echo "   See SETUP_GUIDE.md for instructions on obtaining API keys."
    exit 1
fi

echo "✅ Environment validation passed"

# Check if Qdrant is accessible (if not :memory:)
if [ "$QDRANT_URL" != ":memory:" ] && [ "$QDRANT_URL" != "memory" ]; then
    echo "🔗 Testing Qdrant connection..."
    if python -c "
import os
from qdrant_client import QdrantClient
try:
    client = QdrantClient(url='$QDRANT_URL', api_key=os.getenv('QDRANT_API_KEY'))
    collections = client.get_collections()
    print('✅ Qdrant connection successful')
except Exception as e:
    print(f'⚠️  Qdrant connection warning: {e}')
    print('   The bot will still work but vector search may be limited')
"; then
        echo "✅ Qdrant connection verified"
    fi
else
    echo "ℹ️  Using in-memory Qdrant (data will not persist between restarts)"
fi

# Run tests to ensure everything works
echo "🧪 Running basic functionality tests..."
if python -c "
from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew
crew = UltimateDiscordIntelligenceBotCrew()
print(f'✅ CrewAI system loaded: {len(crew.agents)} agents, {len(crew.tasks)} tasks')
" 2>/dev/null; then
    echo "✅ Core system tests passed"
else
    echo "❌ Core system tests failed. Check your configuration."
    exit 1
fi

echo ""
echo "🎉 Deployment validation complete!"
echo "====================================="
echo ""

# Offer deployment options
echo "Choose how to start the bot:"
echo ""
echo "1) Discord Bot (recommended for interactive use)"
echo "   python start_bot.py"
echo ""
echo "2) CrewAI Analysis Pipeline (for batch processing)"  
echo "   python -m ultimate_discord_intelligence_bot.main run"
echo ""
echo "3) Content Ingestion (for processing specific URLs)"
echo "   python -m ingest <URL> --tenant default --workspace main"
echo ""
echo "4) FastAPI Server (for HTTP API access)"
echo "   python -m server.app"
echo ""

read -p "Enter your choice (1-4) or press Enter to start Discord bot: " choice
choice=${choice:-1}

case $choice in
    1)
        echo "🤖 Starting Discord bot..."
        python start_bot.py
        ;;
    2)
        echo "🔄 Starting CrewAI pipeline..."
        python -m ultimate_discord_intelligence_bot.main run
        ;;
    3)
        read -p "Enter URL to process: " url
        if [ -n "$url" ]; then
            echo "📥 Processing URL: $url"
            python -m ingest "$url" --tenant default --workspace main
        else
            echo "❌ No URL provided"
        fi
        ;;
    4)
        echo "🌐 Starting FastAPI server..."
        python -m server.app
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        ;;
esac
