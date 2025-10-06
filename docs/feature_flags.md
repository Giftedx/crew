<!-- AUTO-GENERATED: Run `scripts/generate_feature_flags_doc.py` to refresh. Manual edits will be overwritten. -->
## Feature Flags & Environment Toggles

(Do not edit by hand; regenerate instead.)

### Api / Runtime

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_A2A_API` | server/a2a_discovery.py, server/a2a_tools.py |
| `ENABLE_A2A_API_KEY` | server/a2a_discovery.py, server/a2a_tools.py |
| `ENABLE_A2A_SKILL_RAG_HYBRID` | server/a2a_tools.py |
| `ENABLE_A2A_SKILL_RAG_INGEST` | server/a2a_tools.py |
| `ENABLE_A2A_SKILL_RAG_INGEST_URL` | server/a2a_tools.py |
| `ENABLE_A2A_SKILL_RAG_OFFLINE` | server/a2a_tools.py |
| `ENABLE_A2A_SKILL_RAG_VECTOR` | server/a2a_tools.py |
| `ENABLE_A2A_SKILL_RESEARCH_AND_BRIEF_MULTI` | server/a2a_tools.py |
| `ENABLE_A2A_SKILL_RESEARCH_BRIEF` | server/a2a_tools.py |
| `ENABLE_A2A_SKILL_RESEARCH_BRIEF_MULTI` | server/a2a_tools.py |
| `ENABLE_A2A_SKILL_SUMMARIZE` | server/a2a_tools.py |
| `ENABLE_A2A_STREAMING_DEMO` | server/a2a_streaming.py |
| `ENABLE_ACTIVITIES_ECHO` | server/routes/activities.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_AUTOINTEL_API` | core/settings.py, server/routes/autointel.py |
| `ENABLE_CORS` | server/middleware.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_CREW_CONFIG_VALIDATION` | mcp_server/crewai_server.py, ultimate_discord_intelligence_bot/crew.py |
| `ENABLE_CREW_STEP_VERBOSE` | mcp_server/crewai_server.py, ultimate_discord_intelligence_bot/crew.py |
| `ENABLE_LANGGRAPH_PILOT` | graphs/langgraph_pilot.py, server/routes/pilot.py |
| `ENABLE_LANGGRAPH_PILOT_API` | server/routes/pilot.py |
| `ENABLE_MCP_A2A` | mcp_server/server.py |
| `ENABLE_MCP_CREWAI` | mcp_server/crewai_server.py, mcp_server/server.py |
| `ENABLE_MCP_CREWAI_EXECUTION` | mcp_server/crewai_server.py |
| `ENABLE_MCP_HTTP` | mcp_server/server.py |
| `ENABLE_MCP_INGEST` | mcp_server/server.py |
| `ENABLE_MCP_KG` | mcp_server/server.py |
| `ENABLE_MCP_MEMORY` | mcp_server/server.py |
| `ENABLE_MCP_OBS` | mcp_server/obs_server.py, mcp_server/server.py |
| `ENABLE_MCP_OBS_PROM_RESOURCE` | mcp_server/obs_server.py |
| `ENABLE_MCP_ROUTER` | mcp_server/server.py |
| `ENABLE_PIPELINE_RUN_API` | core/settings.py, server/routes/pipeline_api.py |
| `ENABLE_PROMETHEUS_ENDPOINT` | core/secure_config.py, core/settings.py |
| `ENABLE_RATE_LIMITING` | core/secure_config.py, core/settings.py |

### Archiver / Discord

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_DISCORD_ARCHIVER` | archive/discord_store/api.py, core/secure_config.py |

