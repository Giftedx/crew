# Developer Onboarding Guide

Welcome to the Ultimate Discord Intelligence Bot! This guide will help you get started with the codebase after the major restructure to a clean 3-layer architecture.

## Quick Start

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Git
- Basic understanding of Python, Discord bots, and AI/ML concepts

### Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd ultimate-discord-intelligence-bot
```

2. **Set up environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Install dependencies**:
```bash
pip install -r requirements.lock
# or in development mode
pip install -e .[dev]
```

4. **Start services**:
```bash
docker-compose up -d
```

5. **Run the bot**:
```bash
python -m app.main
```

## Architecture Overview

The codebase uses a **clean 3-layer architecture**:

### 1. Platform Layer (`src/platform/`)

**Purpose**: Infrastructure and foundational services with zero domain knowledge.

**Key Components**:
- **core/**: Core protocols (StepResult, error handling)
- **http/**: HTTP utilities, resilience, circuit breakers
- **cache/**: Multi-level caching (Redis, semantic, LRU)
- **llm/**: LLM providers (OpenAI, Anthropic, OpenRouter), routing, structured outputs
- **rl/**: Reinforcement learning (bandits, meta-learning, feature engineering)
- **observability/**: Metrics, tracing, logging (Prometheus, Logfire)
- **security/**: Security, privacy, rate limiting, moderation
- **prompts/**: Prompt engineering (DSPy optimization)
- **rag/**: RAG capabilities (LlamaIndex integration)
- **config/**: Configuration management

**Key Principles**:
- ✅ Zero domain knowledge
- ✅ Reusable across projects
- ✅ Framework-agnostic where possible
- ✅ Well-tested and documented

### 2. Domain Layer (`src/domains/`)

**Purpose**: Business logic organized by capability.

**Key Domains**:
- **orchestration/**: CrewAI agents, tasks, crew management
- **ingestion/**: Multi-platform content ingestion (YouTube, TikTok, Twitter, etc.)
- **intelligence/**: Content analysis and verification
- **memory/**: Knowledge storage and retrieval (vector, graph, continual learning)

**Key Principles**:
- ✅ Domain-specific logic only
- ✅ Uses platform layer for infrastructure
- ✅ Well-organized by capability
- ✅ Framework-specific integrations consolidated

### 3. App Layer (`src/app/`)

**Purpose**: Application-specific Discord bot code.

**Key Components**:
- **discord/**: Discord bot integration (commands, events, handlers)
- **config/**: Application configuration (agents.yaml, tasks.yaml, settings.py)
- **crew_executor.py**: CrewAI execution wrapper
- **main.py**: Application entry point

**Key Principles**:
- ✅ Application-specific only
- ✅ Thin layer over domains
- ✅ Minimal business logic
- ✅ Easy to understand

## Directory Structure

```
src/
├── platform/          # Infrastructure (zero domain knowledge)
├── domains/           # Business logic (organized by capability)
└── app/               # Application layer (Discord bot)
```

## Import Patterns

### Platform Layer
```python
from platform.core.step_result import StepResult
from platform.http.http_utils import resilient_get
from platform.cache import get_cache
from platform.llm.providers.openrouter import OpenRouterService
from platform.observability.metrics import get_metrics
```

### Domain Layer
```python
from domains.ingestion.providers.tools import YouTubeDownloadTool
from domains.intelligence.analysis.tools import SentimentAnalysisTool
from domains.memory.vector.qdrant import QdrantClient
from domains.orchestration.crewai.agents import AnalysisAgent
```

### App Layer
```python
from app.discord.bot import DiscordBot
from app.config.settings import Settings
from app.crew_executor import UltimateDiscordIntelligenceBotCrew
```

## Common Development Tasks

### Adding a New Tool

1. **Choose Domain**:
   - Ingestion tools → `domains/ingestion/providers/tools/`
   - Analysis tools → `domains/intelligence/analysis/tools/`
   - Verification tools → `domains/intelligence/verification/tools/`
   - Memory tools → `domains/memory/tools/`

2. **Create Tool Class**:
```python
from platform.core.step_result import StepResult
from domains.ingestion.providers._base import BaseAcquisitionTool

class MyTool(BaseAcquisitionTool):
    def _run(self, input_data: str, tenant: str, workspace: str) -> StepResult:
        try:
            # Tool implementation
            result = self._process(input_data)
            return StepResult.ok(data=result)
        except Exception as e:
            return StepResult.fail(str(e))
