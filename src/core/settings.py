"""Central application settings using Pydantic.

All environment driven knobs should live here so that other modules avoid
scattered ``os.environ.get`` calls.  This makes configuration discoverable,
testable, and documents defaults in one place.

Convention: Boolean flags default to *disabled* unless the legacy behaviour
prior to centralisation assumed enabled (e.g. HTTP metrics).  New features
should ship behind an ``ENABLE_*`` style flag for opt‑in safety.
"""

from __future__ import annotations

import importlib
import sys
from functools import lru_cache
from importlib import util as importlib_util
from types import ModuleType

try:
    from pydantic import AliasChoices, Field

    _HAS_PYDANTIC = True
except Exception:  # pragma: no cover - fallback when pydantic unavailable
    _HAS_PYDANTIC = False

    def Field(*_args, **kwargs):
        return kwargs.get("default")

    def AliasChoices(*_args, **_kwargs):
        return None


if _HAS_PYDANTIC:
    try:  # Pydantic v2 (preferred)
        from pydantic_settings import BaseSettings, SettingsConfigDict

        _HAS_PYDANTIC_V2 = True
    except Exception:  # pragma: no cover - fall back to pydantic v1 style
        try:
            from pydantic import BaseSettings
        except Exception:  # pragma: no cover
            BaseSettings = object

        SettingsConfigDict = dict
        _HAS_PYDANTIC_V2 = False
else:  # pragma: no cover - no pydantic available at all
    BaseSettings = object
    SettingsConfigDict = dict
    _HAS_PYDANTIC_V2 = False
try:
    _spec = importlib_util.find_spec("dotenv")
    _DOTENV_AVAILABLE = _spec is not None and getattr(_spec, "loader", None) is not None
except Exception:  # pragma: no cover - extremely defensive
    _DOTENV_AVAILABLE = False

# If real package available but a stub without __file__ was inserted earlier by tests, drop it
if _DOTENV_AVAILABLE and "dotenv" in sys.modules and getattr(sys.modules["dotenv"], "__file__", None) is None:
    del sys.modules["dotenv"]
    importlib.import_module("dotenv")

# Provide stub only if absent (offers dotenv_values for pydantic-settings provider import)
if not _DOTENV_AVAILABLE:  # pragma: no cover
    fake = ModuleType("dotenv")

    def dotenv_values(_path: str | None = None) -> dict[str, str]:
        return {}

    fake.dotenv_values = dotenv_values  # type: ignore[attr-defined]
    sys.modules["dotenv"] = fake


