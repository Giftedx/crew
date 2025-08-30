"""Store transcripts and analysis in a Qdrant vector database with tenant isolation."""

from __future__ import annotations

import os
import uuid
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, Protocol, TypedDict, cast, runtime_checkable

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


class _MemoryStorageResult(TypedDict, total=False):
    status: str
    collection: str
    tenant_scoped: bool
    error: str


class MemoryStorageTool(BaseTool[_MemoryStorageResult]):
    """Persist text and metadata to a tenant-scoped Qdrant collection."""

    name: str = "Qdrant Memory Storage Tool"
    description: str = (
        "Stores documents in a tenant-isolated Qdrant vector database for later retrieval."
    )

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
        env_collection = os.getenv("QDRANT_COLLECTION")
        base_collection = collection or env_collection or "content"
        embed = embedding_fn or (lambda text: [float(len(text))])
        if client is not None:
            qclient = cast(_QdrantLike, client)
        else:
            if QdrantClient is None:  # pragma: no cover - real client missing
                raise RuntimeError("qdrant-client package is not installed")
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            api_key = os.getenv("QDRANT_API_KEY")
            qclient = cast(_QdrantLike, QdrantClient(url=url, api_key=api_key))
        # Assign via object.__setattr__ to avoid pydantic required-field validation
        object.__setattr__(self, "base_collection", base_collection)
        object.__setattr__(self, "embedding_fn", embed)
        object.__setattr__(self, "client", qclient)
        self._ensure_collection(base_collection)

    def _ensure_collection(self, name: str) -> None:  # pragma: no cover - setup
        try:
            if self.client is None:
                raise RuntimeError("Qdrant client not initialised")
            self.client.get_collection(name)
        except Exception:  # pragma: no cover - creation branch
            if self.client is None:
                raise
            self.client.recreate_collection(
                name,
                vectors_config=VectorParams(size=1, distance=Distance.COSINE),
            )

    def _get_tenant_collection(self) -> str:
        """Get tenant-scoped collection name."""
        tenant_ctx = current_tenant()
        base = self.base_collection or "content"
        if tenant_ctx:
            return mem_ns(tenant_ctx, base)
        return base

    def _run(
        self, text: str, metadata: dict[str, object], collection: str | None = None
    ) -> _MemoryStorageResult:
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

            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={**enhanced_metadata, "text": text},
            )
            if self.client is None:
                raise RuntimeError("Qdrant client not initialised")
            self.client.upsert(collection_name=target, points=[point])
            return _MemoryStorageResult(
                status="success",
                collection=target,
                tenant_scoped=tenant_ctx is not None,
            )
        except Exception as exc:  # pragma: no cover - network errors
            return _MemoryStorageResult(status="error", error=str(exc))

    # Explicit run wrapper for pipeline compatibility
    def run(
        self, text: str, metadata: dict[str, object], collection: str | None = None
    ) -> _MemoryStorageResult:  # pragma: no cover - thin wrapper
        return self._run(text, metadata, collection=collection)

__all__ = ["MemoryStorageTool"]
