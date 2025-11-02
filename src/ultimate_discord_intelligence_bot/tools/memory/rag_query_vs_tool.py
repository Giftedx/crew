"""VectorStore-backed RAG tool (tenant-aware) with offline fallback.

This tool queries a tenant-scoped VectorStore (Qdrant via memory.vector_store)
for nearest neighbours to a query embedding. If the vector index is empty or
unavailable, and optional `documents` are provided, it falls back to an
offline TF-IDF cosine ranking over those documents.

Contract:
- run(query: str, index: str = "memory", top_k: int = 3, documents: list[str] | None = None) -> StepResult
  data := { "hits": [{"text": str, "score": float, "payload": dict}], "count": int, "source": "vector"|"offline" }
  When vector search yields no hits and no documents provided, returns an
  'uncertain' StepResult with empty hits to signal best-effort outcome.
"""
from __future__ import annotations
import contextlib
from typing import Any
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ._base import BaseTool

class RagQueryVectorStoreTool(BaseTool[StepResult]):
    name: str = 'VectorStore RAG Tool'
    description: str = 'Query a tenant-aware vector index for relevant snippets; fall back to offline TF-IDF if needed.'

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def _vector_search(self, namespace: str, query_text: str, top_k: int) -> list[dict[str, Any]]:
        from memory import embeddings
        from memory.vector_store import VectorStore
        store = VectorStore()
        vec = embeddings.embed([query_text])[0]
        try:
            points = store.query(namespace, vec, top_k=top_k)
        except Exception:
            return []
        hits: list[dict[str, Any]] = []
        for p in getattr(points, 'points', points) or []:
            payload = getattr(p, 'payload', {}) or {}
            text = payload.get('text') if isinstance(payload, dict) else None
            score = getattr(p, 'score', None)
            rec: dict[str, Any] = {}
            if isinstance(text, str):
                rec['text'] = text
            if isinstance(score, (int, float)):
                rec['score'] = float(score)
            if isinstance(payload, dict) and payload:
                rec['payload'] = payload
            hits.append(rec)
        return hits

    def _offline_rank(self, query_text: str, documents: list[str], top_k: int) -> list[dict[str, Any]]:
        from .offline_rag_tool import _rank
        ranked = _rank(query_text or '', documents, top_k)
        return [{'text': h.snippet, 'score': h.score, 'payload': {'index': h.index}} for h in ranked]

    def run(self, *, query: str, index: str='memory', top_k: int=3, documents: list[str] | None=None) -> StepResult:
        try:
            from ultimate_discord_intelligence_bot.tenancy.context import current_tenant, mem_ns
            ctx = current_tenant()
            namespace = mem_ns(ctx, index) if ctx else index
        except Exception:
            namespace = index
        try:
            top_k = int(top_k)
            if top_k <= 0 or top_k > 25:
                top_k = 3
        except Exception:
            top_k = 3
        hits = self._vector_search(namespace, query, top_k)
        if hits:
            with contextlib.suppress(Exception):
                self._metrics.counter('tool_runs_total', labels={'tool': 'rag_query_vs', 'outcome': 'success'}).inc()
            return StepResult.ok(data={'hits': hits, 'count': len(hits), 'source': 'vector'})
        if isinstance(documents, list) and documents:
            try:
                off_hits = self._offline_rank(query, documents, top_k)
                with contextlib.suppress(Exception):
                    self._metrics.counter('tool_runs_total', labels={'tool': 'rag_query_vs', 'outcome': 'fallback_offline'}).inc()
                return StepResult.ok(data={'hits': off_hits, 'count': len(off_hits), 'source': 'offline'})
            except Exception as exc:
                with contextlib.suppress(Exception):
                    self._metrics.counter('tool_runs_total', labels={'tool': 'rag_query_vs', 'outcome': 'error_offline'}).inc()
                return StepResult.fail(str(exc), data={'hits': [], 'count': 0, 'source': 'offline'})
        with contextlib.suppress(Exception):
            self._metrics.counter('tool_runs_total', labels={'tool': 'rag_query_vs', 'outcome': 'no_results'}).inc()
        return StepResult.uncertain(data={'hits': [], 'count': 0, 'source': 'vector'})
__all__ = ['RagQueryVectorStoreTool']