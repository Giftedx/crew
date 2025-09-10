"""Search Qdrant memory for relevant documents."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Protocol, TypedDict, cast, runtime_checkable

from core.secure_config import get_config
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

try:  # pragma: no cover - optional dependency
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    _QDRANT_OK = True
except Exception:  # pragma: no cover - used for testing without qdrant
    _QDRANT_OK = False


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


class VectorSearchTool(BaseTool):
    """Retrieve stored text snippets from a Qdrant collection.

    Returns a StepResult with ``hits`` list on success. Errors surface via
    ``success=False`` and ``error`` message for uniform handling upstream.
    """

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
        self._metrics = get_metrics()
        if client is not None:
            self.client = cast(_QdrantLike, client)
        else:
            if not _QDRANT_OK:  # pragma: no cover - real client missing
                raise RuntimeError("qdrant-client package is not installed")
            config = get_config()
            url = config.qdrant_url
            api_key = config.qdrant_api_key
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

    def _run(self, query: str, limit: int = 3, collection: str | None = None) -> StepResult:
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
            self._metrics.counter("tool_runs_total", labels={"tool": "vector_search", "outcome": "success"}).inc()
            # For legacy tests expecting the tool result itself to equal a list of dicts we
            # expose a canonical 'results' key in addition to 'hits'. StepResult.__eq__ treats a
            # list comparison specially when the payload contains only a 'results' key, so keep
            # both keys (hits for explicit access, results for direct equality to list).
            return StepResult.ok(hits=hits, results=hits)
        except Exception as exc:  # pragma: no cover - network / client errors
            self._metrics.counter("tool_runs_total", labels={"tool": "vector_search", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))

    def run(self, *args: Any, **kwargs: Any) -> StepResult:  # pragma: no cover
        query = str(args[0]) if args else str(kwargs.get("query", ""))
        limit = int(kwargs.get("limit", 3))
        collection = kwargs.get("collection")
        return self._run(query, limit=limit, collection=collection)


__all__ = ["VectorSearchTool"]
