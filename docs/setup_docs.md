# Setup Docs

**Current Implementation** (verified November 3, 2025):

- **Tools**: 111 across 9 categories
- **Agents**: 18 specialized agents
- **Pipeline**: 7-phase orchestration
- **Services**: Discord bot, FastAPI server, CrewAI, MCP server

*This document consolidates multiple related files for better organization.*

## Setup Cli

# Setup & Run Wizard

The unified setup wizard configures everything you need (core + advanced) and writes/merges your `.env`, creates folders, and optionally scaffolds tenant files.

## Quick Start

- Run the wizard: `python -m ultimate_discord_intelligence_bot.setup_cli`
- Check health: `python -m ultimate_discord_intelligence_bot.setup_cli doctor`
- Run bot: `python -m ultimate_discord_intelligence_bot.setup_cli run discord`
- Run crew: `python -m ultimate_discord_intelligence_bot.setup_cli run crew`

Make shortcuts: `make setup`, `make doctor`, `make run-discord`, `make run-crew`.

## Prompts & Options

- Tokens: `DISCORD_BOT_TOKEN`, `DISCORD_WEBHOOK`, `DISCORD_PRIVATE_WEBHOOK`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `EXA_API_KEY`, `PERPLEXITY_API_KEY`.
  - Optional backends used by some tools: `SERPLY_API_KEY`, `WOLFRAM_ALPHA_APP_ID`.
- Vector DB: `QDRANT_URL` (default `http://localhost:6333`), `QDRANT_API_KEY`.
- Downloads: `DEFAULT_DOWNLOAD_QUALITY` (default `1080p`).
- Paths: `CREWAI_BASE_DIR`, `CREWAI_DOWNLOADS_DIR`, `CREWAI_CONFIG_DIR`, `CREWAI_LOGS_DIR`, `CREWAI_PROCESSING_DIR`, `CREWAI_YTDLP_DIR`.
- Google: `GOOGLE_CREDENTIALS` path.
- Feature flags: enable/disable ingestion (YouTube/Twitch/TikTok, `ENABLE_INGEST_CONCURRENT`), RAG/vector/grounding, caching, RL (global/routing/prompt/retrieval), Discord features, privacy/moderation/rate limiting, tracing/metrics/audit.
- HTTP & retries: `HTTP_TIMEOUT`, `ENABLE_HTTP_RETRY`, `RETRY_MAX_ATTEMPTS`.
- Tracing (optional): `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS`.
- Tenant scaffolding: `TENANT_SLUG`, guild id, `tenants/<slug>/routing.yaml` allowed models, budgets (`daily_cap_usd`, `max_per_request`), policy overrides (allowed sources). Files are written to `tenants/<slug>/`.
- Ingest DB (optional): `INGEST_DB_PATH` for provenance/usage logs.
- Discord upload limits (optional): `DISCORD_UPLOAD_LIMIT_BYTES`, `DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES`, and per‑guild overrides via `guild:bytes` CSV.

## Doctor Checks

- Ensures required env (at minimum `DISCORD_BOT_TOKEN`) is present.
- Verifies `ffmpeg` is installed (required). Warns if `yt-dlp` is missing (optional).

The wizard is safe to re-run; it merges updates without discarding existing values.

---

## Phase1 Environment Setup Guide

# Phase 1 Environment Setup Guide

## Current Status Assessment

Based on the Phase 1 environment setup report, here's what needs to be configured:

### ❌ Critical Issues (Must Fix)

1. **Missing Required Environment Variables**
   - `DISCORD_BOT_TOKEN` - Required for Discord bot functionality
   - `OPENAI_API_KEY` - Required for LLM functionality
   - `QDRANT_URL` - Required for vector database

2. **Service Dependencies Not Running**
   - Qdrant vector database (port 6333)
   - MinIO object storage (port 9000)
   - PostgreSQL database (port 5432)
   - Redis cache (port 6379)

3. **OAuth Configuration Missing**
   - All platform OAuth credentials (YouTube, Twitch, TikTok, Instagram, X)

### ⚠️ Optional Issues (Should Fix)

1. **Optional Environment Variables**
   - `OPENROUTER_API_KEY` - Alternative LLM provider
   - `POSTGRES_URL` - Database connection
   - `REDIS_URL` - Cache connection
   - `MINIO_URL` - Object storage connection

## Phase 1 Minimal Configuration

For Phase 1 implementation, we need to set up the minimal required configuration to get the system operational.

### Step 1: Environment Variables Setup

Create a `.env` file with the following minimal configuration:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your actual values
nano .env
```

**Required Variables:**

```bash
# Discord Bot Token (get from Discord Developer Portal)
DISCORD_BOT_TOKEN=your-actual-discord-bot-token

