---
title: Claude Assistant Development Guide
origin: CLAUDE.md (formerly root)
status: relocated
last_moved: 2025-09-02
---

## Claude Assistant Development Guide

> Relocated from repository root to `docs/architecture/` during the documentation restructure. Update any bookmarks pointing to the old path.

<!-- START ORIGINAL CONTENT -->
## Overview

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ultimate Discord Intelligence Bot is a tenant-aware Discord platform built with CrewAI that ingests public media, builds grounded context, and provides intelligent analysis through cost-guarded model routing and reinforcement learning. The system emphasizes privacy, provenance, and reliability with staged feature rollouts.

## Development Commands

### Common Development Tasks

```bash
# Install dependencies
pip install -e .[dev]

# Development workflow
make format          # Auto-fix style & imports with ruff
make lint            # Lint check (CI style)
make type            # Static type check with mypy (non-blocking)
make test            # Run pytest suite
make docs            # Validate documentation & config references

# Alternative dev script usage
./scripts/dev.sh format
./scripts/dev.sh type-changed           # mypy only changed files vs origin/main
./scripts/dev.sh type-baseline          # check current mypy error count vs baseline
./scripts/dev.sh type-baseline-update   # update baseline if improved

# Pre-commit hooks
pre-commit install --install-hooks
```

### Bot Execution

```bash
# Quick start Discord bot with full features
python -m ultimate_discord_intelligence_bot.setup_cli run discord

# Alternative standalone bot scripts
python -m ultimate_discord_intelligence_bot.setup_cli run discord  # Full feature bot

# Test specific ingestion
python -m ingest.pipeline https://youtu.be/dummy --tenant default --workspace main
```

### Testing

```bash
pytest                                    # Run all tests
pytest -q                                 # Quick quiet mode
pytest -m "not integration"               # Skip integration tests
pytest tests/test_specific_module.py      # Single test file
pytest -k "retry_precedence"             # Tests matching pattern
```

## Architecture Overview

### Core Pipeline Flow

```text
Multi-Platform Download → Drive Upload → Transcription → Analysis → Memory Storage → Discord Delivery
```

### Key Components

**CrewAI Orchestration:**

- Main entry: `src/ultimate_discord_intelligence_bot/main.py`
- Crew configuration: `src/ultimate_discord_intelligence_bot/crew.py`
- Agent definitions: `src/ultimate_discord_intelligence_bot/config/agents.yaml`
- Task definitions: `src/ultimate_discord_intelligence_bot/config/tasks.yaml`

**Core Services (src/):**

- `core/` - Foundation utilities, HTTP retry logic, learning engine, token metering
- `memory/` - Vector store with Qdrant backend, in-memory fallback for testing
- `obs/` - Tracing, metrics, and observability (OpenTelemetry)
- `security/` - Moderation, RBAC, rate limiting, webhook verification
- `grounding/` - Citation enforcement and verification
- `eval/` - Golden test harnesses and scoring
- `scheduler/` - Priority queue for ingestion and analysis tasks

**Analysis Pipeline:**

- `analysis/` - Transcription, segmentation, topic extraction
- `ingest/` - Multi-platform content ingestion (YouTube, Twitch, etc.)
- `debate/` - Multi-role debate panels and perspective synthesis

### Tool Development Patterns

All tools must inherit from `BaseTool` and return structured results:

```python
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from ultimate_discord_intelligence_bot.step_result import StepResult

class MyTool(BaseTool[dict]):
    name: str = "My Tool"
    description: str = "Tool description for CrewAI agents"

    def _run(self, input_param: str) -> dict:
        try:
            if not input_param:
                return {"status": "error", "error": "Input required"}

            result = process_input(input_param)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}
```

Tools are registered to agents in `crew.py`:

```python
@agent
def my_agent(self) -> Agent:
    return Agent(
        config=self.agents_config["my_agent"],
        tools=[MyTool(), OtherTool()],
    )
```

### Configuration & Feature Flags

**IMPORTANT: Use centralized secure configuration instead of os.getenv():**

```python
from core.secure_config import get_config

config = get_config()
api_key = config.get_api_key("openai")  # Secure API key access with validation
webhook_url = config.get_webhook("discord_private")  # Webhook URL validation
is_enabled = config.is_feature_enabled("http_retry")  # Feature flag checking
```

Feature flags follow `ENABLE_<AREA>_<FEATURE>` pattern:

