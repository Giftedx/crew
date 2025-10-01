"""Search Qdrant memory for relevant documents."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Protocol, TypedDict, cast, runtime_checkable

from memory.qdrant_provider import get_qdrant_client
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant, mem_ns

from ..obs.metrics import get_metrics
from ..step_result import StepResult
from ._base import BaseTool

try:  # pragma: no cover - optional dependency
    from qdrant_client.models import Distance, VectorParams

    _HAS_QDRANT_MODELS = True
except Exception:  # pragma: no cover - used for testing without qdrant
    _HAS_QDRANT_MODELS = False


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


class VectorSearchTool(BaseTool[StepResult]):
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
        # Default to tenant-scoped collection when available; fall back to global "content"
        if collection:
            self.collection = collection
        else:
            try:
                ctx = current_tenant()
                self.collection = mem_ns(ctx, "content") if ctx is not None else "content"
            except Exception:
                # Defensive: never fail construction due to tenancy issues
                self.collection = "content"
        self.embedding_fn = embedding_fn or (lambda text: [float(len(text))])
        self._metrics = get_metrics()
        if client is not None:
            self.client = cast(_QdrantLike, client)
        else:
            # Centralized provider returns a real QdrantClient or an in-memory dummy
            self.client = cast(_QdrantLike, get_qdrant_client())
        self._ensure_collection(self.collection)

    @staticmethod
    def _physical_name(name: str) -> str:
        # Mirror VectorStore and MemoryStorageTool: replace ':' with '__' for Qdrant
        return name.replace(":", "__")

    def _ensure_collection(self, name: str) -> None:  # pragma: no cover - setup
        physical = self._physical_name(name)
        try:
            self.client.get_collection(physical)
        except Exception:  # pragma: no cover - creation branch
            # Prefer recreate_collection if available, else fall back to create_collection
            recreate = getattr(self.client, "recreate_collection", None)
            if callable(recreate) and _HAS_QDRANT_MODELS:
                recreate(
                    physical,
                    vectors_config=VectorParams(size=1, distance=Distance.COSINE),
                )
            else:
                create = getattr(self.client, "create_collection", None)
                if callable(create):
                    # When models are unavailable (dummy client), size/distance are irrelevant
                    try:
                        if _HAS_QDRANT_MODELS:
                            create(physical, vectors_config=VectorParams(size=1, distance=Distance.COSINE))
                        else:
                            create(physical)
                    except TypeError:
                        # Some client versions use keyword 'collection_name'
                        if _HAS_QDRANT_MODELS:
                            create(
                                collection_name=physical, vectors_config=VectorParams(size=1, distance=Distance.COSINE)
                            )
                        else:
                            create(collection_name=physical)
                else:  # pragma: no cover - unexpected client surface
                    raise RuntimeError("Qdrant client does not support collection creation APIs")

    def _run(self, query: str, limit: int = 3, collection: str | None = None) -> StepResult:
        # Prefer explicit collection, else tenant-scoped default computed at init time
        target = collection or self.collection
        physical = self._physical_name(target)
        vector = self.embedding_fn(query)
        try:
            res = self.client.query_points(
                collection_name=physical,
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
        # Accept alias 'question' used by QA agents
        query = str(args[0]) if args else str(kwargs.get("query", kwargs.get("question", "")))
        try:
            limit = int(kwargs.get("limit", 3))
        except Exception:
            limit = 3
        collection = kwargs.get("collection")
        if not query or not query.strip():
            self._metrics.counter("tool_runs_total", labels={"tool": "vector_search", "outcome": "skipped"}).inc()
            return StepResult.skip(reason="empty query", data={"hits": [], "results": []})
        return self._run(query, limit=limit, collection=collection)


__all__ = ["VectorSearchTool"]
