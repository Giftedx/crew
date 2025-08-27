# Giftedx Crew

Giftedx Crew is a tenant‑aware Discord platform that ingests public media, builds grounded context, and answers questions through cost‑guarded model routing and reinforcement learning. The system emphasises privacy, provenance, and reliability so features can be rolled out safely.

## Features
- **Core services** – prompt builder, token meter, router with cost guards, caching, and RL hooks.
- **Ingestion & RAG** – async adapters for YouTube and Twitch, transcript analysis, Qdrant vector memory, and Discord commands like `/creator`, `/latest`, `/context`, `/collabs`, and `/verify_profiles`.
- **Privacy & governance** – policy engine, deterministic PII detection and redaction, provenance logging, retention sweeps, export tooling.
- **Cost & reliability** – budgets, retries, circuit breakers, shadow/canary rollout, feature flags.
- **Discord CDN archiver** – size‑aware compression, policy checks, channel routing, manifest deduplication, and rehydration of expiring CDN links.
- **Unified memory layer** – SQLite/Qdrant backed store with retention policies, pinning, archival, and hybrid retrieval.
- **Grounded answers** – citation‑enforced responses with verifier checks and Discord audit helpers.
- **Reinforcement learning** – feature store, reward engine, bandit policies, and a `learn` helper to integrate decision loops across routing, prompting, and retrieval.
- **Debate & scheduler** – multi-role debate panel and RL-paced ingest scheduler for ongoing refinement.

See the documentation for full subsystem guides:
- [Core services](docs/core_services.md)
- [Cost guards and caching](docs/cost_and_caching.md)
- [Ingestion](docs/ingestion.md) and [RAG usage](docs/rag.md)
- [Privacy](docs/privacy.md), [provenance](docs/provenance.md), and [retention](docs/retention.md)
- [Discord CDN archiver](docs/archiver.md)
- [Reinforcement learning](docs/rl_overview.md)
- [Scheduler and connectors](docs/scheduler.md)
- [Knowledge graph](docs/kg.md)
- [Unified memory](docs/memory.md)
- [Grounding guarantees](docs/grounding.md)

## Getting started
1. Install Python ≥3.10 and clone the repository.
2. Install dependencies:
   ```bash
   pip install -e .
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
Subsystems are disabled by default and enabled via environment flags:
- `ENABLE_INGEST_YOUTUBE`, `ENABLE_INGEST_TWITCH`
- `ENABLE_RAG_CONTEXT`
- `ENABLE_CACHE`
- `ENABLE_RL_GLOBAL` (plus `ENABLE_RL_ROUTING`, `ENABLE_RL_PROMPT`, `ENABLE_RL_RETRIEVAL`)
- `ENABLE_DISCORD_ARCHIVER`

## Contributing
Follow the guidelines in [AGENTS.md](AGENTS.md): reuse existing modules, add tests, run `pytest`, and commit using Conventional Commits.

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
