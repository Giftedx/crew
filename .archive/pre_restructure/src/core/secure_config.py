"""Central secure configuration management (clean rewrite)."""

# ruff: noqa: I001  (optional dependency import ordering is intentional)

from __future__ import annotations

import contextlib
import logging
import os
import warnings
from typing import Any

from security.secrets import get_secret

logger = logging.getLogger(__name__)

_HAS_PYDANTIC = False
_HAS_PYDANTIC_V2 = False

try:  # Full pydantic-settings + pydantic
    from pydantic import AliasChoices, Field as _PydField, validator
    from pydantic_settings import BaseSettings, SettingsConfigDict

    _HAS_PYDANTIC = True
    _HAS_PYDANTIC_V2 = True
except Exception:  # pragma: no cover
    try:  # Plain pydantic only
        from pydantic import AliasChoices, BaseSettings, Field as _PydField, validator  # type: ignore[no-redef]

        class _SettingsConfigDict(dict):
            pass

        SettingsConfigDict = _SettingsConfigDict  # type: ignore[assignment,misc]
        _HAS_PYDANTIC = True
        _HAS_PYDANTIC_V2 = False
    except Exception:  # Final minimal stubs

        class BaseSettings:  # type: ignore[no-redef]
            pass

        class SettingsConfigDict(dict):  # type: ignore[no-redef]
            pass

        class AliasChoices:  # type: ignore[no-redef]
            def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
                pass

        def _PydField(*_args: Any, **kw: Any) -> Any:  # type: ignore[no-redef]  # pragma: no cover
            return kw.get("default")

        def validator(*_v_args: Any, **_v_kwargs: Any):  # pragma: no cover
            def _wrap(f):
                return f

            return _wrap

        _HAS_PYDANTIC = False
        _HAS_PYDANTIC_V2 = False


def Field(*args: Any, **kwargs: Any) -> Any:  # unified wrapper adding env->alias mapping
    if _HAS_PYDANTIC and "env" in kwargs:
        env = kwargs.pop("env")
        kwargs.setdefault("alias", env)
        if "validation_alias" not in kwargs:
            with contextlib.suppress(Exception):  # pragma: no cover - defensive
                kwargs["validation_alias"] = AliasChoices(env, kwargs.get("alias", env))
    return _PydField(*args, **kwargs)


__all__ = [
    "_HAS_PYDANTIC",
    "_HAS_PYDANTIC_V2",
    "AliasChoices",
    "BaseSettings",
    "Field",
    "SettingsConfigDict",
    "validator",
]


