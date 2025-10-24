# 🚀 Ultimate Discord Intelligence Bot - Complete System Guide

## Quick Access Scripts

I've created 4 powerful scripts to help you manage the entire system:

### 1. 🎮 Interactive Service Manager (RECOMMENDED)

```bash
./manage-services.sh
```

**Full-featured menu for all operations:**

- Start/Stop individual or all services
- Monitor status and logs
- Run health checks
- Development tools (tests, linting)
- Documentation access
- Troubleshooting help

### 2. 🚀 Start All Services

```bash
./start-all-services.sh
```

**Interactive startup wizard:**

- Validates environment
- Checks dependencies
- Starts selected services
- Shows status and next steps

### 3. 📊 Check Status

```bash
./check-status.sh
```

**Comprehensive system overview:**

- Running services
- Port status
- Configuration validation
- Recent activity

### 4. 🛑 Stop All Services

```bash
./stop-all-services.sh
```

**Clean shutdown of all services**

---

## System Architecture

### Core Services

1. **Discord Bot** - Main intelligence pipeline
   - Downloads content from multiple platforms
   - Transcribes audio/video
   - Analyzes content with LLMs
   - Stores memories in vector DB
   - Posts results to Discord

2. **FastAPI Server** - HTTP API + A2A endpoints
   - REST API for content processing
   - A2A JSON-RPC adapter
   - Prometheus metrics endpoint
   - Health checks

3. **CrewAI** - Autonomous agent orchestration
   - Multi-agent task execution
   - Research and analysis workflows
   - Automatic task planning

4. **MCP Server** - Model Context Protocol server
   - Tool access for AI agents
   - Memory management
   - Observability integration

### Infrastructure Services (Docker)

- **Qdrant** (port 6333) - Vector database
- **Redis** (port 6379) - Caching layer
- **PostgreSQL** (port 5432) - Metadata storage
- **MinIO** (port 9000/9001) - Object storage
- **Prometheus** (port 9090) - Metrics
- **Grafana** (port 3000) - Dashboards
- **Alertmanager** (port 9093) - Alerts

---

## First Time Setup (5 Minutes)

### Step 1: Environment Setup

```bash
# Option A: Interactive manager (recommended)
./manage-services.sh
# Select option 1 or run quick start

# Option B: Direct startup
./start-all-services.sh
```

This will:

1. Create Python virtual environment (`.venv/`)
2. Install all dependencies
3. Create `.env` file from template
4. Run system health check

### Step 2: Configure API Keys

Edit `.env` file and set these required values:

```bash
# Required - Get from Discord Developer Portal
DISCORD_BOT_TOKEN=your-actual-discord-bot-token

# Required - Choose one:
OPENROUTER_API_KEY=your-openrouter-api-key
# OR
OPENAI_API_KEY=your-openai-api-key

# Optional - For advanced features:
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
```

### Step 3: Start Services

```bash
# Interactive menu (easiest)
./manage-services.sh

# Or specific service:
./start-all-services.sh
# Then select option:
#   2 = Discord Bot Enhanced (RECOMMENDED)
#   5 = All local services
#   6 = Full stack with Docker
```

### Step 4: Verify

```bash
./check-status.sh
```

---

## Running Options

### Development Mode (No Docker Required)

Perfect for local development without external services:

```bash
# Services use in-memory storage
export ENABLE_DEVELOPMENT_MODE=true
export QDRANT_URL=":memory:"

./start-all-services.sh
```

### Production Mode (Docker Required)

Full infrastructure with all services:

```bash
cd ops/deployment/docker
docker-compose up -d

# Or use the manager
./manage-services.sh
# Select option 8
```

### Enhanced Mode (AI Features)

Discord bot with all AI enhancements enabled:

```bash
make run-discord-enhanced

# Or
./manage-services.sh
# Select option 3
```

This enables:

- Semantic caching
- Prompt compression
- Graph memory
- HippoRAG continual memory

---

## Common Tasks

### Process a Video via Discord

1. Start Discord bot:

   ```bash
   ./manage-services.sh  # Option 2 or 3
   ```

2. In Discord channel, send:

   ```
   !analyze https://youtube.com/watch?v=VIDEO_ID
   ```