# OpenAI API Key (get from OpenAI Platform)
OPENAI_API_KEY=sk-your-actual-openai-key

# Qdrant Vector Database URL
QDRANT_URL=http://localhost:6333

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Optional Variables (for full functionality):**

```bash
# OpenRouter API Key (alternative LLM provider)
OPENROUTER_API_KEY=sk-your-openrouter-key

# Database URLs
POSTGRES_URL=postgresql://localhost:5432/ultimate_discord_intelligence_bot
REDIS_URL=redis://localhost:6379/0
MINIO_URL=http://localhost:9000

# OAuth Credentials (for content platform access)
YOUTUBE_CLIENT_ID=your-youtube-client-id
YOUTUBE_CLIENT_SECRET=your-youtube-client-secret
TWITCH_CLIENT_ID=your-twitch-client-id
TWITCH_CLIENT_SECRET=your-twitch-client-secret
TIKTOK_CLIENT_ID=your-tiktok-client-id
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret
INSTAGRAM_CLIENT_ID=your-instagram-client-id
INSTAGRAM_CLIENT_SECRET=your-instagram-client-secret
X_CLIENT_ID=your-x-client-id
X_CLIENT_SECRET=your-x-client-secret
```

### Step 2: Service Dependencies Setup

Since Docker is not available in this WSL environment, we have several options:

#### Option A: Use Cloud Services (Recommended for Phase 1)

- **Qdrant Cloud**: Use Qdrant's cloud service instead of local instance
- **PostgreSQL Cloud**: Use a cloud PostgreSQL service (AWS RDS, Google Cloud SQL, etc.)
- **Redis Cloud**: Use a cloud Redis service (AWS ElastiCache, Redis Cloud, etc.)

#### Option B: Install Services Locally

```bash
# Install Qdrant locally
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz | tar xz
./qdrant

# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install Redis
sudo apt install redis-server

# Install MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
./minio server /tmp/minio
```

#### Option C: Use Docker Desktop (if available)

```bash
# Start services with Docker Compose
docker-compose up -d qdrant postgres redis minio
```

### Step 3: OAuth Setup (Optional for Phase 1)

OAuth credentials are required for accessing content from external platforms. For Phase 1, we can proceed without them and add them later.

**To get OAuth credentials:**

1. Go to each platform's developer portal
2. Create a new application
3. Get the Client ID and Client Secret
4. Add them to your `.env` file

**Platforms:**

- YouTube: <https://console.developers.google.com/>
- Twitch: <https://dev.twitch.tv/console/apps>
- TikTok: <https://developers.tiktok.com/>
- Instagram: <https://developers.facebook.com/>
- X (Twitter): <https://developer.twitter.com/>

## Phase 1 Implementation Strategy

### Immediate Actions (Today)

1. **Set up minimal environment variables**
   - Discord Bot Token
   - OpenAI API Key
   - Qdrant URL (use cloud service)

2. **Configure cloud services**
   - Set up Qdrant Cloud account
   - Configure Qdrant URL in environment

3. **Test basic functionality**
   - Run doctor check
   - Test basic bot functionality

### Short-term Actions (This Week)

1. **Complete service setup**
   - Set up remaining cloud services
   - Configure all environment variables

2. **OAuth configuration**
   - Set up OAuth credentials for at least one platform
   - Test OAuth flows

3. **End-to-end testing**
   - Test complete workflows
   - Validate all integrations

## Testing the Setup

After configuration, test the setup:

```bash
# Test environment configuration
python3 scripts/setup_phase1_environment.py --check-only

# Test system health
make doctor

# Test basic functionality
python3 -m ultimate_discord_intelligence_bot.main --help
```

## Troubleshooting

### Common Issues

1. **"Connection refused" errors**
   - Services are not running
   - Check service status and start them

2. **"Module not found" errors**
   - Python path issues
   - Install dependencies: `pip install -r requirements.txt`

3. **"API key invalid" errors**
   - Check API key format and validity
   - Ensure keys are properly set in environment

4. **"OAuth authentication failed"**
   - Check OAuth credentials
   - Verify redirect URIs in platform settings

## Next Steps

Once the minimal configuration is working:

1. **Phase 1.2**: Set up SLO monitoring
2. **Phase 1.3**: Complete service integration
3. **Phase 1.4**: Production deployment
4. **Phase 1.5**: Performance optimization

---

**Status**: Ready for implementation
**Priority**: Critical
**Estimated Time**: 2-4 hours for minimal setup

---

## Monitoring Setup Report

# Monitoring Setup Report

## Setup Status

