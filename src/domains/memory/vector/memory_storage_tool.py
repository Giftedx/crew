"""Store transcripts and analysis in a Qdrant vector database with tenant isolation."""
from __future__ import annotations
import os
import uuid
from platform.config.configuration import get_config
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, TypedDict, cast, runtime_checkable
from ..tenancy import current_tenant, mem_ns
from ._base import BaseTool
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams
    except Exception:
        QdrantClient = Any
        Distance = Any
        PointStruct = Any
        VectorParams = Any
else:
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams
    except Exception:
        QdrantClient = None

        class PointStruct:

            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        class VectorParams:

            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        class Distance:
            COSINE = 'cosine'
try:
    from domains.memory.vector.qdrant import get_qdrant_client
except Exception:

    def get_qdrant_client():
        return None

@runtime_checkable
class _QdrantLike(Protocol):

    def get_collection(self, name: str) -> Any:
        ...

    def recreate_collection(self, name: str, *, vectors_config: Any) -> Any:
        ...

    def upsert(self, *, collection_name: str, points: Sequence[Any]) -> Any:
        ...

class _MemoryStorageResult(TypedDict, total=False):
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
    name: str = 'Qdrant Memory Storage Tool'
    description: str = 'Stores documents in a tenant-isolated Qdrant vector database for later retrieval.'
    model_config: ClassVar[dict[str, Any]] = {'arbitrary_types_allowed': True, 'extra': 'allow'}
    base_collection: str | None = None
    embedding_fn: Callable[[str], list[float]] | None = None
    client: _QdrantLike | None = None
    _physical_names: ClassVar[dict[str, str]] = {}

    def __init__(self, client: object | None=None, collection: str | None=None, embedding_fn: Callable[[str], list[float]] | None=None) -> None:
        super().__init__()
        config = get_config()
        env_collection = config.get_setting('qdrant_collection')
        base_collection = collection or env_collection or 'content'
        embed = embedding_fn
        if client is not None:
            qclient = cast('_QdrantLike', client)
        else:
            try:
                qclient = cast('_QdrantLike', get_qdrant_client())
            except Exception:
                qclient = cast('_QdrantLike', None)
        object.__setattr__(self, 'base_collection', base_collection)
        object.__setattr__(self, 'embedding_fn', embed)
        object.__setattr__(self, 'client', qclient)
        self._metrics = get_metrics()
        if embed is not None:
            self._ensure_collection(base_collection)
        self._enable_ttl = str(os.getenv('ENABLE_MEMORY_TTL', '0')).lower() in {'1', 'true', 'yes', 'on'}
        self._ttl_seconds = int(os.getenv('MEMORY_TTL_SECONDS', '0') or 0)

    @staticmethod
    def _physical_name(name: str) -> str:
        """Map logical namespace to a Qdrant-safe physical collection name.

        Qdrant collections typically disallow ':' in names for HTTP APIs,
        so we mirror VectorStore's convention by replacing ':' with '__'.
        """
        return name.replace(':', '__')

    def _ensure_collection(self, name: str) -> None:
        """Ensure the collection exists by creating it if missing.

        Uses lazy imports to support multiple qdrant-client versions and avoid
        hard failures when the library isn't installed in light test envs.
        """
        if self.client is None:
            raise RuntimeError('Qdrant client not initialised')
        physical = self._physical_name(name)
        try:
            self.client.get_collection(physical)
            return
        except Exception:
            pass
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
            try:
                vp_dict = {'size': 1, 'distance': getattr(Distance, 'COSINE', 'Cosine') if Distance else 'Cosine'}
                self.client.recreate_collection(physical, vectors_config=vp_dict)
                return
            except Exception:
                try:
                    if hasattr(self.client, 'create_collection'):
                        self.client.create_collection(physical, vectors_config=vp_dict)
                except Exception:
                    return
            return
        try:
            distance_val = Distance.COSINE if hasattr(Distance, 'COSINE') else 'Cosine'
            vp_obj = VectorParams(size=1, distance=distance_val)
            self.client.recreate_collection(physical, vectors_config=vp_obj)
        except Exception:
            try:
                if hasattr(self.client, 'create_collection'):
                    self.client.create_collection(physical, vectors_config=vp_obj)
            except Exception:
                return

    def _get_tenant_collection(self) -> str:
        """Get tenant-scoped collection name."""
        tenant_ctx = current_tenant()
        base = self.base_collection or 'content'
        if tenant_ctx:
            return mem_ns(tenant_ctx, base)
        return base

    def _run(self, text: str, metadata: dict[str, object], collection: str | None=None, tenant: str='global', workspace: str='global') -> StepResult:
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
        from platform.core.step_result import ErrorContext
        context = ErrorContext(operation='memory_storage', component='MemoryStorageTool', tenant=tenant, workspace=workspace)
        if self.embedding_fn is None:
            self._metrics.counter('tool_runs_total', labels={'tool': 'memory_storage', 'outcome': 'skipped', 'reason': 'no_embedding_fn'}).inc()
            return StepResult.skip(reason='No embedding function configured - vector storage skipped to prevent semantic search degradation', context=context, text_length=len(text), metadata_keys=list(metadata.keys()))
        if collection is None:
            target = self._get_tenant_collection()
        else:
            tenant_ctx_override = current_tenant()
            target = mem_ns(tenant_ctx_override, collection) if tenant_ctx_override else collection
        try:
            self._ensure_collection(target)
            vector = self.embedding_fn(text)
            if not isinstance(vector, list) or not vector:
                return StepResult.validation_error('embedding function returned invalid vector (must be non-empty list)', context=context, collection=target)
            if not all((isinstance(v, (float, int)) for v in vector)):
                return StepResult.validation_error('embedding vector must contain only numeric values', context=context, collection=target)
            if len(vector) == 1:
                self._metrics.counter('tool_runs_total', labels={'tool': 'memory_storage', 'outcome': 'skipped', 'reason': 'invalid_embedding_dimension'}).inc()
                return StepResult.skip(reason='Single-dimension embedding vector rejected (breaks semantic search). Use proper embedding model with 384+ dimensions.', context=context, vector_dimension=len(vector), collection=target)
            enhanced_metadata = dict(metadata)
            tenant_ctx = current_tenant()
            if tenant_ctx:
                enhanced_metadata.update({'tenant_id': tenant_ctx.tenant_id, 'workspace_id': tenant_ctx.workspace_id})
            payload: dict[str, object] = dict(enhanced_metadata)
            if self._enable_ttl and self._ttl_seconds > 0:
                payload['_ttl'] = int(self._ttl_seconds)
            if 'created_at' not in payload:
                try:
                    import time as _t
                    payload['created_at'] = int(_t.time())
                except Exception:
                    ...
            payload['text'] = text
            if 'PointStruct' in globals() and callable(PointStruct):
                point = cast('Any', PointStruct)(id=str(uuid.uuid4()), vector=vector, payload=payload)
            else:
                point = {'id': str(uuid.uuid4()), 'vector': vector, 'payload': payload}
            if self.client is None:
                raise RuntimeError('Qdrant client not initialised')
            points: Sequence[Any] = [point]
            physical = self._physical_name(target)
            self.client.upsert(collection_name=physical, points=points)
            self._metrics.counter('tool_runs_total', labels={'tool': 'memory_storage', 'outcome': 'success', 'tenant_scoped': str(tenant_ctx is not None).lower()}).inc()
            return StepResult.ok(collection=target, tenant_scoped=tenant_ctx is not None, vector_dimension=len(vector))
        except Exception as exc:
            self._metrics.counter('tool_runs_total', labels={'tool': 'memory_storage', 'outcome': 'error', 'tenant_scoped': str(current_tenant() is not None).lower()}).inc()
            return StepResult.storage_error(error=f'Storage failed: {exc!s}', context=context, collection=target, tenant_scoped=current_tenant() is not None)

    def run(self, *args: Any, **kwargs: Any) -> StepResult:
        text = str(args[0]) if args else str(kwargs.get('text', ''))
        if len(args) >= 2 and isinstance(args[1], dict):
            metadata: Any = args[1]
        else:
            metadata = kwargs.get('metadata', {})
        if not isinstance(metadata, dict):
            try:
                metadata = dict(metadata)
            except Exception:
                metadata = {}
        collection = kwargs.get('collection')
        return self._run(text, metadata, collection=collection)