# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ultimate Discord Intelligence Bot is a production-ready Discord bot system powered by CrewAI agents for autonomous content analysis, fact-checking, and intelligence gathering across multiple platforms (YouTube, TikTok, Twitter, Reddit, etc.). The architecture includes 20+ AI agents, 110+ specialized tools, and comprehensive multi-platform intelligence capabilities.

## Core Technology Stack

- **Python 3.10-3.14** with src layout project structure
- **CrewAI** for agent orchestration with 20+ specialized agents
- **Discord.py** for Discord integration
- **FastAPI** for HTTP API services
- **Qdrant** for vector database and semantic search
- **PostgreSQL** (metadata), **Redis** (caching), **SQLite** (fallback)
- **Docker** with comprehensive docker-compose setup

## Essential Development Commands

### Environment Setup
```bash
make first-run                 # Bootstrap environment (uv preferred, pip fallback)
make init-env                  # Create .env from template
make doctor                    # System health check
```

### Daily Development Workflow
```bash
make quick-check               # Fast checks (format + lint + test-fast)
make full-check               # Comprehensive checks
make run-discord              # Standard Discord bot
make run-discord-enhanced     # With experimental features
make run-crew                 # CrewAI execution mode
```

### Quality Assurance
```bash
make test                     # Full test suite
make test-fast               # Quick subset for development
make format                  # Auto-format with ruff
make lint                    # Linting checks
make type                    # MyPy type checking
make guards                  # Validate architectural constraints
make compliance              # HTTP & StepResult compliance audits
```

### API and Services
```bash
python -m server.app          # FastAPI server with /metrics endpoint
make run-mcp                  # MCP server for Claude Desktop integration
```

## Architecture Overview

### Source Structure
- `src/ultimate_discord_intelligence_bot/` - Main bot application with agents and tools
- `src/core/` - Core platform services (routing, caching, resilience)
- `src/ai/` - AI routing and optimization systems
- `src/memory/` - Vector storage and retrieval systems
- `src/analysis/` - Content analysis services
- `src/obs/` - Observability framework
- `src/server/` - FastAPI application
- `src/mcp_server/` - Model Context Protocol server

### Agent System
20+ specialized agents with clear domain responsibilities:
- Content analysis, fact-checking, controversy tracking
- Guest intelligence, network discovery, live monitoring
- Executive supervision and workflow management

### Tool Architecture
110+ domain-specific tools organized by:
- **Acquisition**: Content ingestion from multiple platforms
- **Analysis**: Content processing, sentiment, safety analysis
- **Verification**: Fact-checking and source validation
- **Memory**: Vector storage, graph memory, retrieval
- **Observability**: Performance monitoring and metrics

## Critical Development Patterns

### StepResult Protocol
All tools must return `StepResult` objects with proper error categorization:
```python
from tools._base import StepResult
return StepResult.success(data=result)
return StepResult.error("Category", "Message", context={...})
```

### HTTP Compliance
Use wrapped HTTP calls, never raw requests:
```python
from core.http_utils import resilient_get, resilient_post
response = await resilient_get(url)
```

### Tool Registration
All tools must be exported in `__all__` and registered in MAPPING dictionaries for proper discovery.

### Multi-Tenancy
Use tenant context for workspace isolation:
```python
from core.tenancy import with_tenant, current_tenant
with with_tenant(tenant_id):
    # tenant-aware operations
```

### Feature Flags
Gate new features behind environment flags with proper documentation in `.env.example`.

## Testing Strategy

- **Fast Feedback**: `make test-fast` for rapid development cycles
- **Pytest-based**: Uses pytest with asyncio support and custom markers
- **Integration Tests**: Comprehensive A2A and MCP integration tests
- **Quality Gates**: Pre-commit hooks with ruff, MyPy, secret scanning

## Performance Features

- **Reinforcement Learning**: Contextual bandits (LinUCB, Vowpal Wabbit) for AI routing
- **Caching Strategy**: Multi-level caching with semantic cache and GPTCache integration
- **Memory Systems**: Vector search, graph memory, continual learning (HippoRAG)
- **Model Optimization**: Intelligent model routing and cost optimization

## Multi-Platform Integration

Supports content ingestion and analysis from:
- YouTube, TikTok, Twitter/X, Instagram, Twitch, Reddit
- Creator intelligence and trend analysis
- Cross-platform narrative tracking

## Observability

- **Metrics**: Prometheus metrics via `obs.metrics`
- **Monitoring**: Grafana dashboards and AlertManager integration
- **Performance Tracking**: Cache hit rates, agent performance, error categorization
- **Health Checks**: Built-in system health monitoring

## Configuration

- **Environment-Driven**: 100+ feature flags in `.env.example`
- **Security-First**: Secure configuration with secret rotation
- **Tenant-Aware**: Multi-tenant support with workspace isolation

## Common Development Tasks

### Adding a New Tool
1. Inherit from `tools._base.BaseTool`
2. Return `StepResult` objects
3. Add to domain-specific `__all__` export
4. Register in appropriate MAPPING
5. Add tests with proper markers

### Adding a New Agent
1. Define in `src/ultimate_discord_intelligence_bot/agents/`
2. Follow existing agent patterns for configuration
3. Integrate with orchestration system
4. Add performance monitoring

### Working with Memory
1. Use tenant-aware memory operations
2. Leverage vector search capabilities
3. Consider caching implications
4. Monitor performance metrics

Always run `make guards` before submitting changes to validate architectural compliance.
