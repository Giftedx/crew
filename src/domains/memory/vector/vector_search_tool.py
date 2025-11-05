"""Search Qdrant memory for relevant documents."""

from __future__ import annotations

from platform.cache.tool_cache_decorator import cache_tool_result
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, TypedDict, cast, runtime_checkable

from domains.memory.vector.qdrant import get_qdrant_client
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant, mem_ns

from .._base import BaseTool


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
try:
    from qdrant_client.models import Distance, VectorParams

    _HAS_QDRANT_MODELS = True
except Exception:
    _HAS_QDRANT_MODELS = False


@runtime_checkable
class _QdrantLike(Protocol):
    def get_collection(self, name: str) -> Any: ...

    def recreate_collection(self, name: str, *, vectors_config: Any) -> Any: ...

    def query_points(self, *, collection_name: str, query: Sequence[float], limit: int, with_payload: bool) -> Any: ...


class _VectorSearchHit(TypedDict, total=False):
    text: str
    score: float
    payload: dict[str, object]


class _VectorSearchResult(TypedDict, total=False):
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
    model_config: ClassVar[dict[str, Any]] = {"extra": "allow"}

    def __init__(
        self,
        client: object | None = None,
        collection: str | None = None,
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        super().__init__()
        if collection:
            self.collection = collection
        else:
            try:
                ctx = current_tenant()
                self.collection = mem_ns(ctx, "content") if ctx is not None else "content"
            except Exception:
                self.collection = "content"
        self.embedding_fn = embedding_fn or (lambda text: [float(len(text))])
        self._metrics = get_metrics()
        if client is not None:
            self.client = cast("_QdrantLike", client)
        else:
            self.client = cast("_QdrantLike", get_qdrant_client())
        self._ensure_collection(self.collection)

    @staticmethod
    def _physical_name(name: str) -> str:
        return name.replace(":", "__")

    def _ensure_collection(self, name: str) -> None:
        physical = self._physical_name(name)
        try:
            self.client.get_collection(physical)
        except Exception:
            recreate = getattr(self.client, "recreate_collection", None)
            if callable(recreate) and _HAS_QDRANT_MODELS:
                recreate(physical, vectors_config=VectorParams(size=1, distance=Distance.COSINE))
            else:
                create = getattr(self.client, "create_collection", None)
                if callable(create):
                    try:
                        if _HAS_QDRANT_MODELS:
                            create(physical, vectors_config=VectorParams(size=1, distance=Distance.COSINE))
                        else:
                            create(physical)
                    except TypeError:
                        if _HAS_QDRANT_MODELS:
                            create(
                                collection_name=physical, vectors_config=VectorParams(size=1, distance=Distance.COSINE)
                            )
                        else:
                            create(collection_name=physical)
                else:
                    raise RuntimeError("Qdrant client does not support collection creation APIs") from None

    @cache_tool_result(namespace="tool:vector_search", ttl=3600)
    def _run(self, query: str, limit: int = 3, collection: str | None = None) -> StepResult:
        target = collection or self.collection
        physical = self._physical_name(target)
        vector = self.embedding_fn(query)
        try:
            res = self.client.query_points(collection_name=physical, query=vector, limit=limit, with_payload=True)
            hits: list[dict[str, object]] = []
            for hit in getattr(res, "points", []) or []:
                payload = getattr(hit, "payload", {}) or {}
                if not isinstance(payload, dict):
                    continue
                text_val = payload.get("text")
                score_val = getattr(hit, "score", None)
                record: dict[str, object] = {}
                if isinstance(text_val, str):
                    record["text"] = text_val
                if isinstance(score_val, int | float):
                    record["score"] = float(score_val)
                hits.append(record)
            self._metrics.counter("tool_runs_total", labels={"tool": "vector_search", "outcome": "success"}).inc()
            return StepResult.ok(hits=hits, results=hits)
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "vector_search", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))

    def run(self, *args: Any, **kwargs: Any) -> StepResult:
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