- **Prometheus Config**: ✅ Created
- **Grafana Datasource**: ✅ Created
- **Grafana Dashboard**: ✅ Created
- **Docker Compose**: ✅ Created
- **Alertmanager Config**: ✅ Created
- **Metrics Endpoint**: ✅ Tested

## Available Metrics

- `app_request_count_total`
- `app_request_latency_seconds`
- `app_error_count_total`
- `app_cache_hit_count_total`
- `app_cache_miss_count_total`
- `app_vector_search_latency_seconds`
- `app_mcp_tool_call_count_total`
- `app_oauth_token_refresh_count_total`
- `app_content_ingestion_count_total`
- `app_discord_message_count_total`
- `app_memory_store_count_total`
- `app_model_routing_count_total`

## SLOs Defined

- P95 latency < 2.0s
- Vector search latency < 0.05s
- Cache hit rate >= 60%
- Error rate < 1%

## Alerts Configured

- High error rate
- High latency
- Vector search latency
- Low cache hit rate
- OAuth token refresh failures
- MCP tool call failures
- Discord message failures
- Content ingestion failures
- Memory store failures
- Model routing failures

## Next Steps

1. Start monitoring stack: `docker-compose -f ops/monitoring/docker-compose.yml up -d`
2. Access Grafana: <http://localhost:3000> (admin/admin)
3. Access Prometheus: <http://localhost:9090>
4. Start metrics server: `python3 -m obs.metrics_endpoint`

---

## Installation

# Installation Guide

## Quick Start (Minimal Installation)

For basic functionality with core features:

```bash
pip install ultimate-discord-intelligence-bot
```

This installs only the essential dependencies for:

- Discord bot functionality
- Basic content analysis
- Vector storage with Qdrant
- Core AI/ML capabilities

## Full Installation

For complete functionality with all features:

```bash
pip install ultimate-discord-intelligence-bot[all]
```

This includes:

- All core features
- Machine learning capabilities
- Computer vision processing
- Advanced memory systems
- Development tools
- Documentation tools

## Specialized Installations

### Machine Learning Features

```bash
pip install ultimate-discord-intelligence-bot[ml]
```

Includes: PyTorch, Transformers, Scikit-learn, NumPy, Pandas

### Computer Vision Features

```bash
pip install ultimate-discord-intelligence-bot[vision]
```

Includes: OpenCV, Pillow, ImageIO, Scikit-image

### Advanced Memory Systems

```bash
pip install ultimate-discord-intelligence-bot[memory]
```

Includes: ChromaDB, Mem0, NetworkX, Neo4j

### Development Tools

```bash
pip install ultimate-discord-intelligence-bot[dev]
```

Includes: Pytest, Black, Ruff, MyPy, Pre-commit

### Documentation Tools

```bash
pip install ultimate-discord-intelligence-bot[docs]
```

Includes: MkDocs, MkDocs-Material, Mkdocstrings

## Environment Setup

1. **Create virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   # Minimal installation
   pip install ultimate-discord-intelligence-bot

   # Or full installation
   pip install ultimate-discord-intelligence-bot[all]
   ```

3. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Docker Installation

For containerized deployment:

```bash
# Build with minimal dependencies
docker build -t ultimate-discord-bot:minimal .

# Build with full dependencies
docker build -t ultimate-discord-bot:full --target full .
```

## System Requirements

### Minimal Installation

- Python 3.10+
- 2GB RAM
- 1GB disk space

### Full Installation

- Python 3.10+
- 8GB RAM (for ML models)
- 5GB disk space
- CUDA support (optional, for GPU acceleration)

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you have the correct optional dependencies installed
2. **Memory issues**: Use minimal installation for resource-constrained environments
3. **CUDA errors**: Install CPU-only versions of PyTorch if GPU is not available

### Getting Help

- Check the [Configuration Guide](configuration.md)
- Review [Troubleshooting Guide](troubleshooting.md)
- Join our Discord server for support

---

## Development Mode Setup Report

# Development Mode Setup Report

Generated: 2025-10-18 02:53:31 UTC

## Environment File

Status: healthy

- File exists: ✅
- File size: 2211 bytes

## Environment Variables

Status: healthy

- All required variables set: ✅

## Feature Flags

Status: healthy

- Enabled flags: 4
  - ENABLE_DISCORD_COMMANDS
  - ENABLE_CONTENT_MODERATION
  - ENABLE_VECTOR_SEARCH
  - ENABLE_LLM_CACHE

## Mock Services

Status: healthy

- Enabled mocks: 4
  - MOCK_LLM_RESPONSES
  - MOCK_VECTOR_STORE
  - MOCK_OAUTH_FLOWS
  - MOCK_DISCORD_API

---
