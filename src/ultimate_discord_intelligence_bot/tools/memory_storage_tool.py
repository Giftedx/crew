"""Store transcripts and analysis in a Qdrant vector database with tenant isolation."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, Protocol, TypedDict, cast, runtime_checkable

from core.secure_config import get_config
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ..tenancy import current_tenant, mem_ns
from ._base import BaseTool

if TYPE_CHECKING:  # pragma: no cover - type checking only
    try:  # noqa: SIM105
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams
    except Exception:  # pragma: no cover
        QdrantClient = Any  # type: ignore
        Distance = Any  # type: ignore
        PointStruct = Any  # type: ignore
        VectorParams = Any  # type: ignore
else:  # runtime fallback lightweight stubs to avoid dependency requirement in tests
    try:  # pragma: no cover - optional dependency
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams
    except Exception:  # pragma: no cover - provide minimal stand-ins
        QdrantClient = None  # type: ignore

        class PointStruct:  # pragma: no cover - simple container
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        class VectorParams:  # pragma: no cover - simple container
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        class Distance:  # pragma: no cover - constant enum stub
            COSINE = "cosine"


@runtime_checkable
class _QdrantLike(Protocol):
    def get_collection(self, name: str) -> Any: ...
    def recreate_collection(self, name: str, *, vectors_config: Any) -> Any: ...
    def upsert(self, *, collection_name: str, points: Sequence[Any]) -> Any: ...


class _MemoryStorageResult(TypedDict, total=False):  # retained for legacy ref usage
    status: str
    collection: str
    tenant_scoped: bool
    error: str


class MemoryStorageTool(BaseTool):
    """Persist text and metadata to a tenant-scoped Qdrant collection."""

    name: str = "Qdrant Memory Storage Tool"
    description: str = "Stores documents in a tenant-isolated Qdrant vector database for later retrieval."

    # Provide loose config so pydantic doesn't require field population pre-init
    model_config = {"arbitrary_types_allowed": True, "extra": "allow"}
    # Annotations for readability; set at runtime (avoid pydantic required errors)
    base_collection: str | None = None
    embedding_fn: Callable[[str], list[float]] | None = None
    client: _QdrantLike | None = None

    def __init__(
        self,
        client: object | None = None,
        collection: str | None = None,
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        super().__init__()  # initialise pydantic machinery first
        config = get_config()
        env_collection = config.get_setting("qdrant_collection")
        base_collection = collection or env_collection or "content"
        embed = embedding_fn or (lambda text: [float(len(text))])
        if client is not None:
            qclient = cast(_QdrantLike, client)
        else:
            # Attempt to construct a real client; fall back to None on any error/missing dep
            url = config.qdrant_url
            api_key = config.qdrant_api_key
            try:
                QdrantCtor = cast(Callable[..., Any], QdrantClient)
                qclient = cast(_QdrantLike, QdrantCtor(url=url, api_key=api_key))
            except Exception:  # pragma: no cover - fallback to None on instantiation issues
                qclient = cast(_QdrantLike, None)
        # Assign via object.__setattr__ to avoid pydantic required-field validation
        object.__setattr__(self, "base_collection", base_collection)
        object.__setattr__(self, "embedding_fn", embed)
        object.__setattr__(self, "client", qclient)
        self._metrics = get_metrics()
        self._ensure_collection(base_collection)

    def _ensure_collection(self, name: str) -> None:  # pragma: no cover - setup
        try:
            if self.client is None:
                raise RuntimeError("Qdrant client not initialised")
            self.client.get_collection(name)
        except Exception:  # pragma: no cover - creation branch
            if self.client is None:
                raise
            if (
                self.client is None or "VectorParams" not in globals() or "Distance" not in globals()
            ):  # pragma: no cover
                return  # silently skip creation when dependencies absent
            try:
                if "VectorParams" in globals() and "Distance" in globals() and callable(VectorParams):
                    try:
                        vp = VectorParams(size=1, distance=getattr(Distance, "COSINE", "cosine"))  # type: ignore[arg-type]
                        self.client.recreate_collection(name, vectors_config=vp)
                    except Exception:  # pragma: no cover - ignore when stub mismatch
                        return
            except Exception:  # pragma: no cover - ignore creation issues in fallback
                return

    def _get_tenant_collection(self) -> str:
        """Get tenant-scoped collection name."""
        tenant_ctx = current_tenant()
        base = self.base_collection or "content"
        if tenant_ctx:
            return mem_ns(tenant_ctx, base)
        return base

    def _run(self, text: str, metadata: dict[str, object], collection: str | None = None) -> StepResult:
        # Use tenant-scoped collection if available
        if collection is None:
            target = self._get_tenant_collection()
        else:
            tenant_ctx_override = current_tenant()
            target = mem_ns(tenant_ctx_override, collection) if tenant_ctx_override else collection

        try:
            self._ensure_collection(target)
            if self.embedding_fn is None:
                raise RuntimeError("embedding_fn not initialised")
            vector = self.embedding_fn(text)

            # Enhance metadata with tenant context
            enhanced_metadata = dict(metadata)
            tenant_ctx = current_tenant()
            if tenant_ctx:
                enhanced_metadata.update(
                    {
                        "tenant_id": tenant_ctx.tenant_id,
                        "workspace_id": tenant_ctx.workspace_id,
                    }
                )

            payload: dict[str, object] = dict(enhanced_metadata)
            payload["text"] = text
            if "PointStruct" in globals() and callable(PointStruct):
                point = cast(Any, PointStruct)(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=payload,
                )
            else:  # pragma: no cover - fallback plain dict
                point = {
                    "id": str(uuid.uuid4()),
                    "vector": vector,
                    "payload": payload,
                }
            if self.client is None:
                raise RuntimeError("Qdrant client not initialised")
            points: Sequence[Any] = [point]
            self.client.upsert(collection_name=target, points=points)
            self._metrics.counter(
                "tool_runs_total",
                labels={
                    "tool": "memory_storage",
                    "outcome": "success",
                    "tenant_scoped": str(tenant_ctx is not None).lower(),
                },
            ).inc()
            return StepResult.ok(collection=target, tenant_scoped=tenant_ctx is not None)
        except Exception as exc:  # pragma: no cover - network errors
            self._metrics.counter(
                "tool_runs_total",
                labels={
                    "tool": "memory_storage",
                    "outcome": "error",
                    "tenant_scoped": str("tenant_ctx" in locals() and tenant_ctx is not None).lower(),
                },
            ).inc()
            return StepResult.fail(error=str(exc), collection=target if "target" in locals() else None)

    # Explicit run wrapper for pipeline compatibility
    def run(
        self, text: str, metadata: dict[str, object], collection: str | None = None
    ) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(text, metadata, collection=collection)


__all__ = ["MemoryStorageTool"]
