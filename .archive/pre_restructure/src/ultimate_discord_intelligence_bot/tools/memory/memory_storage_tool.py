"""Store transcripts and analysis in a Qdrant vector database with tenant isolation."""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, TypedDict, cast, runtime_checkable

from core.secure_config import get_config

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ..tenancy import current_tenant, mem_ns
from ._base import BaseTool


if TYPE_CHECKING:  # pragma: no cover - type checking only
    from collections.abc import Callable, Sequence

    try:
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


# Centralized provider for qdrant client (ensures consistent config & fallbacks)
try:
    from memory.qdrant_provider import get_qdrant_client
except Exception:  # pragma: no cover - fallback to None; tool will error gracefully if used

    def get_qdrant_client():  # type: ignore
        return None


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


class MemoryStorageTool(BaseTool[StepResult]):
    """Persist text and metadata to a tenant-scoped Qdrant vector database.

    Stores documents with embeddings in a tenant-isolated Qdrant collection
    for semantic search and retrieval. Handles vector validation, tenant isolation,
    and optional TTL (time-to-live) for automatic cleanup.

    Args:
        text: Text content to store (str)
        metadata: Additional metadata dictionary
        collection: Optional collection name override
        tenant: Tenant identifier for data isolation
        workspace: Workspace identifier for organization

    Returns:
        StepResult with storage results including:
        - collection: Target collection name
        - tenant_scoped: Whether tenant isolation is active
        - vector_dimension: Embedding vector dimension
        - stored_id: Unique identifier for stored document

    Raises:
        StepResult.fail: If storage fails or invalid embedding
        StepResult.skip: If no embedding function configured

    Example:
        >>> tool = MemoryStorageTool(embedding_fn=my_embedding_fn)
        >>> result = tool._run("content", {"source": "web"})
        >>> assert result.success
        >>> print(f"Stored in collection: {result.data['collection']}")
    """

    name: str = "Qdrant Memory Storage Tool"
    description: str = "Stores documents in a tenant-isolated Qdrant vector database for later retrieval."

    # Provide loose config so pydantic doesn't require field population pre-init
    model_config: ClassVar[dict[str, Any]] = {"arbitrary_types_allowed": True, "extra": "allow"}
    # Annotations for readability; set at runtime (avoid pydantic required errors)
    base_collection: str | None = None
    embedding_fn: Callable[[str], list[float]] | None = None
    client: _QdrantLike | None = None
    # maintain a simple logical->physical mapping to keep return values logical
    _physical_names: ClassVar[dict[str, str]] = {}

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

        # CRITICAL FIX: Do NOT use single-dimension fallback embedding
        # Single-dimension vectors like [float(len(text))] break semantic search
        # If no proper embedding function is provided, we'll skip vector storage
        # and return StepResult.skip() to maintain pipeline flow
        embed = embedding_fn  # No fallback - require proper embedding or skip

        if client is not None:
            qclient = cast("_QdrantLike", client)
        else:
            # Use centralized provider to avoid scattered construction differences
            try:
                qclient = cast("_QdrantLike", get_qdrant_client())
            except Exception:
                qclient = cast("_QdrantLike", None)
        # Assign via object.__setattr__ to avoid pydantic required-field validation
        object.__setattr__(self, "base_collection", base_collection)
        object.__setattr__(self, "embedding_fn", embed)
        object.__setattr__(self, "client", qclient)
        self._metrics = get_metrics()

        # Only ensure collection if we have a valid embedding function
        if embed is not None:
            self._ensure_collection(base_collection)

        # feature flags
        self._enable_ttl = str(os.getenv("ENABLE_MEMORY_TTL", "0")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self._ttl_seconds = int(os.getenv("MEMORY_TTL_SECONDS", "0") or 0)

    @staticmethod
    def _physical_name(name: str) -> str:
        """Map logical namespace to a Qdrant-safe physical collection name.

        Qdrant collections typically disallow ':' in names for HTTP APIs,
        so we mirror VectorStore's convention by replacing ':' with '__'.
        """
        return name.replace(":", "__")

    def _ensure_collection(self, name: str) -> None:  # pragma: no cover - setup
        """Ensure the collection exists by creating it if missing.

        Uses lazy imports to support multiple qdrant-client versions and avoid
        hard failures when the library isn't installed in light test envs.
        """
        if self.client is None:
            raise RuntimeError("Qdrant client not initialised")
        physical = self._physical_name(name)
        try:
            self.client.get_collection(physical)
            return
        except Exception:
            pass

        # Lazy-import model types (modern path first, then legacy)
        Distance = None
        VectorParams = None
        try:
            from qdrant_client.http.models import Distance as _Distance
            from qdrant_client.http.models import VectorParams as _VectorParams

            Distance = _Distance
            VectorParams = _VectorParams
        except Exception:
            try:
                from qdrant_client.models import Distance as _Distance
                from qdrant_client.models import VectorParams as _VectorParams

                Distance = _Distance
                VectorParams = _VectorParams
            except Exception:
                Distance = None
                VectorParams = None

        if Distance is None or VectorParams is None:
            # Attempt best-effort create using loose dict when models aren't importable in tests.
            try:
                vp_dict = {
                    "size": 1,
                    "distance": getattr(Distance, "COSINE", "Cosine") if Distance else "Cosine",
                }
                self.client.recreate_collection(physical, vectors_config=vp_dict)
                return
            except Exception:
                try:
                    # Only try create_collection if method exists
                    if hasattr(self.client, "create_collection"):
                        self.client.create_collection(physical, vectors_config=vp_dict)
                except Exception:
                    return
            return

        try:
            # Use proper Distance enum value with safe fallback
            distance_val = Distance.COSINE if hasattr(Distance, "COSINE") else "Cosine"
            vp_obj = VectorParams(size=1, distance=distance_val)  # type: ignore[arg-type]
            # Use positional for name to be compatible across client versions
            self.client.recreate_collection(physical, vectors_config=vp_obj)
        except Exception:
            try:
                # Only try create_collection if method exists
                if hasattr(self.client, "create_collection"):
                    self.client.create_collection(physical, vectors_config=vp_obj)
            except Exception:
                return

    def _get_tenant_collection(self) -> str:
        """Get tenant-scoped collection name."""
        tenant_ctx = current_tenant()
        base = self.base_collection or "content"
        if tenant_ctx:
            return mem_ns(tenant_ctx, base)
        return base

    def _run(
        self,
        text: str,
        metadata: dict[str, object],
        collection: str | None = None,
        tenant: str = "global",
        workspace: str = "global",
    ) -> StepResult:
        """Store text and metadata in tenant-scoped Qdrant collection.

        Args:
            text: Text content to store
            metadata: Additional metadata dictionary
            collection: Optional collection name override
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier

        Returns:
            StepResult with storage results or error information
        """
        from ultimate_discord_intelligence_bot.step_result import ErrorContext

        context = ErrorContext(
            operation="memory_storage",
            component="MemoryStorageTool",
            tenant=tenant,
            workspace=workspace,
        )

        # Check if we have a proper embedding function
        if self.embedding_fn is None:
            # Skip vector storage if no proper embedding available
            # This prevents breaking semantic search with invalid single-dimension vectors
            self._metrics.counter(
                "tool_runs_total",
                labels={
                    "tool": "memory_storage",
                    "outcome": "skipped",
                    "reason": "no_embedding_fn",
                },
            ).inc()
            return StepResult.skip(
                reason="No embedding function configured - vector storage skipped to prevent semantic search degradation",
                context=context,
                text_length=len(text),
                metadata_keys=list(metadata.keys()),
            )

        # Use tenant-scoped collection if available
        if collection is None:
            target = self._get_tenant_collection()
        else:
            tenant_ctx_override = current_tenant()
            target = mem_ns(tenant_ctx_override, collection) if tenant_ctx_override else collection

        try:
            self._ensure_collection(target)
            vector = self.embedding_fn(text)

            # Validate embedding vector quality
            if not isinstance(vector, list) or not vector:
                return StepResult.validation_error(
                    "embedding function returned invalid vector (must be non-empty list)",
                    context=context,
                    collection=target,
                )

            if not all(isinstance(v, (float, int)) for v in vector):
                return StepResult.validation_error(
                    "embedding vector must contain only numeric values",
                    context=context,
                    collection=target,
                )

            # CRITICAL: Reject single-dimension vectors that break semantic search
            if len(vector) == 1:
                self._metrics.counter(
                    "tool_runs_total",
                    labels={
                        "tool": "memory_storage",
                        "outcome": "skipped",
                        "reason": "invalid_embedding_dimension",
                    },
                ).inc()
                return StepResult.skip(
                    reason="Single-dimension embedding vector rejected (breaks semantic search). Use proper embedding model with 384+ dimensions.",
                    context=context,
                    vector_dimension=len(vector),
                    collection=target,
                )

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
            # optional TTL metadata
            if self._enable_ttl and self._ttl_seconds > 0:
                payload["_ttl"] = int(self._ttl_seconds)
            # record a creation timestamp if caller didn't provide one; used by compaction
            if "created_at" not in payload:
                try:
                    import time as _t  # local import to avoid global dependency at module import

                    payload["created_at"] = int(_t.time())
                except Exception:
                    ...
            payload["text"] = text
            if "PointStruct" in globals() and callable(PointStruct):
                point = cast("Any", PointStruct)(
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
            physical = self._physical_name(target)
            self.client.upsert(collection_name=physical, points=points)
            self._metrics.counter(
                "tool_runs_total",
                labels={
                    "tool": "memory_storage",
                    "outcome": "success",
                    "tenant_scoped": str(tenant_ctx is not None).lower(),
                },
            ).inc()
            return StepResult.ok(
                collection=target,
                tenant_scoped=tenant_ctx is not None,
                vector_dimension=len(vector),
            )
        except Exception as exc:  # pragma: no cover - network/errors
            self._metrics.counter(
                "tool_runs_total",
                labels={
                    "tool": "memory_storage",
                    "outcome": "error",
                    "tenant_scoped": str(current_tenant() is not None).lower(),
                },
            ).inc()
            return StepResult.storage_error(
                error=f"Storage failed: {exc!s}",
                context=context,
                collection=target,
                tenant_scoped=current_tenant() is not None,
            )

    def run(self, *args: Any, **kwargs: Any) -> StepResult:  # pragma: no cover - public shim
        text = str(args[0]) if args else str(kwargs.get("text", ""))
        if len(args) >= 2 and isinstance(args[1], dict):
            metadata: Any = args[1]
        else:
            metadata = kwargs.get("metadata", {})
        if not isinstance(metadata, dict):
            try:
                metadata = dict(metadata)
            except Exception:
                metadata = {}
        collection = kwargs.get("collection")
        return self._run(text, metadata, collection=collection)
