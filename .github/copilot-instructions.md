## AI agent guide for this repo (read first)

This repo implements a tenant-aware Discord intelligence platform with a staged content pipeline, FastAPI surface, and optional MCP server. Follow these repo-specific rules to be productive and avoid guardrail failures.

### 🚀 Quick Start Checklist (for AI agents)

Before making changes, verify you understand:
1. ✅ **HTTP calls**: Use `core.http_utils.resilient_get/resilient_post` (NEVER `requests` directly)
2. ✅ **Return types**: Tools/pipeline stages return `StepResult.ok/fail/skip/uncertain`
3. ✅ **Tenancy**: Wrap operations with `with_tenant(TenantContext(...))`
4. ✅ **Downloads**: Use `MultiPlatformDownloadTool` (NEVER invoke `yt-dlp` directly)
5. ✅ **Testing**: Run `make test-fast` (8s) before committing; `make guards` for compliance
6. ✅ **Metrics**: Instrument tools with `get_metrics().counter("tool_runs_total", labels={...})`

**First-time setup**: `make first-run` (creates venv, installs deps, runs checks)

### Architecture map (files to know)
- **Orchestrator**: `src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py` (aka `ContentPipeline`). Stages: download → Drive upload → transcription → analysis → memory/Discord/graph. Each stage returns `StepResult` and runs under budget/tracing.
- **Universal result**: `src/ultimate_discord_intelligence_bot/step_result.py` (`ok/skip/uncertain/fail`, Mapping behavior, `.to_dict()` for legacy).
- **Tenancy**: `src/ultimate_discord_intelligence_bot/tenancy/` (`with_tenant(TenantContext(...))`, `mem_ns()` to derive `<tenant>:<workspace>:<suffix>` namespaces).
- **Server**: `src/server/app.py` (feature-flagged middleware + routers; pipeline routes behind `ENABLE_PIPELINE_RUN_API=1`; A2A behind `ENABLE_A2A_API=1`).
- **Model routing**: `src/ultimate_discord_intelligence_bot/services/openrouter_service.py` (adaptive routing, semantic cache, Redis integration; respects `ENABLE_SEMANTIC_CACHE*`).
- **Settings/flags**: `src/core/settings.py` (simple, env-driven; 80+ `ENABLE_*` toggles; see `.env.example` for catalog). Vector store: Qdrant; if `QDRANT_URL` missing, tests use in‑memory fallback.
- **Modular src/ layout**: Packages are split by concern (`core/`, `obs/`, `memory/`, `ingest/`, `analysis/`, `security/`, `scheduler/`, `server/`, etc.). All must be listed in `pyproject.toml` `[tool.hatch.build.targets.wheel].packages` for distribution.

### Do this (repo conventions)

#### HTTP requests (CRITICAL - enforced by guard)
```python
# ❌ NEVER - will fail validate_http_wrappers_usage.py
import requests
response = requests.get(url)

# ✅ ALWAYS - retry precedence: call args → tenant retry.yaml → config/retry.yaml → RETRY_MAX_ATTEMPTS env
from core.http_utils import resilient_get, resilient_post
response = resilient_get(url, timeout_seconds=30)
response = resilient_post(url, json_payload={"key": "value"}, timeout_seconds=30)
```

#### Build tools (enforced by guard + metrics)
```python
# Subclass BaseTool, return StepResult, register in tools/__all__ and tools.MAPPING
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from ultimate_discord_intelligence_bot.step_result import StepResult
from obs.metrics import get_metrics

class MyTool(BaseTool[dict]):
    name: str = "my_tool"
    description: str = "Does something useful"
    
    def _run(self, input_data: str) -> StepResult:
        # Instrument with metrics (required by metrics_instrumentation_guard.py)
        outcome = "success"
        try:
            result = self._process(input_data)
            get_metrics().counter("tool_runs_total", labels={"tool": self.name, "outcome": outcome})
            return StepResult.ok(result=result)
        except Exception as e:
            outcome = "error"
            get_metrics().counter("tool_runs_total", labels={"tool": self.name, "outcome": outcome})
            return StepResult.fail(error=str(e))
```

