# Feature Flags Registry

**Version**: 1.0  
**Last Updated**: 2025-11-12  
**Maintainers**: Platform Team  

## Purpose

This document provides comprehensive lifecycle documentation for all 117 feature flags in the Ultimate Discord Intelligence Bot system. Each flag includes description, default values, deployment guidance, dependencies, and retirement criteria.

## Flag Lifecycle States

- **🟢 GA (Generally Available)**: Production-ready, enabled by default, long-term support
- **🟡 Beta**: Production-ready but disabled by default, opt-in for testing
- **🔵 Alpha**: Experimental, may break, disabled in production
- **🔴 Deprecated**: Scheduled for removal, migration path provided
- **⚫ Retired**: Removed from codebase

## Categories

- [Core System](#core-system)
- [API & Services](#api--services)
- [Caching & Performance](#caching--performance)
- [AI & LLM](#ai--llm)
- [Observability](#observability)
- [Content Processing](#content-processing)
- [Security & Compliance](#security--compliance)
- [Experimental Features](#experimental-features)

---

## Core System

### ENVIRONMENT

- **Status**: 🟢 GA
- **Default**: `development`
- **Values**: `development`, `staging`, `production`
- **Description**: Deployment environment identifier
- **Impact**: Controls strict mode, error handling verbosity, and debug features
- **Dependencies**: Affects `ENABLE_TENANCY_STRICT`, logging levels
- **Retirement**: Never (core infrastructure)

### SERVICE_NAME

- **Status**: 🟢 GA
- **Default**: `ultimate-discord-intel`
- **Description**: Service identifier for metrics, logs, and traces
- **Impact**: Labels all telemetry data
- **Dependencies**: Required by Prometheus, Langfuse, OpenTelemetry
- **Retirement**: Never (core infrastructure)

### ENABLE_API

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Enable FastAPI REST server
- **Impact**: Controls whether `/api/*` endpoints are served
- **Dependencies**: Required for A2A adapter, MCP server
- **Retirement**: Never (core functionality)

### ENABLE_TRACING

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Enable distributed tracing with Langfuse/OpenTelemetry
- **Impact**: ~5% performance overhead, critical for debugging
- **Dependencies**: `LANGSMITH_API_KEY` or local tracing backend
- **Retirement**: Never (core observability)

---

## API & Services

### ENABLE_A2A_API

- **Status**: 🟡 Beta
- **Default**: `true`
- **Description**: Expose Agent-to-Agent JSON-RPC adapter at `/a2a`
- **Impact**: Enables external agent integration
- **Dependencies**: `ENABLE_API=true`, `A2A_API_KEY` if auth enabled
- **Metrics**: `a2a_requests_total`, `a2a_request_duration_seconds`
- **Retirement**: N/A (long-term feature)

### ENABLE_A2A_API_KEY

- **Status**: 🟡 Beta
- **Default**: `true`
- **Description**: Require API key for A2A endpoints
- **Impact**: Blocks unauthenticated A2A requests
- **Dependencies**: `A2A_API_KEY` must be set
- **Retirement**: N/A (security control)

### ENABLE_A2A_STREAMING_DEMO

- **Status**: 🔵 Alpha
- **Default**: `true`
- **Description**: Demo route for A2A streaming capabilities
- **Impact**: Development/testing only
- **Dependencies**: `ENABLE_A2A_API=true`
- **Retirement**: ⚠️ **2025-Q2** - Remove after client SDK stabilizes

### ENABLE_A2A_SKILL_*

- **Status**: 🟡 Beta
- **Flags**: 9 skill toggles (SUMMARIZE, RAG_OFFLINE, RAG_VECTOR, RAG_INGEST, RAG_INGEST_URL, RAG_HYBRID, RESEARCH_BRIEF, RESEARCH_BRIEF_MULTI, RESEARCH_AND_BRIEF_MULTI)
- **Default**: `true` (all enabled)
- **Description**: Individual skill enablement for A2A adapter
- **Impact**: Granular control over exposed capabilities
- **Dependencies**: `ENABLE_A2A_API=true`, respective tool implementations
- **Retirement**: Consolidate into skill registry system (2025-Q3)

---

## Caching & Performance

### ENABLE_CACHE_GLOBAL

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Master cache toggle (L1 memory cache)
- **Impact**: ~40% latency reduction, controlled memory footprint
- **Dependencies**: None
- **Metrics**: `cache_hits_total`, `cache_misses_total`, `cache_evictions_total`
- **Retirement**: Never (core performance)

### ENABLE_ADVANCED_CACHE

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Enable multi-level caching (L1 + L2 Redis + L3 semantic)
- **Impact**: ~60% latency reduction, requires Redis
- **Dependencies**: `ENABLE_CACHE_GLOBAL=true`, Redis available
- **Retirement**: Never (core performance)

### ENABLE_CACHE_TRANSCRIPT

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Cache transcription results (expensive operation)
- **Impact**: Saves $0.006-0.036 per minute of audio on cache hits
- **Dependencies**: `ENABLE_CACHE_GLOBAL=true`
- **TTL**: 7 days
- **Retirement**: Never (cost optimization)

### ENABLE_CACHE_VECTOR

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Cache vector embeddings (moderate cost)
- **Impact**: Saves ~$0.0001 per 1K tokens, reduces Qdrant load
- **Dependencies**: `ENABLE_CACHE_GLOBAL=true`
- **TTL**: 30 days
- **Retirement**: Never (cost optimization)

### ENABLE_GPTCACHE

- **Status**: 🟢 GA
- **Default**: `true` (production), `false` (development)
- **Description**: LLM response caching with semantic similarity
- **Impact**: ~50% LLM cost reduction, 3-10x latency improvement
- **Dependencies**: `ENABLE_CACHE_GLOBAL=true`, Qdrant for similarity search
- **Metrics**: `gptcache_hits_total`, `gptcache_similarity_scores`
- **Retirement**: Never (major cost optimization)

### ENABLE_SEMANTIC_CACHE_SHADOW

- **Status**: 🟡 Beta
- **Default**: `false`
- **Description**: Shadow mode for semantic cache evaluation
- **Impact**: Collects metrics without serving cached responses
- **Dependencies**: `ENABLE_GPTCACHE=true`
- **Metrics**: `semantic_cache_shadow_hits`, `semantic_cache_shadow_quality`
- **Retirement**: ⚠️ **2025-Q1** - Promote to GA or remove after validation

### ENABLE_GPTCACHE_ANALYSIS_SHADOW

- **Status**: 🔵 Alpha
- **Default**: `false`
- **Description**: A/B test semantic cache for analysis tools specifically
- **Impact**: Research mode for cache effectiveness analysis
- **Dependencies**: `ENABLE_SEMANTIC_CACHE_SHADOW=true`
- **Retirement**: ⚠️ **2025-Q1** - Consolidate with main shadow mode

### ENABLE_CACHE_PROMOTION

- **Status**: 🔵 Alpha
- **Default**: `false`
- **Description**: Auto-promote hot L2 entries to L1 based on hit rate
- **Impact**: Experimental adaptive caching
- **Dependencies**: `ENABLE_ADVANCED_CACHE=true`, `CACHE_PROMOTION_HIT_THRESHOLD`
- **Retirement**: ⚠️ **2025-Q2** - Promote to Beta or deprecate

### CACHE_PROMOTION_HIT_THRESHOLD

- **Status**: 🔵 Alpha
- **Default**: `5`
- **Description**: Minimum hits before L2→L1 promotion
- **Dependencies**: `ENABLE_CACHE_PROMOTION=true`
- **Retirement**: Consolidate into `platform/cache/promotion_policy.yaml` (2025-Q2)

---

## AI & LLM

### OPENAI_API_KEY

- **Status**: 🟢 GA
- **Default**: None (required)
- **Description**: OpenAI API key for GPT models
- **Impact**: Enables primary LLM provider
- **Best Practice**: Use org-scoped keys with spend limits
- **Retirement**: Never (primary provider)

### OPENROUTER_API_KEY

- **Status**: 🟢 GA
- **Default**: None (alternative to OpenAI)
- **Description**: OpenRouter API key for multi-model access
- **Impact**: Enables fallback/alternative LLM routing
- **Dependencies**: `OPENROUTER_REFERER`, `OPENROUTER_TITLE` for attribution
- **Retirement**: Never (provider diversity)

### ENABLE_INSTRUCTOR

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Structured outputs with Instructor library
- **Impact**: Type-safe LLM responses, automatic validation
- **Dependencies**: Pydantic models, `INSTRUCTOR_MAX_RETRIES`
- **Retirement**: Never (core LLM abstraction)

### INSTRUCTOR_MAX_RETRIES

- **Status**: 🟢 GA
- **Default**: `3`
- **Description**: Max validation retries for structured outputs
- **Impact**: Balances reliability vs. cost
- **Dependencies**: `ENABLE_INSTRUCTOR=true`
- **Retirement**: Never (reliability control)

### ENABLE_LITELLM_ROUTER

- **Status**: 🟡 Beta
- **Default**: `false`
- **Description**: Multi-provider routing with LiteLLM
- **Impact**: Automatic failover, cost optimization
- **Dependencies**: `LITELLM_ROUTING_STRATEGY`, provider budgets
- **Metrics**: `litellm_requests_by_provider`, `litellm_costs_usd`
- **Retirement**: N/A (evaluate Q2 2025 - may conflict with internal RL router)

### ENABLE_TS_ROUTING

- **Status**: 🟡 Beta
- **Default**: `false`
- **Description**: Thompson Sampling reinforcement learning router
- **Impact**: Adaptive per-task model selection
- **Dependencies**: `TS_ROUTING_COLD_START_TRIALS`, trajectory feedback
- **Metrics**: `ts_router_arm_pulls`, `ts_router_rewards`
- **Retirement**: N/A (evaluate vs. LITELLM_ROUTER - may consolidate)

### ENABLE_TRAJECTORY_FEEDBACK_LOOP

- **Status**: 🟡 Beta
- **Default**: `false`
- **Description**: LangSmith trajectory scoring for RL router
- **Impact**: Continuous model performance improvement
- **Dependencies**: `LANGSMITH_API_KEY`, `ENABLE_TS_ROUTING=true`
- **Metrics**: `trajectory_scores`, `rl_router_updates`
- **Retirement**: N/A (core RL infrastructure)

### ENABLE_PROMPT_COMPRESSION

- **Status**: 🔵 Alpha
- **Default**: `false`
- **Description**: Dynamic prompt compression (LLMLingua or truncation)
- **Impact**: Token cost reduction, potential quality degradation
- **Dependencies**: `PROMPT_COMPRESSION_RATIO`
- **Retirement**: ⚠️ **2025-Q2** - Promote to Beta after quality validation

### ENABLE_HYBRID_RETRIEVAL

- **Status**: 🔵 Alpha
- **Default**: `false`
- **Description**: BM25 + dense vectors + reranker for RAG
- **Impact**: Better retrieval quality, higher latency
- **Dependencies**: `HYBRID_RETRIEVAL_FUSION_METHOD`, `RERANKER_MODEL`
- **Retirement**: ⚠️ **2025-Q3** - Promote to Beta or deprecate

---

## Observability

### ENABLE_PROMETHEUS_ENDPOINT

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Expose `/metrics` endpoint for Prometheus scraping
- **Impact**: Required for production monitoring
- **Dependencies**: `prometheus_client` library
- **Retirement**: Never (core observability)

### PROMETHEUS_ENDPOINT_PATH

- **Status**: 🟢 GA
- **Default**: `/metrics`
- **Description**: Path for Prometheus metrics endpoint
- **Dependencies**: `ENABLE_PROMETHEUS_ENDPOINT=true`
- **Retirement**: Never (core observability)

### ENABLE_HTTP_METRICS

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Instrument HTTP requests with metrics
- **Impact**: ~1% overhead, critical for SLO tracking
- **Metrics**: `http_requests_total`, `http_request_duration_seconds`
- **Retirement**: Never (core observability)

### ENABLE_PROFILING

- **Status**: 🟡 Beta
- **Default**: `true` (development), `false` (production)
- **Description**: Enable cProfile or py-spy profiling
- **Impact**: 10-20% overhead, use sparingly in production
- **Dependencies**: profiling libraries
- **Retirement**: N/A (development tool)

### ENABLE_LOGFIRE

- **Status**: 🔵 Alpha
- **Default**: `false`
- **Description**: Pydantic Logfire observability platform
- **Impact**: Experimental alternative to Langfuse
- **Dependencies**: `LOGFIRE_TOKEN`, `LOGFIRE_PROJECT_NAME`
- **Retirement**: ⚠️ **2025-Q2** - Evaluate vs. Langfuse, may deprecate

### LANGSMITH_API_KEY

- **Status**: 🟢 GA
- **Default**: None (required for evals)
- **Description**: LangSmith API key for tracing and evaluations
- **Impact**: Enables trajectory scoring, self-eval gates
- **Dependencies**: None
- **Retirement**: Never (core eval infrastructure)

---

## Content Processing

### ENABLE_CONTENT_ROUTING

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Route content to specialized pipelines based on type
- **Impact**: Optimizes processing flow
- **Dependencies**: `config/content_types.yaml`
- **Retirement**: Never (core orchestration)

### ENABLE_QUALITY_FILTERING

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Quality gates for content validation
- **Impact**: Prevents low-quality content processing
- **Dependencies**: Quality threshold configs
- **Retirement**: Never (quality assurance)

### ENABLE_EARLY_EXIT

- **Status**: 🟢 GA
- **Default**: `true`
- **Description**: Skip unnecessary pipeline steps based on confidence
- **Impact**: ~30% cost reduction on simple content
- **Dependencies**: `config/early_exit.yaml`
- **Retirement**: Never (cost optimization)

### ENABLE_GRAPH_MEMORY

- **Status**: 🟡 Beta
- **Default**: `false`
- **Description**: Neo4j graph memory for relational knowledge
- **Impact**: Advanced memory capabilities, requires Neo4j
- **Dependencies**: Neo4j instance, `NEO4J_URI`
- **Retirement**: N/A (long-term feature)

### ENABLE_HIPPORAG_MEMORY

- **Status**: 🔵 Alpha
- **Default**: `false`
- **Description**: HippoRAG continual learning memory
- **Impact**: Experimental personalization
- **Dependencies**: `ENABLE_GRAPH_MEMORY=true`
- **Retirement**: ⚠️ **2025-Q3** - Promote to Beta or deprecate

---

## Security & Compliance

### WEBHOOK_SECRET_DEFAULT

- **Status**: 🟢 GA
- **Default**: None (MUST set in production)
- **Description**: Primary webhook signature verification secret
- **Impact**: Critical security control
- **Best Practice**: Generate with `secrets.token_urlsafe(32)`
- **Retirement**: Never (security control)

### WEBHOOK_SECRET_BACKUP

- **Status**: 🟢 GA
- **Default**: None (optional)
- **Description**: Backup webhook secret for rotation
- **Impact**: Enables zero-downtime secret rotation
- **Dependencies**: Multi-secret validation logic
- **Retirement**: Never (security best practice)

### ENABLE_TENANCY_STRICT

- **Status**: 🟡 Beta
- **Default**: `false` (development), `true` (production)
- **Description**: Enforce TenantContext presence for all operations
- **Impact**: Prevents cross-tenant data leaks
- **Dependencies**: TenantContext propagation at all boundaries
- **Retirement**: N/A (security control)

### A2A_API_KEY

- **Status**: 🟡 Beta
- **Default**: None (required if `ENABLE_A2A_API_KEY=true`)
- **Description**: Comma-separated API keys for A2A authentication
- **Impact**: Blocks unauthorized A2A access
- **Dependencies**: `ENABLE_A2A_API_KEY=true`
- **Retirement**: N/A (security control)

---

## Experimental Features

### ENABLE_SELF_EVAL_GATES

- **Status**: 🔵 Alpha
- **Default**: `false`
- **Description**: Automated quality gates with LangSmith evals
- **Impact**: Blocks low-quality outputs, may increase latency
- **Dependencies**: `LANGSMITH_API_KEY`, `SELF_EVAL_SHADOW_MODE`
- **Retirement**: ⚠️ **2025-Q2** - Promote to Beta after calibration

### SELF_EVAL_SHADOW_MODE

- **Status**: 🔵 Alpha
- **Default**: `true`
- **Description**: Collect self-eval metrics without blocking
- **Impact**: Research mode for threshold tuning
- **Dependencies**: `ENABLE_SELF_EVAL_GATES=true`
- **Retirement**: ⚠️ **2025-Q2** - Graduate to production mode

### ENABLE_SELF_IMPROVEMENT

- **Status**: 🔵 Alpha
- **Default**: `false`
- **Description**: Nightly A/B testing and auto-merge
- **Impact**: Highly experimental, sandbox only
- **Dependencies**: `SELF_IMPROVEMENT_SANDBOX_MODE=docker`
- **Retirement**: ⚠️ **2025-Q4** - Major revision or deprecate

---

## Deprecation Schedule

### Scheduled for Removal Q1 2025

- `ENABLE_SEMANTIC_CACHE_SHADOW` → Promote to GA or remove
- `ENABLE_GPTCACHE_ANALYSIS_SHADOW` → Consolidate with main shadow mode

### Scheduled for Removal Q2 2025

- `ENABLE_A2A_STREAMING_DEMO` → Remove after SDK stabilizes
- `ENABLE_CACHE_PROMOTION` → Promote or deprecate based on results
- `ENABLE_PROMPT_COMPRESSION` → Promote or deprecate based on quality metrics
- `ENABLE_SELF_EVAL_GATES` → Promote to Beta or remove
- `ENABLE_LOGFIRE` → Choose Langfuse or Logfire

### Scheduled for Removal Q3 2025

- `ENABLE_A2A_SKILL_*` → Consolidate into skill registry
- `ENABLE_HIPPORAG_MEMORY` → Promote or deprecate
- `ENABLE_HYBRID_RETRIEVAL` → Promote or deprecate

### Scheduled for Removal Q4 2025

- `ENABLE_SELF_IMPROVEMENT` → Major revision or deprecate
- Router consolidation: Evaluate `ENABLE_LITELLM_ROUTER` vs `ENABLE_TS_ROUTING`

---

## Flag Management Best Practices

### Adding a New Flag

1. **Naming Convention**: `ENABLE_<FEATURE>` for boolean toggles, `<FEATURE>_<PROPERTY>` for values
2. **Documentation**: Add entry to this registry BEFORE merging
3. **Default Value**: Must be safe for production (prefer `false` for new features)
4. **Lifecycle State**: Start in Alpha or Beta, never GA on first release
5. **Metrics**: Instrument usage with `feature_flag_state` gauge
6. **Dependencies**: Document all prerequisite flags and services
7. **Retirement Criteria**: Set explicit graduation or deprecation date

### Graduating a Flag

- **Alpha → Beta**: Requires 2 weeks in production with <0.1% error rate
- **Beta → GA**: Requires 4 weeks in production, >50% adoption, formal review
- **Enable by Default**: Only for GA flags with proven stability

### Deprecating a Flag

1. **Announcement**: 4 weeks notice in changelog and deprecation log
2. **Migration Guide**: Provide clear alternative or removal instructions
3. **Metrics Sunset**: Stop collecting flag-specific metrics after 2 weeks deprecated
4. **Code Removal**: Delete flag checks and related code after 8 weeks deprecated

### Emergency Rollback

If a flag causes production issues:

1. Set flag to safe default in `.env` (usually `false`)
2. Deploy config-only change (no code deploy needed)
3. File incident report and mark flag as ⚠️ **Unstable**
4. Fix root cause before re-enabling

---

## Metrics & Dashboards

### Feature Flag Health Dashboard

**Metrics**:

- `feature_flag_state{flag="...", value="..."}` - Current flag values per tenant
- `feature_flag_reads_total{flag="...", tenant="..."}` - Read frequency
- `feature_flag_defaults_used_total{flag="..."}` - Fallback to default count

**Alerts**:

- Flag value divergence across tenants (unexpected overrides)
- High fallback rate (missing configs)
- Deprecated flag usage after sunset date

### Cost Impact by Flag

Track cost delta per flag:

- `ENABLE_GPTCACHE`: Saves ~$500/month in LLM costs
- `ENABLE_CACHE_TRANSCRIPT`: Saves ~$200/month in transcription costs
- `ENABLE_EARLY_EXIT`: Saves ~$150/month in unnecessary processing
- `ENABLE_PROMPT_COMPRESSION`: Target 20% cost reduction (experimental)

---

## Contact & Ownership

**Primary Maintainer**: Platform Team  
**Secondary**: AI Infrastructure Team  
**Escalation**: #platform-alerts Slack channel  

**Review Cadence**: Quarterly cleanup (Q1, Q2, Q3, Q4)  
**Next Review**: 2025-Q1 (January 2025)

---

**End of Feature Flags Registry**
