## AI Agent Guide

### Platform Overview
Tenant-aware Discord intelligence pipeline streaming `download → transcription → analysis → memory` tasks per tenant. 84+ specialized tools orchestrated through `ContentPipeline` with circuit breakers, retry logic, and comprehensive observability.

**Runtime Surfaces**:
- Discord bot: `python -m ultimate_discord_intelligence_bot.setup_cli run discord`
- FastAPI server: `server/app.py` with modular routes under `server/routes/*.py`
- Optional MCP server: `crew_mcp` (requires `pip install -e '.[mcp]'`)
- Feature flags: 50+ `ENABLE_*` toggles in `core/settings.py` control caching, memory, routing, observability

**Critical Shell Note**: Always quote extras in zsh: `pip install -e '.[dev]'` (brackets trigger glob expansion).

---

### Architecture Essentials

**Pipeline Orchestration** (`src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py`):
- `ContentPipeline` orchestrates: download → transcription → analysis → memory → Discord posting
- Each phase returns `StepResult` and runs under `_pipeline_context` for tracing + budget tracking
- **Universal contract**: `StepResult.ok/skip/fail/uncertain(data, step="<phase>", error_category=ErrorCategory.*, retryable=bool)`
- For detailed debugging, attach `ErrorContext` to failures with retry counts, mitigation suggestions
- Circuit breaker protection: `PipelineTool` wraps pipeline with failure threshold, recovery timeout

**Tenant Isolation** (Critical for multi-workspace deployments):
- Wrap external I/O in `with_tenant(TenantContext(...))` from `tenancy/__init__.py`
- Derive cache/vector namespaces via `mem_ns(ctx, "suffix")` to scope keys per tenant
- Non-strict mode falls back gracefully but increments `tenancy_fallback_total` metric

**Model Routing & Caching**:
- All LLM calls flow through `services/openrouter_service.py` (expects tenant context)
- Semantic cache (Redis + bandits) controlled by `ENABLE_SEMANTIC_CACHE*` flags
- See `docs/architecture/adr-0001-cache-platform.md` for unified cache strategy

**Feature Flags**:
- Declared in `core/settings.py`; regenerate docs with `make docs-flags-write` after adding toggles
- 50+ flags control caching, memory, routing, observability, rate limiting, etc.

---

### Mandatory Conventions

**HTTP Requests** (Enforced by `make guards`):
- ❌ Never `import requests` directly
- ✅ Use `core.http_utils.resilient_get/resilient_post/http_request_with_retry` for automatic retries, circuit breakers, timeout handling
- Guard script `validate_http_wrappers_usage.py` fails CI on violations

**Downloads**:
- ✅ Use `tools/multi_platform_download_tool.MultiPlatformDownloadTool`
- ❌ Direct `yt-dlp` usage fails `validate_dispatcher_usage.py`

**Tool Development** (84+ tools in `src/ultimate_discord_intelligence_bot/tools/`):
- Subclass `tools/_base.BaseTool[R_co]` with typed return via generic parameter
- Implement `run(*args, **kwargs) -> R_co` returning `StepResult` or structured dict
- Register in `tools/__all__` + `MAPPING` dict (name → relative module path, e.g., `"AudioTranscriptionTool": ".audio_transcription_tool"`)
- **Mandatory metrics**: `get_metrics().counter("tool_runs_total", labels={"tool": self.name, "outcome": status})`
- Optional: use `self.publish_message(msg_type, content, **metadata)` for agent comms bus
- Example tools: `PipelineTool`, `AudioTranscriptionTool`, `TextAnalysisTool`, `MemoryStorageTool`, `LogicalFallacyTool`

**Concurrency Patterns**:
- When fanning out (e.g., analysis + fallacy + graph memory), cancel unfinished siblings on first exception
- Surface failing `StepResult` rather than raising; pipeline expects structured outcomes

**Config/Secrets**:
- Read via `core.secure_config.get_config()` for audit logging and per-tenant overrides
- Never hardcode keys or read `.env` directly in production code

---

### CrewAI Autonomous Intel (`/autointel`)

- Entry: `autonomous_orchestrator.py`
- Build one `Crew` with tasks chained via `context=[previous_task]` for automatic output flow
- Reuse agents: `self._get_or_create_agent("agent_name")` (avoid ad hoc Crew instantiation)
- Task descriptions stay high level ("Analyze transcript"); data passes via kickoff inputs + Crew context, never embedded in strings
- Disable telemetry noise: `CREWAI_DISABLE_TELEMETRY=1`, `OTEL_SDK_DISABLED=true`

---

### FastAPI Server & Middleware

**App Factory** (`server/app.py`):
- Middleware order matters: CORS → metrics → API cache → Prometheus `/metrics` → rate limiting
- Route registration: modular `server/routes/*.py` registrars, each takes `(app, settings)` and handles flags internally
- Middleware exclusions: `/metrics` and `/health` bypass rate limiting; metrics route skips self-instrumentation

**Key Feature Flags**:
- `ENABLE_HTTP_METRICS`: Request histogram + counter
- `ENABLE_PROMETHEUS_ENDPOINT`: Expose `/metrics` endpoint
- `ENABLE_RATE_LIMITING`: Per-IP rate limiting with Redis backend
- `ENABLE_API_CACHE`: API response caching
- `ENABLE_CORS`: CORS middleware with configurable origins

---

### Workflow & Commands

