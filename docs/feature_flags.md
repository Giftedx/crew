<!-- AUTO-GENERATED: Run `scripts/generate_feature_flags_doc.py` to refresh. Manual edits will be overwritten. -->
## Feature Flags & Environment Toggles

(Do not edit by hand; regenerate instead.)

> Note: `ENABLE_ANALYSIS_HTTP_RETRY` is **deprecated** and superseded by `ENABLE_HTTP_RETRY` (see `config/deprecations.yaml`). The global flag now unifies retry precedence (tenant retry.yaml overrides global, explicit function args override both).

Deprecated Symbols:

| Symbol | Replacement |
|--------|-------------|
| `services.learning_engine.LearningEngine` | `core.learning_engine.LearningEngine` |

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

### Misc

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_ADVANCED_CACHE` | core/settings.py |
| `ENABLE_API` | core/secure_config.py, core/settings.py |
| `ENABLE_API_CACHE` | core/settings.py |
| `ENABLE_AUDIT_LOGGING` | core/secure_config.py, core/settings.py |
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
| `ENABLE_PROMPT_COMPRESSION` | core/settings.py |
| `ENABLE_RAG_CONTEXT` | core/settings.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_RERANKER` | core/secure_config.py |
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
| `ENABLE_RL_GLOBAL` | core/learn.py, core/secure_config.py |
| `ENABLE_RL_LINTS` | core/learning_engine.py, core/settings.py |
| `ENABLE_RL_PROMPT` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_RETRIEVAL` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_ROUTING` | core/secure_config.py, core/settings.py |
| `ENABLE_RL_THOMPSON` | core/learning_engine.py |
| `ENABLE_RL_CONTEXTUAL` | core/learning_engine.py |
| `ENABLE_RL_SHADOW` | core/learning_engine.py |
| `ENABLE_RETRIEVAL_ADAPTIVE_K` | ultimate_discord_intelligence_bot/services/memory_service.py |

_Generated digest: `13b1c4166d07`_
