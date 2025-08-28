"""Central application settings using Pydantic.

All environment driven knobs should live here so that other modules avoid
scattered ``os.environ.get`` calls.  This makes configuration discoverable,
testable, and documents defaults in one place.

Convention: Boolean flags default to *disabled* unless the legacy behaviour
prior to centralisation assumed enabled (e.g. HTTP metrics).  New features
should ship behind an ``ENABLE_*`` style flag for opt‑in safety.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
try:
    from pydantic import ConfigDict  # v2
except Exception:  # pragma: no cover
    ConfigDict = dict  # type: ignore
try:  # Pydantic v2: BaseSettings moved to pydantic-settings
    from pydantic_settings import BaseSettings  # type: ignore
except Exception:  # pragma: no cover - fallback if package missing (tests will surface)
    from pydantic import BaseSettings  # type: ignore


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=False)  # type: ignore[arg-type]
    # Service metadata
    service_name: str = Field("ultimate-discord-intel", env="SERVICE_NAME")

    # API / server enablement
    enable_api: bool = Field(False, env="ENABLE_API")

    # Metrics / Prometheus
    enable_prometheus_endpoint: bool = Field(False, env="ENABLE_PROMETHEUS_ENDPOINT")
    prometheus_endpoint_path: str = Field("/metrics", env="PROMETHEUS_ENDPOINT_PATH")
    enable_http_metrics: bool = Field(True, env="ENABLE_HTTP_METRICS")

    # Tracing / OpenTelemetry
    enable_tracing: bool = Field(False, env="ENABLE_TRACING")
    otel_endpoint: Optional[str] = Field(None, env="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_headers: Optional[str] = Field(None, env="OTEL_EXPORTER_OTLP_HEADERS")
    otel_traces_sampler: Optional[str] = Field(None, env="OTEL_TRACES_SAMPLER")
    otel_traces_sampler_arg: Optional[str] = Field(None, env="OTEL_TRACES_SAMPLER_ARG")

    # Qdrant / vector store
    qdrant_url: str = Field(":memory:", env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(None, env="QDRANT_API_KEY")
    qdrant_prefer_grpc: bool = Field(False, env="QDRANT_PREFER_GRPC")
    qdrant_grpc_port: Optional[int] = Field(None, env="QDRANT_GRPC_PORT")
    vector_batch_size: int = Field(128, env="VECTOR_BATCH_SIZE")

    # Behaviour / feature flags
    enable_rate_limiting: bool = Field(False, env="ENABLE_RATE_LIMITING")
    rate_limit_rps: int = Field(10, env="RATE_LIMIT_RPS")
    rate_limit_burst: int = Field(20, env="RATE_LIMIT_BURST")
    enable_http_retry: bool = Field(False, env="ENABLE_HTTP_RETRY")  # Mirrors previous flag

    # Tokens / secrets (do not log!)
    archive_api_token: Optional[str] = Field(None, env="ARCHIVE_API_TOKEN")
    discord_bot_token: Optional[str] = Field(None, env="DISCORD_BOT_TOKEN")



@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance.

    Pydantic already performs validation so repeated construction is cheap but
    centralising through an LRU ensures a single object for lifecycle hooks.
    """

    return Settings()


__all__ = ["Settings", "get_settings"]
