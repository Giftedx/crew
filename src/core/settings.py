"""Minimal, mypy-clean settings baseline.

This intentionally removes all dynamic pydantic import complexity. We expose a
very small stable surface so the type checker has zero noise. If / when richer
validation is required we can layer it back in behind feature flags.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any


class BaseSettings:
    """Lightweight base; stores provided kwargs as attributes."""

    _IS_STUB = True

    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


def Field(default: Any = None, **_: Any) -> Any:  # noqa: D401
    return default


class AliasChoices(tuple):  # compatibility shim
    def __new__(cls, *choices: str):
        return super().__new__(cls, choices)

    def first(self) -> str:  # pragma: no cover - trivial
        return self[0] if self else ""


class Settings(BaseSettings):
    # Service metadata
    service_name: str = Field("crew-service")
    environment: str = Field("dev")

    # Core API / metrics / tracing / rate limiting toggles
    enable_api: bool = Field(False, alias="ENABLE_API")
    enable_http_metrics: bool = Field(False, alias="ENABLE_HTTP_METRICS")
    enable_tracing: bool = Field(False, alias="ENABLE_TRACING")
    enable_prometheus_endpoint: bool = Field(False, alias="ENABLE_PROMETHEUS_ENDPOINT")
    enable_rate_limiting: bool = Field(False, alias="ENABLE_RATE_LIMITING")
    prometheus_endpoint_path: str = Field("/metrics")
    rate_limit_rps: int = Field(10)
    rate_limit_burst: int = Field(10)
    rate_limit_redis_url: str | None = Field(None)

    # Feature flag surface (documented flags kept in sync with docs/feature_flags.md)
    enable_advanced_cache: bool = Field(False, alias="ENABLE_ADVANCED_CACHE")
    enable_api_cache: bool = Field(False, alias="ENABLE_API_CACHE")
    enable_dependency_tracking: bool = Field(False, alias="ENABLE_DEPENDENCY_TRACKING")
    enable_pipeline_run_api: bool = Field(False, alias="ENABLE_PIPELINE_RUN_API")
    enable_pipeline_job_queue: bool = Field(False, alias="ENABLE_PIPELINE_JOB_QUEUE")
    enable_autointel_api: bool = Field(False, alias="ENABLE_AUTOINTEL_API")
    enable_http_cache: bool = Field(False, alias="ENABLE_HTTP_CACHE")
    enable_llm_cache: bool = Field(False, alias="ENABLE_LLM_CACHE")
    enable_degradation_reporter: bool = Field(
        False, alias="ENABLE_DEGRADATION_REPORTER"
    )
    enable_discord_archiver: bool = Field(False, alias="ENABLE_DISCORD_ARCHIVER")
    enable_rag_context: bool = Field(False, alias="ENABLE_RAG_CONTEXT")
    enable_vector_search: bool = Field(False, alias="ENABLE_VECTOR_SEARCH")
    enable_discord_commands: bool = Field(False, alias="ENABLE_DISCORD_COMMANDS")
    enable_discord_monitor: bool = Field(False, alias="ENABLE_DISCORD_MONITOR")
    enable_audit_logging: bool = Field(False, alias="ENABLE_AUDIT_LOGGING")
    enable_cache_global: bool = Field(False, alias="ENABLE_CACHE_GLOBAL")
    enable_cache_transcript: bool = Field(False, alias="ENABLE_CACHE_TRANSCRIPT")
    enable_cache_vector: bool = Field(False, alias="ENABLE_CACHE_VECTOR")
    enable_distr_rate_limiting: bool = Field(
        False, alias="ENABLE_DISTRIBUTED_RATE_LIMITING"
    )
    enable_rl_global: bool = Field(False, alias="ENABLE_RL_GLOBAL")
    enable_rl_routing: bool = Field(False, alias="ENABLE_RL_ROUTING")
    enable_rl_prompt: bool = Field(False, alias="ENABLE_RL_PROMPT")
    enable_rl_retrieval: bool = Field(False, alias="ENABLE_RL_RETRIEVAL")
    enable_rl_vowpal: bool = Field(False, alias="ENABLE_RL_VOWPAL")
    enable_experiment_harness: bool = Field(False, alias="ENABLE_EXPERIMENT_HARNESS")
    enable_rl_lints: bool = Field(False, alias="ENABLE_RL_LINTS")
    enable_secure_path_fallback: bool = Field(
        False, alias="ENABLE_SECURE_PATH_FALLBACK"
    )
    enable_secure_qdrant_fallback: bool = Field(
        False, alias="ENABLE_SECURE_QDRANT_FALLBACK"
    )

    # Caching toggles
    cache_compression_enabled: bool = Field(True)
    cache_promotion_enabled: bool = Field(True)

    # Feature flags
    enable_reranker: bool = Field(False)
    enable_faster_whisper: bool = Field(False)
    enable_local_llm: bool = Field(False)
    enable_prompt_compression: bool = Field(False, alias="ENABLE_PROMPT_COMPRESSION")
    enable_prompt_compression_flag: bool = Field(
        False, alias="ENABLE_PROMPT_COMPRESSION"
    )  # doc sync
    enable_llmlingua: bool = Field(False, alias="ENABLE_LLMLINGUA")
    enable_llmlingua_shadow: bool = Field(False, alias="ENABLE_LLMLINGUA_SHADOW")
    enable_token_aware_chunker: bool = Field(False)
    enable_semantic_cache: bool = Field(False)
    enable_gptcache: bool = Field(False, alias="ENABLE_GPTCACHE")
    enable_gptcache_analysis_shadow: bool = Field(
        False, alias="ENABLE_GPTCACHE_ANALYSIS_SHADOW"
    )
    enable_transcript_compression: bool = Field(
        False, alias="ENABLE_TRANSCRIPT_COMPRESSION"
    )
    enable_graph_memory: bool = Field(False, alias="ENABLE_GRAPH_MEMORY")
    enable_ax_routing: bool = Field(False, alias="ENABLE_AX_ROUTING")
    enable_agent_ops: bool = Field(False, alias="ENABLE_AGENT_OPS")
    enable_enhanced_memory: bool = Field(False, alias="ENABLE_ENHANCED_MEMORY")

    # Performance optimization flags
    enable_parallel_memory_ops: bool = Field(False, alias="ENABLE_PARALLEL_MEMORY_OPS")
    enable_parallel_analysis: bool = Field(False, alias="ENABLE_PARALLEL_ANALYSIS")
    enable_parallel_fact_checking: bool = Field(
        False, alias="ENABLE_PARALLEL_FACT_CHECKING"
    )

    # Provider + model routing
    rerank_provider: str | None = Field(None)
    local_llm_url: str | None = Field(None)
    openrouter_referer: str | None = Field(None)
    openrouter_title: str | None = Field(None)

    # RL / reward shaping
    reward_cost_weight: float = Field(0.5)
    reward_latency_weight: float = Field(0.5)
    reward_latency_ms_window: int = Field(2000)
    rl_policy_model_selection: str = Field("epsilon_greedy")
    vw_bandit_args: str | None = Field(None, alias="VW_BANDIT_ARGS")

    # Prompt compression parameters
    token_chunk_target_tokens: int = Field(220)
    prompt_compression_max_repeated_blank_lines: int = Field(1)
    prompt_compression_default_target: float = Field(0.0)
    prompt_compression_max_tokens: int | None = Field(None)
    transcript_compression_min_tokens: int = Field(1200)
    transcript_compression_target_ratio: float = Field(0.35)
    transcript_compression_max_tokens: int | None = Field(None)

    # LLMLingua configuration
    llmlingua_target_ratio: float = Field(0.35)
    llmlingua_target_tokens: int = Field(1200)
    llmlingua_min_tokens: int = Field(600)
    llmlingua_stage: str = Field("round2")
    llmlingua_device: str | None = Field(None)

    # Semantic cache params
    semantic_cache_threshold: float = Field(0.85)
    semantic_cache_ttl_seconds: int = Field(3600)
    semantic_cache_shadow_tasks: str | None = Field(None)

    # Misc ingestion
    download_quality_default: str = Field("1080p")

    # Pipeline job queue configuration
    pipeline_max_concurrent_jobs: int = Field(5)
    pipeline_job_ttl_seconds: int = Field(3600)

    # Secrets (never log these)
    agent_ops_api_key: str | None = Field(None, alias="AGENT_OPS_API_KEY")
    mem0_api_key: str | None = Field(None, alias="MEM0_API_KEY")
    archive_api_token: str | None = Field(None)
    discord_bot_token: str | None = Field(None)

    # Vector store (Qdrant) configuration
    # These are intentionally simple so other modules (memory.qdrant_provider) can
    # pick them up via get_settings() and environment overlay without importing
    # heavy config layers.
    qdrant_url: str = Field("")
    qdrant_api_key: str = Field("")
    qdrant_prefer_grpc: bool = Field(False)
    qdrant_grpc_port: int | None = Field(None)

    # Vector ingest tuning
    vector_batch_size: int = Field(128)


_BOOL_TRUE = {"1", "true", "yes", "on"}


def _coerce_env(raw: str, current: Any) -> Any:
    """Coerce raw env string to the existing attribute's type.

    Only basic primitives are supported; complex coercion intentionally avoided
    to keep this layer predictable. If coercion fails we return the existing
    value (silent fallback) to avoid raising during import paths.
    """
    try:
        if isinstance(current, bool):
            return raw.lower() in _BOOL_TRUE
        if isinstance(current, int) and not isinstance(
            current, bool
        ):  # bool is subclass of int
            return int(raw)
        if isinstance(current, float):
            return float(raw)
    except Exception:  # pragma: no cover - defensive
        return current
    return raw


def _apply_env_overrides(s: Settings) -> None:
    if os.getenv("DISABLE_SETTINGS_ENV_OVERLAY") in ("1", "true", "yes", "on"):
        return
    # Build attribute map (uppercase -> attr name)
    attr_map: dict[str, str] = {}
    for name in dir(s):
        if name.startswith("_"):
            continue
        # Only consider attributes with non-callable values
        try:
            val = getattr(s, name)
        except Exception:  # pragma: no cover - defensive
            continue
        if callable(val):  # skip methods
            continue
        attr_map[name.upper()] = name
    # Pass 1: direct name matches (SERVICE_NAME, RATE_LIMIT_RPS, etc.)
    for env_key, raw in os.environ.items():
        if env_key in attr_map:
            attr_name = attr_map[env_key]
            current = getattr(s, attr_name)
            setattr(s, attr_name, _coerce_env(raw, current))
    # Pass 2: ENABLE_* flags that map to attributes with enable_* or matching alias
    for env_key, raw in os.environ.items():
        if not env_key.startswith("ENABLE_"):
            continue
        # Derive attribute guess: enable_x (lowercase)
        guess = "enable_" + env_key[len("ENABLE_") :].lower()
        if guess in attr_map:  # direct enable_* attribute
            current = getattr(s, guess)
            setattr(s, guess, _coerce_env(raw, current))
        else:
            # Some attributes use slightly different internal names (e.g. ENABLE_CACHE_GLOBAL -> enable_cache_global)
            lowered = env_key.lower()
            if lowered in attr_map:
                current = getattr(s, lowered)
                setattr(s, lowered, _coerce_env(raw, current))


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    _apply_env_overrides(s)
    return s


def _reset_cache_for_tests() -> None:  # pragma: no cover - simple test seam
    try:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass


__all__ = ["Settings", "get_settings", "BaseSettings", "Field", "AliasChoices"]
