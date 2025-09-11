"""Minimal Qdrant wrapper with namespace support."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypedDict

try:
    from core.settings import get_settings
except Exception:  # pragma: no cover - fallback when pydantic/settings unavailable

    def get_settings() -> Any:
        class _S:
            vector_batch_size = 128

        return _S()


from memory.qdrant_provider import get_qdrant_client

from .qdrant_provider import (
    _DummyClient as _DC,  # lazy import to avoid cycles in typing
)

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from qdrant_client import QdrantClient as _QdrantClient  # noqa: F401
    from qdrant_client.http import models as _qmodels  # noqa: F401
else:
    _QdrantClient = Any  # runtime fallback type
    _qmodels = Any

try:
    from qdrant_client import QdrantClient

    QDRANT_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    QDRANT_AVAILABLE = False

# Constants for vector dimensions and batch sizing
LARGE_EMBEDDING_DIM = 768
MEDIUM_EMBEDDING_DIM = 384
SMALL_BATCH_SIZE = 64
MEDIUM_BATCH_SIZE = 128


@dataclass
class PointStruct:
    id: int
    vector: list[float]
    payload: dict[str, Any]


class VectorPayload(TypedDict, total=False):
    text: str
    id: int  # optional internal monotonic id for memory items
    video_id: str
    title: str
    platform: str
    sentiment: str
    summary: str
    keywords: list[str]
    # Additional optional keys used by ingest payloads / context queries
    source_url: str
    start: float
    end: float
    tags: list[str]
    episode_id: str
    published_at: str


@dataclass
class VectorRecord:
    vector: list[float]
    payload: VectorPayload


class VectorStore:
    """Lightweight wrapper around :class:`qdrant_client.QdrantClient`.

    The store defaults to an in-memory Qdrant instance which is perfectly
    adequate for unit tests.
    """

    def __init__(self, url: str | None = None, api_key: str | None = None):
        # Prefer central singleton unless explicit override provided. When qdrant-client is
        # unavailable the provider returns an in-memory dummy client suitable for tests.
        if url is None:
            self.client = get_qdrant_client()
        elif not QDRANT_AVAILABLE:  # pragma: no cover - fallback to dummy when constructing directly
            self.client = _DC()
        else:
            self.client = QdrantClient(url, api_key=api_key)
        settings = get_settings()
        self._batch_size = max(1, getattr(settings, "vector_batch_size", 128))
        # Track per-collection dimension + id counters (monotonic ids)
        self._dims: dict[str, int] = {}
        self._counters: dict[str, int] = {}
        # Map logical namespace -> physical collection name (sanitized)
        self._physical_names: dict[str, str] = {}

    @staticmethod
    def namespace(tenant: str, workspace: str, creator: str) -> str:
        return f"{tenant}:{workspace}:{creator}"

    def _ensure_collection(self, name: str, dim: int) -> None:
        physical = self._physical_names.get(name)
        if physical is None:
            # Sanitize for backends that disallow ':' but keep logical namespace outwardly.
            physical = name.replace(":", "__")
            self._physical_names[name] = physical
        cols = self.client.get_collections().collections
        if not any(c.name == physical for c in cols):
            if QDRANT_AVAILABLE:
                from qdrant_client.http import models as qmodels

                vec_conf = qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE)
            else:
                vec_conf = None
            # Dummy client ignores vectors_config
            self.client.create_collection(physical, vectors_config=vec_conf)
            self._dims[name] = dim
        elif name not in self._dims:
            self._dims[name] = dim
        elif self._dims[name] != dim:
            raise ValueError(f"Dimension mismatch for namespace '{name}': expected {self._dims[name]}, got {dim}")

    def upsert(self, namespace: str, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        dim = len(records[0].vector)
        self._ensure_collection(namespace, dim)
        physical = self._physical_names.get(namespace, namespace)

        # Monotonic base ID
        base = self._counters.get(namespace, 0)

        # Dynamic batch sizing based on vector dimensions for optimal performance
        # Larger vectors need smaller batches to avoid memory issues
        if dim > LARGE_EMBEDDING_DIM:  # Large embedding models
            effective_batch_size = min(self._batch_size // 2, SMALL_BATCH_SIZE)
        elif dim > MEDIUM_EMBEDDING_DIM:  # Medium embedding models
            effective_batch_size = min(self._batch_size, MEDIUM_BATCH_SIZE)
        else:  # Small embedding models
            effective_batch_size = self._batch_size

        # Chunk large batches to reduce memory usage and allow streaming ingest
        for offset in range(0, len(records), effective_batch_size):
            chunk = records[offset : offset + effective_batch_size]
            points: list[Any] = []

            # Pre-allocate points list for better performance
            if not QDRANT_AVAILABLE:
                points = []
                for i, r in enumerate(chunk):
                    payload_dict = dict(r.payload)
                    pid = base + offset + i
                    point = PointStruct(id=pid, vector=r.vector, payload=payload_dict)
                    points.append(point)
            else:
                # Use more efficient list comprehension for PointStruct creation
                from qdrant_client.http import models as qmodels

                points = [
                    qmodels.PointStruct(id=base + offset + i, vector=r.vector, payload=dict(r.payload))
                    for i, r in enumerate(chunk)
                ]

            self.client.upsert(collection_name=physical, points=points)
        self._counters[namespace] = base + len(records)

    def query(self, namespace: str, vector: Sequence[float], top_k: int = 3) -> list[Any]:
        """Return top ``top_k`` matches for ``vector`` in ``namespace``.

        Uses ``query_points`` which supersedes the deprecated ``search`` API
        and ensures payloads are returned with each scored point.
        """

        physical = self._physical_names.get(namespace, namespace)
        res = self.client.query_points(
            collection_name=physical,
            query=list(vector),
            limit=top_k,
            with_payload=True,
        )
        return list(res.points)