- `ENABLE_INGEST_YOUTUBE`, `ENABLE_INGEST_TWITCH` - Platform ingestion
- `ENABLE_RAG_CONTEXT`, `ENABLE_VECTOR_SEARCH` - Memory and retrieval
- `ENABLE_RL_GLOBAL`, `ENABLE_RL_ROUTING` - Reinforcement learning
- `ENABLE_DISCORD_COMMANDS`, `ENABLE_DISCORD_ARCHIVER` - Discord integration
- `ENABLE_PII_DETECTION`, `ENABLE_CONTENT_MODERATION` - Privacy/security
- `ENABLE_HTTP_RETRY` - HTTP resilience (replaces deprecated `ENABLE_ANALYSIS_HTTP_RETRY`)

**Security Requirements:**

- Webhook secrets must be set via `WEBHOOK_SECRET_DEFAULT` environment variable
- Never use default values like "CHANGE_ME" for secrets
- API keys are validated and audit logged when accessed

### Tenancy Requirements

All operations must be tenant-aware:

```python
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant
from obs import metrics

# Always thread tenant context
with with_tenant(TenantContext("tenant", "workspace")):
    metrics.ROUTER_DECISIONS.labels(**metrics.label_ctx()).inc()
```

### Error Handling

Use `StepResult` for pipeline operations:

```python
from ultimate_discord_intelligence_bot.step_result import StepResult

def pipeline_step() -> StepResult:
    try:
        result = process_data()
        return StepResult.ok(data=result)
    except Exception as e:
        return StepResult.fail(error=str(e), detail="Additional context")
```

### HTTP Retry Patterns

Use existing retry wrappers instead of manual loops:

```python
from core.http_utils import retrying_get, retrying_post

# Respects ENABLE_HTTP_RETRY flag and retry configuration
response = retrying_get(url, timeout=30)
response = retrying_post(url, json=payload, timeout=30)
```

## Code Style Requirements

- **Python 3.10+** with type hints required for all functions
- **Line length: 120 characters** (ruff configured)
- **Use timezone-aware UTC** timestamps (`datetime.now(timezone.utc)`)
- **Follow StepResult pattern** for tool returns
- **Add comprehensive tests** for all new functionality
- **Document new configuration** in relevant docs/ files

## Type Checking

The project uses incremental mypy adoption:

- Current baseline: ~120 errors (tracked in `mypy_baseline.json`)
- New code should be fully typed
- Never increase the baseline error count
- Use `./scripts/dev.sh type-baseline-update` if error count decreases

## Testing Patterns

### In-Memory Fallbacks

- Qdrant: Set `QDRANT_URL=:memory:` for lightweight testing
- Use `LIGHTWEIGHT_IMPORT=1` to avoid heavy Discord/FastAPI imports in unit tests

### Test Categories

- Unit tests: Fast, isolated, mock external dependencies
- Integration tests: Use `@pytest.mark.integration` decorator
- Golden tests: Run with `make eval` for routing/prompt changes

### Deterministic Testing

- Functions with randomness should accept injectable providers
- Use uppercase summaries or add deterministic flags for assertion stability
- Timezone handling: Always use UTC, test with `tests/test_tenancy_timezone.py` patterns

## Key Anti-Patterns to Avoid

- ❌ Using `datetime.utcnow()` (naive timestamps)
- ❌ Manual retry loops (use `retrying_get`/`retrying_post`)
- ❌ Cross-tenant data without namespace isolation
- ❌ Hardcoded external API calls without feature flags
- ❌ Tools raising exceptions for recoverable errors
- ❌ Missing type hints on new public functions
- ❌ Increasing mypy baseline error count

## Deprecation Handling

Current deprecated patterns:

- `ENABLE_ANALYSIS_HTTP_RETRY` → `ENABLE_HTTP_RETRY` (grace period: 2025-12-31)
- `services.learning_engine.LearningEngine` → `core.learning_engine.LearningEngine`
- Root `trustworthiness.json` → `data/trustworthiness.json`

Run tests with `-Wd` to surface deprecation warnings as errors.

## Observability Integration

Wrap expensive operations with metrics and tracing:

```python
from obs import tracing, metrics
from ultimate_discord_intelligence_bot.tenancy import with_tenant

@with_tenant
def operation(tc: TenantContext) -> StepResult:
    with tracing.start_span("operation", tenant=tc.tenant) as span:
        metrics.operations_total.labels(tenant=tc.tenant).inc()
        # ... implementation
```

## Golden Evaluation

For changes affecting routing, prompting, or grounding:

```bash
make eval
# or
python -m eval.runner datasets/golden/core/v1 baselines/golden/core/v1/summary.json
```

This file should be updated when new architectural patterns or development workflows are established.

<!-- END ORIGINAL CONTENT -->
