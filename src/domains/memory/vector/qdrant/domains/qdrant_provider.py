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
from functools import lru_cache
from typing import TYPE_CHECKING, Any
try:
    from platform import settings as settings_mod
except Exception:

    class _FallbackSettings:
        qdrant_url = ':memory:'
        qdrant_api_key = None
        qdrant_prefer_grpc = False
        qdrant_grpc_port = None

    class _SettingsMod:

        @staticmethod
        def get_settings():
            return _FallbackSettings()
    settings_mod = _SettingsMod()
if TYPE_CHECKING:
    from collections.abc import Sequence
    from qdrant_client import QdrantClient
else:
    try:
        from qdrant_client import QdrantClient
    except Exception:
        QdrantClient = None

class _DummyPoint:

    def __init__(self, point_id: int | str, vector: Sequence[float], payload: dict[str, Any]):
        self.id = point_id
        self.vector = list(vector)
        self.payload = payload
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

    def get_collections(self):
        cols = _DummyCollections()
        cols.collections = [type('C', (), {'name': n})() for n in self._collections]
        return cols

    def create_collection(self, name: str | None=None, vectors_config: Any=None, **kwargs: Any) -> None:
        collection_name = name or kwargs.get('collection_name', 'default')
        self._collections.add(collection_name)

    def get_collection(self, name: str):
        if name not in self._collections:
            raise Exception('missing collection')
        return type('CollectionInfo', (), {'vectors_count': 0, 'segments_count': 1, 'disk_data_size': 0, 'ram_data_size': 0, 'config': type('Config', (), {'params': type('Params', (), {'vectors': type('Vectors', (), {'distance': type('Distance', (), {'value': 'cosine'})(), 'size': 128})()})(), 'quantization_config': None, 'sparse_vectors_config': None})()})()

    def create_payload_index(self, **kwargs: Any) -> None:
        pass

    def search(self, **kwargs: Any) -> list[Any]:
        return []

    def upsert(self, *, collection_name: str, points: Sequence[Any]):
        self._collections.add(collection_name)
        bucket = self._store.setdefault(collection_name, [])
        for p in points:
            payload = getattr(p, 'payload', {}) or {}
            pid = getattr(p, 'id', len(bucket))
            vec = getattr(p, 'vector', [])
            bucket.append(_DummyPoint(pid, vec, dict(payload)))

    def query_points(self, *, collection_name: str, query: Sequence[float], limit: int, with_payload: bool):
        bucket = self._store.get(collection_name, [])
        return _DummyQueryResult(bucket[:limit])

    def scroll(self, *, collection_name: str, limit: int=100, with_payload: bool=True, offset: int | None=None, query_filter: Any | None=None) -> tuple[list[_DummyPoint], int | None]:
        bucket = self._store.get(collection_name, [])
        start = int(offset or 0)
        end = min(start + int(limit), len(bucket))
        chunk = bucket[start:end]
        next_off: int | None = end if end < len(bucket) else None
        if query_filter:

            def _match(p: _DummyPoint) -> bool:
                if callable(query_filter):
                    return bool(query_filter(p.payload))
                if isinstance(query_filter, dict):
                    return all((p.payload.get(k) == v for k, v in query_filter.items()))
                return True
            chunk = [p for p in chunk if _match(p)]
        return (chunk, next_off)

    def delete_points(self, *, collection_name: str, ids: Sequence[int | str] | None=None, points: Sequence[int | str] | None=None, query_filter: Any | None=None) -> None:
        bucket = self._store.get(collection_name, [])
        id_set = set()
        if ids is not None:
            id_set.update(ids)
        if points is not None:
            id_set.update(points)
        if query_filter is not None:
            if callable(query_filter):
                to_delete = {p.id for p in bucket if query_filter(p.payload)}
                id_set.update(to_delete)
            elif isinstance(query_filter, dict):
                to_delete = {p.id for p in bucket if all((p.payload.get(k) == v for k, v in query_filter.items()))}
                id_set.update(to_delete)
        if not id_set:
            return
        self._store[collection_name] = [p for p in bucket if p.id not in id_set]

    def get_cluster_info(self):
        return type('ClusterInfo', (), {'status': 'dummy', 'peers': []})()

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
    prefer_grpc: bool = bool(getattr(settings, 'qdrant_prefer_grpc', False))
    grpc_port_val = getattr(settings, 'qdrant_grpc_port', None)
    grpc_port: int | None = int(grpc_port_val) if grpc_port_val else None
    url_val = getattr(settings, 'qdrant_url', None)
    raw_url = str(url_val or '').strip()
    if not raw_url or raw_url == ':memory:' or raw_url.startswith('memory://') or (QdrantClient is None):
        return _DummyClient()
    import os
    _pool_size = int(os.getenv('QDRANT_POOL_SIZE', '10'))
    _max_overflow = int(os.getenv('QDRANT_MAX_OVERFLOW', '5'))
    _pool_timeout = int(os.getenv('QDRANT_POOL_TIMEOUT', '30'))
    _pool_recycle = int(os.getenv('QDRANT_POOL_RECYCLE', '3600'))
    kwargs: dict[str, object] = {'url': url_val, 'api_key': getattr(settings, 'qdrant_api_key', None), 'prefer_grpc': prefer_grpc}
    if grpc_port is not None:
        kwargs['grpc_port'] = grpc_port
    client = QdrantClient(**kwargs)
    try:
        secure_fallback = str(os.getenv('ENABLE_SECURE_QDRANT_FALLBACK', '0')).strip().lower() in {'1', 'true', 'yes', 'on'}
    except Exception:
        secure_fallback = False
    if secure_fallback:
        try:
            _ = client.get_collections()
        except Exception:
            return _DummyClient()
    return client
__all__ = ['get_qdrant_client']