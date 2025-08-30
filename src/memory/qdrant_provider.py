"""Centralised Qdrant client factory.

Having a single construction point lets us:
* Enable / disable gRPC preferentially from config.
* Re‑use an underlying HTTP connection pool.
* Add future lifecycle hooks (shutdown, telemetry) in one place.

Typing notes:
The project declares a runtime dependency on :mod:`qdrant_client`, but we still
guard the import so that a minimal subset of functionality (e.g. certain unit
tests that patch this provider) can run in environments where the package is
absent. During type checking we always import the real class so the exported
return type is stable and we avoid ``Any`` leakage.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - mypy / pyright only
    from qdrant_client import QdrantClient
else:  # runtime fallback if dependency unavailable (tests may monkeypatch)
    try:  # pragma: no cover - defensive
        from qdrant_client import QdrantClient  # type: ignore
    except Exception:  # pragma: no cover
        QdrantClient = None  # type: ignore

from core.settings import get_settings


class _DummyPoint:
    def __init__(self, id: int | str, vector: Sequence[float], payload: dict[str, Any]):
        self.id = id
        self.vector = list(vector)
        self.payload = payload
        # mimic qdrant point search result attribute
        self.score = 1.0


class _DummyQueryResult:
    def __init__(self, points: list[_DummyPoint]):
        self.points = points


class _DummyCollections:
    def __init__(self):
        self.collections: list[Any] = []


class _DummyClient:
    """Extremely small in-memory stand in used for tests.

    Only implements methods exercised by our unit tests / thin wrappers:
    * get_collections()
    * create_collection(name, vectors_config=...)
    * get_collection(name)
    * recreate_collection(name, vectors_config=...)
    * upsert(collection_name, points)
    * query_points(collection_name, query, limit, with_payload=True)
    """

    def __init__(self):
        self._store: dict[str, list[_DummyPoint]] = {}
        self._collections: set[str] = set()

    # vector_store usage
    def get_collections(self):  # pragma: no cover - trivial
        cols = _DummyCollections()
        cols.collections = [type("C", (), {"name": n})() for n in self._collections]
        return cols

    def create_collection(self, name: str, vectors_config: Any):  # pragma: no cover - trivial
        self._collections.add(name)

    # memory_storage_tool / vector_search_tool usage
    def get_collection(self, name: str):  # pragma: no cover - trivial
        if name not in self._collections:
            raise Exception("missing collection")
        return {}

    def recreate_collection(self, name: str, *, vectors_config: Any):  # pragma: no cover
        self._collections.add(name)
        self._store.setdefault(name, [])

    def upsert(self, *, collection_name: str, points: Sequence[Any]):  # pragma: no cover
        self._collections.add(collection_name)
        bucket = self._store.setdefault(collection_name, [])
        for p in points:
            # normalise into dummy point object; tests only inspect payload count
            payload = getattr(p, "payload", {}) or {}
            pid = getattr(p, "id", len(bucket))
            vec = getattr(p, "vector", [])
            bucket.append(_DummyPoint(pid, vec, dict(payload)))

    def query_points(
        self,
        *,
        collection_name: str,
        query: Sequence[float],
        limit: int,
        with_payload: bool,
    ):  # pragma: no cover
        bucket = self._store.get(collection_name, [])
        # naive: just return first N points; score constant
        return _DummyQueryResult(bucket[:limit])


@lru_cache
def get_qdrant_client() -> QdrantClient | _DummyClient:
    """Return a cached :class:`QdrantClient` instance configured from settings.

    Raises
    ------
    RuntimeError
        If the optional dependency *qdrant-client* is not installed at runtime.
    """
    settings = get_settings()
    if QdrantClient is None:  # pragma: no cover - safety net
        raise RuntimeError("qdrant-client not installed")

    # Build explicit kwargs so static type checkers can match the signature
    prefer_grpc: bool = bool(getattr(settings, "qdrant_prefer_grpc", False))
    grpc_port_val = getattr(settings, "qdrant_grpc_port", None)
    grpc_port: int | None = int(grpc_port_val) if grpc_port_val else None

    # Some downstream environments may have older qdrant-client versions lacking kwargs; keep explicit
    kwargs: dict[str, object] = {
        "url": settings.qdrant_url,
        "api_key": settings.qdrant_api_key,
        "prefer_grpc": prefer_grpc,
    }
    if grpc_port is not None:
        kwargs["grpc_port"] = grpc_port
    # Provide an in-memory dummy fallback for tests requesting ':memory:' or empty URL.
    raw_url = str(kwargs.get("url") or "").strip()
    if not raw_url or raw_url == ":memory:" or raw_url.startswith("memory://"):
        return _DummyClient()
    client = QdrantClient(**kwargs)  # type: ignore[arg-type]
    return client


__all__ = ["get_qdrant_client"]
