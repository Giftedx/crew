"""Unified memory facade tying storage, vector search, and retention."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from analysis.rerank import rerank
from archive import archive_file
from core.learning_engine import LearningEngine
from core.privacy import privacy_filter
from core.secure_config import get_config
from memory import embeddings, vector_store
from memory.store import MemoryItem, MemoryStore


@dataclass
class MemoryHit:
    id: int
    score: float
    text: str
    meta: dict


def store(  # noqa: PLR0913,PLR0912 - explicit param groups (identity/payload/classification/policy) improve readability & validation; collapsing into **kwargs or a dict would reduce static typing
    store: MemoryStore,
    vstore: vector_store.VectorStore,
    *,
    tenant: str,
    workspace: str,
    text: str,
    item_type: str = "long",
    policy: str = "default",
) -> int:
    """Store ``text`` and associated metadata in both SQLite and vector store.

    Parameter grouping reflects distinct conceptual domains (identity, payload,
    classification, retention policy). Consolidating into a dict would remove
    static typing benefits and shift validation burden downstream.
    """

    clean, _ = privacy_filter.filter_text(text, {"tenant": tenant})
    vec = embeddings.embed([clean])[0]
    now = datetime.now(UTC).isoformat()
    item = MemoryItem(
        id=None,
        tenant=tenant,
        workspace=workspace,
        type=item_type,
        content_json=json.dumps({"text": clean}),
        embedding_json=json.dumps(vec),
        ts_created=now,
        ts_last_used=now,
        retention_policy=policy,
        decay_score=1.0,
        pinned=0,
        archived=0,
    )
    item_id = store.add_item(item)
    namespace = vector_store.VectorStore.namespace(tenant, workspace, "memory")
    vstore.upsert(namespace, [vector_store.VectorRecord(vector=vec, payload={"id": item_id, "text": clean})])
    return item_id


def retrieve(  # noqa: PLR0913,PLR0912 - explicit search knobs aid experimentation; refactoring into a config object would spread logic to call sites
    store: MemoryStore,
    vstore: vector_store.VectorStore,
    *,
    tenant: str,
    workspace: str,
    query: str,
    k: int = 5,
    strategies: Sequence[str] | None = None,
    engine: LearningEngine | None = None,
) -> list[MemoryHit]:
    strategies = list(strategies or ["vector", "symbolic"])
    if engine:
        order = engine.recommend("retrieval_scoring", {"len": len(query)}, strategies)
        # ensure returned arm appears first
        strategies.sort(key=lambda s: 0 if s == order else 1)

    hits: list[MemoryHit] = []
    if "vector" in strategies:
        vec = embeddings.embed([query])[0]
        namespace = vector_store.VectorStore.namespace(tenant, workspace, "memory")
        res = vstore.query(namespace, vec, top_k=k)
        for r in res:
            payload = r.payload or {}
            hits.append(
                MemoryHit(
                    id=payload.get("id", 0),
                    score=float(r.score),
                    text=payload.get("text", ""),
                    meta=payload,
                )
            )
    if "symbolic" in strategies:
        for item in store.search_keyword(tenant, workspace, query, limit=k):
            payload = json.loads(item.content_json)
            hits.append(MemoryHit(id=item.id or 0, score=0.5, text=payload.get("text", ""), meta=payload))
    # Optional reranker stage
    cfg = get_config()
    if getattr(cfg, "enable_reranker", False) and hits:
        provider = (getattr(cfg, "rerank_provider", None) or "").strip().lower()
        if provider:
            texts = [h.text for h in hits]
            try:
                rr = rerank(query, texts, provider=provider, top_n=min(k, len(texts)))
                # Reorder hits by reranked indexes (limit to top_n)
                ordered = [hits[i] for i in rr.indexes if 0 <= i < len(hits)]
                hits = ordered + [h for h in hits if h not in ordered]
            except Exception:
                # Fall back silently on provider errors
                ...
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:k]


def prune(store: MemoryStore, *, tenant: str) -> int:
    """Prune expired items for ``tenant`` based on retention policies."""

    return store.prune(tenant)


def pin(store: MemoryStore, item_id: int, pinned: bool = True) -> None:
    store.pin_item(item_id, pinned)


def archive(store: MemoryStore, item_id: int, *, tenant: str, workspace: str) -> None:
    item = store.get_item(item_id)
    if not item:
        return
    data = json.loads(item.content_json).get("text", "")
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        archive_file(
            tmp.name,
            {"kind": "memory", "tenant": tenant, "workspace": workspace, "visibility": "private"},
        )
    store.mark_archived(item_id)


__all__ = ["store", "retrieve", "prune", "pin", "archive", "MemoryHit"]