```

3. **Register Tool**:
   - Add to appropriate MAPPING in `src/ultimate_discord_intelligence_bot/tools/__init__.py`
   - Update `docs/tools_reference.md`

4. **Add Tests**:
   - Create test file in `tests/`
   - Test success and error paths
   - Verify tenant isolation

### Adding a New Agent

1. **Define Agent**:
   - Add to `app/config/agents.yaml`
   - Specify role, goal, backstory, tools

2. **Add to Crew**:
   - Update `app/crew_executor.py`
   - Add agent to crew construction

3. **Add Tests**:
   - Test agent creation
   - Test agent execution

### Using Platform Services

**HTTP Utilities**:
```python
from platform.http.http_utils import resilient_get, resilient_post

response = await resilient_get(url, timeout=30)
result = await resilient_post(url, data=payload)
```

**Caching**:
```python
from platform.cache import get_cache

cache = get_cache()
cached_result = cache.get(key)
cache.set(key, value, ttl=3600)
```

**LLM Services**:
```python
from platform.llm.providers.openrouter import OpenRouterService

service = OpenRouterService()
response = await service.generate(
    prompt="Analyze this content",
    model="openai/gpt-4"
)
```

**Observability**:
```python
from platform.observability.metrics import get_metrics

metrics = get_metrics()
metrics.counter('tool_runs_total', labels={'tool': 'my_tool'}).inc()
```

## Code Standards

### StepResult Pattern (REQUIRED)

All tools must return `StepResult` objects:

```python
from platform.core.step_result import StepResult

def my_function() -> StepResult:
    try:
        result = process_data()
        return StepResult.ok(data=result)
    except Exception as e:
        return StepResult.fail(str(e))
```

### Type Hints (MANDATORY)

All functions must have complete type annotations:

```python
from __future__ import annotations

def process_content(url: str, tenant: str, workspace: str) -> StepResult:
    # Implementation
    pass
```

### Tenant-Aware Design (REQUIRED)

All operations must be tenant-aware:

```python
def my_tool(content: str, tenant: str, workspace: str) -> StepResult:
    # Use tenant isolation for data storage
    # Derive namespaces using tenant/workspace
    pass
```

## Quality Gates

Before submitting code, ensure all quality gates pass:

```bash
make format     # Code formatting
make lint       # Linting
make type       # Type checking
make test       # Testing
make docs       # Documentation validation
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/tools/          # Tool tests
pytest tests/domains/         # Domain tests
pytest tests/platform/        # Platform tests
pytest tests/integration/    # Integration tests
```

### Writing Tests

```python
import pytest
from platform.core.step_result import StepResult

class TestMyTool:
    def test_successful_processing(self):
        tool = MyTool()
        result = tool._run("input", "tenant", "workspace")
        assert result.success
        assert result.data is not None

    def test_error_handling(self):
        tool = MyTool()
        result = tool._run("", "tenant", "workspace")
        assert not result.success
```

## Configuration

### Environment Variables

See `docs/configuration.md` for complete configuration reference.

### Feature Flags

Feature flags use pattern: `ENABLE_<AREA>_<FEATURE>=true`

Example:
```bash
ENABLE_DEBATE_ANALYSIS=true
ENABLE_FACT_CHECKING=true
ENABLE_MULTI_PLATFORM_MONITORING=true
```

## Documentation

- **Architecture**: `docs/architecture/overview.md`
- **Tools Reference**: `docs/tools_reference.md`
- **Configuration**: `docs/configuration.md`
- **Restructure**: `docs/restructure/MIGRATION_COMPLETE.md`

## Getting Help

1. **Check Documentation**: Start with `docs/` directory
2. **Review Architecture**: See `docs/architecture/overview.md`
3. **Check Examples**: Look at existing tools in `domains/`
4. **Ask Questions**: Open an issue or join Discord

## Common Pitfalls

1. ❌ **Don't**: Use legacy import paths (`core.*`, `ai.*`, `obs.*`)
2. ❌ **Don't**: Put domain logic in platform layer
3. ❌ **Don't**: Put infrastructure in domain layer
4. ❌ **Don't**: Return raw data from tools (use StepResult)
5. ❌ **Don't**: Skip type hints
6. ❌ **Don't**: Ignore tenant context

7. ✅ **Do**: Use new import paths (`platform.*`, `domains.*`, `app.*`)
8. ✅ **Do**: Follow 3-layer architecture principles
9. ✅ **Do**: Return StepResult from tools
10. ✅ **Do**: Include complete type hints
11. ✅ **Do**: Pass tenant/workspace parameters
12. ✅ **Do**: Run quality gates before submitting

## Next Steps

1. ✅ Read architecture overview
2. ✅ Explore directory structure
3. ✅ Review existing tools
4. ✅ Set up development environment
5. ✅ Run tests to verify setup
6. ✅ Create first contribution

Welcome to the team! 🚀