#### Never invoke `yt-dlp` directly (enforced by guard)
```python
# ❌ NEVER - will fail validate_dispatcher_usage.py
import yt_dlp
ydl = yt_dlp.YoutubeDL()

# ✅ ALWAYS - use the dispatcher
from ultimate_discord_intelligence_bot.tools.multi_platform_download_tool import MultiPlatformDownloadTool
tool = MultiPlatformDownloadTool()
result = tool.run(url="https://youtube.com/watch?v=...")
```

#### Concurrent branches (pipeline pattern)
```python
# When fanning out concurrent tasks, cancel siblings on error
async def _analysis_phase(self, ctx, download_info, transcription_bundle):
    tasks = [
        asyncio.create_task(self._run_analysis(...)),
        asyncio.create_task(self._run_fallacy(...)),
        asyncio.create_task(self._run_perspective(...)),
    ]
    try:
        results = await asyncio.gather(*tasks)
    except Exception as e:
        # Cancel pending tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        # Bubble error with step name for retry accounting
        return None, self._fail(ctx.span, ctx.start_time, "analysis", {"error": str(e)})
```

### ⚠️ CRITICAL: CrewAI Tool Data Flow Pattern

**The `/autointel` command was completely rewritten (2025-01-03)** to use proper CrewAI architecture. See implementation in `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py`.

**✅ CORRECT PATTERN - Task Chaining (ALWAYS USE THIS)**:

CrewAI is designed for task chaining via the `context` parameter. Task outputs automatically flow to dependent tasks.

```python
# ✅ CORRECT: Build ONE crew with chained tasks
def _build_intelligence_crew(self, url: str, depth: str) -> Crew:
    # Get cached agents (created once, reused across all tasks)
    acquisition_agent = self._get_or_create_agent("acquisition_specialist")
    transcription_agent = self._get_or_create_agent("transcription_engineer")
    analysis_agent = self._get_or_create_agent("analysis_cartographer")
    
    # Create tasks with high-level descriptions (NO embedded data!)
    acquisition_task = Task(
        description="Acquire and download content from {url}",  # Uses {url} placeholder for kickoff inputs
        agent=acquisition_agent,
        expected_output="Complete media file with metadata"
    )
    
    # Chain tasks via context parameter (data flows automatically)
    transcription_task = Task(
        description="Enhance and index the acquired media transcript",  # High-level instruction
        agent=transcription_agent,
        context=[acquisition_task],  # ✅ CRITICAL: Receives acquisition output automatically
        expected_output="Enhanced transcript with timeline anchors"
    )
    
    analysis_task = Task(
        description="Analyze linguistic patterns and sentiment in transcript",
        agent=analysis_agent,
        context=[transcription_task],  # ✅ Receives transcription output automatically
        expected_output="Comprehensive content analysis"
    )
    
    # Return ONE crew with all tasks
    return Crew(
        agents=[acquisition_agent, transcription_agent, analysis_agent],
        tasks=[acquisition_task, transcription_task, analysis_task],
        process=Process.sequential
    )

# Execute crew with initial inputs
result = await asyncio.to_thread(crew.kickoff, inputs={"url": url, "depth": depth})
```

**❌ BROKEN PATTERNS (NEVER DO THIS)**:

```python
# ❌ WRONG: Creating separate crews per stage
for stage in stages:
    crew = Crew(agents=[agent], tasks=[Task(...)])  # Breaks data flow!
    result = crew.kickoff()

# ❌ WRONG: Embedding data in task descriptions
task = Task(
    description=f"Analyze this transcript: {transcript[:500]}...",  # LLMs can't extract this!
    agent=agent
)

# ❌ WRONG: Creating fresh agent instances mid-workflow
crew_instance = UltimateDiscordIntelligenceBotCrew()
agent = crew_instance.analysis_cartographer()  # Bypasses caching and context population!
```

**Why This Matters**:
- CrewAI LLMs **cannot** extract structured data from task descriptions
- When you write `description=f"Analyze: {transcript}"`, the LLM sees text but provides placeholder params like `"the transcript"` when calling tools
- Task chaining via `context=[previous_task]` makes outputs flow automatically through CrewAI's internal context system
- Creating separate crews breaks the data pipeline between stages