class Settings(BaseSettings):
    # If python-dotenv is not installed, avoid referencing .env to prevent import error inside
    # pydantic-settings provider chain. Tests rely on environment variable injection directly.
    if _HAS_PYDANTIC_V2:
        # Pydantic v2 settings configuration (class var expected by BaseSettings)
        model_config = SettingsConfigDict(
            env_file=".env" if _DOTENV_AVAILABLE else None,
            case_sensitive=False,
            # Tests (and real deployments) may inject many more environment variables
            # than the curated subset we explicitly model here. We ignore unknown keys
            # so that adding a new secret or flag externally does not immediately break
            # Settings() construction with a ValidationError (pydantic's default would
            # otherwise forbid extras in this context).
            extra="ignore",
        )
    else:  # pragma: no cover - pydantic v1 compatibility

        class Config:
            env_file = ".env" if _DOTENV_AVAILABLE else None
            case_sensitive = False

    # Service metadata
    service_name: str = Field(
        default="ultimate-discord-intel",
        validation_alias=AliasChoices("SERVICE_NAME", "service_name"),
        alias="SERVICE_NAME",
    )

    # API / server enablement
    enable_api: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_API", "enable_api"),
        alias="ENABLE_API",
    )

    # Metrics / Prometheus
    enable_prometheus_endpoint: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_PROMETHEUS_ENDPOINT", "enable_prometheus_endpoint"),
        alias="ENABLE_PROMETHEUS_ENDPOINT",
    )
    prometheus_endpoint_path: str = Field(
        default="/metrics",
        validation_alias=AliasChoices("PROMETHEUS_ENDPOINT_PATH", "prometheus_endpoint_path"),
        alias="PROMETHEUS_ENDPOINT_PATH",
    )
    enable_http_metrics: bool = Field(
        default=True,
        validation_alias=AliasChoices("ENABLE_HTTP_METRICS", "enable_http_metrics"),
        alias="ENABLE_HTTP_METRICS",
    )

    # Tracing / OpenTelemetry
    enable_tracing: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_TRACING", "enable_tracing"),
        alias="ENABLE_TRACING",
    )
    otel_endpoint: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OTEL_EXPORTER_OTLP_ENDPOINT", "otel_endpoint"),
        alias="OTEL_EXPORTER_OTLP_ENDPOINT",
    )
    otel_headers: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OTEL_EXPORTER_OTLP_HEADERS", "otel_headers"),
        alias="OTEL_EXPORTER_OTLP_HEADERS",
    )
    otel_traces_sampler: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OTEL_TRACES_SAMPLER", "otel_traces_sampler"),
        alias="OTEL_TRACES_SAMPLER",
    )
    otel_traces_sampler_arg: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OTEL_TRACES_SAMPLER_ARG", "otel_traces_sampler_arg"),
        alias="OTEL_TRACES_SAMPLER_ARG",
    )

    # Qdrant / vector store
    qdrant_url: str = Field(
        default=":memory:",
        validation_alias=AliasChoices("QDRANT_URL", "qdrant_url"),
        alias="QDRANT_URL",
    )
    qdrant_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("QDRANT_API_KEY", "qdrant_api_key"),
        alias="QDRANT_API_KEY",
    )
    qdrant_prefer_grpc: bool = Field(
        default=False,
        validation_alias=AliasChoices("QDRANT_PREFER_GRPC", "qdrant_prefer_grpc"),
        alias="QDRANT_PREFER_GRPC",
    )
    qdrant_grpc_port: int | None = Field(
        default=None,
        validation_alias=AliasChoices("QDRANT_GRPC_PORT", "qdrant_grpc_port"),
        alias="QDRANT_GRPC_PORT",
    )
    vector_batch_size: int = Field(
        default=128,
        validation_alias=AliasChoices("VECTOR_BATCH_SIZE", "vector_batch_size"),
        alias="VECTOR_BATCH_SIZE",
    )

    # Behaviour / feature flags
    enable_rate_limiting: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_RATE_LIMITING", "enable_rate_limiting"),
        alias="ENABLE_RATE_LIMITING",
    )
    enable_distributed_rate_limiting: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_DISTRIBUTED_RATE_LIMITING", "enable_distributed_rate_limiting"),
        alias="ENABLE_DISTRIBUTED_RATE_LIMITING",
    )
    rate_limit_redis_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RATE_LIMIT_REDIS_URL", "rate_limit_redis_url"),
        alias="RATE_LIMIT_REDIS_URL",
    )
    rate_limit_rps: int = Field(
        default=10,
        validation_alias=AliasChoices("RATE_LIMIT_RPS", "rate_limit_rps"),
        alias="RATE_LIMIT_RPS",
    )
    rate_limit_burst: int = Field(
        default=20,
        validation_alias=AliasChoices("RATE_LIMIT_BURST", "rate_limit_burst"),
        alias="RATE_LIMIT_BURST",
    )
    enable_http_retry: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_HTTP_RETRY", "enable_http_retry"),
        alias="ENABLE_HTTP_RETRY",
    )  # Mirrors previous flag
    enable_http_cache: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_HTTP_CACHE", "enable_http_cache"),
        alias="ENABLE_HTTP_CACHE",
    )
    http_cache_ttl_seconds: int = Field(
        default=300,
        validation_alias=AliasChoices("HTTP_CACHE_TTL_SECONDS", "http_cache_ttl_seconds"),
        alias="HTTP_CACHE_TTL_SECONDS",
    )

    # Advanced Caching System
    enable_advanced_cache: bool = Field(
        default=True,
        validation_alias=AliasChoices("ENABLE_ADVANCED_CACHE", "enable_advanced_cache"),
        alias="ENABLE_ADVANCED_CACHE",
    )
    enable_llm_cache: bool = Field(
        default=True,
        validation_alias=AliasChoices("ENABLE_LLM_CACHE", "enable_llm_cache"),
        alias="ENABLE_LLM_CACHE",
    )
    enable_api_cache: bool = Field(
        default=True,
        validation_alias=AliasChoices("ENABLE_API_CACHE", "enable_api_cache"),
        alias="ENABLE_API_CACHE",
    )
    enable_dependency_tracking: bool = Field(
        default=True,
        validation_alias=AliasChoices("ENABLE_DEPENDENCY_TRACKING", "enable_dependency_tracking"),
        alias="ENABLE_DEPENDENCY_TRACKING",
    )
    cache_redis_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CACHE_REDIS_URL", "cache_redis_url"),
        alias="CACHE_REDIS_URL",
    )
    cache_ttl_llm: int = Field(
        default=3600,  # 1 hour
        validation_alias=AliasChoices("CACHE_TTL_LLM", "cache_ttl_llm"),
        alias="CACHE_TTL_LLM",
    )
    cache_ttl_api: int = Field(
        default=300,  # 5 minutes
        validation_alias=AliasChoices("CACHE_TTL_API", "cache_ttl_api"),
        alias="CACHE_TTL_API",
    )
    cache_max_size_mb: int = Field(
        default=100,
        validation_alias=AliasChoices("CACHE_MAX_SIZE_MB", "cache_max_size_mb"),
        alias="CACHE_MAX_SIZE_MB",
    )
    cache_compression_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("CACHE_COMPRESSION_ENABLED", "cache_compression_enabled"),
        alias="CACHE_COMPRESSION_ENABLED",
    )
    cache_promotion_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("CACHE_PROMOTION_ENABLED", "cache_promotion_enabled"),
        alias="CACHE_PROMOTION_ENABLED",
    )

    enable_reranker: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_RERANKER", "enable_reranker"),
        alias="ENABLE_RERANKER",
    )
    rerank_provider: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RERANK_PROVIDER", "rerank_provider"),
        alias="RERANK_PROVIDER",
    )
    enable_faster_whisper: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_FASTER_WHISPER", "enable_faster_whisper"),
        alias="ENABLE_FASTER_WHISPER",
    )
    enable_local_llm: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_LOCAL_LLM", "enable_local_llm"),
        alias="ENABLE_LOCAL_LLM",
    )
    local_llm_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LOCAL_LLM_URL", "local_llm_url"),
        alias="LOCAL_LLM_URL",
    )

    # Content ingestion defaults
    download_quality_default: str = Field(
        default="1080p",
        validation_alias=AliasChoices("DEFAULT_DOWNLOAD_QUALITY", "download_quality_default"),
        alias="DEFAULT_DOWNLOAD_QUALITY",
    )

    # RL reward shaping weights
    reward_cost_weight: float = Field(
        default=0.5,
        validation_alias=AliasChoices("REWARD_COST_WEIGHT", "reward_cost_weight"),
        alias="REWARD_COST_WEIGHT",
    )
    reward_latency_weight: float = Field(
        default=0.5,
        validation_alias=AliasChoices("REWARD_LATENCY_WEIGHT", "reward_latency_weight"),
        alias="REWARD_LATENCY_WEIGHT",
    )

    # Reward normalization window for latency (milliseconds)
    reward_latency_ms_window: int = Field(
        default=2000,
        validation_alias=AliasChoices("REWARD_LATENCY_MS_WINDOW", "reward_latency_ms_window"),
        alias="REWARD_LATENCY_MS_WINDOW",
    )

    # RL policy selection for model routing
    rl_policy_model_selection: str = Field(
        default="epsilon_greedy",
        validation_alias=AliasChoices("RL_POLICY_MODEL_SELECTION", "rl_policy_model_selection"),
        alias="RL_POLICY_MODEL_SELECTION",
    )

    # OpenRouter recommended headers (see docs)
    openrouter_referer: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_REFERER", "openrouter_referer"),
        alias="OPENROUTER_REFERER",
    )
    openrouter_title: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_TITLE", "openrouter_title"),
        alias="OPENROUTER_TITLE",
    )

    # Tokens / secrets (do not log!)
    archive_api_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ARCHIVE_API_TOKEN", "archive_api_token"),
        alias="ARCHIVE_API_TOKEN",
    )
    discord_bot_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DISCORD_BOT_TOKEN", "discord_bot_token"),
        alias="DISCORD_BOT_TOKEN",
    )


