# Capability Map

This document maps the project’s capabilities across all major subsystems, with key modules, flags, and cross-dependencies to help you navigate and extend the codebase.

## Architecture Overview

Ingestion → Transcription → Analysis (segment, topics, rerank) → Memory (store + vector) → Grounding/Retriever/Verifier → Routing & RL → API/Discord/Crew entrypoints → Scheduler → Observability → Policy/Security → HTTP/Retry/Caching.

## Ingestion

- Orchestrator: `src/ingest/pipeline.py`
  - Steps: fetch metadata + transcript (concurrent flag), transcription (Whisper/faster‑whisper fallback), segmentation, privacy filter, topics extraction, dedup embeddings, Qdrant upsert, optional provenance to SQLite.
  - Flags: `ENABLE_INGEST_CONCURRENT`, `ENABLE_INGEST_STRICT`, privacy and caching flags (see Policy/Security, Memory).
  - Metrics: step counters/histograms via `obs.metrics`.
- Providers: `src/ingest/providers/youtube.py`, `src/ingest/providers/twitch.py`
  - Metadata/transcript helpers; yt-dlp path.
- Sources/connectors: `src/ingest/sources/base.py`, `src/ingest/sources/youtube.py`, `src/ingest/sources/twitch.py`
  - Discovery emitters used by scheduler.
- Models/DB: `src/ingest/models.py`
  - SQLite tables and helpers for provenance, usage, jobs, watchlists, ingest state.

## Transcription

- Module: `src/analysis/transcribe.py`
  - Primary: OpenAI Whisper; Optional: `faster-whisper` when `enable_faster_whisper` is true.
  - Fallbacks: plaintext line-per-second with degradation events via `core.degradation_reporter`.
  - Config: `Settings.enable_faster_whisper`, `Settings.whisper_model` (via `core.secure_config`).

## Analysis

- Segmenter: `src/analysis/segmenter.py`
  - Chunks transcript into overlapping windows.
  - Token-aware mode: `Settings.enable_token_aware_chunker`, target tokens `token_chunk_target_tokens`.
  - Metrics: chunk sizes, merges, step counter.
- Topics: `src/analysis/topics.py`
  - Extracts hashtags, entities, keywords, phrases; naive topic categories.
- Reranker: `src/analysis/rerank.py`
  - Providers: Cohere, Jina via `core.http_utils.resilient_post`; degradation identity fallbacks.
  - Config: `enable_reranker`, `rerank_provider` in secure config.

## Memory Layer

- Unified API: `src/memory/api.py`
  - store/retrieve/prune/pin/archive; optional rerank on retrieve.
  - Privacy filter applied before storage; archived content persisted via `archive.archive_file`.
- Store: `src/memory/store.py`
  - SQLite tables for items + retention policies; TTL prune, pin/archive flags.
- Embeddings: `src/memory/embeddings.py`
  - Deterministic hash-based vectors; optional Redis cache (`enable_cache_vector`, `rate_limit_redis_url`).
- Vector store: `src/memory/vector_store.py`
  - Qdrant wrapper with namespace mapping `tenant:workspace:creator`; batch upsert; dummy fallback OK.
- Qdrant provider: `src/memory/qdrant_provider.py`
  - Central factory; in‑memory dummy for `:memory:` or when client missing; supports gRPC prefs.

## Grounding / Retrieval / Verification

- Retriever: `src/grounding/retriever.py` delegates to memory API; returns `EvidencePack`.
- Verifier: `src/grounding/verifier.py` checks `AnswerContract` against rules; reports missing citations/contradictions.
- Schema: `src/grounding/schema.py` for `Evidence` and `AnswerContract` (requires at least one citation).

## Routing and Reinforcement Learning

- Learning engine: `src/core/learning_engine.py`
  - Policies: EpsilonGreedy, Thompson, UCB1, LinUCB, LinTS; experiment harness and shadow bakeoffs.
  - Flags: `ENABLE_RL_*`, `ENABLE_EXPERIMENT_HARNESS`, `ENABLE_RL_SHADOW`.
- Router: `src/core/router.py`
  - Candidate filtering via tenant registry; preflight with budget guard (`core/token_meter`).
- Token/cost meter: `src/core/token_meter.py`
  - Heuristic tokens, cost estimates, per‑tenant budgets with `BudgetStore`.

## Scheduler and Queueing

- Scheduler: `src/scheduler/scheduler.py`
  - Watchlists, discovery, RL‑paced polling, batch enqueues/updates, worker loop, metrics.
- Priority queue: `src/scheduler/priority_queue.py`
  - SQLite-backed enqueue/dequeue; bulk operations; batching metrics exposure.

## Policy and Security

- Policy engine: `src/policy/policy_engine.py` (loads `config/policy.yaml` + tenants overrides).
- Security modules: `src/security/*`
  - Moderation (`moderation.py`) with review queue + events.
  - Network guard (`net_guard.py`) safe fetch with redirect/content/type enforcement.
  - Webhook guard (`webhook_guard.py`) HMAC verification with rotation.
  - Secrets (`secrets.py`) env‑backed with simple versioning + cache.
  - Rate limiters, RBAC, validation, signing, secret rotation (see package for details).

