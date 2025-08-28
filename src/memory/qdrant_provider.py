"""Qdrant client provider / singleton.

Centralising creation allows us to enable gRPC, share a single connection
pool, and integrate lifecycle management (future: closing / telemetry).
"""

from __future__ import annotations

from functools import lru_cache

try:  # optional dependency handling
    from qdrant_client import QdrantClient
except Exception:  # pragma: no cover
    QdrantClient = None  # type: ignore

from core.settings import get_settings


@lru_cache()
def get_qdrant_client() -> "QdrantClient":  # type: ignore[override]
    settings = get_settings()
    if QdrantClient is None:  # pragma: no cover
        raise RuntimeError("qdrant-client not installed")

    kwargs = {}
    if settings.qdrant_prefer_grpc:
        kwargs["prefer_grpc"] = True
        if settings.qdrant_grpc_port:
            kwargs["grpc_port"] = settings.qdrant_grpc_port

    return QdrantClient(
        settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        **kwargs,  # type: ignore[arg-type]
    )


__all__ = ["get_qdrant_client"]
