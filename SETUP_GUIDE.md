# Ultimate Discord Intelligence Bot - Setup Guide

## 🎯 Quick Start

This guide will get you up and running with the Ultimate Discord Intelligence Bot in under 10 minutes.

## 📋 Prerequisites

- Python 3.10 or higher
- Git
- A Discord account and server where you can add bots

## ⚙️ Installation

### 1. Clone and Setup Environment

```bash
# If not already done
git clone <your-repo>
cd ultimate_discord_intelligence_bot

# Activate virtual environment (already exists)
source venv/bin/activate

# Dependencies should already be installed, but if needed:
pip install -e .
```

### 2. Create Environment Configuration

```bash
# Copy template and customize
cp .env.template .env
nano .env  # or your preferred editor
```

## 🔑 Required API Keys

### Discord Bot Token

1. Go to <https://discord.com/developers/applications>
2. Create New Application → Give it a name
3. Go to "Bot" section → Create Bot
4. Copy the Token → Add to `.env` as `DISCORD_BOT_TOKEN`
5. Enable "Message Content Intent" and "Server Members Intent"

### OpenAI API Key (Recommended)

1. Visit <https://platform.openai.com/api-keys>  
2. Create new API key
3. Add to `.env` as `OPENAI_API_KEY=sk-...`

**OR** Use OpenRouter (Alternative):

1. Visit <https://openrouter.ai/keys>
2. Create API key  
3. Add to `.env` as `OPENROUTER_API_KEY=sk-...`

### Qdrant Vector Database

#### Option 1: Local Docker (Easiest)

```bash
docker run -p 6333:6333 qdrant/qdrant
# Set QDRANT_URL=http://localhost:6333
```

#### Option 2: Qdrant Cloud

1. Visit <https://cloud.qdrant.io>
2. Create cluster → Get API key and URL
3. Add to `.env`:
   - `QDRANT_URL=https://your-cluster.qdrant.io`
   - `QDRANT_API_KEY=your-api-key`

### Discord Webhooks (Optional but recommended)

1. In your Discord server → Server Settings → Integrations → Webhooks
2. Create webhook for notifications → Copy URL
3. Add to `.env` as `DISCORD_WEBHOOK_URL`

## 🚀 Running the Bot

### Method 1: Simple Startup Script

```bash
# Make sure you're in venv
source venv/bin/activate

# Run the bot
python start_bot.py
```

### Method 2: CrewAI Pipeline (for content analysis)

```bash
# Analyze a video URL
python -m ultimate_discord_intelligence_bot.main run
```

### Method 3: Individual Components

```bash
# Content ingestion
python -m ingest https://youtube.com/watch?v=example --tenant default --workspace main

# Start FastAPI server
python -m server.app
```

## 🤖 Discord Commands

Once your bot is running, invite it to your server and try:


- `!analyze <youtube-url>` - Analyze video for debate content
- `!status` - Check bot status
- `!help_bot` - Show available commands

## 🔧 Troubleshooting

### "ModuleNotFoundError"

```bash
source venv/bin/activate
pip install -e .
```

### "Invalid Discord Token"

- Check your `.env` file has correct `DISCORD_BOT_TOKEN`
- Regenerate token in Discord Developer Portal if needed

### "Qdrant Connection Failed"
  
- If using Docker: `docker run -p 6333:6333 qdrant/qdrant`
- Check `QDRANT_URL` in `.env` file

### "OpenAI API Error"

- Verify `OPENAI_API_KEY` in `.env`
- Check your OpenAI account has credits
- Alternative: Use `OPENROUTER_API_KEY` instead

## 🎛️ Configuration

### Essential Settings (in .env)

```bash
# Required
DISCORD_BOT_TOKEN=your-bot-token
OPENAI_API_KEY=sk-your-key  # or OPENROUTER_API_KEY  
QDRANT_URL=http://localhost:6333

# Recommended  
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
ENABLE_DISCORD_COMMANDS=true
ENABLE_CONTENT_MODERATION=true
LOG_LEVEL=INFO
```

### Performance Tuning

```bash
MAX_WORKERS=4              # Parallel processing threads
VECTOR_BATCH_SIZE=100      # Vector operation batch size  
RATE_LIMIT_RPS=10         # API rate limiting
CACHE_TTL_SECONDS=3600    # Cache duration
```

## 🏗️ Architecture Overview

The system consists of:

- **CrewAI Agents**: Specialized AI agents for different tasks
- **Multi-platform Ingestion**: YouTube, Twitch, TikTok, Reddit support  
- **Vector Memory**: Qdrant-based semantic search
- **Discord Integration**: Bot commands and webhooks
- **Analysis Pipeline**: Fact-checking, debate analysis, trustworthiness scoring

## 📚 Next Steps

1. **Test the bot** with a simple YouTube URL
2. **Explore the tools** in `src/ultimate_discord_intelligence_bot/tools/`  
3. **Check the documentation** in `docs/` for advanced features
4. **Review the test suite** with `pytest` to understand functionality
5. **Customize agents** in `src/ultimate_discord_intelligence_bot/config/`

## 🆘 Getting Help

- Check the comprehensive documentation in `docs/`
- Review test files in `tests/` for usage examples
- Look at `AGENTS.md` for project overview and progress
- Examine `ARCHITECTURE.md` for system design details

## 🎉 Success

If you see "🟢 Bot is online and operational!" in Discord, you're ready to start analyzing content!

Try: `!analyze https://www.youtube.com/watch?v=dQw4w9WgXcQ`
