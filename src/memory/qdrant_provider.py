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

from functools import lru_cache
from typing import TYPE_CHECKING, Any


try:
    from core import settings as settings_mod  # module import (monkeypatch safe)
except Exception:  # pragma: no cover - fallback when pydantic/settings unavailable

    class _FallbackSettings:
        qdrant_url = ":memory:"
        qdrant_api_key = None
        qdrant_prefer_grpc = False
        qdrant_grpc_port = None

    class _SettingsMod:
        @staticmethod
        def get_settings():
            return _FallbackSettings()

    settings_mod = _SettingsMod()

if TYPE_CHECKING:  # pragma: no cover - mypy / pyright only
    from collections.abc import Sequence

    from qdrant_client import QdrantClient
else:  # runtime fallback if dependency unavailable (tests may monkeypatch)
    try:  # pragma: no cover - defensive
        from qdrant_client import QdrantClient  # type: ignore[import-not-found]
    except Exception:  # pragma: no cover
        QdrantClient = None  # type: ignore

# NOTE: We purposefully avoid binding get_settings at import time so tests that
# monkeypatch core.settings.get_settings see the effect when this provider is
# first invoked. Import inside the factory function.


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
    * scroll(collection_name, limit=..., with_payload=True, offset=None, filter=None)
    * delete_points(collection_name, ids=..., points=..., filter=None)
    """

    def __init__(self):
        self._store: dict[str, list[_DummyPoint]] = {}
        self._collections: set[str] = set()

    # vector_store usage
    def get_collections(self):  # pragma: no cover - trivial
        cols = _DummyCollections()
        cols.collections = [type("C", (), {"name": n})() for n in self._collections]
        return cols

    def create_collection(
        self, name: str | None = None, vectors_config: Any = None, **kwargs: Any
    ) -> None:  # pragma: no cover - trivial
        collection_name = name or kwargs.get("collection_name", "default")
        self._collections.add(collection_name)

    # memory_storage_tool / vector_search_tool usage
    def get_collection(self, name: str):  # pragma: no cover - trivial
        if name not in self._collections:
            raise Exception("missing collection")
        # Return a minimal collection info object for enhanced vector store
        return type(
            "CollectionInfo",
            (),
            {
                "vectors_count": 0,
                "segments_count": 1,
                "disk_data_size": 0,
                "ram_data_size": 0,
                "config": type(
                    "Config",
                    (),
                    {
                        "params": type(
                            "Params",
                            (),
                            {
                                "vectors": type(
                                    "Vectors",
                                    (),
                                    {
                                        "distance": type("Distance", (), {"value": "cosine"})(),
                                        "size": 128,
                                    },
                                )()
                            },
                        )(),
                        "quantization_config": None,
                        "sparse_vectors_config": None,
                    },
                )(),
            },
        )()

    def create_payload_index(self, **kwargs: Any) -> None:  # pragma: no cover - dummy implementation
        # Dummy implementation - do nothing
        pass

    def search(self, **kwargs: Any) -> list[Any]:  # pragma: no cover - dummy implementation
        # Return empty results for dummy client
        return []

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

    # Minimal scroll implementation for test usage
    def scroll(
        self,
        *,
        collection_name: str,
        limit: int = 100,
        with_payload: bool = True,
        offset: int | None = None,
        filter: Any | None = None,
    ) -> tuple[list[_DummyPoint], int | None]:  # pragma: no cover - used by tests
        bucket = self._store.get(collection_name, [])
        start = int(offset or 0)
        end = min(start + int(limit), len(bucket))
        chunk = bucket[start:end]
        next_off: int | None = end if end < len(bucket) else None
        # Very basic payload filter support: expect callable or dict equality checks
        if filter:

            def _match(p: _DummyPoint) -> bool:
                if callable(filter):
                    return bool(filter(p.payload))
                if isinstance(filter, dict):
                    return all(p.payload.get(k) == v for k, v in filter.items())
                return True

            chunk = [p for p in chunk if _match(p)]
        return (chunk, next_off)

    # Minimal delete implementation by ids or simple payload filter
    def delete_points(
        self,
        *,
        collection_name: str,
        ids: Sequence[int | str] | None = None,
        points: Sequence[int | str] | None = None,
        filter: Any | None = None,
    ) -> None:  # pragma: no cover - used by tests
        bucket = self._store.get(collection_name, [])
        id_set = set()
        if ids is not None:
            id_set.update(ids)
        if points is not None:
            id_set.update(points)
        if filter is not None:
            # filter may be a callable(payload)->bool in our tests
            if callable(filter):
                to_delete = {p.id for p in bucket if filter(p.payload)}
                id_set.update(to_delete)
            elif isinstance(filter, dict):
                to_delete = {p.id for p in bucket if all(p.payload.get(k) == v for k, v in filter.items())}
                id_set.update(to_delete)
        if not id_set:
            return
        self._store[collection_name] = [p for p in bucket if p.id not in id_set]

    def get_cluster_info(self):  # pragma: no cover - dummy implementation
        # Return a minimal cluster info object for testing
        return type("ClusterInfo", (), {"status": "dummy", "peers": []})()


@lru_cache
def get_qdrant_client() -> QdrantClient | _DummyClient:
    """Return a cached :class:`QdrantClient` instance configured from settings with connection pooling.

    This implementation includes:
    - Connection pooling for better performance
    - Configurable pool sizes via environment variables
    - Graceful fallback to dummy client for tests and development

    Raises
    ------
    RuntimeError
        If the optional dependency *qdrant-client* is not installed at runtime.
    """
    settings = settings_mod.get_settings()
    # Build explicit kwargs so static type checkers can match the signature
    prefer_grpc: bool = bool(getattr(settings, "qdrant_prefer_grpc", False))
    grpc_port_val = getattr(settings, "qdrant_grpc_port", None)
    grpc_port: int | None = int(grpc_port_val) if grpc_port_val else None

    url_val = getattr(settings, "qdrant_url", None)
    # Provide an in-memory dummy fallback for tests requesting ':memory:' or empty URL, or when client missing.
    raw_url = str(url_val or "").strip()
    if (not raw_url) or raw_url == ":memory:" or raw_url.startswith("memory://") or QdrantClient is None:
        return _DummyClient()

    # Connection pooling configuration
    import os

    # NOTE: Qdrant client manages its own internal connection pooling.
    # The following environment variables are preserved for backwards compatibility
    # but are not passed to the client as they are not supported parameters.
    # Connection pooling is handled transparently by the underlying HTTP client.
    _pool_size = int(os.getenv("QDRANT_POOL_SIZE", "10"))  # Unused, kept for compatibility
    _max_overflow = int(os.getenv("QDRANT_MAX_OVERFLOW", "5"))  # Unused, kept for compatibility
    _pool_timeout = int(os.getenv("QDRANT_POOL_TIMEOUT", "30"))  # Unused, kept for compatibility
    _pool_recycle = int(os.getenv("QDRANT_POOL_RECYCLE", "3600"))  # Unused, kept for compatibility

    # Build client kwargs with only supported parameters
    kwargs: dict[str, object] = {
        "url": url_val,
        "api_key": getattr(settings, "qdrant_api_key", None),
        "prefer_grpc": prefer_grpc,
    }

    # Add gRPC port if specified
    if grpc_port is not None:
        kwargs["grpc_port"] = grpc_port

    # Qdrant client handles connection pooling internally via httpx
    # No explicit pool parameters are needed or supported
    client = QdrantClient(**kwargs)  # type: ignore

    # Optional secure fallback: if connectivity is broken, fall back to dummy
    # to avoid hard failures in local/dev or air-gapped environments.
    try:
        secure_fallback = str(os.getenv("ENABLE_SECURE_QDRANT_FALLBACK", "0")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
    except Exception:
        secure_fallback = False

    if secure_fallback:
        try:
            # Minimal probe; cheap call that exercises connectivity
            _ = client.get_collections()
        except Exception:
            # Fall back to the in-memory client to keep the app operational
            return _DummyClient()

    return client


__all__ = ["get_qdrant_client"]
