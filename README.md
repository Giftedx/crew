# Giftedx Crew

Giftedx Crew is a tenant‑aware Discord platform that ingests public media, builds grounded context, and answers questions through cost‑guarded model routing and reinforcement learning. The system emphasises privacy, provenance, and reliability so features can be rolled out safely.

## Features
- **Core services** – prompt builder, token meter, router with cost guards, caching, RL hooks, alerts, reliability patterns, and tool planning.
- **Ingestion & RAG** – async adapters for YouTube, Twitch, and TikTok, transcript analysis with segmentation, Qdrant vector memory, and Discord commands like `/creator`, `/latest`, `/context`, `/collabs`, and `/verify_profiles`.
- **Privacy & governance** – policy engine, deterministic PII detection and redaction, provenance logging, retention sweeps, export tooling, and RBAC security.
- **Cost & reliability** – budgets, retries, circuit breakers, shadow/canary rollout, feature flags, and comprehensive observability.
- **Discord CDN archiver** – size‑aware compression, policy checks, channel routing, manifest deduplication, and rehydration of expiring CDN links.
- **Unified memory layer** – SQLite/Qdrant backed store with retention policies, pinning, archival, and hybrid retrieval.
- **Grounded answers** – citation‑enforced responses with verifier checks, claim extraction, logical fallacy detection, and Discord audit helpers.
- **Reinforcement learning** – feature store, reward engine, bandit policies, and a `learn` helper to integrate decision loops across routing, prompting, and retrieval.
- **Debate & scheduler** – multi-role debate panel, perspective synthesis, steelman arguments, and RL-paced ingest scheduler for ongoing refinement.
- **Advanced analysis** – sentiment analysis, trustworthiness tracking, timeline construction, and comprehensive content analysis tools.

See the documentation for full subsystem guides:
- [Tools Reference](docs/tools_reference.md) - Comprehensive tool documentation
- [Network & HTTP Conventions](docs/network_conventions.md) - Shared helpers for URL validation, resilient POST/GET, timeouts, and rate limiting
- [Analysis Modules](docs/analysis_modules.md) - Transcript processing and content analysis
- [Configuration Reference](docs/configuration.md) - Complete configuration guide
- [Core services](docs/core_services.md) - Foundation utilities and services
- [Cost guards and caching](docs/cost_and_caching.md) - Budget management and caching
- [Ingestion](docs/ingestion.md) and [RAG usage](docs/rag.md) - Content ingestion and retrieval
- [Privacy](docs/privacy.md), [provenance](docs/provenance.md), and [retention](docs/retention.md) - Data governance
- [Discord CDN archiver](docs/archiver.md) - CDN link preservation
- [Reinforcement learning](docs/rl_overview.md) - RL system overview
- [Scheduler and connectors](docs/scheduler.md) - Content polling and scheduling
- [Knowledge graph](docs/kg.md) - Entity and relationship extraction
- [Unified memory](docs/memory.md) - Memory management and storage
- [Grounding guarantees](docs/grounding.md) - Citation enforcement and verification
 - [Runtime data artifacts](docs/runtime_data.md) - Locations and overrides for mutable state (SQLite/JSON)

## Getting started
1. Install Python ≥3.10 and clone the repository.
2. Install dependencies (editable mode) and dev extras for tooling:
   ```bash
   pip install -e .[dev]
   # add [metrics] extra to enable Prometheus support
   # pip install -e .[metrics]
   ```
3. Copy the example environment and fill in required tokens such as
   `OPENAI_API_KEY` or `OPENROUTER_API_KEY` plus Discord webhooks:
   ```bash
   cp .env.example .env
   # edit .env
   ```
4. Run the tests:
   ```bash
   pytest
   ```

### Developer workflow

Core quality tooling is configured via Ruff (lint + format) and mypy (incremental typing). See `CONTRIBUTING.md` for full guidelines and the baseline policy:

```bash
make format   # auto-fix style & imports
make lint     # lint only (CI style)
make type     # static type check (non-blocking initially)
make test     # run pytest suite
make docs     # validate documentation & config references
```

Or use the helper script:

```bash
./scripts/dev.sh format
./scripts/dev.sh type-changed            # mypy only changed files vs origin/main
./scripts/dev.sh type-baseline           # check current mypy error count vs baseline
./scripts/dev.sh type-baseline-update    # update baseline if improved
```