class SecureConfig(BaseSettings):
    """Centralized configuration with security validation and caching."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Allow unknown env vars
    )

    # ====== CORE SYSTEM ======
    service_name: str = Field(
        default="ultimate-discord-intel",
        validation_alias=AliasChoices("SERVICE_NAME", "service_name"),
        alias="SERVICE_NAME",
    )
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # ====== API KEYS (CRITICAL) ======
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"),
        alias="OPENAI_API_KEY",
    )
    openrouter_api_key: str | None = Field(default=None, env="OPENROUTER_API_KEY")
    google_api_key: str | None = Field(default=None, env="GOOGLE_API_KEY")
    perspective_api_key: str | None = Field(default=None, env="PERSPECTIVE_API_KEY")
    serply_api_key: str | None = Field(default=None, env="SERPLY_API_KEY")
    exa_api_key: str | None = Field(default=None, env="EXA_API_KEY")
    perplexity_api_key: str | None = Field(default=None, env="PERPLEXITY_API_KEY")
    wolfram_alpha_app_id: str | None = Field(default=None, env="WOLFRAM_ALPHA_APP_ID")
    cohere_api_key: str | None = Field(default=None, env="COHERE_API_KEY")
    jina_api_key: str | None = Field(default=None, env="JINA_API_KEY")

    # ====== DISCORD INTEGRATION ======
    discord_bot_token: str | None = Field(default=None, env="DISCORD_BOT_TOKEN")
    discord_webhook: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DISCORD_WEBHOOK", "discord_webhook"),
        alias="DISCORD_WEBHOOK",
    )
    enable_reranker: bool = Field(default=False, env="ENABLE_RERANKER")
    rerank_provider: str | None = Field(default=None, env="RERANK_PROVIDER")
    discord_private_webhook: str | None = Field(default=None, env="DISCORD_PRIVATE_WEBHOOK")
    discord_alert_webhook: str | None = Field(default=None, env="DISCORD_ALERT_WEBHOOK")

    # ====== VECTOR DATABASE ======
    qdrant_url: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, env="QDRANT_API_KEY")
    qdrant_prefer_grpc: bool = Field(default=False, env="QDRANT_PREFER_GRPC")
    qdrant_grpc_port: int = Field(
        default=6334,
        validation_alias=AliasChoices("QDRANT_GRPC_PORT", "qdrant_grpc_port"),
        alias="QDRANT_GRPC_PORT",
    )

    # ====== FEATURE FLAGS ======
    enable_api: bool = Field(default=True, env="ENABLE_API")
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    enable_prometheus_endpoint: bool = Field(default=False, env="ENABLE_PROMETHEUS_ENDPOINT")
    enable_http_metrics: bool = Field(default=True, env="ENABLE_HTTP_METRICS")

    # Content processing
    enable_cache_global: bool = Field(default=True, env="ENABLE_CACHE_GLOBAL")
    enable_cache_transcript: bool = Field(default=True, env="ENABLE_CACHE_TRANSCRIPT")
    enable_cache_vector: bool = Field(default=True, env="ENABLE_CACHE_VECTOR")

    # Reinforcement learning
    enable_rl_global: bool = Field(default=True, env="ENABLE_RL_GLOBAL")
    enable_rl_routing: bool = Field(default=True, env="ENABLE_RL_ROUTING")
    enable_rl_prompt: bool = Field(default=True, env="ENABLE_RL_PROMPT")
    enable_rl_retrieval: bool = Field(default=True, env="ENABLE_RL_RETRIEVAL")

    # Discord integrations
    enable_discord_archiver: bool = Field(default=True, env="ENABLE_DISCORD_ARCHIVER")
    enable_discord_commands: bool = Field(default=True, env="ENABLE_DISCORD_COMMANDS")
    enable_discord_monitor: bool = Field(default=True, env="ENABLE_DISCORD_MONITOR")

    # Security and privacy
    enable_pii_detection: bool = Field(default=True, env="ENABLE_PII_DETECTION")
    enable_content_moderation: bool = Field(default=True, env="ENABLE_CONTENT_MODERATION")
    enable_playwright_automation: bool = Field(default=False, env="ENABLE_PLAYWRIGHT_AUTOMATION")
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    enable_audit_logging: bool = Field(default=True, env="ENABLE_AUDIT_LOGGING")

    # AI enhancements
    enable_instructor: bool = Field(default=True, env="ENABLE_INSTRUCTOR")
    enable_litellm_router: bool = Field(default=False, env="ENABLE_LITELLM_ROUTER")
    enable_logfire: bool = Field(default=False, env="ENABLE_LOGFIRE")
    enable_langsmith_eval: bool = Field(default=False, env="ENABLE_LANGSMITH_EVAL")
    enable_langfuse_export: bool = Field(default=False, env="ENABLE_LANGFUSE_EXPORT")
    enable_agent_ops: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_AGENT_OPS", "ENABLE_AGENTOPS_EXPORT"),
        alias="ENABLE_AGENT_OPS",
    )
    enable_vw_router: bool = Field(default=False, env="ENABLE_VW_ROUTER")
    enable_llmlingua: bool = Field(default=False, env="ENABLE_LLMLINGUA")
    enable_letta_memory: bool = Field(default=False, env="ENABLE_LETTA_MEMORY")

    # Autonomous AI features
    enable_self_eval_gates: bool = Field(default=False, env="ENABLE_SELF_EVAL_GATES")
    enable_ts_routing: bool = Field(default=False, env="ENABLE_TS_ROUTING")
    enable_hybrid_retrieval: bool = Field(default=False, env="ENABLE_HYBRID_RETRIEVAL")
    enable_cache_promotion: bool = Field(default=False, env="ENABLE_CACHE_PROMOTION")
    enable_prompt_compression: bool = Field(default=False, env="ENABLE_PROMPT_COMPRESSION")
    enable_self_improvement: bool = Field(default=False, env="ENABLE_SELF_IMPROVEMENT")

    # LLM provider routing configuration (new)
    # Policy: quality_first | cost | latency
    router_policy: str = Field(default="quality_first", env="ROUTER_POLICY")
    # Allowlist supports CSV via raw env; parsed list exposed via llm_provider_allowlist
    llm_provider_allowlist_raw: str | None = Field(default=None, env="LLM_PROVIDER_ALLOWLIST")
    llm_provider_allowlist: list[str] | None = Field(default=None)
    # Tasks that should force quality-first
    quality_first_tasks_raw: str | None = Field(default=None, env="QUALITY_FIRST_TASKS")
    quality_first_tasks: list[str] | None = Field(default=None)

    # HTTP retry (unified flag)
    enable_http_retry: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_HTTP_RETRY", "enable_http_retry"),
        alias="ENABLE_HTTP_RETRY",
    )

    # ====== PERFORMANCE SETTINGS ======
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    vector_batch_size: int = Field(default=100, env="VECTOR_BATCH_SIZE")
    rate_limit_rps: int = Field(default=10, env="RATE_LIMIT_RPS")
    rate_limit_burst: int = Field(default=20, env="RATE_LIMIT_BURST")
    enable_distributed_rate_limiting: bool = Field(default=False, env="ENABLE_DISTRIBUTED_RATE_LIMITING")
    rate_limit_redis_url: str | None = Field(default=None, env="RATE_LIMIT_REDIS_URL")
    http_timeout: int = Field(default=30, env="HTTP_TIMEOUT")
    retry_max_attempts: int = Field(default=3, env="RETRY_MAX_ATTEMPTS")

    # ====== DATABASE ======
    database_url: str = Field(default="sqlite:///crew.db", env="DATABASE_URL")
    memory_db_path: str = Field(default="./memory.db", env="MEMORY_DB_PATH")
    archive_db_path: str = Field(default="./data/archive_manifest.db", env="ARCHIVE_DB_PATH")
    trust_tracker_path: str = Field(default="./data/trustworthiness.json", env="TRUST_TRACKER_PATH")

    # ====== MODEL CONFIGURATION ======
    openrouter_general_model: str | None = Field(default=None, env="OPENROUTER_GENERAL_MODEL")
    openrouter_analysis_model: str | None = Field(default=None, env="OPENROUTER_ANALYSIS_MODEL")

    # ====== COST MANAGEMENT ======
    cost_max_per_request: float = Field(default=1.0, env="COST_MAX_PER_REQUEST")
    cost_budget_daily: float = Field(default=100.0, env="COST_BUDGET_DAILY")

    # ====== DIRECTORY CONFIGURATION ======
    crewai_base_dir: str | None = Field(default=None, env="CREWAI_BASE_DIR")
    crewai_downloads_dir: str | None = Field(default=None, env="CREWAI_DOWNLOADS_DIR")
    crewai_config_dir: str | None = Field(default=None, env="CREWAI_CONFIG_DIR")
    crewai_logs_dir: str | None = Field(default=None, env="CREWAI_LOGS_DIR")
    crewai_processing_dir: str | None = Field(default=None, env="CREWAI_PROCESSING_DIR")
    crewai_ytdlp_dir: str | None = Field(default=None, env="CREWAI_YTDLP_DIR")
    crewai_ytdlp_config: str | None = Field(default=None, env="CREWAI_YTDLP_CONFIG")
    crewai_ytdlp_archive: str | None = Field(default=None, env="CREWAI_YTDLP_ARCHIVE")
    crewai_temp_dir: str | None = Field(default=None, env="CREWAI_TEMP_DIR")

    # ====== INTEGRATION SETTINGS ======
    google_credentials: str | None = Field(default=None, env="GOOGLE_CREDENTIALS")
    qdrant_collection: str | None = Field(default=None, env="QDRANT_COLLECTION")
    whisper_model: str = Field(default="base", env="WHISPER_MODEL")
    enable_faster_whisper: bool = Field(default=False, env="ENABLE_FASTER_WHISPER")
    enable_local_llm: bool = Field(default=False, env="ENABLE_LOCAL_LLM")
    local_llm_url: str | None = Field(default=None, env="LOCAL_LLM_URL")
    disable_google_drive: bool = Field(default=False, env="DISABLE_GOOGLE_DRIVE")
    ingest_db_path: str | None = Field(default=None, env="INGEST_DB_PATH")

    # ====== AI ENHANCEMENT SETTINGS ======
    # Instructor (structured LLM outputs)
    instructor_max_retries: int = Field(default=3, env="INSTRUCTOR_MAX_RETRIES")
    instructor_timeout: int = Field(default=30, env="INSTRUCTOR_TIMEOUT")

    # LiteLLM router
    litellm_routing_strategy: str = Field(default="usage-based-routing", env="LITELLM_ROUTING_STRATEGY")
    litellm_cache_enabled: bool = Field(default=True, env="LITELLM_CACHE_ENABLED")
    litellm_fallback_enabled: bool = Field(default=True, env="LITELLM_FALLBACK_ENABLED")
    litellm_budget_per_model: float = Field(default=10.0, env="LITELLM_BUDGET_PER_MODEL")
    litellm_budget_duration: str = Field(default="1d", env="LITELLM_BUDGET_DURATION")

    # Autonomous AI settings
    self_eval_shadow_mode: bool = Field(default=True, env="SELF_EVAL_SHADOW_MODE")
    self_eval_regression_threshold: float = Field(default=0.1, env="SELF_EVAL_REGRESSION_THRESHOLD")
    ts_routing_cold_start_trials: int = Field(default=100, env="TS_ROUTING_COLD_START_TRIALS")
    hybrid_retrieval_fusion_method: str = Field(default="rrf", env="HYBRID_RETRIEVAL_FUSION_METHOD")
    cache_promotion_hit_threshold: int = Field(default=5, env="CACHE_PROMOTION_HIT_THRESHOLD")
    prompt_compression_ratio: float = Field(default=0.5, env="PROMPT_COMPRESSION_RATIO")
    self_improvement_sandbox_mode: str = Field(default="docker", env="SELF_IMPROVEMENT_SANDBOX_MODE")

    # LangSmith evaluation
    langsmith_api_key: str | None = Field(default=None, env="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="discord-intel-evals", env="LANGSMITH_PROJECT")
    langsmith_evaluation_dataset: str | None = Field(default=None, env="LANGSMITH_EVALUATION_DATASET")

    # Langfuse observability
    langfuse_public_key: str | None = Field(default=None, env="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, env="LANGFUSE_SECRET_KEY")
    langfuse_base_url: str | None = Field(default=None, env="LANGFUSE_BASE_URL")

    # AgentOps instrumentation
    agentops_api_key: str | None = Field(default=None, env="AGENTOPS_API_KEY")

    # Vowpal Wabbit router configuration
    vw_model_repository: str | None = Field(default=None, env="VW_MODEL_REPOSITORY")

    # LLMLingua prompt compression
    llmlingua_model: str | None = Field(default=None, env="LLMLINGUA_MODEL")
    llmlingua_target_tokens: int | None = Field(default=None, env="LLMLINGUA_TARGET_TOKENS")
    llmlingua_compression_ratio: float | None = Field(default=None, env="LLMLINGUA_COMPRESSION_RATIO")

    # Letta memory integration
    letta_base_url: str | None = Field(default=None, env="LETTA_BASE_URL")
    letta_api_key: str | None = Field(default=None, env="LETTA_API_KEY")

    # Reranker configuration
    reranker_model: str = Field(default="Xenova/ms-marco-MiniLM-L-6-v2", env="RERANKER_MODEL")
    reranker_top_k: int = Field(default=10, env="RERANKER_TOP_K")

    # ====== COLLABORATIVE INTELLIGENCE SETTINGS ======
    # Graph memory backends (neo4j, networkx, qdrant)
    graph_backend: str = Field(default="neo4j", env="GRAPH_BACKEND")
    neo4j_uri: str = Field(default="bolt://neo4j:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="neo4j", env="NEO4J_PASSWORD")
    enable_multi_graph_backends: bool = Field(default=True, env="ENABLE_MULTI_GRAPH_BACKENDS")

    # Agent message bus
    enable_agent_message_bus: bool = Field(default=False, env="ENABLE_AGENT_MESSAGE_BUS")
    agent_bus_redis_url: str = Field(default="redis://redis:6379", env="AGENT_BUS_REDIS_URL")
    agent_bus_redis_db: int = Field(default=2, env="AGENT_BUS_REDIS_DB")
    agent_bus_ttl_seconds: int = Field(default=3600, env="AGENT_BUS_TTL_SECONDS")
    enable_global_agent_broadcast: bool = Field(default=True, env="ENABLE_GLOBAL_AGENT_BROADCAST")

    # Cross-tenant meta-learning
    enable_cross_tenant_learning: bool = Field(default=False, env="ENABLE_CROSS_TENANT_LEARNING")
    cross_tenant_epsilon: float = Field(default=1.0, env="CROSS_TENANT_EPSILON")
    meta_learning_sync_interval_seconds: int = Field(default=300, env="META_LEARNING_SYNC_INTERVAL_SECONDS")
    enable_differential_privacy: bool = Field(default=True, env="ENABLE_DIFFERENTIAL_PRIVACY")

    # Multi-agent deliberation
    enable_agent_deliberation: bool = Field(default=False, env="ENABLE_AGENT_DELIBERATION")
    deliberation_confidence_threshold: float = Field(default=0.7, env="DELIBERATION_CONFIDENCE_THRESHOLD")
    deliberation_min_agents: int = Field(default=3, env="DELIBERATION_MIN_AGENTS")
    deliberation_timeout_seconds: int = Field(default=30, env="DELIBERATION_TIMEOUT_SECONDS")

    # Logfire observability
    logfire_token: str | None = Field(default=None, env="LOGFIRE_TOKEN")
    logfire_project_name: str = Field(default="discord-intelligence-bot", env="LOGFIRE_PROJECT_NAME")
    logfire_service_version: str | None = Field(default=None, env="LOGFIRE_SERVICE_VERSION")
    logfire_send_to_logfire: bool = Field(default=True, env="LOGFIRE_SEND_TO_LOGFIRE")

    # ====== CACHING SETTINGS ======
    cache_ttl_llm: int = Field(default=3600, env="CACHE_TTL_LLM")
    cache_ttl_retrieval: int = Field(default=300, env="CACHE_TTL_RETRIEVAL")

    def get_api_key(self, service: str) -> str:
        """Get API key for a service with validation and audit logging.

        Args:
            service: Service name (openai, openrouter, google, etc.)

        Returns:
            API key value

        Raises:
            ValueError: If API key is not configured
        """
        service_lower = service.lower()
        key_mapping = {
            "openai": self.openai_api_key,
            "openrouter": self.openrouter_api_key,
            "google": self.google_api_key,
            "perspective": self.perspective_api_key,
            "serply": self.serply_api_key,
            "exa": self.exa_api_key,
            "perplexity": self.perplexity_api_key,
            "wolfram": self.wolfram_alpha_app_id,
            "langsmith": self.langsmith_api_key,
            "agentops": self.agentops_api_key,
            "langfuse_public": self.langfuse_public_key,
            "langfuse_secret": self.langfuse_secret_key,
            "letta": self.letta_api_key,
        }

        api_key = key_mapping.get(service_lower)
        if not api_key:
            raise ValueError(f"API key for service '{service}' is not configured")

        # Audit log for sensitive access
        if self.enable_audit_logging:
            logger.info(
                f"API key accessed for service: {service}",
                extra={"service": service, "action": "api_key_access", "audit": True},
            )

        return api_key

    def get_webhook(self, webhook_type: str) -> str:
        """Get Discord webhook URL with validation.

        Args:
            webhook_type: Type of webhook (discord, discord_private, discord_alert)

        Returns:
            Webhook URL

        Raises:
            ValueError: If webhook is not configured
        """
        webhook_mapping = {
            "discord": self.discord_webhook,
            "discord_private": self.discord_private_webhook,
            "discord_alert": self.discord_alert_webhook,
        }

        webhook_url = webhook_mapping.get(webhook_type)
        if not webhook_url:
            raise ValueError(f"Webhook '{webhook_type}' is not configured")

        return webhook_url

    def is_feature_enabled(self, feature: str) -> bool:
        feature_mapping = {
            "api": self.enable_api,
            "tracing": self.enable_tracing,
            "prometheus_endpoint": self.enable_prometheus_endpoint,
            "http_metrics": self.enable_http_metrics,
            "cache_global": self.enable_cache_global,
            "cache_transcript": self.enable_cache_transcript,
            "cache_vector": self.enable_cache_vector,
            "rl_global": self.enable_rl_global,
            "rl_routing": self.enable_rl_routing,
            "rl_prompt": self.enable_rl_prompt,
            "rl_retrieval": self.enable_rl_retrieval,
            "discord_archiver": self.enable_discord_archiver,
            "discord_commands": self.enable_discord_commands,
            "discord_monitor": self.enable_discord_monitor,
            "pii_detection": self.enable_pii_detection,
            "content_moderation": self.enable_content_moderation,
            "rate_limiting": self.enable_rate_limiting,
            "audit_logging": self.enable_audit_logging,
            "http_retry": self.enable_http_retry,
            "langsmith_eval": self.enable_langsmith_eval,
            "langfuse_export": self.enable_langfuse_export,
            "agent_ops": self.enable_agent_ops,
            "vw_router": self.enable_vw_router,
            "llmlingua": self.enable_llmlingua,
            "letta_memory": self.enable_letta_memory,
        }
        value = feature_mapping.get(feature)
        if value is None:
            env_key = f"ENABLE_{feature.upper()}"
            env_value = os.getenv(env_key)
            if env_value and env_value.lower() in ("1", "true", "yes", "on"):
                return True
            default_enabled = {
                "api",
                "http_metrics",
                "cache_global",
                "cache_transcript",
                "cache_vector",
                "rl_global",
                "rl_routing",
                "rl_prompt",
                "rl_retrieval",
                "discord_archiver",
                "discord_commands",
                "discord_monitor",
                "pii_detection",
                "content_moderation",
                "rate_limiting",
                "audit_logging",
            }
            return feature in default_enabled
        return bool(value)

    def get_webhook_secret(self, webhook_name: str = "default") -> str:
        """Get webhook secret with mandatory validation.

        This method ensures webhook secrets are never left as default values
        and integrates with the existing security.secrets rotation system.

        Args:
            webhook_name: Name of the webhook secret

        Returns:
            Webhook secret value

        Raises:
            ValueError: If secret is not properly configured
        """
        try:
            # Use existing security.secrets system for versioned secret management
            secret_ref = f"WEBHOOK_SECRET_{webhook_name.upper()}"
            secret_value = get_secret(secret_ref)

            # Critical: prevent deployment with default values
            if secret_value in ("CHANGE_ME", "changeme", "default", ""):
                raise ValueError(
                    f"Webhook secret '{webhook_name}' must be changed from default value. "
                    f"Set environment variable {secret_ref} to a secure random value."
                )

            return secret_value

        except KeyError as exc:
            # Fallback to legacy config for backward compatibility
            legacy_value = os.getenv(f"WEBHOOK_SECRET_{webhook_name.upper()}")
            if not legacy_value or legacy_value in ("CHANGE_ME", "changeme", "default"):
                raise ValueError(
                    f"Webhook secret '{webhook_name}' is not configured or uses default value. "
                    f"Set WEBHOOK_SECRET_{webhook_name.upper()} environment variable."
                ) from exc

            warnings.warn(
                "Using legacy webhook secret configuration. Migrate to security.secrets system for rotation support.",
                DeprecationWarning,
                stacklevel=2,
            )

            return legacy_value

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get any configuration setting by key name.

        Args:
            key: Setting key (snake_case)
            default: Default value if setting not found

        Returns:
            Configuration value or default
        """
        # First try to get from configuration attributes
        value = getattr(self, key, None)
        if value is not None:
            return value

        # Fall back to environment variable (uppercase)
        env_key = key.upper()
        env_value = os.getenv(env_key, default)

        # Convert string environment values to appropriate types
        if env_value and isinstance(env_value, str):
            # Boolean conversion for common flag patterns
            if env_value.lower() in ("1", "true", "yes", "on"):
                return True
            elif env_value.lower() in ("0", "false", "no", "off"):
                return False

        return env_value

    # --- Validators for derived list settings (pydantic v1/v2 compatible) ---
    @validator("llm_provider_allowlist", pre=True, always=True)
    def _parse_provider_allowlist(cls, v: Any, values: dict[str, Any]) -> list[str] | None:
        if isinstance(v, list):
            return [str(x).lower() for x in v]
        raw = values.get("llm_provider_allowlist_raw")
        if isinstance(raw, list):
            return [str(x).lower() for x in raw]
        if isinstance(raw, str):
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            return [p.lower() for p in parts] or None
        return None

    @validator("quality_first_tasks", pre=True, always=True)
    def _parse_quality_tasks(cls, v: Any, values: dict[str, Any]) -> list[str] | None:
        if isinstance(v, list):
            return [str(x) for x in v]
        raw = values.get("quality_first_tasks_raw")
        if isinstance(raw, list):
            return [str(x) for x in raw]
        if isinstance(raw, str):
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            return parts or None
        return None


