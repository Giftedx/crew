"""Search Qdrant memory for relevant documents."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from typing import Any, Protocol, TypedDict, cast, runtime_checkable

from ._base import BaseTool

try:  # pragma: no cover - optional dependency
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
except Exception:  # pragma: no cover - used for testing without qdrant
    QdrantClient = None  # type: ignore


@runtime_checkable
class _QdrantLike(Protocol):  # narrow protocol for methods we use
    def get_collection(self, name: str) -> Any: ...
    def recreate_collection(self, name: str, *, vectors_config: Any) -> Any: ...
    def query_points(self, *, collection_name: str, query: Sequence[float], limit: int, with_payload: bool) -> Any: ...


class _VectorSearchHit(TypedDict, total=False):
    text: str
    score: float
    # Represent original payload verbatim (may include extra keys)
    payload: dict[str, object]


class _VectorSearchResult(TypedDict, total=False):  # retained for backwards compatibility
    status: str
    hits: list[_VectorSearchHit]
    error: str


class VectorSearchTool(BaseTool[list[dict[str, object]]]):
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
            self.client = cast(_QdrantLike, client)
        else:
            if QdrantClient is None:  # pragma: no cover - real client missing
                raise RuntimeError("qdrant-client package is not installed")
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            api_key = os.getenv("QDRANT_API_KEY")
            self.client = cast(_QdrantLike, QdrantClient(url=url, api_key=api_key))
        self._ensure_collection(self.collection)

    def _ensure_collection(self, name: str) -> None:  # pragma: no cover - setup
        try:
            self.client.get_collection(name)
        except Exception:  # pragma: no cover - creation branch
            self.client.recreate_collection(
                name,
                vectors_config=VectorParams(size=1, distance=Distance.COSINE),
            )

    def _run(
        self, query: str, limit: int = 3, collection: str | None = None
    ) -> list[dict[str, object]]:
        target = collection or self.collection
        vector = self.embedding_fn(query)
        try:
            res = self.client.query_points(
                collection_name=target,
                query=vector,
                limit=limit,
                with_payload=True,
            )
            hits: list[dict[str, object]] = []
            for hit in getattr(res, "points", []) or []:  # defensive for stubbed clients
                payload = getattr(hit, "payload", {}) or {}
                if not isinstance(payload, dict):  # pragma: no cover - guard
                    continue
                # Normalise expected keys
                text_val = payload.get("text")
                score_val = getattr(hit, "score", None)
                record: dict[str, object] = {}
                if isinstance(text_val, str):
                    record["text"] = text_val
                if isinstance(score_val, int | float):
                    record["score"] = float(score_val)
                hits.append(record)
            return hits
        except Exception as exc:  # pragma: no cover - network / client errors
            return [{"error": str(exc)}]

    def run(self, *args: Any, **kwargs: Any) -> list[dict[str, object]]:  # pragma: no cover
        query = str(args[0]) if args else str(kwargs.get("query", ""))
        limit = int(kwargs.get("limit", 3))
        collection = kwargs.get("collection")
        return self._run(query, limit=limit, collection=collection)

__all__ = ["VectorSearchTool"]
