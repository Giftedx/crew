<!-- AUTO-GENERATED: Run `scripts/generate_feature_flags_doc.py` to refresh. Manual edits will be overwritten. -->
## Feature Flags & Environment Toggles

(Do not edit by hand; regenerate instead.)

### Api / Runtime

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_PROMETHEUS_ENDPOINT` | core/secure_config.py, core/settings.py |
| `ENABLE_RATE_LIMITING` | core/secure_config.py, core/settings.py |

### Archiver / Discord

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_DISCORD_ARCHIVER` | archive/discord_store/api.py, core/secure_config.py |

### Http Resilience

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_ANALYSIS_HTTP_RETRY` | core/http_utils.py |
| `ENABLE_HTTP_CACHE` | core/settings.py |
| `ENABLE_HTTP_METRICS` | core/secure_config.py, core/settings.py |
| `ENABLE_HTTP_RETRY` | core/http_utils.py, core/secure_config.py |

### Ingestion

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_INGEST_CONCURRENT` | ingest/pipeline.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_STRICT` | ingest/pipeline.py, ultimate_discord_intelligence_bot/services/memory_service.py |
| `ENABLE_UPLOADER_BACKFILL` | ingest/backfill.py |
| `ENABLE_YOUTUBE_CHANNEL_BACKFILL_AFTER_INGEST` | ingest/pipeline.py, ingest/sources/youtube_channel.py |

### Misc

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_A2A_API` | server/app.py |
| `ENABLE_A2A_API_KEY` | server/a2a_router.py |
| `ENABLE_A2A_STREAMING_DEMO` | server/a2a_router.py |
| `ENABLE_A2A_SKILL_SUMMARIZE` | server/a2a_router.py |
| `ENABLE_A2A_SKILL_RAG_OFFLINE` | server/a2a_router.py |
| `ENABLE_A2A_SKILL_RAG_VECTOR` | server/a2a_router.py |
| `ENABLE_A2A_SKILL_RAG_INGEST` | server/a2a_router.py |
| `ENABLE_A2A_SKILL_RAG_INGEST_URL` | server/a2a_router.py |
| `ENABLE_A2A_SKILL_RAG_HYBRID` | server/a2a_router.py |
| `ENABLE_A2A_SKILL_RESEARCH_BRIEF` | server/a2a_router.py |
| `ENABLE_A2A_SKILL_RESEARCH_BRIEF_MULTI` | server/a2a_router.py |
| `ENABLE_A2A_SKILL_RESEARCH_AND_BRIEF_MULTI` | server/a2a_router.py |
| `ENABLE_RESEARCH_AND_BRIEF_MULTI_AGENT` | ultimate_discord_intelligence_bot/tools/research_and_brief_multi_tool.py |
| `ENABLE_ADVANCED_CACHE` | core/settings.py |
| `ENABLE_API` | core/secure_config.py, core/settings.py |
| `ENABLE_API_CACHE` | core/settings.py |
| `ENABLE_AUDIT_LOGGING` | core/secure_config.py, core/settings.py |
| `ENABLE_AUTO_FOLLOW_UPLOADER` | ultimate_discord_intelligence_bot/auto_follow.py |
| `ENABLE_CACHE` | core/cache/llm_cache.py, core/cache/retrieval_cache.py |
| `ENABLE_CACHE_GLOBAL` | core/secure_config.py, core/settings.py |
| `ENABLE_CACHE_TRANSCRIPT` | core/secure_config.py, core/settings.py |
| `ENABLE_CACHE_VECTOR` | core/secure_config.py, core/settings.py |
| `ENABLE_CONTENT_MODERATION` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_CREW_CONFIG_VALIDATION` | ultimate_discord_intelligence_bot/crew.py |
| `ENABLE_CREW_STEP_VERBOSE` | ultimate_discord_intelligence_bot/crew.py |
| `ENABLE_DEGRADATION_REPORTER` | core/degradation_reporter.py, core/settings.py |
| `ENABLE_DEPENDENCY_TRACKING` | core/settings.py |
| `ENABLE_DISCORD_COMMANDS` | core/secure_config.py, core/settings.py |
| `ENABLE_DISCORD_MONITOR` | core/secure_config.py, core/settings.py |
| `ENABLE_DISTRIBUTED_RATE_LIMITING` | core/secure_config.py, core/settings.py |
| `ENABLE_EXPERIMENT_HARNESS` | core/learning_engine.py, core/rl/experiment.py |
| `ENABLE_FASTER_WHISPER` | core/secure_config.py |
| `ENABLE_GROUNDING` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_TIKTOK` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_TWITCH` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_YOUTUBE` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_LLM_CACHE` | core/settings.py |
| `ENABLE_LOCAL_LLM` | core/secure_config.py |
| `ENABLE_METRICS` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_PII_DETECTION` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_PROMPT_COMPRESSION` | core/settings.py, ultimate_discord_intelligence_bot/services/prompt_engine.py |
| `ENABLE_RAG_CONTEXT` | core/settings.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_RERANKER` | core/secure_config.py |
| `ENABLE_RETRIEVAL_ADAPTIVE_K` | ultimate_discord_intelligence_bot/services/memory_service.py |
| `ENABLE_SECURE_PATH_FALLBACK` | core/settings.py, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_SECURE_QDRANT_FALLBACK` | core/settings.py, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_SEMANTIC_CACHE` | ultimate_discord_intelligence_bot/services/openrouter_service.py |
| `ENABLE_TENANCY_STRICT` | ultimate_discord_intelligence_bot/services/memory_service.py, ultimate_discord_intelligence_bot/services/openrouter_service.py |
| `ENABLE_TRACING` | core/secure_config.py, core/settings.py |
| `ENABLE_VECTOR_SEARCH` | core/settings.py, ultimate_discord_intelligence_bot/setup_cli.py |

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
| `ENABLE_RL_CONTEXTUAL` | core/learning_engine.py |
| `ENABLE_RL_GLOBAL` | core/learn.py, core/secure_config.py |
| `ENABLE_RL_LINTS` | core/learning_engine.py, core/settings.py |
| `ENABLE_RL_PROMPT` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_RETRIEVAL` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_ROUTING` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_SHADOW` | core/learning_engine.py |
| `ENABLE_RL_THOMPSON` | core/learning_engine.py |
| `ENABLE_BANDIT_ROUTING` | ai/routing/bandit_router.py, core/llm_router.py |
| `ENABLE_BANDIT_TENANT` | ai/routing/router_registry.py, core/llm_router.py |
| `ENABLE_BANDIT_PERSIST` | ai/routing/bandit_router.py, ai/routing/linucb_router.py |
| `ENABLE_CONTEXTUAL_BANDIT` | ai/routing/linucb_router.py, core/llm_router.py |
| `ENABLE_CONTEXTUAL_HYBRID` | core/llm_router.py |
| `ENABLE_SEMANTIC_LLM_CACHE` | core/llm_cache.py, core/llm_client.py |
| `ENABLE_SEMANTIC_CACHE_SHADOW` | (planned) semantic cache shadow metrics |
| `ENABLE_SEMANTIC_CACHE_PROMOTION` | (planned) semantic cache promotion path |
| `ENABLE_TRAJECTORY_EVALUATION` | eval/trajectory_evaluator.py |
| `ENABLE_TRAJECTORY_EVALUATION_CACHE` | eval/trajectory_evaluator.py |
| `ENABLE_TRAJECTORY_EVALUATION_METRICS` | eval/trajectory_evaluator.py |
| `ENABLE_TRAJECTORY_MATCHING` | eval/trajectory_evaluator.py |
| `ENABLE_TRAJECTORY_SHADOW_EVALUATION` | eval/trajectory_evaluator.py |
| `ENABLE_AGENT_EVALS` | eval/trajectory_evaluator.py |
| `ENABLE_ENHANCED_CREW_EVALUATION` | ultimate_discord_intelligence_bot/enhanced_crew_integration.py |
| `ENABLE_LANGGRAPH_PILOT` | demo_langgraph_pilot.py |
| `ENABLE_LANGGRAPH_PILOT_API` | demo_langgraph_pilot.py |
| `ENABLE_RL_ADVANCED` | core/rl/experiment.py |
| `ENABLE_RL_MONITORING` | core/rl/experiment.py |
| `ENABLE_RL_AUTO_TUNING` | core/rl/experiment.py |
| `ENABLE_RL_SHADOW_EVAL` | core/rl/experiment.py |
| `ENABLE_COST_AWARE_ROUTING_SHADOW` | (planned) cost-aware routing shadow mode |

### Deprecated flags and surfaces

The following items are deprecated or superseded; see configuration docs for timelines and replacements.

- `ENABLE_ANALYSIS_HTTP_RETRY` — replacement: `ENABLE_HTTP_RETRY`; Legacy analysis-scoped retry flag superseded by global ENABLE_HTTP_RETRY.
- `services.learning_engine.LearningEngine` — replacement: `core.learning_engine.LearningEngine`; Shim retained for backward compatibility; remove after grace period.

Additional new flags will be auto-documented by the generator; any placeholders above marked (planned) may be removed if not implemented by next regeneration.

_Generated digest: `placeholder-updated-by-generator`_
