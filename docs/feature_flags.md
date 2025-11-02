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
| `ENABLE_CREW_CONFIG_VALIDATION` | mcp_server/crewai_server.py, ultimate_discord_intelligence_bot/crew_core |
| `ENABLE_CREW_STEP_VERBOSE` | mcp_server/crewai_server.py, ultimate_discord_intelligence_bot/crew_core |
| `ENABLE_LANGGRAPH_PILOT` | graphs/langgraph_pilot.py, server/routes/pilot.py |
| `ENABLE_LANGGRAPH_PILOT_API` | server/routes/pilot.py |
| `ENABLE_MCP_A2A` | mcp_server/server.py, validation/mcp_tools_validator.py |
| `ENABLE_MCP_CREATOR_INTELLIGENCE` | mcp_server/creator_intelligence_server.py |
| `ENABLE_MCP_CREWAI` | mcp_server/crewai_server.py, mcp_server/server.py |
| `ENABLE_MCP_CREWAI_EXECUTION` | mcp_server/crewai_server.py |
| `ENABLE_MCP_HTTP` | mcp_server/server.py, validation/mcp_tools_validator.py |
| `ENABLE_MCP_INGEST` | mcp_server/server.py, validation/mcp_tools_validator.py |
| `ENABLE_MCP_KG` | mcp_server/server.py, validation/mcp_tools_validator.py |
| `ENABLE_MCP_MEMORY` | mcp_server/server.py, validation/mcp_tools_validator.py |
| `ENABLE_MCP_OBS` | mcp_server/obs_server.py, mcp_server/server.py |
| `ENABLE_MCP_OBS_PROM_RESOURCE` | mcp_server/obs_server.py |
| `ENABLE_MCP_ROUTER` | mcp_server/server.py, validation/mcp_tools_validator.py |
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
| `ENABLE_YOUTUBE` | ingest/pipeline.py, ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_YOUTUBE_CHANNEL_BACKFILL_AFTER_INGEST` | ingest/pipeline.py |

### Misc

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_ADAPTIVE_QUALITY` | core/llm_router.py |
| `ENABLE_ADVANCED_CACHE` | core/settings.py |
| `ENABLE_AGENT_BRIDGE` | ultimate_discord_intelligence_bot/crew_core, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_AGENT_EVALS` | eval/trajectory_evaluator.py |
| `ENABLE_AGENT_OPS` | core/settings.py |
| `ENABLE_AI_ROUTING` | ultimate_discord_intelligence_bot/agent_training/performance_monitor.py, ultimate_discord_intelligence_bot/agent_training/performance_monitor_final.py |
| `ENABLE_ALERTS` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/config/validation.py |
| `ENABLE_ANALYSIS_CACHE` | ultimate_discord_intelligence_bot/cache/cache_config.py |
| `ENABLE_API` | core/configuration/config_schema.py, core/secure_config.py |
| `ENABLE_API_CACHE` | core/settings.py |
| `ENABLE_AUDIT_LOGGING` | core/secure_config.py, core/settings.py |
| `ENABLE_AUTO_FOLLOW_UPLOADER` | ultimate_discord_intelligence_bot/auto_follow.py |
| `ENABLE_AUTO_URL_ANALYSIS` | ultimate_discord_intelligence_bot/discord_bot/registrations.py |
| `ENABLE_AX_ROUTING` | core/settings.py, ultimate_discord_intelligence_bot/services/openrouter_service/service.py |
| `ENABLE_BANDIT_PERSIST` | ai/routing/bandit_router.py, ai/routing/linucb_router.py |
| `ENABLE_BANDIT_ROUTING` | ai/routing/bandit_router.py, ai/routing/router_registry.py |
| `ENABLE_BANDIT_TENANT` | core/llm_router.py |
| `ENABLE_BIAS_DETECTION` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_CACHE` | core/cache/llm_cache.py, core/cache/retrieval_cache.py |
| `ENABLE_CACHE_GLOBAL` | core/secure_config.py, core/settings.py |
| `ENABLE_CACHE_OPTIMIZATION` | ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_CACHE_TRANSCRIPT` | core/secure_config.py, core/settings.py |
| `ENABLE_CACHE_V2` | ultimate_discord_intelligence_bot/cache/__init__.py, ultimate_discord_intelligence_bot/services/cache_shadow_harness.py |
| `ENABLE_CACHE_VECTOR` | core/secure_config.py, core/settings.py |
| `ENABLE_CACHING` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_CLEANUP_CLOSED` | core/connection_pool.py |
| `ENABLE_COLLECTIVE_INTELLIGENCE` | ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_COMPLEXITY_ANALYSIS` | core/llm_router.py |
| `ENABLE_CONTENT_MODERATION` | core/configuration/config_loader.py, core/secure_config.py |
| `ENABLE_CONTENT_ROUTING` | ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py |
| `ENABLE_CONTEXTUAL_BANDIT` | ai/routing/linucb_router.py, core/llm_router.py |
| `ENABLE_CONTEXTUAL_HYBRID` | core/llm_router.py |
| `ENABLE_COST_AWARE_ROUTING` | core/cost_aware_routing.py, core/llm_router.py |
| `ENABLE_COST_AWARE_ROUTING_SHADOW` | core/cost_aware_routing.py |
| `ENABLE_CREATOR_OPS` | ultimate_discord_intelligence_bot/creator_ops/__init__.py, ultimate_discord_intelligence_bot/creator_ops/config.py |
| `ENABLE_CREW_YAML_VALIDATION` | ultimate_discord_intelligence_bot/crew_core |
| `ENABLE_CROSS_AGENT_LEARNING` | ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_DASHBOARD` | core/configuration/config_schema.py, ultimate_discord_intelligence_bot/crew_core |
| `ENABLE_DASHBOARD_INTEGRATION` | ultimate_discord_intelligence_bot/crew_core, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_DASHBOARD_METRICS` | ultimate_discord_intelligence_bot/pipeline_components/dashboard_metrics.py |
| `ENABLE_DB_OPTIMIZATIONS` | core/db_optimizer.py |
| `ENABLE_DEBATE_ANALYSIS` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_DEBUG_MODE` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/config/validation.py |
| `ENABLE_DEGRADATION_REPORTER` | core/degradation_reporter.py, core/settings.py |
| `ENABLE_DEPENDENCY_TRACKING` | core/settings.py |
| `ENABLE_DEVELOPMENT_TOOLS` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_DISCORD_ADMIN_COMMANDS` | ultimate_discord_intelligence_bot/discord_bot/runner.py |
| `ENABLE_DISCORD_COMMANDS` | core/secure_config.py, core/settings.py |
| `ENABLE_DISCORD_GATEWAY` | ultimate_discord_intelligence_bot/discord_bot/env.py, ultimate_discord_intelligence_bot/discord_bot/runner.py |
| `ENABLE_DISCORD_INTEGRATION` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_DISCORD_MONITOR` | core/secure_config.py, core/settings.py |
| `ENABLE_DISCORD_USER_COMMANDS` | ultimate_discord_intelligence_bot/discord_bot/registrations.py, ultimate_discord_intelligence_bot/discord_bot/runner.py |
| `ENABLE_DISTRIBUTED_RATE_LIMITING` | core/secure_config.py, core/settings.py |
| `ENABLE_DSPY_OPTIMIZATION` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_EARLY_EXIT` | ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py |
| `ENABLE_ENHANCED_CREW_EVALUATION` | eval/config.py, eval/trajectory_evaluator.py |
| `ENABLE_ENHANCED_MEMORY` | core/settings.py, ultimate_discord_intelligence_bot/tools/memory/mem0_memory_tool.py |
| `ENABLE_ENTERPRISE_TENANT_MANAGEMENT` | ultimate_discord_intelligence_bot/enhanced_crew_integration.py, ultimate_discord_intelligence_bot/services/enterprise_auth_service.py |
| `ENABLE_EXPERIMENTAL_DEPTH` | ultimate_discord_intelligence_bot/autonomous_orchestrator.py |
| `ENABLE_EXPERIMENT_HARNESS` | core/learning_engine.py, core/rl/advanced_experiments.py |
| `ENABLE_FACT_CHECKING` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_FASTER_WHISPER` | core/secure_config.py |
| `ENABLE_FAST_WHISPER` | core/optional_dependencies.py |
| `ENABLE_GPTCACHE` | core/settings.py, ultimate_discord_intelligence_bot/services/openrouter_service/service.py |
| `ENABLE_GPTCACHE_ANALYSIS_SHADOW` | core/settings.py, ultimate_discord_intelligence_bot/services/openrouter_service/service.py |
| `ENABLE_GRAPH_MEMORY` | core/settings.py, ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_GROUNDING` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_HIERARCHICAL_ORCHESTRATION` | ultimate_discord_intelligence_bot/enhanced_crew_integration.py, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_HIPPORAG_CONTINUAL_MEMORY` | ultimate_discord_intelligence_bot/pipeline_components/base.py, ultimate_discord_intelligence_bot/tools/memory/hipporag_continual_memory_tool.py |
| `ENABLE_HIPPORAG_MEMORY` | ultimate_discord_intelligence_bot/pipeline_components/base.py, ultimate_discord_intelligence_bot/tools/memory/hipporag_continual_memory_tool.py |
| `ENABLE_INGEST_TIKTOK` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_TWITCH` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_WORKER` | ultimate_discord_intelligence_bot/discord_bot/registrations.py, ultimate_discord_intelligence_bot/discord_bot/runner.py |
| `ENABLE_INGEST_YOUTUBE` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INSTAGRAM` | ultimate_discord_intelligence_bot/creator_ops/config.py |
| `ENABLE_INTELLIGENT_ALERTING` | ultimate_discord_intelligence_bot/crew_core, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_KNOWLEDGE_SHARING` | ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_LANGGRAPH_PIPELINE` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/crew_core |
| `ENABLE_LAZY_LOADING` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_LLMLINGUA` | core/settings.py, ultimate_discord_intelligence_bot/services/prompt_engine.py |
| `ENABLE_LLMLINGUA_SHADOW` | core/settings.py, ultimate_discord_intelligence_bot/services/prompt_engine.py |
| `ENABLE_LLM_CACHE` | core/settings.py |
| `ENABLE_LOCAL_LLM` | core/secure_config.py |
| `ENABLE_LOGGING` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_MCP_MULTIMODAL` | validation/mcp_tools_validator.py |
| `ENABLE_MEM0_MEMORY` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_MEMORY_COMPACTION` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/tools/memory/memory_compaction_tool.py |
| `ENABLE_MEMORY_OPTIMIZATIONS` | memory/vector_store.py |
| `ENABLE_MEMORY_TTL` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/tools/memory/memory_storage_tool.py |
| `ENABLE_METRICS` | core/configuration/config_schema.py, ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_OBSERVABILITY_WRAPPER` | ultimate_discord_intelligence_bot/observability/stepresult_observer.py, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_OPTIMIZATION` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_OTEL_EXPORT` | ultimate_discord_intelligence_bot/observability/stepresult_observer.py, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_PARALLEL_ANALYSIS` | core/settings.py, ultimate_discord_intelligence_bot/orchestrator/parallel_config.py |
| `ENABLE_PARALLEL_FACT_CHECKING` | core/settings.py, ultimate_discord_intelligence_bot/orchestrator/parallel_config.py |
| `ENABLE_PARALLEL_MEMORY_OPS` | core/settings.py, ultimate_discord_intelligence_bot/orchestrator/parallel_config.py |
| `ENABLE_PARALLEL_PROCESSING` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_PII_DETECTION` | core/configuration/config_loader.py, core/secure_config.py |
| `ENABLE_PIPELINE_JOB_QUEUE` | core/settings.py |
| `ENABLE_PLACEHOLDER_SOCIAL_INTEL` | ultimate_discord_intelligence_bot/autonomous_orchestrator.py |
| `ENABLE_PRIVACY_FILTER` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_PROMPT_COMPRESSION` | core/settings.py, prompt_engine/llmlingua_adapter.py |
| `ENABLE_QDRANT_VECTOR_STORE` | core/optional_dependencies.py |
| `ENABLE_QUALITY_FILTERING` | ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py |
| `ENABLE_RAG_CONTEXT` | core/settings.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_REAL_APIS` | ultimate_discord_intelligence_bot/creator_ops/__init__.py, ultimate_discord_intelligence_bot/creator_ops/config.py |
| `ENABLE_REDIS_CACHE` | core/optional_dependencies.py |
| `ENABLE_RERANKER` | core/secure_config.py, ultimate_discord_intelligence_bot/tools/memory/rag_hybrid_tool.py |
| `ENABLE_RESEARCH_AND_BRIEF_MULTI_AGENT` | ultimate_discord_intelligence_bot/tools/memory/research_and_brief_multi_tool.py |
| `ENABLE_RETRIEVAL_ADAPTIVE_K` | ultimate_discord_intelligence_bot/services/memory_service.py |
| `ENABLE_SECURE_PATH_FALLBACK` | core/settings.py, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_SECURE_QDRANT_FALLBACK` | core/settings.py, memory/qdrant_provider.py |
| `ENABLE_SEMANTIC_CACHE` | core/cache/semantic_cache.py, ultimate_discord_intelligence_bot/discord_bot/scoped/env.py |
| `ENABLE_SEMANTIC_CACHE_PROMOTION` | ultimate_discord_intelligence_bot/services/openrouter_service.py, ultimate_discord_intelligence_bot/services/openrouter_service/service.py |
| `ENABLE_SEMANTIC_CACHE_SHADOW` | ultimate_discord_intelligence_bot/services/openrouter_service.py, ultimate_discord_intelligence_bot/services/openrouter_service/service.py |
| `ENABLE_SEMANTIC_LLM_CACHE` | core/llm_client.py |
| `ENABLE_SEMANTIC_ROUTER` | ultimate_discord_intelligence_bot/services/semantic_router_service.py |
| `ENABLE_SENTENCE_TRANSFORMERS` | core/optional_dependencies.py |
| `ENABLE_SENTIMENT_ANALYSIS` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_SPEAKER_DIARIZATION` | core/optional_dependencies.py |
| `ENABLE_TASK_MANAGEMENT` | ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_TENANCY_STRICT` | ultimate_discord_intelligence_bot/services/memory_service.py, ultimate_discord_intelligence_bot/services/openrouter_helpers.py |
| `ENABLE_TEST_MODE` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/config/validation.py |
| `ENABLE_TIKTOK` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/creator_ops/config.py |
| `ENABLE_TIKTOK_INTEGRATION` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_TRACING` | core/configuration/config_schema.py, core/secure_config.py |
| `ENABLE_TRAJECTORY_EVALUATION` | eval/config.py, eval/trajectory_evaluator.py |
| `ENABLE_TRAJECTORY_EVALUATION_CACHE` | eval/config.py |
| `ENABLE_TRAJECTORY_EVALUATION_METRICS` | eval/config.py |
| `ENABLE_TRAJECTORY_MATCHING` | eval/config.py |
| `ENABLE_TRAJECTORY_SHADOW_EVALUATION` | eval/config.py |
| `ENABLE_TRANSCRIPT_CACHE` | ultimate_discord_intelligence_bot/pipeline_components/base.py |
| `ENABLE_TRANSCRIPT_COMPRESSION` | core/settings.py, ultimate_discord_intelligence_bot/pipeline_components/base.py |
| `ENABLE_TWITCH` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/creator_ops/config.py |
| `ENABLE_TWITCH_INTEGRATION` | ultimate_discord_intelligence_bot/config/feature_flags.py |
| `ENABLE_UNIFIED_CACHE` | ultimate_discord_intelligence_bot/crew_core, ultimate_discord_intelligence_bot/crew_modular.py |
| `ENABLE_UNIFIED_COST_TRACKING` | ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_UNIFIED_KNOWLEDGE` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/config/validation.py |
| `ENABLE_UNIFIED_METRICS` | ultimate_discord_intelligence_bot/crew_core, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_UNIFIED_ORCHESTRATION` | ultimate_discord_intelligence_bot/crew_core, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_UNIFIED_ROUTER` | ultimate_discord_intelligence_bot/crew_core, ultimate_discord_intelligence_bot/crew_modular.py |
| `ENABLE_VECTOR_MEMORY` | ultimate_discord_intelligence_bot/config/feature_flags.py, ultimate_discord_intelligence_bot/config/validation.py |
| `ENABLE_VECTOR_SEARCH` | core/settings.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_VOWPAL_WABBIT_BANDIT` | ai/routing/vw_bandit_router.py, core/llm_router.py |
| `ENABLE_VW_BANDIT` | ai/routing/vw_bandit_router.py, core/llm_router.py |
| `ENABLE_WEBSOCKET_UPDATES` | ultimate_discord_intelligence_bot/enhanced_crew_integration.py, ultimate_discord_intelligence_bot/services/websocket_integration.py |
| `ENABLE_WHISPER_TRANSCRIPTION` | core/optional_dependencies.py |
| `ENABLE_X` | ultimate_discord_intelligence_bot/creator_ops/config.py |
| `ENABLE_YOUTUBE_INTEGRATION` | ultimate_discord_intelligence_bot/config/feature_flags.py |

### Privacy

| Flag | Referenced In (sample) |
|------|------------------------|
| `enable_pii_detection` | core/configuration/config_factory.py, core/configuration/config_loader.py |
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
| `ENABLE_RL_MODEL_ROUTING` | ultimate_discord_intelligence_bot/services/openrouter_service/service.py, ultimate_discord_intelligence_bot/settings.py |
| `ENABLE_RL_MONITORING` | core/rl/advanced_config.py |
| `ENABLE_RL_PROMPT` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_RETRIEVAL` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_ROUTING` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_SHADOW` | core/learning_engine.py, core/rl/advanced_config.py |
| `ENABLE_RL_SHADOW_EVAL` | core/rl/advanced_config.py |
| `ENABLE_RL_THOMPSON` | core/learning_engine.py |
| `ENABLE_RL_VOWPAL` | core/learning_engine.py, core/settings.py |


_Generated digest: `c9fa7c7dbd79`_