### Http Resilience

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_ANALYSIS_HTTP_RETRY` | core/http/retry.py |
| `ENABLE_CONNECTION_POOLING` | core/http/requests_wrappers.py |
| `ENABLE_HTTP_CACHE` | core/settings.py, ultimate_discord_intelligence_bot/discord_bot/scoped/env.py |
| `ENABLE_HTTP_CIRCUIT_BREAKER` | core/http/retry.py |
| `ENABLE_HTTP_METRICS` | core/secure_config.py, core/settings.py |
| `ENABLE_HTTP_RETRY` | core/http/retry.py, core/secure_config.py |

### Ingestion

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_INGEST_CONCURRENT` | ingest/pipeline.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_STRICT` | ingest/pipeline.py, ultimate_discord_intelligence_bot/services/memory_service.py |
| `ENABLE_UPLOADER_BACKFILL` | ingest/backfill.py |
| `ENABLE_YOUTUBE_CHANNEL_BACKFILL_AFTER_INGEST` | ingest/pipeline.py |

### Misc

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_ADVANCED_CACHE` | core/settings.py |
| `ENABLE_AGENT_EVALS` | eval/trajectory_evaluator.py |
| `ENABLE_AI_ROUTING` | ultimate_discord_intelligence_bot/agent_training/performance_monitor.py, ultimate_discord_intelligence_bot/agent_training/performance_monitor_final.py |
| `ENABLE_API` | core/secure_config.py, core/settings.py |
| `ENABLE_API_CACHE` | core/settings.py |
| `ENABLE_AUDIT_LOGGING` | core/secure_config.py, core/settings.py |
| `ENABLE_AUTO_FOLLOW_UPLOADER` | ultimate_discord_intelligence_bot/auto_follow.py |
| `ENABLE_AUTO_URL_ANALYSIS` | ultimate_discord_intelligence_bot/discord_bot/registrations.py |
| `ENABLE_AX_ROUTING` | core/settings.py, ultimate_discord_intelligence_bot/services/openrouter_service/service.py |
| `ENABLE_BANDIT_PERSIST` | ai/routing/bandit_router.py, ai/routing/linucb_router.py |
| `ENABLE_BANDIT_ROUTING` | ai/routing/bandit_router.py, ai/routing/router_registry.py |
| `ENABLE_BANDIT_TENANT` | core/llm_router.py |
| `ENABLE_CACHE` | core/cache/llm_cache.py, core/cache/retrieval_cache.py |
| `ENABLE_CACHE_GLOBAL` | core/secure_config.py, core/settings.py |
| `ENABLE_CACHE_TRANSCRIPT` | core/secure_config.py, core/settings.py |
| `ENABLE_CACHE_VECTOR` | core/secure_config.py, core/settings.py |
| `ENABLE_CONTENT_MODERATION` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_CONTEXTUAL_BANDIT` | ai/routing/linucb_router.py, core/llm_router.py |
| `ENABLE_CONTEXTUAL_HYBRID` | core/llm_router.py |
| `ENABLE_COST_AWARE_ROUTING_SHADOW` | core/cost_aware_routing.py |
| `ENABLE_DEGRADATION_REPORTER` | core/degradation_reporter.py, core/settings.py |
| `ENABLE_DEPENDENCY_TRACKING` | core/settings.py |
| `ENABLE_DISCORD_ADMIN_COMMANDS` | ultimate_discord_intelligence_bot/discord_bot/runner.py |
| `ENABLE_DISCORD_COMMANDS` | core/secure_config.py, core/settings.py |
| `ENABLE_DISCORD_GATEWAY` | ultimate_discord_intelligence_bot/discord_bot/env.py, ultimate_discord_intelligence_bot/discord_bot/runner.py |
| `ENABLE_DISCORD_MONITOR` | core/secure_config.py, core/settings.py |
| `ENABLE_DISCORD_USER_COMMANDS` | ultimate_discord_intelligence_bot/discord_bot/registrations.py, ultimate_discord_intelligence_bot/discord_bot/runner.py |
| `ENABLE_DISTRIBUTED_RATE_LIMITING` | core/secure_config.py, core/settings.py |
| `ENABLE_ENHANCED_CREW_EVALUATION` | eval/config.py, eval/trajectory_evaluator.py |
| `ENABLE_EXPERIMENTAL_DEPTH` | ultimate_discord_intelligence_bot/autonomous_orchestrator.py |
| `ENABLE_EXPERIMENT_HARNESS` | core/learning_engine.py, core/rl/advanced_experiments.py |
| `ENABLE_FASTER_WHISPER` | core/secure_config.py |
| `ENABLE_GPTCACHE` | core/settings.py, ultimate_discord_intelligence_bot/services/openrouter_service/service.py |
| `ENABLE_GPTCACHE_ANALYSIS_SHADOW` | core/settings.py, ultimate_discord_intelligence_bot/services/openrouter_service/service.py |
| `ENABLE_GRAPH_MEMORY` | core/settings.py, ultimate_discord_intelligence_bot/pipeline_components/base.py |
| `ENABLE_GROUNDING` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_HIPPORAG_CONTINUAL_MEMORY` | ultimate_discord_intelligence_bot/pipeline_components/base.py, ultimate_discord_intelligence_bot/tools/hipporag_continual_memory_tool.py |
| `ENABLE_HIPPORAG_MEMORY` | ultimate_discord_intelligence_bot/pipeline_components/base.py, ultimate_discord_intelligence_bot/tools/hipporag_continual_memory_tool.py |
| `ENABLE_INGEST_TIKTOK` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_TWITCH` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_WORKER` | ultimate_discord_intelligence_bot/discord_bot/registrations.py, ultimate_discord_intelligence_bot/discord_bot/runner.py |
| `ENABLE_INGEST_YOUTUBE` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_LLMLINGUA` | core/settings.py, ultimate_discord_intelligence_bot/services/prompt_engine.py |
| `ENABLE_LLMLINGUA_SHADOW` | core/settings.py, ultimate_discord_intelligence_bot/services/prompt_engine.py |
| `ENABLE_LLM_CACHE` | core/settings.py |
| `ENABLE_LOCAL_LLM` | core/secure_config.py |
| `ENABLE_MEMORY_COMPACTION` | ultimate_discord_intelligence_bot/tools/memory_compaction_tool.py |
| `ENABLE_MEMORY_TTL` | ultimate_discord_intelligence_bot/tools/memory_storage_tool.py |
| `ENABLE_METRICS` | ultimate_discord_intelligence_bot/discord_bot/scoped/env.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_PII_DETECTION` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_PIPELINE_JOB_QUEUE` | core/settings.py |
| `ENABLE_PLACEHOLDER_SOCIAL_INTEL` | ultimate_discord_intelligence_bot/autonomous_orchestrator.py |
| `ENABLE_PROMPT_COMPRESSION` | core/settings.py, prompt_engine/llmlingua_adapter.py |
| `ENABLE_RAG_CONTEXT` | core/settings.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_RERANKER` | core/secure_config.py, ultimate_discord_intelligence_bot/tools/rag_hybrid_tool.py |
| `ENABLE_RESEARCH_AND_BRIEF_MULTI_AGENT` | ultimate_discord_intelligence_bot/tools/research_and_brief_multi_tool.py |
| `ENABLE_RETRIEVAL_ADAPTIVE_K` | ultimate_discord_intelligence_bot/services/memory_service.py |
| `ENABLE_SECURE_PATH_FALLBACK` | core/settings.py, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_SECURE_QDRANT_FALLBACK` | core/settings.py, memory/qdrant_provider.py |
| `ENABLE_SEMANTIC_CACHE` | core/cache/semantic_cache.py, ultimate_discord_intelligence_bot/discord_bot/scoped/env.py |
| `ENABLE_SEMANTIC_CACHE_PROMOTION` | ultimate_discord_intelligence_bot/services/openrouter_service.py, ultimate_discord_intelligence_bot/services/openrouter_service/service.py |
| `ENABLE_SEMANTIC_CACHE_SHADOW` | ultimate_discord_intelligence_bot/services/openrouter_service.py, ultimate_discord_intelligence_bot/services/openrouter_service/service.py |
| `ENABLE_SEMANTIC_LLM_CACHE` | core/llm_cache.py, core/llm_client.py |
| `ENABLE_TENANCY_STRICT` | ultimate_discord_intelligence_bot/services/memory_service.py, ultimate_discord_intelligence_bot/services/openrouter_helpers.py |
| `ENABLE_TRACING` | core/secure_config.py, core/settings.py |
| `ENABLE_TRAJECTORY_EVALUATION` | eval/config.py, eval/trajectory_evaluator.py |
| `ENABLE_TRAJECTORY_EVALUATION_CACHE` | eval/config.py |
| `ENABLE_TRAJECTORY_EVALUATION_METRICS` | eval/config.py |
| `ENABLE_TRAJECTORY_MATCHING` | eval/config.py |
| `ENABLE_TRAJECTORY_SHADOW_EVALUATION` | eval/config.py |
| `ENABLE_TRANSCRIPT_CACHE` | ultimate_discord_intelligence_bot/pipeline_components/base.py |
| `ENABLE_TRANSCRIPT_COMPRESSION` | core/settings.py, ultimate_discord_intelligence_bot/pipeline_components/base.py |
| `ENABLE_VECTOR_SEARCH` | core/settings.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_VOWPAL_WABBIT_BANDIT` | ai/routing/vw_bandit_router.py, core/llm_router.py |
| `ENABLE_VW_BANDIT` | ai/routing/vw_bandit_router.py, core/llm_router.py |