**Agent Caching Pattern**:
- ALWAYS use `self._get_or_create_agent("agent_name")` to get agents
- Agents are created ONCE and cached in `self.agent_coordinators`
- `_populate_agent_tool_context(agent, context_data)` populates tools' `_shared_context` as a fallback mechanism
- Same agent instance is reused across all tasks, preserving context

**When adding /autointel features**:
1. Add tasks to `_build_intelligence_crew()` with proper `context=[previous_task]` chaining
2. Use high-level task descriptions like "Analyze transcript" NOT "Analyze: {data}"
3. Get agents via `self._get_or_create_agent("agent_name")`, never create fresh instances
4. Pass initial data through `crew.kickoff(inputs={...})`, not task descriptions

#### Tenant context (multi-tenancy)
```python
# ✅ Wrap tenant-scoped operations
from ultimate_discord_intelligence_bot.tenancy import with_tenant, TenantContext, mem_ns

with with_tenant(TenantContext(tenant_id="acme", workspace_id="main")):
    # All operations here are tenant-scoped
    # Memory namespaces: mem_ns(ctx, "vectors") → "acme:main:vectors"
    result = await openrouter_service.complete(prompt)  # uses tenant cache
    await memory_tool.store(data)  # writes to tenant namespace
```

### Quick workflows (zsh-safe)

#### First-time setup
```bash
make first-run  # Creates .venv, installs .[dev], sets up hooks, runs doctor + quick-check
# If doctor fails (missing secrets), initialize .env:
make init-env   # Creates .env from .env.example
# Edit .env and set DISCORD_BOT_TOKEN, OPENAI_API_KEY or OPENROUTER_API_KEY
```

#### Daily development
```bash
# Quick validation (8 seconds)
make test-fast                    # Core tests: http_utils, guards, vector store

# Clean environment (avoids RETRY_MAX_ATTEMPTS precedence issues)
make test-fast-clean-env          # Unsets env vars before running

# Full test suite
make test                         # All tests (slower)

# Full stack tests (opt-in, very slow)
FULL_STACK_TEST=1 pytest          # Includes root-level test_*.py files

# Format + lint + type check
make format lint type             # Auto-fix style, check types

# Compliance checks
make guards                       # Run all guard scripts (dispatcher, http, metrics, exports)
make compliance                   # HTTP wrappers + StepResult compliance
```

#### Run services
```bash
# Setup wizard (creates .env, tenant config)
python -m ultimate_discord_intelligence_bot.setup_cli wizard

# Health check
python -m ultimate_discord_intelligence_bot.setup_cli doctor

# Run Discord bot
python -m ultimate_discord_intelligence_bot.setup_cli run discord

# Run with enhancements (semantic cache, compression, graph memory, HippoRAG)
make run-discord-enhanced

# Run CrewAI
python -m ultimate_discord_intelligence_bot.setup_cli run crew
```

#### MCP server (optional)
```bash
# Install MCP extras (quote in zsh!)
pip install -e '.[mcp]'

# Run stdio server (Claude Desktop compatible)
crew_mcp

# Or via Make
make run-mcp

# Enable optional modules via env
export ENABLE_MCP_MEMORY=1 ENABLE_MCP_ROUTER=1 ENABLE_MCP_OBS=1
```

### Testing, compliance, and docs
- **Guards bundle**: `make guards` (dispatcher usage, http wrapper usage, metrics instrumentation, tools exports). These enforce repo conventions—run after adding/modifying tools, HTTP clients, or downloaders.
- **Compliance surfaces**: `make compliance` / `compliance-fix` when touching HTTP wrappers or `StepResult` handling. Auto-migration scripts available for bulk fixes.
- **Feature flags doc**: `make docs-flags-write` regenerates `docs/feature_flags.md` (manual edits are overwritten). Always regenerate after adding/changing flags in `core/settings.py`.
- **Type guard**: `make type-guard` fails if mypy error count increases vs baseline. Fix errors instead of updating baseline; only run `make type-guard-update` after reducing errors.