3. Bot will:
   - Download video
   - Transcribe audio
   - Analyze content
   - Store in memory
   - Post summary to Discord

### Use HTTP API

```bash
# Start API server
./manage-services.sh  # Option 4

# Process content
curl -X POST http://localhost:8080/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=...", "quality": "1080p"}'

# A2A JSON-RPC
curl -X POST http://localhost:8080/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "summarize",
    "params": {"text": "Your text here"},
    "id": 1
  }'
```

### Run Autonomous Intelligence

```bash
# Start CrewAI
./manage-services.sh  # Option 5

# Use via API
curl -X POST http://localhost:8080/autointel \
  -H "Content-Type: application/json" \
  -d '{"task": "Research latest AI developments and create a brief"}'
```

---

## Monitoring & Debugging

### View Logs

```bash
# All services
tail -f logs/services/*.log

# Specific service
tail -f logs/services/discord-bot.log

# Via manager
./manage-services.sh  # Option 11
```

### Check Health

```bash
# Comprehensive check
make doctor

# Via manager
./manage-services.sh  # Option 10

# Quick status
./check-status.sh
```

### View Metrics

```bash
# Prometheus
./manage-services.sh  # Option 12
# Opens http://localhost:9090

# Grafana
./manage-services.sh  # Option 13
# Opens http://localhost:3000 (admin/admin)
```

---

## Development Workflow

### Daily Development

```bash
# Quick feedback loop (~8 seconds)
make quick-check

# Full validation
make full-check

# Via manager
./manage-services.sh  # Options 16 or 17
```

### Running Tests

```bash
# Fast tests
make test-fast

# All tests
make test

# Via manager
./manage-services.sh  # Option 18
```

### Code Quality

```bash
# Format code
make format

# Lint
make lint

# Type check
make type

# All guards
make guards
```

---

## Troubleshooting

### Common Issues

#### 1. Module not found errors

```bash
# Recreate environment
make first-run
source .venv/bin/activate
```

#### 2. Docker not available (WSL)

Enable Docker Desktop WSL integration, OR use development mode:

```bash
export ENABLE_DEVELOPMENT_MODE=true
export QDRANT_URL=":memory:"
./start-all-services.sh
```

#### 3. API key errors

```bash
make doctor  # Shows what's missing
vim .env     # Edit configuration
```

#### 4. Port already in use

```bash
# Find and kill process
lsof -ti:8080 | xargs kill -9

# Or use different port
uvicorn server.app:app --port 8081
```

#### 5. Service won't start

```bash
# Check status
./check-status.sh

# View logs
tail -f logs/services/*.log

# Check errors
make doctor
```

#### 6. Import errors in tests

```bash
# Ensure PYTHONPATH is set (automatic via pytest.ini)
PYTHONPATH=src pytest

# Or use make
make test
```

---

## Feature Flags

Edit `.env` to enable/disable features:

### Essential Features

```bash
ENABLE_SEMANTIC_CACHE=true           # LLM response caching
ENABLE_PROMPT_COMPRESSION=true       # Reduce token usage
ENABLE_GRAPH_MEMORY=true            # GraphRAG-style memory
ENABLE_HIPPORAG_MEMORY=true         # Continual learning
```

### APIs & Routing

```bash
ENABLE_A2A_API=true                 # A2A JSON-RPC adapter
ENABLE_BANDIT_ROUTING=true          # Multi-armed bandit routing
ENABLE_CONTEXTUAL_BANDIT=true       # Contextual bandit (LinUCB)
```

### Monitoring

```bash
ENABLE_PROMETHEUS_ENDPOINT=true     # /metrics endpoint
ENABLE_HTTP_METRICS=true            # HTTP request metrics
ENABLE_TRACING=true                 # Distributed tracing
```

### Development

```bash
DEBUG=true                          # Verbose logging
LOG_LEVEL=DEBUG                     # Debug log level
ENABLE_DEVELOPMENT_MODE=true        # Mock services
```

---

## Key Commands Reference

