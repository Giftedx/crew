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

from pydantic import AliasChoices, Field

try:  # Pydantic v2 (preferred)
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _HAS_PYDANTIC_V2 = True
except Exception:  # pragma: no cover - fall back to pydantic v1 style
    from pydantic import BaseSettings  # type: ignore
    SettingsConfigDict = dict  # type: ignore[misc,assignment]
    _HAS_PYDANTIC_V2 = False
_DOTENV_AVAILABLE = importlib_util.find_spec("dotenv") is not None

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



@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance.

    Pydantic already performs validation so repeated construction is cheap but
    centralising through an LRU ensures a single object for lifecycle hooks.
    """

    return Settings()


__all__ = ["Settings", "get_settings"]