### Integration notes and examples
- **OpenRouterService**: prefer `with_tenant(...)` around calls so routing, caches, and bandits are tenant‑aware; semantic cache controlled by `ENABLE_SEMANTIC_CACHE(_PROMOTION|_SHADOW)`.
- **Memory**: `tools/memory_storage_tool` writes to Qdrant when configured; otherwise returns a `StepResult` indicating skipped/dummy—tests may check `custom_status`.
- **Example HTTP usage**: `from core.http_utils import resilient_get; res = resilient_get(url, timeout_seconds=30)` (do not import `requests`).

### Common Issues & Solutions

#### "Nothing happens" - Check feature flags
```bash
# Many features are off by default
export ENABLE_HTTP_RETRY=1
export ENABLE_RAG_CONTEXT=1
export ENABLE_SEMANTIC_CACHE=1
# See docs/feature_flags.md for full list
```

#### Import errors - Use correct paths
```python
# ✅ Correct imports
from core.http_utils import resilient_get
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy import with_tenant, TenantContext
from obs.metrics import get_metrics

# ❌ Wrong - will fail
import requests  # Use core.http_utils instead
from tools import MyTool  # Use full path: ultimate_discord_intelligence_bot.tools
```

#### Test failures - Environment precedence
```bash
# If retry tests fail, env vars may override config
make test-fast-clean-env  # Unsets RETRY_MAX_ATTEMPTS before running

# If vector tests fail, check Qdrant
make doctor  # Shows vector store status
```

#### Type checking - Don't add to baseline
```bash
make type-guard  # Fails if mypy errors increase
# Fix errors instead of updating baseline
# Only update baseline after reducing errors:
make type-guard-update
```

#### Zsh glob expansion
```bash
# ❌ Fails in zsh
pip install -e .[dev]

# ✅ Quote the extras
pip install -e '.[dev]'
```

Questions or gaps? Open a PR comment or ask for clarifications; we'll iterate on unclear sections here.

---

## Architecture Overview

### Pipeline & Orchestration
- **`ContentPipeline`** (`src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py`) orchestrates download → Drive upload → transcription → analysis → memory/Discord in stages; every phase returns a `StepResult`, transcripts/summaries get PII-filtered via `_apply_pii_filtering`, and concurrency is built-in (downloads + Drive run together; analysis fans out to fallacy/perspective/memory/Discord/graph tasks).
- **Budget tracking**: `PipelineExecutionMixin._pipeline_pkg.track_request_budget` provides cost guards; always enter `_pipeline_context` so tracing spans (`tracing_module.start_span`) and metrics counters fire, even on early returns.
- **Legacy shim**: `src/ultimate_discord_intelligence_bot/pipeline.py` exports `ContentPipeline`, `track_request_budget`, `privacy_filter`, and `metrics` for legacy scripts.

### Modular `src/` Layout
- **`ultimate_discord_intelligence_bot`**: main bot + tools + pipeline
- **`core`**: 54+ shared utils (http_utils, secure_config, time, settings)
- **`obs`**: observability (metrics, tracing, enhanced monitoring)
- **`memory`**: vector stores, Qdrant
- **`ingest`**: multi-platform downloaders
- **`analysis`**: transcription, topics, segmentation
- **`security`**: moderation, RBAC, rate limiting
- **`scheduler`**: task scheduling
- **`server`**: FastAPI
- **`mcp_server`**: Model Context Protocol
- **`debate`**: structured argumentation
- **`grounding`**: citation enforcement

---