| Task | Command |
|------|---------|
| **Service Manager** | `./manage-services.sh` |
| **Start Services** | `./start-all-services.sh` |
| **Check Status** | `./check-status.sh` |
| **Stop Services** | `./stop-all-services.sh` |
| **Quick Check** | `make quick-check` |
| **Full Check** | `make full-check` |
| **Run Tests** | `make test` |
| **Health Check** | `make doctor` |
| **Discord Bot** | `make run-discord` |
| **Discord Bot Enhanced** | `make run-discord-enhanced` |
| **API Server** | `python -m uvicorn server.app:app --reload` |
| **CrewAI** | `make run-crew` |
| **View Logs** | `tail -f logs/services/*.log` |
| **Format Code** | `make format` |
| **Lint Code** | `make lint` |
| **Clean Build** | `make clean` |

---

## Project Structure

```
crew/
├── manage-services.sh           # 🎮 Interactive service manager
├── start-all-services.sh        # 🚀 Start services wizard
├── check-status.sh              # 📊 Status checker
├── stop-all-services.sh         # 🛑 Stop all services
├── QUICK_START_GUIDE.md         # 📖 This guide
├── .env                         # ⚙️ Configuration
├── Makefile                     # 🔧 Build automation
│
├── src/
│   ├── core/                    # 54+ utility modules
│   ├── ultimate_discord_intelligence_bot/
│   │   ├── tools/              # 84+ specialized tools
│   │   ├── pipeline_components/ # Orchestration
│   │   └── setup_cli.py        # Main CLI
│   ├── server/                 # FastAPI app
│   ├── memory/                 # Vector & graph memory
│   └── obs/                    # Observability
│
├── ops/
│   └── deployment/
│       ├── docker/             # Docker Compose
│       └── k8s/                # Kubernetes
│
├── tests/                      # 281+ tests
├── docs/                       # 100+ docs
└── logs/                       # Service logs
```

---

## Next Steps

### For First-Time Users

1. ✅ Run `./manage-services.sh` (option 1)
2. ✅ Configure `.env` with API keys
3. ✅ Start Discord Bot Enhanced (option 3)
4. ✅ Test with Discord command: `!analyze URL`

### For Developers

1. Read: `docs/DEVELOPER_ONBOARDING_GUIDE.md`
2. Review: `.github/copilot-instructions.md`
3. Explore: `docs/capability_map.md` (84 tools)
4. Setup: `make setup-hooks` (git hooks)

### For Operators

1. Configure: `ops/deployment/k8s/`
2. Monitor: `ops/monitoring/`
3. Review: `docs/deployment_guide.md`

### For AI/ML Engineers

1. Study: `docs/autonomous_video_follow.md`
2. Configure: `docs/crewai_integration.md`
3. Tune: `docs/advanced-contextual-bandits.md`

---

## Getting Help

- **Quick Start**: This file
- **Architecture**: `.github/copilot-instructions.md`
- **API Reference**: `docs/api_reference.md`
- **Tools Reference**: `docs/capability_map.md`
- **Troubleshooting**: `./manage-services.sh` (option 23)
- **Issues**: `docs/AUTOINTEL_CRITICAL_ISSUES.md`

---

## System Capabilities

### 84+ Specialized Tools

- **Download**: YouTube, Twitch, TikTok, Instagram, X (Twitter)
- **Transcription**: Whisper, AssemblyAI
- **Analysis**: Sentiment, entities, topics, summaries
- **Memory**: Vector search, graph memory, continual learning
- **Routing**: Contextual bandits, multi-armed bandits
- **Observability**: Metrics, tracing, logging

### Multi-Tenant Pipeline

```
download → transcription → analysis → memory → Discord posting
```

Each phase:

- ✅ Circuit breaker protection
- ✅ Retry logic with backoff
- ✅ Comprehensive metrics
- ✅ Tenant isolation
- ✅ Budget tracking

---

**🎉 You're all set! Start with `./manage-services.sh` and explore!**

---

## Emergency Commands

```bash
# Kill everything
pkill -9 -f "ultimate_discord_intelligence_bot"
pkill -9 -f "uvicorn"
docker-compose down

# Fresh start
make deep-clean
make first-run
./start-all-services.sh

# Check what's broken
make doctor
./check-status.sh
```

---

Last Updated: 2025-01-04
Version: 4.0.0
