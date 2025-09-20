"""Hybrid retrieval tool: combine vector search with offline TF-IDF and optional reranker.

Inputs:
- query: str
- index: str = "memory"
- candidate_docs: list[str] | None = None  (optional offline TF-IDF candidates)
- top_k: int = 5
- alpha: float = 0.7 (weight for vector score; (1-alpha) for TF-IDF)
- enable_rerank: bool | None = None (override global flag)

Outputs (StepResult.ok):
{ data: { hits: [{text, score, source}], count: int, method: "hybrid", reranked: bool } }

Notes:
- Offline-safe default (reranker disabled unless flag/provider configured).
- Tenancy respected for vector portion via mem_ns.
"""

from __future__ import annotations

from typing import Any

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


def _flag_enabled(name: str, default: bool = False) -> bool:
    try:
        from core.secure_config import get_config  # type: ignore

        v = get_config(name)
        if v is not None:
            return str(v).lower() in ("1", "true", "yes", "on")
    except Exception:
        ...
    try:
        import os

        raw = os.getenv(name)
        if raw is not None:
            return str(raw).lower() in ("1", "true", "yes", "on")
    except Exception:
        ...
    return bool(default)


class RagHybridTool(BaseTool[StepResult]):
    name: str = "RAG Hybrid Tool"
    description: str = "Merge vector hits with offline TF-IDF and optionally rerank the union."

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def _vector_hits(self, namespace: str, query_text: str, top_k: int) -> list[dict[str, Any]]:
        try:
            from memory import embeddings
            from memory.vector_store import VectorStore

            store = VectorStore()
            vec = embeddings.embed([query_text])[0]
            pts = store.query(namespace, vec, top_k=top_k)
            out: list[dict[str, Any]] = []
            for p in getattr(pts, "points", pts) or []:
                payload = getattr(p, "payload", {}) or {}
                text = payload.get("text") if isinstance(payload, dict) else None
                score = getattr(p, "score", None)
                if isinstance(text, str):
                    out.append(
                        {
                            "text": text,
                            "score": float(score) if isinstance(score, (int, float)) else 0.0,
                            "source": "vector",
                        }
                    )
            return out
        except Exception:
            return []

    def _tfidf_hits(self, query_text: str, documents: list[str], top_k: int) -> list[dict[str, Any]]:
        try:
            from .offline_rag_tool import _rank

            ranked = _rank(query_text or "", documents, top_k)
            return [{"text": h.snippet, "score": h.score, "source": "offline"} for h in ranked]
        except Exception:
            return []

    def _merge(
        self, vec_hits: list[dict[str, Any]], tfidf_hits: list[dict[str, Any]], alpha: float, top_k: int
    ) -> list[dict[str, Any]]:
        # Merge by text key; accumulate scores per source
        alpha = max(0.0, min(1.0, float(alpha)))
        by_text: dict[str, dict[str, Any]] = {}
        for h in vec_hits:
            t = h.get("text")
            if not isinstance(t, str):
                continue
            entry = by_text.setdefault(t, {"text": t, "v": 0.0, "o": 0.0, "source": set()})
            entry["v"] = max(entry["v"], float(h.get("score", 0.0)))
            entry["source"].add("vector")
        for h in tfidf_hits:
            t = h.get("text")
            if not isinstance(t, str):
                continue
            entry = by_text.setdefault(t, {"text": t, "v": 0.0, "o": 0.0, "source": set()})
            entry["o"] = max(entry["o"], float(h.get("score", 0.0)))
            entry["source"].add("offline")
        combined: list[dict[str, Any]] = []
        for v in by_text.values():
            score = alpha * v["v"] + (1.0 - alpha) * v["o"]
            src = v["source"]
            combined.append(
                {
                    "text": v["text"],
                    "score": round(float(score), 6),
                    "source": ("both" if len(src) > 1 else next(iter(src))),
                }
            )
        combined.sort(key=lambda d: d.get("score", 0.0), reverse=True)
        return combined[: max(1, top_k)]

    def _maybe_rerank(
        self, query_text: str, hits: list[dict[str, Any]], enable_rerank: bool | None
    ) -> tuple[list[dict[str, Any]], bool]:
        # Global/flag check
        allow_global = _flag_enabled("ENABLE_RERANKER", False)
        allowed = enable_rerank if isinstance(enable_rerank, bool) else allow_global
        if not allowed or not hits:
            return hits, False
        # Determine provider
        try:
            from core.secure_config import get_config  # type: ignore

            cfg = get_config()
            provider = (getattr(cfg, "rerank_provider", None) or "").strip()
            if not provider:
                return hits, False
        except Exception:
            return hits, False
        # Call reranker provider
        try:
            from analysis.rerank import rerank

            texts = [h.get("text", "") for h in hits]
            rr = rerank(query_text, texts, provider=provider, top_n=min(len(texts), len(texts)))
            # reorder hits by rr.indexes, keeping top_n length
            ordered = [hits[i] for i in rr.indexes if 0 <= i < len(hits)]
            return (ordered if ordered else hits), bool(ordered)
        except Exception:
            return hits, False

    def run(
        self,
        *,
        query: str,
        index: str = "memory",
        candidate_docs: list[str] | None = None,
        top_k: int = 5,
        alpha: float = 0.7,
        enable_rerank: bool | None = None,
    ) -> StepResult:
        # Resolve tenant-aware namespace
        try:
            from ultimate_discord_intelligence_bot.tenancy.context import current_tenant, mem_ns

            ctx = current_tenant()
            namespace = mem_ns(ctx, index) if ctx else index
        except Exception:
            namespace = index

        try:
            top_k = int(top_k)
            if top_k <= 0 or top_k > 25:
                top_k = 5
        except Exception:
            top_k = 5
        try:
            alpha = float(alpha)
        except Exception:
            alpha = 0.7

        vec_hits = self._vector_hits(namespace, query, top_k)
        tfidf_hits = self._tfidf_hits(query, list(candidate_docs or []), top_k) if candidate_docs else []
        merged = self._merge(vec_hits, tfidf_hits, alpha, top_k)
        reranked = False
        merged, reranked = self._maybe_rerank(query, merged, enable_rerank)
        try:
            self._metrics.counter("tool_runs_total", labels={"tool": "rag_hybrid", "outcome": "success"}).inc()
        except Exception:
            pass
        return StepResult.ok(data={"hits": merged, "count": len(merged), "method": "hybrid", "reranked": reranked})


__all__ = ["RagHybridTool"]