## HTTP / Retry / Caching

- HTTP helpers: `src/core/http_utils.py`
  - `resilient_get/post`, feature‑flagged retry/backoff with metrics/tracing.
  - URL validation (`https` + public IPs), cached GETs (Redis/in‑mem), negative cache.
  - Flags: `ENABLE_HTTP_RETRY`, legacy analysis-scoped retry flag (deprecated; see `docs/retries.md`), `RETRY_MAX_ATTEMPTS`.
- Cache stack: `src/core/cache/*` (API cache middleware, multi‒level cache, Redis helpers, semantic cache).

## Observability

- Metrics: `src/obs/metrics.py` (central registry; no‒op fallback when prometheus_client missing).
- Tracing: `src/obs/tracing.py` (OpenTelemetry optional; console or OTLP exporter).
- Degradation reporter: `src/core/degradation_reporter.py` (flag `ENABLE_DEGRADATION_REPORTER`).
- Enhanced monitoring: `src/obs/enhanced_monitoring.py` lifecycle hooks from API lifespan.

## Entrypoints / CLI / Services

- Setup wizard/runner: `src/ultimate_discord_intelligence_bot/setup_cli.py` (writes .env, creates tenants, launches run targets).
- FastAPI app: `src/server/app.py` (metrics middleware, `/metrics`, rate limiting, alert router, optional tracing/monitoring).
- Discord command helpers: `src/discord/commands.py` (ops utilities, ingest actions, memory ops, debate tools).
- Crew orchestration: `src/ultimate_discord_intelligence_bot/crew.py` (agents, tasks, tools, validation, step logging).

## Database Batching Utilities

- `core/batching.py` provides `RequestBatcher`, `BulkInserter`, metrics and managers.
- Used by scheduler and queue for reduced DB round‑trips and better throughput.

## Tests

- Extensive suite under `tests/` covering ingestion, analysis, memory, routing/RL, grounding, HTTP, security, server, tools, and settings behavior (including deprecations).
- Run selectively for fast feedback (example categories):
  - Analysis: `tests/test_analysis_*`
  - HTTP/Retry: `tests/test_http_*`
  - Memory/Vector: `tests/test_memory_*`, `tests/test_vector_*`
  - Scheduler/Ingest: `tests/test_ingest_*`, `tests/test_scheduler_*`

## Feature Flags (selected)

- Ingestion: `ENABLE_INGEST_CONCURRENT`, `ENABLE_INGEST_STRICT`
- Analysis: `enable_token_aware_chunker`, `token_chunk_target_tokens`, `enable_reranker`, `rerank_provider`, `enable_faster_whisper`, `whisper_model`
- Memory/Cache: `ENABLE_CACHE_GLOBAL`, `ENABLE_CACHE_TRANSCRIPT`, `ENABLE_CACHE_VECTOR`, `ENABLE_HTTP_CACHE`, `enable_http_negative_cache`
- Routing/RL: `ENABLE_RL_GLOBAL`, `ENABLE_RL_ROUTING`, `ENABLE_RL_PROMPT`, `ENABLE_RL_RETRIEVAL`, `ENABLE_EXPERIMENT_HARNESS`, `ENABLE_RL_SHADOW`, `ENABLE_RL_LINTS`
- HTTP Retry: `ENABLE_HTTP_RETRY`, `RETRY_MAX_ATTEMPTS` (with `config/retry.yaml` overrides)
- Observability: `ENABLE_TRACING`, `ENABLE_PROMETHEUS_ENDPOINT`, `ENABLE_DEGRADATION_REPORTER`
- Security/Rate limiting: `ENABLE_RATE_LIMITING` (+ Redis url), moderation and network policies via `config/security.yaml`

## Cross‑Dependencies

- Ingestion → Analysis (transcribe/segmenter/topics) → Memory (embeddings/vector_store) → Observability (metrics/degradation).
- Memory retrieval may rerank via Analysis.rerank if enabled.
- Router uses TokenMeter and LearningEngine; TenantRegistry constrains candidates.
- Scheduler uses Watch connectors to enqueue pipeline jobs; DB batching reduces contention.
- API app wires tracing/metrics and monitoring; Discord/Crew layers call into core/memory/grounding.

## Extension Tips

- Add a new ingestion source under `ingest/sources/` and register its connector in the dispatcher; include provider fetcher.
- New analysis step: add a module that returns a simple dataclass result; integrate in pipeline behind a feature flag.
- New rerank provider: extend `src/analysis/rerank.py` following Cohere/Jina pattern using `src/core/http_utils.py`.
- Memory schema changes: prefer additive updates and keep `MemoryStore` pruning deterministic.
- Always thread tenant/workspace context early and use `obs.metrics.label_ctx()` for metric labels.

---
Maintainer note: keep this document in sync when adding features. See also: `docs/feature_flags.md`, `docs/observability.md`, `docs/ingestion.md`, `docs/memory.md`.