def _materialise_settings() -> Settings | object:  # internal helper
    """Instantiate Settings; if runtime returns FieldInfo objects, build a plain container.

    Some constrained environments (or partial pydantic installs) can cause the BaseSettings
    machinery not to convert field descriptors into concrete values, leaving `FieldInfo` objects
    on the instance. That breaks arithmetic in downstream code (e.g. comparisons, math).
    We defensively detect that condition and emit a lightweight plain object with raw defaults.
    """
    inst = Settings()
    try:  # Detect leakage
        from pydantic.fields import FieldInfo  # type: ignore

        leaked = any(isinstance(getattr(inst, n), FieldInfo) for n in getattr(inst.__class__, "__annotations__", {}))
        if not leaked:
            return inst
        # Build plain container
        attrs: dict[str, object] = {}
        for name in getattr(inst.__class__, "__annotations__", {}):
            raw = getattr(inst, name, None)
            if isinstance(raw, FieldInfo):
                attrs[name] = getattr(raw, "default", None)
            else:
                attrs[name] = raw
        # Minimal namespace object
        container = type("SettingsRuntime", (), {})()
        for k, v in attrs.items():
            setattr(container, k, v)
        return container
    except Exception:  # pragma: no cover - fallback to original instance
        return inst


@lru_cache
def get_settings() -> Settings | object:
    return _materialise_settings()


__all__ = ["Settings", "get_settings"]
