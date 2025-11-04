# Ultimate Discord Intelligence Bot - Documentation Index

*Comprehensive guide to all documentation in this repository.*

**System Overview** (verified November 4, 2025):

- **111 specialized tools** across 9 categories
- **18 autonomous agents** with role-based tool access
- **7-phase content pipeline** (download, transcription, content routing, quality filtering, lightweight processing, analysis, finalization)
- **3-layer architecture** (Platform at `src/platform`, Domains at `src/domains`, App at `src/app`)

## Core Documentation

- [README](../README.md) - Project overview and quick start
- [Quick Start Guide](../QUICK_START_GUIDE.md) - Fast track setup (5 minutes)
- [System Guide](../SYSTEM_GUIDE.md) - Complete system guide
- [Configuration](configuration.md) - Configuration reference
- [Tools Reference](tools_reference.md) - Complete tools documentation (111 tools)
- [Agents Reference](agents_reference.md) - Agent documentation (18 agents)

## Architecture & Design

- [Architecture Directory](architecture/) - 34 architecture documents including:
  - [ARCHITECTURE.md](architecture/ARCHITECTURE.md) - Complete system architecture
  - [Agent System](architecture/agent_system.md) - 18 agent roles
  - [Pipeline Architecture](architecture/pipeline_architecture.md) - 7-phase orchestration
  - [Memory System](architecture/memory_system.md) - 4 memory providers
  - [Error Handling](architecture/error_handling.md) - StepResult pattern
  - [ADRs](architecture/) - Architecture decision records (0001-0005)
- [Memory Systems](memory.md) - Unified memory layer (Qdrant, Neo4j, Mem0, HippoRAG)
- [Observability](observability.md) - 26 observability tools and metrics

## API Documentation

- [API Reference](api_reference.md) - FastAPI HTTP endpoints
- [A2A API](a2a_api.md) - Agent-to-Agent JSON-RPC adapter
- [Advanced Bandits API](advanced-bandits-api.md) - LinUCB policy for LLM routing

## Development

- [Contributing Guide](operations/CONTRIBUTING.md) - Development workflow and quality gates
- [Developer Assistants](dev_assistants.md) - AI assistant guidance
- [Test Reports](test_reports.md) - Test coverage and infrastructure
- [Setup Documentation](setup_docs.md) - Setup wizard and environment configuration

## Feature Documentation

- [Reinforcement Learning](rl_overview.md) - LinUCB contextual bandits
- [Semantic Cache](semantic_cache.md) - Multi-level caching with similarity matching
- [Prompt Compression](prompt_compression.md) - Token optimization
- [Privacy](privacy.md) - Privacy controls and PII filtering
- [Grounding](grounding.md) - Citation and source tracking

## Operations

- [Runbooks](operations/runbooks.md) - Operational procedures
- [Changelog](operations/CHANGELOG.md) - Version history
