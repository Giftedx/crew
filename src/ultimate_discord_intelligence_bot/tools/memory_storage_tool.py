"""Store transcripts and analysis in a Qdrant vector database with tenant isolation."""

from __future__ import annotations

import os
import uuid
from collections.abc import Callable

from crewai.tools import BaseTool

from ..tenancy import current_tenant, mem_ns

try:  # pragma: no cover - optional dependency
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
except Exception:  # pragma: no cover - used for testing without qdrant
    QdrantClient = None

    class PointStruct:  # type: ignore
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class VectorParams:  # type: ignore
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Distance:  # type: ignore
        COSINE = "cosine"


class MemoryStorageTool(BaseTool):
    """Persist text and metadata to a tenant-scoped Qdrant collection."""

    name: str = "Qdrant Memory Storage Tool"
    description: str = (
        "Stores documents in a tenant-isolated Qdrant vector database for later retrieval."
    )

    # Properly declare fields for pydantic v2
    base_collection: str = "content"
    embedding_fn: Callable[[str], list[float]] | None = None
    client: object | None = None

    def __init__(
        self,
        client: object | None = None,
        collection: str | None = None,
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        super().__init__()
        self.base_collection = collection or os.getenv("QDRANT_COLLECTION", "content")
        self.embedding_fn = embedding_fn or (lambda text: [float(len(text))])
        if client is not None:
            self.client = client
        else:
            if QdrantClient is None:  # pragma: no cover - real client missing
                raise RuntimeError("qdrant-client package is not installed")
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            api_key = os.getenv("QDRANT_API_KEY")
            self.client = QdrantClient(url=url, api_key=api_key)
        # Initialize default collection to maintain backward compatibility with tests
        self._ensure_collection(self.base_collection)

    def _ensure_collection(self, name: str) -> None:  # pragma: no cover - setup
        try:
            self.client.get_collection(name)
        except Exception:
            self.client.recreate_collection(
                name,
                vectors_config=VectorParams(size=1, distance=Distance.COSINE),
            )

    def _get_tenant_collection(self) -> str:
        """Get tenant-scoped collection name."""
        tenant_ctx = current_tenant()
        if tenant_ctx:
            return mem_ns(tenant_ctx, self.base_collection)
        return self.base_collection

    def _run(self, text: str, metadata: dict, collection: str | None = None) -> dict:
        # Use tenant-scoped collection if available
        if collection is None:
            target = self._get_tenant_collection()
        else:
            # Allow override but still apply tenant scoping if in tenant context
            tenant_ctx = current_tenant()
            target = mem_ns(tenant_ctx, collection) if tenant_ctx else collection

        try:
            self._ensure_collection(target)
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
            self.client.upsert(collection_name=target, points=[point])
            return {
                "status": "success",
                "collection": target,
                "tenant_scoped": tenant_ctx is not None,
            }
        except Exception as exc:  # pragma: no cover - network errors
            return {"status": "error", "error": str(exc)}

    # Explicit run wrapper for pipeline compatibility
    def run(
        self, text: str, metadata: dict, collection: str | None = None
    ):  # pragma: no cover - thin wrapper
        return self._run(text, metadata, collection=collection)
