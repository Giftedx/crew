# Giftedx Crew

Giftedx Crew is a tenant‑aware Discord platform that ingests public media, builds grounded context, and answers questions through cost‑guarded model routing and reinforcement learning. The system emphasises privacy, provenance, and reliability so features can be rolled out safely.

## Features
- **Core services** – prompt builder, token meter, router with cost guards, caching, and RL hooks.
- **Ingestion & RAG** – async adapters for YouTube and Twitch, transcript analysis, Qdrant vector memory, and Discord commands like `/creator`, `/latest`, `/context`, `/collabs`, and `/verify_profiles`.
- **Privacy & governance** – policy engine, deterministic PII detection and redaction, provenance logging, retention sweeps, export tooling.
- **Cost & reliability** – budgets, retries, circuit breakers, shadow/canary rollout, feature flags.
- **Discord CDN archiver** – size‑aware compression, policy checks, channel routing, manifest deduplication, and rehydration of expiring CDN links.
- **Reinforcement learning** – feature store, reward engine, bandit policies, and a `learn` helper to integrate decision loops across routing, prompting, and retrieval.

See the documentation for full subsystem guides:
- [Core services](docs/core_services.md)
- [Cost guards and caching](docs/cost_and_caching.md)
- [Ingestion](docs/ingestion.md) and [RAG usage](docs/rag.md)
- [Privacy](docs/privacy.md), [provenance](docs/provenance.md), and [retention](docs/retention.md)
- [Discord CDN archiver](docs/archiver.md)
- [Reinforcement learning](docs/rl_overview.md)

## Getting started
1. Install Python ≥3.10 and clone the repository.
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Copy the example environment and fill in required tokens:
   ```bash
   cp .env.example .env
   # edit .env
   ```
4. Run the tests:
   ```bash
   pytest
   ```

## Quick ingest example
```bash
python -m ingest.pipeline https://youtu.be/dummy --tenant default --workspace main
```
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

## Feature flags
Subsystems are disabled by default and enabled via environment flags:
- `ENABLE_INGEST_YOUTUBE`, `ENABLE_INGEST_TWITCH`
- `ENABLE_RAG_CONTEXT`
- `ENABLE_CACHE`
- `ENABLE_RL_GLOBAL` (plus `ENABLE_RL_ROUTING`, `ENABLE_RL_PROMPT`, `ENABLE_RL_RETRIEVAL`)
- `ENABLE_DISCORD_ARCHIVER`

## Contributing
Follow the guidelines in [AGENTS.md](AGENTS.md): reuse existing modules, add tests, run `pytest`, and commit using Conventional Commits.