## Architecture Overview
- **`ContentPipeline`** (`src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py`) orchestrates download → Drive upload → transcription → analysis → memory/Discord in stages; every phase returns a `StepResult`, transcripts/summaries get PII-filtered via `_apply_pii_filtering`, and concurrency is built-in (downloads + Drive run together; analysis fans out to fallacy/perspective/memory/Discord/graph tasks).
- Budget tracking: `PipelineExecutionMixin._pipeline_pkg.track_request_budget` provides cost guards; always enter `_pipeline_context` so tracing spans (`tracing_module.start_span`) and metrics counters fire, even on early returns.
- `src/ultimate_discord_intelligence_bot/pipeline.py` is a CLI shim exporting `ContentPipeline`, `track_request_budget`, `privacy_filter`, and `metrics` for legacy scripts.
- **Modular `src/` layout**: `ultimate_discord_intelligence_bot` (main bot + tools + pipeline), `core` (54+ shared utils: http_utils, secure_config, time, settings), `obs` (observability: metrics, tracing, enhanced monitoring), `memory` (vector stores, Qdrant), `ingest` (multi-platform downloaders), `analysis` (transcription, topics, segmentation), `security` (moderation, RBAC, rate limiting), `scheduler`, `server` (FastAPI), `mcp_server` (Model Context Protocol), `debate` (structured argumentation), `grounding` (citation enforcement).

## Runtime Surfaces
- **FastAPI app** (`server/app.create_app`) wires feature-flagged middleware (metrics, tracing, rate limiting, Prometheus) and routers; `register_pipeline_routes` exposes pipeline via `PipelineTool` when `ENABLE_PIPELINE_RUN_API=1`, while `register_a2a_router` enables A2A JSON-RPC adapter behind `ENABLE_A2A_API=1`.
- **Discord bot** (`scripts/start_full_bot.py` delegates to `discord_bot.runner`) runs in gateway mode (`ENABLE_DISCORD_GATEWAY=1`) or headless mode with webhook heartbeat; auto-failover via `AUTO_FALLBACK_HEADLESS=1`. First-time command sync takes up to 60s globally (instant on dev servers).
- **Setup CLI** (`python -m ultimate_discord_intelligence_bot.setup_cli`) is the canonical tool: run `setup_cli wizard` to write `.env`, scaffold tenant config under `tenants/<slug>/`, then `setup_cli run discord|crew` to launch runtimes. Use `setup_cli doctor` for environment health checks.
- **MCP server** (`crew_mcp` after `pip install '.[mcp]'`) provides Model Context Protocol over stdio (Claude Desktop compatible) or HTTP (port 8001); enable feature modules via `ENABLE_MCP_MEMORY`, `ENABLE_MCP_ROUTER`, `ENABLE_MCP_OBS`, `ENABLE_MCP_KG`, `ENABLE_MCP_INGEST`, `ENABLE_MCP_HTTP`, `ENABLE_MCP_A2A`.
- **Qdrant initialization**: Clients eagerly created during FastAPI lifespan (`server/app._lifespan`); missing `QDRANT_URL` falls back to in-memory dummy suitable for tests only—look for debug logs if vector search fails.

## Tenancy & StepResult contract
- Always run tenant-scoped work inside `with_tenant(TenantContext(...))`; use `tenancy.mem_ns(ctx, name)` to derive `<tenant>:<workspace>:<suffix>` namespaces when touching vector memory or caches.
- `StepResult` is the universal return type—use `.ok()/.fail()/.skip()/.uncertain()` helpers and include a `step` field in payloads when bubbling errors so pipeline tests (e.g., `test_content_pipeline_e2e.py`) stay green.
- `StepResult.to_dict()` lowers to legacy payloads; avoid mutating the `.data` dict in-place after returning to keep mapping semantics predictable.
- When adding new pipeline branches (graph memory, compression, etc.), record skips via `_record_step_skip` so metrics plus request/retry counters remain accurate.

## Services & tenancy
- `services/openrouter_service.OpenRouterService` manages model routing, adaptive bandits, tenant-aware semantic cache, and distributed Redis caching; respect feature flags like `ENABLE_SEMANTIC_CACHE(_PROMOTION|_SHADOW)` and pass tenant context via `with_tenant` before invoking.
- Structured memories persist through `tools/memory_storage_tool.MemoryStorageTool`, writing to Qdrant when `QDRANT_URL` is set and falling back to an in-memory stub otherwise—factor this into tests by asserting against `StepResult.custom_status` for skipped graph writes.
- Observability helpers in `obs/` favour `metrics.label_ctx()` and `get_metrics().counter(..., labels={"tool": name, "outcome": status})`; the metrics guard enforces this on new tools.
- Start/stop hooks in `server/app._lifespan` launch enhanced monitoring and attempt a Qdrant warm-up; wrap new async startup tasks there so they inherit the same error handling.

