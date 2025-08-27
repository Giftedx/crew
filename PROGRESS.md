# Progress Tracker

## PR1 – Core Services
- [x] prompt_engine
- [x] token_meter
- [x] router
- [x] learning_engine
- [x] eval_harness
- [x] logging schema

## PR2 – Ingestion → Memory → RAG foundation
- [x] adapters for YouTube/Twitch/VOD/social
- [x] vector DB namespaces per tenant/workspace/creator
- [x] transcription, diarization, topic tagging tasks
- [x] Discord commands: /creator, /latest, /context, /collabs, /verify_profiles

## PR3 – RL Everywhere
- [x] routing domain wiring
- [x] prompt domain wiring
- [x] retrieval domain wiring
 - [x] tool planning domain
- [x] cache/compression domain
- [x] safety/redaction domain
- [x] scheduler domain
 - [x] plugin runtime domain

## PR4 – Cost Guards, Budgets, Caching, Cold-Start & Reliability
- [x] token_meter cost guards and budgets
- [x] multi-tier caching layer
- [x] cold-start priors and shadow bakeoffs
- [x] reliability primitives (retries, breakers)
 - [x] shadow/canary rollout controller

## PR5 – Privacy, PII, Policy & Provenance
- [x] policy engine and config
- [x] PII detection & redaction
- [x] provenance & usage logging
- [x] retention sweeper & export tool
 - [x] Discord ops privacy commands

## PR6 – Multi-Tenant Isolation
- [x] tenancy models + context + registry
- [x] per-tenant routing profiles
- [x] per-tenant budgets
 - [x] policy/privacy overrides
 - [x] observability & audit tagging

## PR7 – Discord CDN Archiver (future-proof)
- [x] router + routes config
- [x] policy layer + EXIF redaction
- [x] limits detection
- [x] compressors and segmenting stubs
- [x] uploader with retries
- [x] manifest with dedup & compression params
- [x] rehydrate helpers
- [x] REST façade + CLI
- [x] basic tests & docs

## PR8 – Plugins & Extensions
- [x] manifest schema and sandbox executor
- [x] tenant-scoped registry and adapters
- [x] plugin ops commands and samples
- [x] docs and testkit

## PR9 – Plugin Marketplace, Signing & Trust Tiers
- [x] marketplace models and signing helpers
- [x] trust-tier policies and ceilings
- [x] staged rollout tooling
- [x] tests and docs

## PR10 – Plugin Capability Tests & Publish/Install Gates
- [x] manifest tests block and golden datasets
- [x] testkit runner with scorers
- [x] CI workflow and install gates
- [x] docs and sample plugins

## PR11 – Continuous Poller, Schedulers & Monitoring
- [x] watchlists and ingest job queue
- [x] minimal youtube/twitch connectors
- [x] priority queue + scheduler worker
- [x] Discord ops commands for watchlists
 - [x] RL hooks and advanced metrics

## PR12 – Global Golden Evaluation Suite & Regression Gates
- [x] core dataset and baseline
- [x] evaluation runner and scorers
- [x] regression gate comparison
- [x] GitHub workflow

## PR13 – Observability, Tracing, SLOs & Incident Response
- [x] tracing and metrics helpers
- [x] incident tracker with Discord ops
- [x] SLO evaluator

## PR14 – Knowledge Graph, Cross-Content Linking & Temporal Reasoning
- [x] schema and store for nodes and edges
- [x] naive entity/claim extractor
- [x] timeline reasoner
- [x] DOT renderer for subgraphs

## PR15 – Multi-Agent Debate, Consensus & Ensemble Reasoning
- [x] panel configuration and run helper
- [x] SQLite debate store
 - [x] Discord ops commands
 - [x] RL reward integration

| Phase | Item | Status | Notes |
|------:|------|:------:|-------|
| PR2 | Adapters (YT/Twitch + fixtures) | ✅ | |
| PR2 | Transcription + chunking + tags | ✅ | |
| PR2 | Qdrant namespaces + retriever | ✅ | |
| PR2 | Discord cmds (/latest, /context, /collabs) | ✅ | |
| PR2 | Tests + docs | ✅ | |
| PR3 | Learning domains registered | ✅ | |
| PR3 | learn_helper wired (routing/prompt/retrieval) | ✅ | |
| PR3 | Shadow/canary flags + ops cmds | ✅ | status, snapshot and restore helpers |
| PR3 | Tests + docs | ✅ | |
| PR4 | Budgets + cost guard wired to token_meter/router | ✅ | |
| PR4 | LLM/retrieval caches with TTLs | ✅ | |
| PR4 | Cold-start priors + bakeoff in shadow | ✅ | |
| PR4 | Reliability primitives and circuit breakers | ✅ | |
| PR4 | `/ops status` + alerts | ✅ | |
| PR5 | policy_engine + config/policy.yaml | ✅ | |
| PR5 | pii_detector + redactor + privacy_filter | ✅ | |
| PR5 | provenance + usage_log schema and writes | ✅ | |
| PR5 | retention sweeper + export tool | ✅ | |
| PR5 | ops commands + alerts | ✅ | alerts pending |
| PR7 | manifest stores attachment ids + compression | ✅ | |

## PR16 – Memory Unification, Lifecycles & Forgetting
- [x] memory_items + retention_policies tables
- [x] unified store/api with pin and archive helpers
- [x] hybrid retrieval with RL scoring hook
- [x] ops commands for find/pin/prune/archive
- [x] docs and tests

## PR17 – Grounding Guarantees & Answer Verification
- [x] grounding config and contract models
- [x] verifier stage with citation checks
- [x] retrieval wrapper producing evidence packs
- [x] Discord audit helper
- [x] docs and tests

## PR18 – Security Hardening, Secrets, RBAC & Abuse Prevention
- [x] RBAC module and YAML permissions
- [x] Network guard blocking private hosts
- [x] In-memory token bucket rate limiter
- [x] Security docs and baseline config
- [x] Input validation helpers for URLs and file paths
- [x] Basic content moderation helper
- [x] Security event logger for RBAC and moderation

All planned PR tasks completed.
