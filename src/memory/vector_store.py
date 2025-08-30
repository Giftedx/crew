"""Minimal Qdrant wrapper with namespace support."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, TypedDict

from core.settings import get_settings
from memory.qdrant_provider import get_qdrant_client

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
except Exception:  # pragma: no cover - optional dependency
    QdrantClient = None  # type: ignore
    qmodels = None  # type: ignore


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
        if QdrantClient is None:  # pragma: no cover
            raise RuntimeError("qdrant-client is required for VectorStore")
        # Prefer central singleton unless explicit override provided
        self.client = get_qdrant_client() if url is None else QdrantClient(url, api_key=api_key)
        settings = get_settings()
        self._batch_size = max(1, getattr(settings, "vector_batch_size", 128))
        # Track per-collection dimension + id counters (monotonic ids)
        self._dims: dict[str, int] = {}
        self._counters: dict[str, int] = {}

    @staticmethod
    def namespace(tenant: str, workspace: str, creator: str) -> str:
        return f"{tenant}:{workspace}:{creator}"

    def _ensure_collection(self, name: str, dim: int) -> None:
        cols = self.client.get_collections().collections
        if not any(c.name == name for c in cols):
            self.client.create_collection(
                name,
                vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
            )
            self._dims[name] = dim
        # Verify existing dimension if we have cached value; if not cache it
        elif name not in self._dims:
            # Attempt to infer dimension by inserting a dummy approach is unsafe; instead rely
            # on first record establishing dimension. So just cache expected dim.
            self._dims[name] = dim
        elif self._dims[name] != dim:
            raise ValueError(
                f"Dimension mismatch for namespace '{name}': expected {self._dims[name]}, got {dim}"
            )

    def upsert(self, namespace: str, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        dim = len(records[0].vector)
        self._ensure_collection(namespace, dim)

        # Monotonic base ID
        base = self._counters.get(namespace, 0)

        # Chunk large batches to reduce memory usage and allow streaming ingest
        for offset in range(0, len(records), self._batch_size):
            chunk = records[offset : offset + self._batch_size]
            points = []
            for i, r in enumerate(chunk):
                # qdrant_client stubs expect a plain dict; our TypedDict is compatible at runtime
                payload_dict = dict(r.payload)
                points.append(
                    qmodels.PointStruct(id=base + offset + i, vector=r.vector, payload=payload_dict)
                )
            self.client.upsert(collection_name=namespace, points=points)
        self._counters[namespace] = base + len(records)

    def query(self, namespace: str, vector: Sequence[float], top_k: int = 3) -> list[Any]:
        """Return top ``top_k`` matches for ``vector`` in ``namespace``.

        Uses ``query_points`` which supersedes the deprecated ``search`` API
        and ensures payloads are returned with each scored point.
        """

        res = self.client.query_points(
            collection_name=namespace,
            query=list(vector),
            limit=top_k,
            with_payload=True,
        )
        return list(res.points)