Install pre-commit hooks to ensure consistent formatting before commits:

```bash
pre-commit install --install-hooks
```

The type checking configuration is intentionally permissive for gradual adoption; prefer adding precise annotations to new/modified code rather than sweeping refactors.

### Plugin capability tests

Plugins can validate their behaviour via a lightweight testkit:

```bash
python -m ultimate_discord_intelligence_bot.plugins.testkit.cli --plugin ultimate_discord_intelligence_bot.plugins.example_summarizer
```

## Quick ingest example
```bash
python -m ingest.pipeline https://youtu.be/dummy --tenant default --workspace main
```

Tenants are configured under `tenants/<slug>/` with a `tenant.yaml` plus optional
`routing.yaml` and `budgets.yaml` for model allowlists and per-tenant cost caps.
Then query stored context:
```bash
python - <<'PY'
from memory.vector_store import VectorStore
from discord.commands import context_query

store = VectorStore()
ns = VectorStore.namespace('default', 'main', 'dummy')
print(context_query(store, ns, 'hello'))
PY
```

## Poller quickstart
```python
from scheduler import Scheduler, PriorityQueue
from ingest.sources.youtube import YouTubeConnector
from ingest import models

conn = models.connect('ingest.db')
queue = PriorityQueue(conn)
sched = Scheduler(conn, queue, {"youtube": YouTubeConnector()})
sched.add_watch(tenant='default', workspace='main', source_type='youtube', handle='vid1')
sched.tick()
sched.worker_run_once(store=None)
```

## Feature flags
Core subsystems are disabled by default and enabled via environment flags:
- **Ingestion:** `ENABLE_INGEST_YOUTUBE`, `ENABLE_INGEST_TWITCH`, `ENABLE_INGEST_TIKTOK`
- **RAG & Context:** `ENABLE_RAG_CONTEXT`, `ENABLE_VECTOR_SEARCH`, `ENABLE_GROUNDING`
- **Caching & Performance:** `ENABLE_CACHE`, `ENABLE_CACHE_LLM`, `ENABLE_CACHE_VECTOR`
- **Reinforcement Learning:** `ENABLE_RL_GLOBAL` (plus `ENABLE_RL_ROUTING`, `ENABLE_RL_PROMPT`, `ENABLE_RL_RETRIEVAL`)
- **Discord Integration:** `ENABLE_DISCORD_ARCHIVER`, `ENABLE_DISCORD_COMMANDS`, `ENABLE_DISCORD_MONITOR`
- **Security & Privacy:** `ENABLE_PII_DETECTION`, `ENABLE_CONTENT_MODERATION`, `ENABLE_RATE_LIMITING`
- **Observability:** `ENABLE_TRACING`, `ENABLE_METRICS`, `ENABLE_AUDIT_LOGGING`
 - **HTTP Resilience:** `ENABLE_ANALYSIS_HTTP_RETRY` (enables exponential backoff + jitter retry layer via `retrying_post` / `retrying_get`; when disabled, single-attempt behavior preserved)

See [Configuration Reference](docs/configuration.md) for complete flag documentation.

## Contributing
Follow the guidelines in [AGENTS.md](AGENTS.md) and the broader contribution steps in [CONTRIBUTING.md](CONTRIBUTING.md): reuse existing modules, add tests, run `pytest`, and commit using Conventional Commits.

Additional guidelines:
- Keep changes tenant‑aware (always pass explicit tenant/workspace context).
- Guard new subsystems with `ENABLE_<AREA>_<FEATURE>` flags.
- Return `StepResult` instead of raising for recoverable tool/pipeline errors.
- Add/extend docs under `docs/` for new config keys or tools and run `make docs`.
- Prefer small, focused PRs: config, typing, logic changes separate when feasible.

## Golden Evaluation Suite

Run the golden tests to ensure quality, cost, and latency stay within limits:

```bash
python -m eval.runner datasets/golden/core/v1 baselines/golden/core/v1/summary.json
```

## Observability

Tracing and metrics utilities live under `obs`.  Initialise tracing and record a
router decision:

```python
from obs import tracing, metrics
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant
tracing.init_tracing("crew-dev")
with with_tenant(TenantContext("t", "w")):
    metrics.ROUTER_DECISIONS.labels(**metrics.label_ctx()).inc()
```

See [docs/observability.md](docs/observability.md) for more details.
