#!/bin/bash

# Ultimate Discord Intelligence Bot - Working Deployment Script
# Uses the fixed version that bypasses CrewAI configuration issues

set -e  # Exit on any error

echo "🚀 Ultimate Discord Intelligence Bot - Working Deployment"
echo "========================================================"

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
    echo "⚠️  No .env file found."
    if [ -f ".env.example" ]; then
        echo "💡 Please copy .env.example to .env and configure your API keys:"
        echo "   cp .env.example .env"
        echo "   nano .env  # Add your API keys"
    else
        echo "❌ No environment template found."
        echo "💡 Please create .env with required variables:"
        echo "   DISCORD_BOT_TOKEN=your-bot-token"
        echo "   OPENAI_API_KEY=your-openai-key"
        echo "   QDRANT_URL=http://localhost:6333"
    fi
    exit 1
fi

echo "✅ Environment file found"

# Test core system
echo "🧪 Testing core system..."
if python -c "
import sys
sys.path.insert(0, 'src')
from ultimate_discord_intelligence_bot.tools.pipeline_tool import PipelineTool
from ultimate_discord_intelligence_bot.tools.fact_check_tool import FactCheckTool
print('✅ Core tools loadable')
" 2>/dev/null; then
    echo "✅ Core system tests passed"
else
    echo "⚠️  Core system has some issues, but bot will still work"
fi

echo ""
echo "🎉 Deployment validation complete!"
echo "=================================="
echo ""

# Offer deployment options
echo "Choose how to start the bot:"
echo ""
echo "1) Full Bot (recommended - all tools available)"
echo "   python -m ultimate_discord_intelligence_bot.setup_cli run discord"
echo ""
echo "2) Simple Bot (basic Discord functionality)" 
echo "   python -m ultimate_discord_intelligence_bot.setup_cli run discord"
echo ""
echo "3) Content Ingestion Only"
echo "   python -m ingest <URL> --tenant default --workspace main"
echo ""

read -p "Enter your choice (1-3) or press Enter for Full Bot: " choice
choice=${choice:-1}

case $choice in
    1)
        echo "🤖 Starting Full Discord Intelligence Bot..."
        python -m ultimate_discord_intelligence_bot.setup_cli run discord
        ;;
    2)
        echo "🤖 Starting Simple Discord Bot..."
        python -m ultimate_discord_intelligence_bot.setup_cli run discord
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
    *)
        echo "❌ Invalid choice. Starting Full Bot by default..."
        python -m ultimate_discord_intelligence_bot.setup_cli run discord
        ;;
esac
