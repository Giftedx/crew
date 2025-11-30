# Ultimate Discord Intelligence Bot

[![CI Pipeline](https://github.com/Giftedx/crew/workflows/CI%20Pipeline/badge.svg)](https://github.com/Giftedx/crew/actions)
[![Test Coverage](https://codecov.io/gh/Giftedx/crew/branch/main/graph/badge.svg)](https://codecov.io/gh/Giftedx/crew)
[![MyPy](https://img.shields.io/badge/MyPy-type--checked-blue "Production-ready type safety")](https://github.com/Giftedx/crew)

A production-ready, multi-tenant intelligence system powered by autonomous AI agents for content analysis, fact-checking, and cross-platform monitoring. Built with CrewAI orchestration, 31 specialized agents, 111 specialized tools, and a modern 3-layer architecture.

## 🚀 Overview

The Ultimate Discord Intelligence Bot provides:

- **Autonomous Content Analysis**: AI-powered deep analysis of videos, articles, and social media content
- **Fact-Checking & Verification**: Multi-source claim verification with confidence scoring
- **Multi-Platform Intelligence**: Monitors YouTube, TikTok, Twitter/X, Reddit, Instagram, and Discord
- **Real-Time Processing**: Live stream analysis and real-time content monitoring
- **Advanced Memory Systems**: Qdrant vector storage, Neo4j graph memory, Mem0/HippoRAG continual learning
- **Quality Assurance**: Content validation, consistency checking, and quality gates
- **Trajectory Evaluation**: LangSmith-powered scoring with RL feedback loops for model routing
- **Performance Optimization**: Multi-level caching, intelligent model routing, prompt compression
- **OpenAI Integration**: Structured outputs, function calling, streaming, multimodal analysis
- **Multi-Tenant Architecture**: Complete workspace and resource isolation

## 🏗️ Architecture

### 3-Layer Architecture

The system employs a clean 3-layer architecture following domain-driven design principles:

1. **Platform Layer** (`src/platform/`): Infrastructure and cross-cutting concerns
   - **Core protocols**: `StepResult` pattern for unified error handling
   - **HTTP layer**: Resilient HTTP client with circuit breakers, retries, and timeout management
   - **Cache layer**: Multi-level caching (L1 in-memory, L2 Redis, L3 semantic)
   - **LLM layer**: Provider-agnostic routing with quality/cost/latency policies
   - **RL layer**: Reinforcement learning (contextual bandits) for adaptive model selection
   - **Observability**: Prometheus metrics, Langfuse tracing, structured logging
   - **Security**: Rate limiting, privacy controls, policy enforcement

2. **Domain Layer** (`src/domains/`): Business logic organized by bounded contexts
   - **Orchestration** (`orchestration/`): CrewAI agents, tasks, and crew management
   - **Ingestion** (`ingestion/`): Multi-platform content providers
     - YouTube, TikTok, Twitter/X, Reddit, Instagram, Discord, Twitch
   - **Intelligence** (`intelligence/`): Analysis and verification
     - Analysis: Content processing, sentiment, fallacy detection, timeline construction
     - Verification: Fact-checking, claim extraction, confidence scoring
   - **Memory** (`memory/`): Storage and retrieval systems
     - Vector: Qdrant integration for semantic search
     - Graph: Neo4j knowledge graphs
     - Continual: Mem0, HippoRAG for long-term learning

3. **App Layer** (`src/app/`): Application entry points and interfaces
   - **Discord bot** (`discord/`): Commands, events, and bot lifecycle management
   - **Crew executor**: Agent orchestration and task execution
   - **Configuration**: Agent definitions (YAML), feature flags, runtime settings
   - **Main entry point** (`main.py`)

### Core Components

- **CrewAI Framework**: Orchestrates 31 specialized agents with role-based tool access across strategic, operational, and specialized domains
- **111 Tools**: Comprehensive tool ecosystem organized across 9 categories
- **Multi-Tenant Support**: Complete tenant isolation and workspace management
- **Advanced Memory**: Vector stores, graph databases, and traditional storage
- **Performance Optimization**: Intelligent caching and model routing
- **Quality Assurance**: Comprehensive validation and consistency checking
- **Observability Pipeline**: Langfuse tracing, Prometheus metrics, and StepResult instrumentation

### Agent Specialists

#### Executive & Strategic Layer (2 agents)

1. **Executive Supervisor**: Strategic oversight, resource allocation, and mission success
1. **Workflow Manager**: Task routing, dependency management, and load balancing across agent hierarchies

#### Coordination & Mission Control (1 agent)

1. **Mission Orchestrator**: End-to-end mission coordination, depth sequencing, and budget management

#### Content Acquisition & Processing (3 agents)

1. **Acquisition Specialist**: Multi-platform content download with rate-limit handling and quality fallbacks
1. **Transcription Engineer**: Audio/video transcription and searchable indexing
1. **Analysis Cartographer**: Linguistic, sentiment, and thematic signal mapping

#### Verification & Risk (2 agents)

1. **Verification Director**: Fact-checking, claim extraction, and defensible verdicts
1. **Risk Intelligence Analyst**: Deception scoring, trust metrics, and longitudinal tracking

#### Knowledge & Personas (2 agents)

1. **Persona Archivist**: Living dossiers with behavior, sentiment, and trust milestones
1. **Knowledge Integrator**: Memory consolidation across vector, graph, and continual memory

#### Signal Intelligence (2 agents)

1. **Signal Recon Specialist**: Cross-platform discourse and sentiment tracking
1. **Trend Intelligence Scout**: Emerging content detection and prioritization

#### Community & Research (4 agents)

1. **Community Liaison**: Community Q&A with verified intelligence and context retrieval
1. **Argument Strategist**: Steelman arguments, debate prep, and persuasive narratives
1. **Research Synthesist**: Deep background briefs harmonizing multiple perspectives
1. **Intelligence Briefing Curator**: Stakeholder-ready intelligence packets

#### System Reliability (2 agents)

1. **System Reliability Officer**: Pipeline health, dashboards, and operational visibility
1. **Personality Synthesis Manager**: Consistent tone, style, and persona alignment

#### Specialized AI Agents - Phase 3.1 (5 agents)

1. **Visual Intelligence Specialist**: Computer vision, image analysis, OCR, and visual fact-checking
1. **Audio Intelligence Specialist**: Speaker diarization, emotion analysis, and acoustic classification
1. **Trend Intelligence Specialist**: Real-time trend monitoring and long-term forecasting
1. **Content Generation Specialist**: AI-powered content creation, adaptation, and optimization
1. **Cross-Platform Intelligence Specialist**: Multi-platform correlation and propagation analysis

#### Creator Network Intelligence (6 agents)

1. **Network Discovery Specialist**: Social network mapping, collaboration patterns, and influence dynamics
1. **Deep Content Analyst**: Multimodal long-form analysis and narrative arc tracking
1. **Guest Intelligence Specialist**: Guest profiling, collaborator tracking, and monitoring recommendations
1. **Controversy Tracker Specialist**: Drama detection, conflict tracking, and early warnings
1. **Insight Generation Specialist**: Pattern synthesis and actionable intelligence delivery
1. **Quality Assurance Specialist**: Output validation, consistency checks, and re-analysis triggers

#### Discord AI Conversational (2 agents)

1. **Conversational Response Agent**: Natural, context-aware Discord responses
1. **Personality Evolution Agent**: RL-based personality optimization from interaction feedback

### Import Patterns

**After domains/ migration, use these import paths:**

```python
# Platform layer - infrastructure
from platform.core.step_result import StepResult, ErrorCategory
from platform.http.http_utils import resilient_get, resilient_post
from platform.cache.tool_cache_decorator import cache_tool_result
from platform.llm.llm_router import LLMRouter

# Tenancy - multi-tenant isolation
from ultimate_discord_intelligence_bot.tenancy.context import (
    TenantContext,
    with_tenant,
    current_tenant,
    require_tenant,
)

# Domain layer - business logic
from domains.intelligence.analysis.logical_fallacy_tool import LogicalFallacyTool
from domains.intelligence.verification.fact_check_tool import FactCheckTool
from domains.intelligence.acquisition.youtube_downloader_tool import YouTubeDownloaderTool
from domains.memory.vector_memory_tool import VectorMemoryTool
from domains.orchestration.crew.compat import CrewAICompatExecutor

# Observability
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
```

**Deprecated paths (pre-migration):**

- ❌ `from ultimate_discord_intelligence_bot.crew import ...`
- ❌ `from ultimate_discord_intelligence_bot.tools import ...`
- ✅ Use `from domains.orchestration.crew import ...` instead
- ✅ Use `from domains.intelligence.* import ...` for tools

## 🤖 OpenAI Integration

The bot includes comprehensive OpenAI integration with advanced AI capabilities:

### Core Features

- **Structured Outputs**: Generate validated, structured responses using JSON schemas
- **Function Calling**: Enable AI models to call custom functions during analysis
- **Streaming**: Real-time streaming of AI responses for better user experience
- **Voice Processing**: Convert between text and speech using OpenAI's voice models
- **Vision Analysis**: Analyze images and visual content with advanced vision models
- **Multimodal Analysis**: Process content across multiple modalities (text, images, audio)

### Services

- **OpenAIStructuredOutputsService**: Generate structured, validated responses
- **OpenAIFunctionCallingService**: Enable function calling capabilities
- **OpenAIStreamingService**: Stream responses in real-time
- **OpenAIVoiceService**: Text-to-speech and speech-to-text conversion
- **OpenAIVisionService**: Image analysis and visual content processing
- **MultimodalAnalysisService**: Cross-modal content analysis
- **OpenAIIntegrationService**: Main service combining all capabilities
- **OpenAICostMonitoringService**: Track API usage and costs

### Discord Commands

- `!openai-health` - Check OpenAI service health
- `!openai-analyze-structured <content>` - Perform structured analysis
- `!openai-analyze-multimodal <prompt>` - Analyze multimodal content
- `!openai-voice-command` - Process voice commands

### CrewAI Integration

The OpenAI capabilities are available as CrewAI tools:

- **OpenAIEnhancedAnalysisTool**: Enhanced analysis with OpenAI capabilities
- Integrated with analysis agents for advanced content processing
- Supports structured outputs, function calling, and multimodal analysis

For detailed documentation, see [OpenAI Integration Features](docs/openai_integration_features.md).

## 🛠️ Installation

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Discord Bot Token
- OpenAI/OpenRouter API Key
- Qdrant Vector Database

### Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd ultimate-discord-intelligence-bot
   ```

2. **Set up environment**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**

   ```bash
   # Recommended for development
   pip install -e '.[dev]'

   # Minimal install (production)
   pip install -e .

   # Optional feature sets
   pip install -e '.[metrics]'     # Prometheus metrics
   pip install -e '.[whisper]'     # Whisper transcription
   pip install -e '.[vllm]'        # VLLM inference
   pip install -e '.[mcp]'         # Model Context Protocol
   ```

1. **Start services**

   ```bash
   # Development compose
   docker compose -f config/docker/docker-compose.yml up -d
   ```

1. **Run the bot**

   ```bash
   # Ensure virtualenv is active; sitecustomize.py auto-adds src/ to PYTHONPATH when launched from repo root
   source .venv/bin/activate
   python -m app.main run

   # OR use explicit PYTHONPATH
   PYTHONPATH=src python -m app.main run

   # OR call the file directly
   python src/app/main.py run
   ```

   Troubleshooting: If you see a Python error like "Could not find platform independent libraries <prefix>" or sys.prefix shows "/install" and "No module named 'encodings'", your virtual environment is corrupted (often due to an external Python shim such as uv). Fix by recreating a clean venv with your system Python:

   ```bash
   # from repo root
   deactivate || true
   rm -rf .venv
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -U pip wheel setuptools
   pip install -e .
   # then:
   python -m app.main run
   ```

   Note on stdlib platform module conflict: This repository contains a top-level `platform/` package. Some environments ship a system `sitecustomize.py` that loads before project-level startup hooks, which can cause `from platform.core ...` imports to resolve the stdlib module instead. We've implemented two safeguards:

   - Entry-point bootstrap: `app/main.py` and `server/app.py` call a tiny bootstrap (`ultimate_discord_intelligence_bot.core.bootstrap.ensure_platform_proxy()`) at process start to make the stdlib `platform` module behave as a package exposing our `platform/*` submodules.
   - User customizations: a minimal `src/usercustomize.py` performs the same augmentation on Python startup when supported by your environment.

   With these in place, imports like `from platform.core.step_result import StepResult` work consistently across shells, venvs, and containers.

## 🛡️ Compliance Guards

This project enforces automated compliance checks to maintain code quality and architectural standards:

### Automated Enforcement

- **Local Development**: Pre-commit hooks validate all changes before commit
- **CI Pipeline**: GitHub Actions workflow runs on every PR and push to main branches
- **Merge Blocking**: PRs cannot merge if compliance checks fail (when branch protection enabled)

### Five Guards Enforced

1. **HTTP Wrapper Guard** - Prevents direct `requests.*` calls; enforces resilient HTTP wrappers with circuit breakers and retries
2. **Tools Export Guard** - Ensures all tools are registered in `__all__` for dynamic discovery (112 tools validated)
3. **Metrics Instrumentation Guard** - Enforces consistent metric naming conventions and observability patterns
4. **Deprecated Directories Guard** - Blocks new files in deprecated paths during architecture migration
5. **Dispatcher Usage Guard** - Validates tenant context propagation in async/thread boundaries

### Quick Start

```bash
# One-time setup: Install pre-commit hooks
make setup-hooks

# Manual execution: Run all guards
make guards

# Check specific guard
python scripts/validate_http_wrappers_usage.py

# Generate compliance report
python scripts/generate_guard_report.py --input <(make guards 2>&1) --output report.json --pretty
```

### Emergency Bypass

For critical hotfixes only:

```bash
# Bypass local hook (CI still enforces)
git commit --no-verify -m "hotfix: critical issue"
```

**Note**: Bypassed commits still run in CI. Document bypass reason in commit message.

### Documentation

- **Full Guide**: [docs/compliance-guards.md](docs/compliance-guards.md) - 557 lines covering setup, troubleshooting, examples
- **CI Workflow**: [.github/workflows/guards-ci.yml](.github/workflows/guards-ci.yml) - Automated enforcement with PR comments
- **Implementation**: [F011_F014_GUARD_CI_INTEGRATION_COMPLETE_2025-11-12.md](F011_F014_GUARD_CI_INTEGRATION_COMPLETE_2025-11-12.md)

## ⚙️ Configuration

### Environment Variables

#### Core Services

```bash
# Discord Bot
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_PRIVATE_WEBHOOK=your_private_webhook_url

# LLM Services
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key
```

#### LLM Provider Routing (new)

Configure the provider-agnostic router that selects the best model per request.

```bash
# Comma-separated provider allowlist used to build routing candidates
# Examples: openai,anthropic,google,openrouter,groq,together,cohere,mistral,fireworks,perplexity,xai,deepseek,azure_openai,bedrock
LLM_PROVIDER_ALLOWLIST=openai,anthropic,google,openrouter

# Router policy: quality_first | cost | latency
ROUTER_POLICY=quality_first

# Comma-separated task names that should force quality-first routing
QUALITY_FIRST_TASKS=analysis,reasoning,coding
```

These values are also available at runtime via `get_config()` from `platform.config.configuration`
as `llm_provider_allowlist` (parsed list) and `router_policy`.

#### Feature Flags

```bash
# Core Features
ENABLE_DEBATE_ANALYSIS=true
ENABLE_FACT_CHECKING=true
ENABLE_MULTI_PLATFORM_MONITORING=true

# Advanced Features
ENABLE_UNIFIED_KNOWLEDGE=true
ENABLE_UNIFIED_METRICS=true
ENABLE_UNIFIED_ORCHESTRATION=true
ENABLE_UNIFIED_ROUTER=true

# Performance Features
ENABLE_CACHE_OPTIMIZATION=true
ENABLE_MODEL_ROUTING=true
ENABLE_PERFORMANCE_OPTIMIZATION=true

# OpenAI Integration Features
ENABLE_OPENAI_STRUCTURED_OUTPUTS=true
ENABLE_OPENAI_STREAMING=true
ENABLE_OPENAI_VOICE=false
ENABLE_OPENAI_VISION=false
ENABLE_OPENAI_MULTIMODAL=false
ENABLE_OPENAI_FUNCTION_CALLING=true
ENABLE_OPENAI_FALLBACK=true

# Evaluation & Observability
ENABLE_TRAJECTORY_EVALUATION=1  # Set to 1 to enable runtime scoring
ENABLE_TRAJECTORY_FEEDBACK_LOOP=0  # Set to 1 to push scores into RL router
RL_FEEDBACK_BATCH_SIZE=25  # Optional: number of feedback items processed per tick
RL_FEEDBACK_LOOP_INTERVAL_SECONDS=15  # Optional: delay (seconds) between feedback loop runs
ENABLE_LANGSMITH_EVAL=false
ENABLE_LANGFUSE_EXPORT=false
```

#### Performance Settings

```bash
# CrewAI Configuration
CREW_MAX_RPM=10
CREW_EMBEDDER_PROVIDER=openai

# Cache Settings
CACHE_TTL=3600
CACHE_MAX_SIZE=1000

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10
```

#### Performance Optimization

The codebase includes comprehensive performance analysis and optimization tools. See [Performance Initiative Summary](docs/PERFORMANCE_INITIATIVE_SUMMARY.md) for details.

**Quick Performance Check**:

```bash
# Analyze performance issues
python3 scripts/performance_improvements.py --report

# Check for performance regressions
python3 -m ruff check src --select PERF
```

**Documentation**:

- [Performance Improvement Recommendations](docs/PERFORMANCE_IMPROVEMENT_RECOMMENDATIONS.md) - Comprehensive analysis of 258 performance issues
- [Performance Best Practices](docs/PERFORMANCE_BEST_PRACTICES.md) - Best practices for high-performance Python code
- [Performance Fixes Applied](docs/PERFORMANCE_FIXES_APPLIED.md) - Summary of automated fixes

**Benchmarking**:

```bash
# Run performance benchmarks
python3 benchmarks/performance_benchmarks.py

# Profile tool imports
python3 profile_tool_imports.py
```

## 🎯 Usage

### Discord Commands

#### Basic Commands

- `!analyze <url>` - Analyze content from any supported platform
- `!factcheck <claim>` - Fact-check a specific claim
- `!monitor <creator>` - Start monitoring a creator
- `!status` - Get system status and metrics

#### Advanced Commands

- `!deep_analysis <url>` - Comprehensive content analysis
- `!verify_claims <url>` - Extract and verify all claims
- `!trend_analysis <topic>` - Analyze trends for a topic
- `!quality_assess <content>` - Assess content quality

### API Usage

#### Content Analysis

```python
# Recommended: domain-based import
from domains.orchestration.crew import get_crew, UltimateDiscordIntelligenceBotCrew

# Factory pattern
crew_adapter = get_crew()
crew_obj = crew_adapter.crew()
result = crew_obj.kickoff(inputs={"url": "https://youtube.com/watch?v=example"})

# Or instantiate directly
crew_instance = UltimateDiscordIntelligenceBotCrew()
result = crew_instance.crew().kickoff(inputs={"url": "https://youtube.com/watch?v=example"})
```

#### Fact-Checking

```python
result = crew.crew().kickoff(inputs={
    "claim": "The Earth is flat",
    "context": "Scientific discussion"
})
```

## 📊 Monitoring & Observability

### Langfuse Tracing

- Feature-gated exporter capturing traces and spans for every pipeline step via `LangfuseService`
- Configure with `ENABLE_LANGFUSE_EXPORT`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and optional `LANGFUSE_BASE_URL`
- StepResult-aware sanitization ensures payload safety and tenant metadata tagging
- Validate instrumentation with `python run_observability_tests.py` or enable live export in staging

### Metrics Dashboard

- Real-time performance metrics
- Agent execution statistics
- Tool usage analytics
- Error rates and success rates

### Logging

- Structured logging with tenant isolation
- Performance tracing
- Error tracking and alerting
- Audit trails for compliance

### Health Checks

- System health endpoints
- Service availability monitoring
- Resource usage tracking
- Automated alerting

## 🧪 Testing

### Run Tests

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/tools/          # Tool tests
pytest tests/agents/         # Agent tests
pytest tests/services/       # Service tests
pytest tests/integration/    # Integration tests
```

### Trajectory Evaluation Suite

- Validates LangSmith adapters and heuristic fallbacks.
- Execute `pytest tests_new/unit/eval/test_langsmith_adapter.py` for focused coverage.
- Enable `ENABLE_TRAJECTORY_EVALUATION=1` and `ENABLE_TRAJECTORY_FEEDBACK_LOOP=1` to exercise reinforcement feedback paths in integration environments.

### Quality Gates

```bash
make format     # Code formatting
make lint       # Linting
make type       # Type checking
make test       # Testing
make docs       # Documentation validation
```

For detailed quality gate requirements, see [docs/quality-gates.md](docs/quality-gates.md).

## 📚 Documentation

### Core Documentation

- [Architecture Overview](docs/architecture/system_overview.md)
- [Agent Reference](docs/agent_reference.md)
- [Tools Reference](docs/tools_reference.md)
- [Configuration Guide](docs/configuration.md)

### Specialized Guides

- [Quality Assurance Tools](docs/tools/quality_assurance.md)
- [Performance Optimization](docs/tools/performance_optimization.md)
- [Compliance Tools](docs/tools/compliance.md)
- [MCP Integration](docs/tools/mcp_enhanced.md)

### API Documentation

- [Tools API](docs/api/tools_api.md)
- [Agents API](docs/api/agents_api.md)
- [Services API](docs/api/services_api.md)

## 🚀 Deployment

### Docker Deployment

```bash
# Build and deploy (production)
docker compose -f config/docker/docker-compose.prod.yml up -d

# Scale services
docker compose -f config/docker/docker-compose.prod.yml up -d --scale bot=3
```

### Kubernetes Deployment (optional)

Kubernetes manifests are not included by default in this repository. If you maintain your own manifests,
apply them in your deployment repository or ops layer.

### Environment-Specific Configs

- `config/docker/docker-compose.yml` - Development
- `config/docker/docker-compose.prod.yml` - Production

## 🔧 Development

### Project Structure

```text
src/
├── platform/               # Platform layer: Infrastructure & cross-cutting concerns
│   ├── core/               # Core protocols (StepResult, config)
│   ├── http/               # Resilient HTTP client (circuit breakers, retries)
│   ├── cache/              # Multi-level caching (memory, Redis, semantic)
│   ├── llm/                # LLM providers, routing, structured outputs
│   ├── rl/                 # Reinforcement learning (contextual bandits)
│   ├── observability/      # Metrics, tracing, logging
│   ├── security/           # Security, privacy, rate limiting
│   ├── prompts/            # Prompt engineering (DSPy)
│   └── rag/                # RAG capabilities (LlamaIndex)
│
├── domains/                # Domain layer: Business logic by bounded context
│   ├── orchestration/      # CrewAI agents, tasks, crew
│   │   ├── crewai/         # CrewAI-specific components
│   │   └── legacy/         # Legacy orchestration code
│   ├── ingestion/          # Multi-platform content ingestion
│   │   ├── pipeline/       # Ingestion pipeline orchestrator
│   │   └── providers/      # Platform-specific providers
│   ├── intelligence/       # Analysis & verification
│   │   ├── analysis/       # Content analysis tools
│   │   └── verification/   # Fact-checking & verification
│   └── memory/             # Memory systems
│       ├── vector/         # Vector storage (Qdrant)
│       ├── graph/          # Graph memory (Neo4j)
│       └── continual/      # Continual learning (Mem0, HippoRAG)
│
├── app/                    # App layer: Application-specific code
│   ├── main.py             # Application entry point
│   ├── crew_executor.py    # CrewAI crew execution
│   ├── discord/            # Discord bot integration
│   │   ├── bot.py          # Bot implementation
│   │   ├── commands/       # Discord commands
│   │   └── events/         # Event handlers
│   └── config/             # Application configuration
│       ├── settings.py     # Global settings
│       └── agents.yaml     # Agent definitions
│
└── ultimate_discord_intelligence_bot/  # Legacy: being migrated to domains/
    ├── tools/              # 111 specialized tools (registry)
    ├── pipeline_components/# Pipeline orchestrator
    └── tenancy/            # Multi-tenant context management
```

### Adding New Tools

1. Create tool class inheriting from `BaseTool`
1. Implement `_run` method returning `StepResult`
1. Add to `tools/__init__.py` exports
1. Register in `crew.py` with appropriate agent
1. Add comprehensive tests

### Adding New Agents

1. Define agent in `crew.py` with `@agent` decorator
1. Specify role, goal, backstory, and tools
1. Add to crew construction in `crew()` method
1. Update agent documentation

## 🤝 Contributing

### Development Workflow

1. Fork the repository
1. Create feature branch
1. Implement changes with tests
1. Run quality gates
1. Submit pull request

### Code Standards

- Follow PEP 8 and project formatting rules
- Include comprehensive type hints
- Write tests for all new functionality
- Update documentation for new features
- Use `StepResult` for all tool returns
- **Documentation**: All public modules, classes, and functions must have Google-style docstrings explaining purpose, arguments, and return values.

### Quality Requirements

- All quality gates must pass
- 100% test coverage for new code
- Documentation updates required
- No increase in MyPy error baseline

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- Check [documentation](docs/) for detailed guides
- Review [troubleshooting guide](docs/operations/troubleshooting.md)
- Open an issue for bugs or feature requests
- Join our Discord server for community support

### Reporting Issues

When reporting issues, please include:

- System information (OS, Python version)
- Error logs and stack traces
- Steps to reproduce
- Expected vs actual behavior

## 🗺️ Roadmap

### Phase 1: Core System ✅

- [x] Tool registration and organization
- [x] Agent architecture implementation
- [x] Basic functionality testing

### Phase 2: Advanced Features ✅

- [x] Quality assurance systems
- [x] Performance optimization
- [x] Enhanced MCP integration

### Phase 3: Production Readiness 🚧

- [ ] Complete system configuration
- [ ] Comprehensive testing
- [ ] Documentation updates
- [ ] Performance optimization

### Phase 4: Scale & Optimize 📋

- [ ] Advanced monitoring
- [ ] Auto-scaling capabilities
- [ ] Advanced analytics
- [ ] Machine learning optimization

## 🏆 Features

### ✅ Implemented

- **111 specialized tools** across 9 categories (ingestion, analysis, verification, memory, observability, etc.)
- **31 autonomous AI agents** with role-based tool access
- **Multi-platform content ingestion** (YouTube, TikTok, Twitter/X, Reddit, Instagram, Discord, Twitch)
- **Advanced fact-checking** with claim extraction and multi-source verification
- **Multi-level memory systems** (Qdrant vectors, Neo4j graphs, Mem0/HippoRAG continual learning)
- **Quality assurance** with validation, consistency checking, and quality gates
- **Performance optimization** with semantic caching, prompt compression, and model routing
- **Multi-tenancy** support with complete workspace and resource isolation
- **Observability** with Prometheus metrics, Langfuse tracing, and structured logging
- **Reinforcement learning** for adaptive model selection via contextual bandits

### 🚧 In Development

- Advanced analytics dashboard
- Real-time collaboration features
- Enhanced security features
- Advanced workflow automation

### 📋 Planned

- Machine learning model training
- Advanced visualization tools
- Enterprise integrations
- Mobile applications

---

**Built with ❤️ using CrewAI, Discord.py, and modern Python technologies.**
