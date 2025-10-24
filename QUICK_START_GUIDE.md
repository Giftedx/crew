# 🚀 Quick Start Guide - Ultimate Discord Intelligence Bot

## Fast Track (5 Minutes)

### 1. First Time Setup

```bash
# One-command bootstrap
./start-all-services.sh
```

The script will:

- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Create .env from template
- ✅ Run health checks
- ✅ Start selected services

### 2. Configure API Keys

Edit `.env` and set these required values:

```bash
DISCORD_BOT_TOKEN=your-discord-bot-token-here
OPENROUTER_API_KEY=your-openrouter-key-here
# OR
OPENAI_API_KEY=sk-your-openai-key-here
```

### 3. Run

```bash
./start-all-services.sh
# Then select option 2 for enhanced mode
```

---

## Service Architecture

### Core Services

1. **Discord Bot** - Main intelligence pipeline
2. **FastAPI Server** - HTTP API + A2A endpoints  
3. **CrewAI** - Autonomous agent orchestration
4. **MCP Server** - Model Context Protocol server

### Infrastructure (Optional - Docker)

- **Qdrant** - Vector database (port 6333)
- **Redis** - Caching layer (port 6379)
- **PostgreSQL** - Metadata storage (port 5432)
- **MinIO** - Object storage (port 9000/9001)
- **Prometheus** - Metrics (port 9090)
- **Grafana** - Dashboards (port 3000)

---

## Running Services

### Option 1: Interactive Startup (Recommended)

```bash
./start-all-services.sh
```

Choose from menu:

- `1` - Discord Bot (basic)
- `2` - Discord Bot Enhanced (with AI features)
- `3` - API Server only
- `5` - All local services (background)
- `6` - Full stack with Docker

### Option 2: Individual Services

#### Discord Bot

```bash
# Basic mode
make run-discord

# Enhanced mode (semantic cache, compression, memory)
make run-discord-enhanced

# OR directly
python -m ultimate_discord_intelligence_bot.setup_cli run discord
```

#### API Server

```bash
python -m uvicorn server.app:app --host 0.0.0.0 --port 8080 --reload
```

#### CrewAI

```bash
make run-crew
# OR
python -m ultimate_discord_intelligence_bot.setup_cli run crew
```

#### MCP Server

```bash
make run-mcp
```

### Option 3: Docker Compose (Full Stack)

```bash
cd ops/deployment/docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all
docker-compose down
```

---

## Development Workflow

### Daily Workflow

```bash
# Quick checks (8 seconds)
make quick-check

# Full checks (format, lint, type, test)
make full-check

# Run specific tests
make test-fast
make test
```

### Git Hooks (Recommended)

```bash
make setup-hooks
```

Auto-runs checks on commit.

---

## Health & Diagnostics

### Check System Health

```bash
make doctor
```

Validates:

- ✅ API keys present
- ✅ Services reachable
- ✅ Configuration valid

### Monitor Services

```bash
# If running in background
tail -f logs/services/*.log

# Check PIDs
cat logs/services/*.pid

# Stop background services
kill $(cat logs/services/*.pid)
```

### View Metrics

- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3000> (admin/admin)
- Qdrant: <http://localhost:6333/dashboard>

---

## Common Tasks

### Process a Video

1. Start Discord bot
2. In Discord channel: `!analyze https://youtube.com/watch?v=...`
3. Bot downloads → transcribes → analyzes → posts results

### Use API Endpoint

```bash
curl -X POST http://localhost:8080/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=...", "options": {}}'
```

### Run Autonomous Intelligence

```bash
# Start CrewAI
make run-crew

# Access via API
curl http://localhost:8080/autointel -d '{"task": "Research and summarize..."}
```

---

## Troubleshooting

### "Module not found" errors

```bash
# Recreate environment
make first-run
source .venv/bin/activate
```

### Docker not available (WSL)

Enable Docker Desktop WSL integration, OR use development mode:

```bash
export ENABLE_DEVELOPMENT_MODE=true
export QDRANT_URL=":memory:"
./start-all-services.sh
```

### API key errors

```bash
# Check configuration
make doctor

# Edit .env
vim .env  # or code .env
```

### Port conflicts

```bash
# Find process using port
lsof -ti:8080

# Kill it
kill $(lsof -ti:8080)
```

### Import errors in tests

```bash
# Tests require src in PYTHONPATH (automatic via pytest.ini)
# If running manually:
PYTHONPATH=src pytest
```

---

## Feature Flags (Key Toggles)

Edit `.env` to enable/disable features:

### Performance

```bash
ENABLE_SEMANTIC_CACHE=true
ENABLE_PROMPT_COMPRESSION=true
ENABLE_GRAPH_MEMORY=true
ENABLE_HIPPORAG_MEMORY=true
```

### APIs & Routing

```bash
ENABLE_A2A_API=true
ENABLE_BANDIT_ROUTING=true
ENABLE_CONTEXTUAL_BANDIT=true
```

### Monitoring

```bash
ENABLE_PROMETHEUS_ENDPOINT=true
ENABLE_HTTP_METRICS=true
ENABLE_TRACING=true
```

### Development

```bash
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_DEVELOPMENT_MODE=true
```

---

## Project Structure

```
crew/
├── src/
│   ├── core/                    # 54+ utility modules
│   ├── ultimate_discord_intelligence_bot/
│   │   ├── tools/              # 84+ specialized tools
│   │   ├── pipeline_components/ # Orchestration
│   │   └── setup_cli.py        # Main CLI
│   ├── server/                 # FastAPI app
│   ├── memory/                 # Graph & vector memory
│   └── obs/                    # Observability
├── ops/
│   └── deployment/
│       ├── docker/             # Docker Compose
│       └── k8s/                # Kubernetes manifests
├── tests/                      # 281+ tests
├── docs/                       # 100+ documentation files
├── Makefile                    # Build automation
└── start-all-services.sh       # This startup script
```

---

## Next Steps

### For Developers

1. Read: `docs/DEVELOPER_ONBOARDING_GUIDE.md`
2. Review: `.github/copilot-instructions.md` (architecture overview)
3. Explore: `docs/capability_map.md` (84 tools reference)

### For Operators

1. Configure: `ops/deployment/k8s/` (production)
2. Monitor: `ops/monitoring/` (Prometheus + Grafana)
3. Review: `docs/deployment_guide.md`

### For AI/ML Engineers

1. Study: `docs/autonomous_video_follow.md`
2. Configure: `docs/crewai_integration.md`
3. Tune: `docs/advanced-contextual-bandits.md`

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| Start everything | `./start-all-services.sh` |
| Quick check | `make quick-check` |
| Full check | `make full-check` |
| Run tests | `make test` |
| Health check | `make doctor` |
| Discord bot | `make run-discord` |
| API server | `python -m uvicorn server.app:app --reload` |
| Stop services | `kill $(cat logs/services/*.pid)` |
| View logs | `tail -f logs/services/*.log` |
| Clean build | `make clean` |
| Deep clean | `make deep-clean` |

---

## Getting Help

- **Architecture**: `.github/copilot-instructions.md`
- **API Reference**: `docs/api_reference.md`
- **Tools**: `docs/capability_map.md`
- **Issues**: Check `docs/AUTOINTEL_CRITICAL_ISSUES.md`
- **Changes**: `docs/CHANGELOG_AGENT_GUIDE.md`

---

**Ready to build?** Start with `./start-all-services.sh` 🚀
