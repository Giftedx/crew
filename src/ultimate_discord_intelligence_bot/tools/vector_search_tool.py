"""Search Qdrant memory for relevant documents."""

from __future__ import annotations

import os
from collections.abc import Callable

from crewai.tools import BaseTool

try:  # pragma: no cover - optional dependency
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
except Exception:  # pragma: no cover - used for testing without qdrant
    QdrantClient = None  # type: ignore


class VectorSearchTool(BaseTool):
    """Retrieve stored text snippets from a Qdrant collection."""

    name: str = "Qdrant Vector Search Tool"
    description: str = "Query the vector database for similar documents."
    model_config = {"extra": "allow"}

    def __init__(
        self,
        client: object | None = None,
        collection: str | None = None,
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        super().__init__()
        self.collection = collection or "content"
        self.embedding_fn = embedding_fn or (lambda text: [float(len(text))])
        if client is not None:
            self.client = client
        else:
            if QdrantClient is None:  # pragma: no cover - real client missing
                raise RuntimeError("qdrant-client package is not installed")
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            api_key = os.getenv("QDRANT_API_KEY")
            self.client = QdrantClient(url=url, api_key=api_key)
        self._ensure_collection(self.collection)

    def _ensure_collection(self, name: str) -> None:  # pragma: no cover - setup
        try:
            self.client.get_collection(name)
        except Exception:
            self.client.recreate_collection(
                name,
                vectors_config=VectorParams(size=1, distance=Distance.COSINE),
            )

    def _run(self, query: str, limit: int = 3, collection: str | None = None) -> list[dict]:
        target = collection or self.collection
        vector = self.embedding_fn(query)
        res = self.client.query_points(
            collection_name=target,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        return [getattr(hit, "payload", {}) for hit in res.points]

    def run(
        self, query: str, limit: int = 3, collection: str | None = None
    ):  # pragma: no cover - thin wrapper
        return self._run(query, limit=limit, collection=collection)