# Global configuration instance
_config: SecureConfig | None = None


def get_config() -> SecureConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = SecureConfig()
    return _config


def reload_config() -> SecureConfig:
    """Reload configuration from environment (useful for testing)."""
    global _config
    _config = None
    return get_config()


# Backward compatibility helpers for gradual migration
def get_api_key(service: str) -> str:
    """Backward compatibility wrapper for get_api_key."""
    return get_config().get_api_key(service)


def get_webhook_url(webhook_type: str) -> str:
    """Backward compatibility wrapper for get_webhook."""
    return get_config().get_webhook(webhook_type)


def is_feature_enabled(feature: str) -> bool:
    """Backward compatibility wrapper for feature flags."""
    return get_config().is_feature_enabled(feature)


def get_setting(key: str, default: Any = None) -> Any:
    """Get any configuration setting by key name.

    Args:
        key: Setting key (snake_case)
        default: Default value if setting not found

    Returns:
        Configuration value or default
    """
    config = get_config()
    return getattr(config, key, default)


# ---------------------------------------------------------------------------
# Lightweight fallback initialization when Pydantic is unavailable
# ---------------------------------------------------------------------------
if not _HAS_PYDANTIC:
    # Inject a basic __init__ to populate critical fields from environment and enforce
    # minimal validation expected by tests. This keeps API compatible without
    # requiring pydantic in ultra-minimal environments.
    def _fallback_init(self) -> None:
        import os as _os

        # Core system
        self.service_name = _os.getenv("SERVICE_NAME", "ultimate-discord-intel")
        self.environment = _os.getenv("ENVIRONMENT", "development")
        self.debug = _os.getenv("DEBUG", "false").lower() in ("1", "true", "yes", "on")
        self.log_level = _os.getenv("LOG_LEVEL", "INFO")

        # Critical secrets / API keys
        self.openai_api_key = _os.getenv("OPENAI_API_KEY")
        self.discord_webhook = _os.getenv("DISCORD_WEBHOOK")

        # Feature flags (commonly used ones)
        self.enable_http_retry = _os.getenv("ENABLE_HTTP_RETRY", "false").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        self.enable_audit_logging = _os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() in ("1", "true", "yes", "on")
        self.enable_pii_detection = _os.getenv("ENABLE_PII_DETECTION", "true").lower() in ("1", "true", "yes", "on")
        self.enable_rate_limiting = _os.getenv("ENABLE_RATE_LIMITING", "true").lower() in ("1", "true", "yes", "on")
        self.enable_tracing = _os.getenv("ENABLE_TRACING", "false").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

        # API keys and webhooks (commonly accessed)
        self.openrouter_api_key = _os.getenv("OPENROUTER_API_KEY")
        self.discord_private_webhook = _os.getenv("DISCORD_PRIVATE_WEBHOOK")
        self.discord_alert_webhook = _os.getenv("DISCORD_ALERT_WEBHOOK")

        # Networking
        self.http_timeout = int(_os.getenv("HTTP_TIMEOUT", "30"))
        self.retry_max_attempts = int(_os.getenv("RETRY_MAX_ATTEMPTS", "3"))

        # Qdrant gRPC port with validation
        grpc_val = _os.getenv("QDRANT_GRPC_PORT", "6334")
        try:
            self.qdrant_grpc_port = int(grpc_val)
        except ValueError as exc:
            # Match test expectation: invalid numeric env should raise ValueError on reload
            raise ValueError("Invalid QDRANT_GRPC_PORT") from exc

        # Cost management settings
        self.cost_max_per_request = float(_os.getenv("COST_MAX_PER_REQUEST", "1.0"))
        self.cost_budget_daily = float(_os.getenv("COST_BUDGET_DAILY", "100.0"))

        # LLM provider routing (fallback parsing)
        self.router_policy = _os.getenv("ROUTER_POLICY", "quality_first")
        self.llm_provider_allowlist_raw = _os.getenv("LLM_PROVIDER_ALLOWLIST")
        if self.llm_provider_allowlist_raw:
            self.llm_provider_allowlist = [
                p.strip().lower() for p in self.llm_provider_allowlist_raw.split(",") if p.strip()
            ]
        else:
            self.llm_provider_allowlist = None
        self.quality_first_tasks_raw = _os.getenv("QUALITY_FIRST_TASKS")
        if self.quality_first_tasks_raw:
            self.quality_first_tasks = [p.strip() for p in self.quality_first_tasks_raw.split(",") if p.strip()]
        else:
            self.quality_first_tasks = None

        # Database / paths (only those referenced in docs/tests)
        self.archive_db_path = _os.getenv("ARCHIVE_DB_PATH", "./data/archive_manifest.db")

    # Bind the lightweight initializer
    SecureConfig.__init__ = _fallback_init  # type: ignore[assignment]