## Tooling patterns
- New tools subclass `tools/_base.BaseTool`, implement `_run`, and return `StepResult.ok/skip/fail`; register them in `tools/__all__`, `tools.MAPPING`, and, when needed, `tools/multi_platform_download_tool.py::_init_dispatchers`.
- Instrument every tool run: call `metrics.get_metrics().counter("tool_runs_total", labels={"tool": self.name, "outcome": outcome})` (or equivalent) so `scripts/metrics_instrumentation_guard.py` passes; long-running tasks can layer `.histogram("tool_run_seconds", ...")`.
- Never call `yt-dlp` or `requests` directly—use `MultiPlatformDownloadTool` and `core/http_utils` wrappers; guard scripts (`validate_dispatcher_usage.py`, `validate_http_wrappers_usage.py`) will fail otherwise.
- When scheduling concurrent steps (analysis, fallacy, perspective, Discord, graph memory) cancel pending tasks if any branch errors and surface `StepResult.fail(..., step="<name>")` to preserve retry accounting.

### ⚠️ CRITICAL: CrewAI Tool Data Flow Pattern

**The `/autointel` command was completely rewritten (2025-01-03)** to use proper CrewAI architecture. See implementation in `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py`.

**✅ CORRECT PATTERN - Task Chaining (ALWAYS USE THIS)**:

CrewAI is designed for task chaining via the `context` parameter. Task outputs automatically flow to dependent tasks.

```python
# ✅ CORRECT: Build ONE crew with chained tasks
def _build_intelligence_crew(self, url: str, depth: str) -> Crew:
    # Get cached agents (created once, reused across all tasks)
    acquisition_agent = self._get_or_create_agent("acquisition_specialist")
    transcription_agent = self._get_or_create_agent("transcription_engineer")
    analysis_agent = self._get_or_create_agent("analysis_cartographer")
    
    # Create tasks with high-level descriptions (NO embedded data!)
    acquisition_task = Task(
        description="Acquire and download content from {url}",  # Uses {url} placeholder for kickoff inputs
        agent=acquisition_agent,
        expected_output="Complete media file with metadata"
    )
    
    # Chain tasks via context parameter (data flows automatically)
    transcription_task = Task(
        description="Enhance and index the acquired media transcript",  # High-level instruction
        agent=transcription_agent,
        context=[acquisition_task],  # ✅ CRITICAL: Receives acquisition output automatically
        expected_output="Enhanced transcript with timeline anchors"
    )
    
    analysis_task = Task(
        description="Analyze linguistic patterns and sentiment in transcript",
        agent=analysis_agent,
        context=[transcription_task],  # ✅ Receives transcription output automatically
        expected_output="Comprehensive content analysis"
    )
    
    # Return ONE crew with all tasks
    return Crew(
        agents=[acquisition_agent, transcription_agent, analysis_agent],
        tasks=[acquisition_task, transcription_task, analysis_task],
        process=Process.sequential
    )

# Execute crew with initial inputs
result = await asyncio.to_thread(crew.kickoff, inputs={"url": url, "depth": depth})
```

**❌ BROKEN PATTERNS (NEVER DO THIS)**:

```python
# ❌ WRONG: Creating separate crews per stage
for stage in stages:
    crew = Crew(agents=[agent], tasks=[Task(...)])  # Breaks data flow!
    result = crew.kickoff()

# ❌ WRONG: Embedding data in task descriptions
task = Task(
    description=f"Analyze this transcript: {transcript[:500]}...",  # LLMs can't extract this!
    agent=agent
)

# ❌ WRONG: Creating fresh agent instances mid-workflow
crew_instance = UltimateDiscordIntelligenceBotCrew()
agent = crew_instance.analysis_cartographer()  # Bypasses caching and context population!
```