**First-Time Setup**:
1. `make first-run` → bootstraps venv (prefers `uv` if available, falls back to pip)
2. `make init-env` → creates `.env` from `.env.example` if missing
3. Edit `.env`: set `DISCORD_BOT_TOKEN`, one of `OPENAI_API_KEY`/`OPENROUTER_API_KEY`
4. `python -m ultimate_discord_intelligence_bot.setup_cli wizard` → tenant scaffolding
5. `make doctor` → validates Qdrant, Redis, Discord tokens

**Daily Development Loop**:
- `make quick-check` or `./scripts/dev-workflow.sh quick-check` → format + lint + test-fast (~8s)
- `make full-check` → format + lint + type + full test suite (~10s)
- `make setup-hooks` → install git hooks for pre-commit validation

**Start Services**:
- Discord bot: `python -m ultimate_discord_intelligence_bot.setup_cli run discord`
- Enhanced mode: `make run-discord-enhanced` (enables semantic cache, prompt compression, graph memory, HippoRAG)
- CrewAI: `python -m ultimate_discord_intelligence_bot.setup_cli run crew`
- MCP server: `crew_mcp` (after `pip install -e '.[mcp]'`)

**Health & Debug**:
- `make doctor` → validates external service connectivity
- `make docs` → regenerates ops documentation when configs change

---

### Testing & Compliance

**Fast Feedback Loop**:
- `make test-fast` (~8s): targets core modules (http_utils, guards, vector dimensions/namespaces)
- `make test-fast-clean-env`: clears env vars before retry precedence tests (prevents flakiness)

**Full Suite**:
- `make test`: 281 tests, ~10s
- `FULL_STACK_TEST=1 pytest`: slow end-to-end paths
- `make type`: mypy/ruff gate (incremental adoption, non-zero tolerated locally)

**Test Structure**:
- Unit: `tests/orchestrator/modules/test_*_unit.py`
- Integration: marked with `@pytest.mark.integration`
- Shared fixtures: `tests/orchestrator/fixtures.py`

**Mocking Patterns**:
```python
from unittest.mock import MagicMock, AsyncMock
mock_tool = MagicMock()
mock_tool.run.return_value = {"status": "success", "data": {...}}
# or for async:
mock_async_tool = AsyncMock()
mock_async_tool.run.return_value = StepResult.ok(...)
mock_async_tool.run.assert_called_once_with(expected_args)
```

**Guard Rails** (Run after touching tools/network code):
- `make guards`: runs 5 validators
  1. `validate_http_wrappers_usage.py` → enforces `core.http_utils` wrappers
  2. `validate_dispatcher_usage.py` → blocks direct `yt-dlp` usage
  3. `metrics_instrumentation_guard.py` → ensures tool metrics
  4. `validate_tools_exports.py` → checks tool registration
  5. `guards/deprecated_directories_guard.py` → blocks new code in deprecated paths (`core/routing/`, `ai/routing/`, `performance/`)

**Compliance Audits**:
- `make compliance`: audits HTTP + `StepResult` usage
- `make compliance-fix`: auto-migrates simple violations
- `make type-guard`: snapshot-based mypy regression guard (must stay green)
- `make type-guard-update`: regenerate baseline (only after verifying improvements)

---

### Package Structure & Imports

**Src Layout**:
- `src/core/` → 54+ utility modules (http, cache, settings, config, metrics)
- `src/ultimate_discord_intelligence_bot/` → main app + 84 tools + pipeline components
- `src/analysis/`, `src/memory/`, `src/ingest/`, `src/server/`
- `src/obs/` → observability (metrics, tracing, monitoring)
- `src/mcp_server/` → Model Context Protocol server (optional)

**Import Discipline**:
- Lazy imports: `tools/`, `obs/` avoid eager submodule loads
- ✅ `from tools.specific_tool import SpecificTool`
- ❌ `from tools import *`
- Tool registration: `tools/MAPPING` dict maps name → relative module path (e.g., `"PipelineTool": ".pipeline_tool"`)

**Test Imports**:
- Tests require `PYTHONPATH=src` (auto-set by `.config/pytest.ini`)
- Scripts should prepend: `sys.path.insert(0, str(repo_root / "src"))`

---

### Troubleshooting

**Missing Outputs**:
- Feature flags likely off → check `.env` or run `make doctor`

**Vector Store Issues**:
- Falls back to in-memory Qdrant if `QDRANT_URL` unset
- Check startup logs from `server/app._lifespan`

**Retry Flakiness**:
- Lingering env vars interfere with precedence tests
- Solution: `make test-fast-clean-env` resets environment

**Import Errors in Tests**:
- Ensure `PYTHONPATH=src` (automatic via `.config/pytest.ini`)

**CrewAI Telemetry Noise**:
- Export `CREWAI_DISABLE_TELEMETRY=1` and `OTEL_SDK_DISABLED=true` in shell

---

### Architecture Consolidation (In Progress)

Project underwent major consolidation (see `ARCHITECTURE_CONSOLIDATION_SESSION_COMPLETE.md`):
- **5 ADRs** documenting unified cache, memory, routing, orchestration, analytics strategies
- **3 Unified Facades**: `UnifiedCache`, `UnifiedMemoryService`, orchestration facade
- **Deprecation Markers**: `core/routing/`, `ai/routing/`, `performance/` directories deprecated
- **Migration**: New code should use facades, not deprecated modules
- **Guards**: CI blocks new code in deprecated paths via `guards/deprecated_directories_guard.py`

See `docs/architecture/consolidation-status.md` for migration tracking.
