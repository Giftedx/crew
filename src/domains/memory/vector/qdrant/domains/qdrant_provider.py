"""Centralised Qdrant client factory.

Having a single construction point lets us:
* Enable / disable gRPC preferentially from config.
* Re-use an underlying HTTP connection pool.
* Add future lifecycle hooks (shutdown, telemetry) in one place.

Typing notes:
The project declares a runtime dependency on :mod:`qdrant_client`, but we still
guard the import so that a minimal subset of functionality (e.g. certain unit
tests that patch this provider) can run in environments where the package is
absent. During type checking we always import the real class so the exported
return type is stable and we avoid ``Any`` leakage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domains.memory.vector.client_factory import get_qdrant_client
from domains.memory.vector.client_factory import _DummyClient


if TYPE_CHECKING:
    from qdrant_client import QdrantClient
else:
    try:
        from qdrant_client import QdrantClient
    except Exception:
        QdrantClient = None


__all__ = ["get_qdrant_client", "_DummyClient"]
