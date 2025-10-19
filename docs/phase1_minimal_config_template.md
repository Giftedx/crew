# Phase 1 Minimal Configuration Template

## Environment Variables Setup

Create a `.env` file in the project root with the following configuration:

```bash
# Ultimate Discord Intelligence Bot - Phase 1 Development Configuration
# This is a minimal configuration for Phase 1 testing and development

# ====== REQUIRED API KEYS ======
# Using development/mock values for Phase 1 testing
DISCORD_BOT_TOKEN=development-bot-token-placeholder
OPENAI_API_KEY=sk-development-key-placeholder
OPENROUTER_API_KEY=sk-development-openrouter-key-placeholder

# ====== SERVICE CONFIGURATION ======
# Using cloud services for Phase 1
QDRANT_URL=https://your-qdrant-cloud-instance.qdrant.tech
POSTGRES_URL=postgresql://user:password@your-postgres-host:5432/ultimate_discord_intelligence_bot
REDIS_URL=redis://your-redis-host:6379/0
MINIO_URL=https://your-minio-instance.com

# ====== ENVIRONMENT SETTINGS ======
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=true

# ====== PERFORMANCE SETTINGS ======
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
CACHE_TTL=3600

# ====== MONITORING SETTINGS ======
ENABLE_METRICS=true
ENABLE_TRACING=true
METRICS_PORT=9090

# ====== SECURITY SETTINGS ======
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# ====== OAUTH CONFIGURATION (OPTIONAL FOR PHASE 1) ======
# YouTube OAuth
YOUTUBE_CLIENT_ID=your-youtube-client-id
YOUTUBE_CLIENT_SECRET=your-youtube-client-secret

# Twitch OAuth
TWITCH_CLIENT_ID=your-twitch-client-id
TWITCH_CLIENT_SECRET=your-twitch-client-secret

# TikTok OAuth
TIKTOK_CLIENT_ID=your-tiktok-client-id
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret

# Instagram OAuth
INSTAGRAM_CLIENT_ID=your-instagram-client-id
INSTAGRAM_CLIENT_SECRET=your-instagram-client-secret

# X (Twitter) OAuth
X_CLIENT_ID=your-x-client-id
X_CLIENT_SECRET=your-x-client-secret

# ====== DISCORD INTEGRATION ======
# Discord webhooks for notifications
DISCORD_WEBHOOK=https://discord.com/api/webhooks/your-webhook-url
DISCORD_PRIVATE_WEBHOOK=https://discord.com/api/webhooks/your-private-webhook-url

# ====== PHASE 1 SPECIFIC SETTINGS ======
# Enable Phase 1 features
ENABLE_PHASE1_FEATURES=true
ENABLE_DEVELOPMENT_MODE=true
ENABLE_MOCK_SERVICES=true

# Development overrides
MOCK_LLM_RESPONSES=true
MOCK_VECTOR_STORE=true
MOCK_OAUTH_FLOWS=true
```

## Setup Instructions

### Step 1: Create Environment File

```bash
# Copy the template
cp .env.example .env

# Edit with your actual values
nano .env
```

### Step 2: Replace Placeholder Values

**Required for Basic Functionality:**

- `DISCORD_BOT_TOKEN`: Get from Discord Developer Portal
- `OPENAI_API_KEY`: Get from OpenAI Platform
- `QDRANT_URL`: Use Qdrant Cloud or local instance

**Optional for Full Functionality:**

- `OPENROUTER_API_KEY`: Alternative LLM provider
- Database URLs: PostgreSQL, Redis, MinIO
- OAuth credentials: For content platform access

### Step 3: Test Configuration

```bash
# Test environment setup
python3 scripts/setup_phase1_environment.py --check-only

# Test system health
make doctor
```

## Cloud Service Setup (Recommended)

### Qdrant Cloud

1. Go to <https://cloud.qdrant.io/>
2. Create a free account
3. Create a new cluster
4. Get the cluster URL
5. Set `QDRANT_URL` in your `.env` file

### Alternative: Local Qdrant

```bash
# Download and run Qdrant locally
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz | tar xz
./qdrant
```

## Development Mode Features

When `ENABLE_DEVELOPMENT_MODE=true`, the system will:

- Use mock responses for LLM calls
- Use mock vector store operations
- Skip OAuth authentication
- Enable additional logging
- Use development-friendly timeouts

This allows testing the system architecture without requiring actual API keys or external services.

## Next Steps

1. **Set up minimal configuration** (30 minutes)
2. **Test basic functionality** (15 minutes)
3. **Configure cloud services** (1 hour)
4. **Test end-to-end workflows** (30 minutes)

Total estimated time: 2-3 hours for basic Phase 1 setup.
