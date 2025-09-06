<!-- AUTO-GENERATED: Run `scripts/generate_feature_flags_doc.py` to refresh. Manual edits will be overwritten. -->
## Feature Flags & Environment Toggles

(Do not edit by hand; regenerate instead.)

Note: The unified `ENABLE_HTTP_RETRY` supersedes the legacy `ENABLE_ANALYSIS_HTTP_RETRY` (deprecated).

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
| `ENABLE_API_CACHE` | core/settings.py |
| `ENABLE_ADVANCED_CACHE` | core/settings.py, server/app.py |
| `ENABLE_LLM_CACHE` | core/settings.py |
| `ENABLE_DEPENDENCY_TRACKING` | core/settings.py, tests/test_dependency_invalidation.py |

### Ingestion

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_INGEST_CONCURRENT` | ingest/pipeline.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_STRICT` | ingest/pipeline.py |

### Misc

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_API` | core/secure_config.py, core/settings.py |
| `ENABLE_AUDIT_LOGGING` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_CACHE` | core/cache/llm_cache.py, core/cache/retrieval_cache.py |
| `ENABLE_CACHE_GLOBAL` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_CACHE_TRANSCRIPT` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_CACHE_VECTOR` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_CONTENT_MODERATION` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_DISCORD_COMMANDS` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_DISCORD_MONITOR` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_DISTRIBUTED_RATE_LIMITING` | core/secure_config.py, core/settings.py |
| `ENABLE_FASTER_WHISPER` | core/secure_config.py, core/settings.py |
| `ENABLE_GROUNDING` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_TIKTOK` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_TWITCH` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_INGEST_YOUTUBE` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_LOCAL_LLM` | core/secure_config.py, core/settings.py |
| `ENABLE_METRICS` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_PII_DETECTION` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_PROMETHEUS_ENDPOINT` | core/secure_config.py, core/settings.py |
| `ENABLE_RAG_CONTEXT` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_RATE_LIMITING` | core/secure_config.py, core/settings.py |
| `ENABLE_RERANKER` | core/secure_config.py, core/settings.py |
| `ENABLE_TRACING` | core/secure_config.py, core/settings.py |
| `ENABLE_VECTOR_SEARCH` | ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_CREW_CONFIG_VALIDATION` | ultimate_discord_intelligence_bot/crew.py |
| `ENABLE_CREW_STEP_VERBOSE` | ultimate_discord_intelligence_bot/crew.py |
| `CREW_ENABLE_SECURE_QDRANT_FALLBACK` | ultimate_discord_intelligence_bot/settings.py, docs/configuration.md |

### Privacy

| Flag | Referenced In (sample) |
|------|------------------------|
| `enable_pii_detection` | core/privacy/privacy_filter.py, core/secure_config.py |
| `enable_pii_redaction` | core/privacy/privacy_filter.py |

### Rl / Routing

| Flag | Referenced In (sample) |
|------|------------------------|
| `ENABLE_RL_` | core/learn.py, core/secure_config.py |
| `ENABLE_RL_<DOMAIN>` | - |
| `ENABLE_RL_GLOBAL` | core/learn.py, core/secure_config.py |
| `ENABLE_RL_PROMPT` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_RL_RETRIEVAL` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |
| `ENABLE_RL_ROUTING` | core/secure_config.py, ultimate_discord_intelligence_bot/setup_cli.py |

_Generated digest: `978ac569bde6`_

### Deprecated Surfaces

- `services.learning_engine.LearningEngine`: deprecated; use `core.learning_engine.LearningEngine`.