### Privacy

| Flag | Referenced In (sample) |
|------|------------------------|
| `enable_pii_detection` | core/privacy/privacy_filter.py, core/secure_config.py |
| `enable_pii_redaction` | core/privacy/privacy_filter.py |

### Rl / Routing

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_RL_` | core/learn.py, core/learning_engine.py |
| `ENABLE_RL_<DOMAIN>` | - |
| `ENABLE_RL_ADVANCED` | core/learning_engine.py, core/rl/advanced_config.py |
| `ENABLE_RL_AUTO_TUNING` | core/rl/advanced_config.py |
| `ENABLE_RL_CONTEXTUAL` | core/learning_engine.py |
| `ENABLE_RL_GLOBAL` | core/learn.py, core/secure_config.py |
| `ENABLE_RL_LINTS` | core/learning_engine.py, core/rl/shadow_regret.py |
| `ENABLE_RL_MONITORING` | core/rl/advanced_config.py |
| `ENABLE_RL_PROMPT` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_RETRIEVAL` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_ROUTING` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_SHADOW` | core/learning_engine.py, core/rl/advanced_config.py |
| `ENABLE_RL_SHADOW_EVAL` | core/rl/advanced_config.py |
| `ENABLE_RL_THOMPSON` | core/learning_engine.py |

