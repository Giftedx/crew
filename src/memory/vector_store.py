from __future__ import annotations

"""Minimal Qdrant wrapper with namespace support."""

from dataclasses import dataclass
from typing import Iterable, List, Sequence

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
except Exception:  # pragma: no cover - optional dependency
    QdrantClient = None  # type: ignore
    qmodels = None  # type: ignore


@dataclass
class VectorRecord:
    vector: List[float]
    payload: dict


class VectorStore:
    """Lightweight wrapper around :class:`qdrant_client.QdrantClient`.

    The store defaults to an in-memory Qdrant instance which is perfectly
    adequate for unit tests.
    """

    def __init__(self, url: str | None = None, api_key: str | None = None):
        if QdrantClient is None:  # pragma: no cover
            raise RuntimeError("qdrant-client is required for VectorStore")
        self.client = QdrantClient(url or ":memory:", api_key=api_key)

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

    def upsert(self, namespace: str, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        self._ensure_collection(namespace, len(records[0].vector))
        points = [
            qmodels.PointStruct(id=i, vector=r.vector, payload=r.payload)
            for i, r in enumerate(records)
        ]
        self.client.upsert(collection_name=namespace, points=points)

    def query(self, namespace: str, vector: Sequence[float], top_k: int = 3):
        return self.client.search(
            collection_name=namespace, query_vector=list(vector), limit=top_k
        )
