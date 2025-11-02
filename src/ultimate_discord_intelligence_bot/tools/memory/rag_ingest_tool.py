"""RAG ingestion tool: chunk text and upsert into tenant-scoped VectorStore.

Offline-safe: operates on provided text only (no network). For URL ingestion,
add a separate flagged path later using core.http_utils.

Contract:
- run(texts: list[str], index: str = "memory", chunk_size: int = 400, overlap: int = 50)
  -> StepResult with data: { inserted: int, chunks: int, index: str, tenant_scoped: bool }
"""
from __future__ import annotations
import contextlib
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ._base import BaseTool

def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = (text or '').strip()
    if not text:
        return []
    chunk_size = max(50, int(chunk_size))
    overlap = max(0, min(int(overlap), max(0, chunk_size - 1)))
    out: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        out.append(text[start:end])
        if end >= n:
            break
        start = end - overlap
    return out

class RagIngestTool(BaseTool[StepResult]):
    name: str = 'RAG Ingest Tool'
    description: str = 'Chunk and upsert text into a tenant-scoped VectorStore for retrieval.'

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def run(self, *, texts: list[str], index: str='memory', chunk_size: int=400, overlap: int=50) -> StepResult:
        if not isinstance(texts, list) or any((not isinstance(t, str) for t in texts)):
            return StepResult.fail('Invalid params: texts must be a list of strings')
        inserted = 0
        chunks_total = 0
        tenant_scoped = False
        try:
            try:
                from ultimate_discord_intelligence_bot.tenancy.context import current_tenant, mem_ns
                ctx = current_tenant()
                namespace = mem_ns(ctx, index) if ctx else index
                tenant_scoped = ctx is not None
            except Exception:
                namespace = index
                tenant_scoped = False
            from memory import embeddings
            from memory.vector_store import VectorRecord, VectorStore
            vstore = VectorStore()
            to_upsert: list[VectorRecord] = []
            for t in texts:
                chunks = _chunk_text(t, chunk_size, overlap)
                chunks_total += len(chunks)
                if not chunks:
                    continue
                vecs = embeddings.embed(chunks)
                for chunk, vec in zip(chunks, vecs, strict=False):
                    to_upsert.append(VectorRecord(vector=vec, payload={'text': chunk}))
            if to_upsert:
                vstore.upsert(namespace, to_upsert)
                inserted = len(to_upsert)
            with contextlib.suppress(Exception):
                self._metrics.counter('tool_runs_total', labels={'tool': 'rag_ingest', 'outcome': 'success', 'tenant_scoped': str(tenant_scoped).lower()}).inc()
            return StepResult.ok(data={'inserted': inserted, 'chunks': chunks_total, 'index': namespace, 'tenant_scoped': tenant_scoped})
        except Exception as exc:
            with contextlib.suppress(Exception):
                self._metrics.counter('tool_runs_total', labels={'tool': 'rag_ingest', 'outcome': 'error', 'tenant_scoped': str(tenant_scoped).lower()}).inc()
            return StepResult.fail(str(exc), data={'inserted': inserted, 'chunks': chunks_total, 'index': index, 'tenant_scoped': tenant_scoped})
__all__ = ['RagIngestTool']