### Deprecated flags and surfaces

The following items are deprecated or superseded; see configuration docs for timelines and replacements.

- `ENABLE_ANALYSIS_HTTP_RETRY` — replacement: `ENABLE_HTTP_RETRY`; Legacy analysis-scoped retry flag superseded by global ENABLE_HTTP_RETRY.
- `services.learning_engine.LearningEngine` — replacement: `core.learning_engine.LearningEngine`; Shim retained for backward compatibility; remove after grace period.

#### 🚨 Week 3 Parallelization Flags (Deprecated - Do Not Use)

The following performance optimization flags were empirically validated (Week 3 Phase 1, 12 iterations across 4 combinations) to introduce severe runtime regressions (+76% to +329% slower) and are now formally deprecated. Root cause: API rate limiting + CrewAI async coordination overhead (60–100s per phase) exceeded any theoretical concurrency benefit for short‑form workloads.

- `ENABLE_PARALLEL_MEMORY_OPS` — Adds +108% mean overhead (5.91 min vs 2.84 min baseline). No true concurrency due to serialized embedding + vector writes.
- `ENABLE_PARALLEL_ANALYSIS` — Catastrophic +329% overhead (12.19 min mean; 21.48 min outlier; 57% CV). Largest context payloads amplify coordination + rate limit penalties.
- `ENABLE_PARALLEL_FACT_CHECKING` — Adds +76% overhead (5.00 min vs 2.84 min baseline). Limited by external API / LLM call serialization.

Status: Marked HARMFUL. These flags should remain disabled in all environments. See `docs/WEEK_3_PHASE_1_FINAL_REPORT.md` and `docs/WEEK_3_PHASE_1_EXECUTIVE_SUMMARY.md` for full statistical methodology and root cause analysis.

Recommended Alternatives (Week 3 Phase 2 pivot):

1. `ENABLE_SEMANTIC_CACHE` – Leverage semantic reuse to reduce duplicate LLM calls (expected 20–30% improvement).
2. `ENABLE_PROMPT_COMPRESSION` – Reduce token + latency footprint for large context payloads (expected 10–20% improvement).
3. Combined cache + compression (expected 30–40% total improvement) without instability risk.

_Generated digest: `38810a7e6a70`_