**Why This Matters**:
- CrewAI LLMs **cannot** extract structured data from task descriptions
- When you write `description=f"Analyze: {transcript}"`, the LLM sees text but provides placeholder params like `"the transcript"` when calling tools
- Task chaining via `context=[previous_task]` makes outputs flow automatically through CrewAI's internal context system
- Creating separate crews breaks the data pipeline between stages

**Agent Caching Pattern**:
- ALWAYS use `self._get_or_create_agent("agent_name")` to get agents
- Agents are created ONCE and cached in `self.agent_coordinators`
- `_populate_agent_tool_context(agent, context_data)` populates tools' `_shared_context` as a fallback mechanism
- Same agent instance is reused across all tasks, preserving context

**When adding /autointel features**:
1. Add tasks to `_build_intelligence_crew()` with proper `context=[previous_task]` chaining
2. Use high-level task descriptions like "Analyze transcript" NOT "Analyze: {data}"
3. Get agents via `self._get_or_create_agent("agent_name")`, never create fresh instances
4. Pass initial data through `crew.kickoff(inputs={...})`, not task descriptions

## HTTP, config, and time
- Use `core/http_utils` (`resilient_get`, `resilient_post`, `http_request_with_retry`) for outbound calls; retry precedence is call args → tenant `retry.yaml` → `config/retry.yaml` → `RETRY_MAX_ATTEMPTS` env → secure-config defaults.
- Read secrets/config via `core.secure_config.get_config()` instead of `os.getenv`; this also enforces audit logging when `ENABLE_AUDIT_LOGGING` is on.
- Generate timestamps with `core/time.ensure_utc()` or `default_utc_now()` so logs, metrics, and storage remain UTC; the Discord heartbeat loop relies on this.
- Feature toggles live in `core/settings.py` + `.env`; regenerate docs via `make docs-flags-write` because `docs/feature_flags.md` is auto-generated (manual edits are overwritten).

## Developer Workflow
- **First-time setup**: `make first-run` (creates `.venv`, installs `.[dev]`, configures hooks, runs doctor, then executes `make quick-check`); always quote extras in zsh (`pip install -e '.[dev]'`).
- **Daily loop**: `make quick-check` (ruff format + lint + test-fast) or `./scripts/dev-workflow.sh quick-check`; the script also offers `full-check`, `fix-common`, `setup-hooks`, and `organize-root` helpers.
- **Operations CLI** lives at `python -m ultimate_discord_intelligence_bot.setup_cli`; run `setup_cli doctor` for env checks and `setup_cli run discord|crew` to start runtimes (or use legacy `scripts/start_full_bot.py`).
- **Enhanced Discord**: use `make run-discord-enhanced` to enable semantic cache, prompt compression, graph memory, and HippoRAG with shadow-safe defaults.
- **Situational Make targets**: `make test-fast` / `test-fast-clean-env` (resets `RETRY_MAX_ATTEMPTS`), `make type`, `make docs`, `make docs-flags-write` (regenerate feature_flags.md), `make run-crew`, `make run-a2a-client-demo`, `make run-mcp`, `make compliance` when touching HTTP/tool surfaces.
- **Optional extras**: `pip install -e '.[metrics]'` (Prometheus), `'.[whisper]'` (OpenAI Whisper - requires Python 3.11 if numba issues on 3.12), `'.[vllm]'` (local GPU inference), `'.[mcp]'` (Model Context Protocol server).

## Testing & compliance
- `tests/test_content_pipeline_e2e.py` asserts success/error flows, concurrency (<0.18s path), tenant isolation, and `graph_memory` payloads; adjust mocks when adding new pipeline outputs.
- `tests/test_openrouter_*` lock down routing/caching; update shadow/promotion flags alongside tests when touching OpenRouterService semantics.
- `make guards` chains `scripts/validate_dispatcher_usage.py`, `scripts/validate_http_wrappers_usage.py`, `scripts/metrics_instrumentation_guard.py`, and `scripts/validate_tools_exports.py`; run after adding tools, HTTP clients, or downloaders.
- Run `make compliance` (or `make compliance-fix`) whenever touching HTTP wrappers or `StepResult` handling; docs/config parity relies on `make docs`, which also regenerates deprecation badges and configuration manifests.
