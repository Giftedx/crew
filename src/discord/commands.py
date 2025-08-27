from __future__ import annotations

"""Minimal Discord command helpers used in tests.

These functions are intentionally lightweight; they operate directly on
in-memory stores and return plain dictionaries that mimic Discord
responses.  A full bot wiring is outside the scope of the tests but the
interfaces make later integration straightforward.
"""

from typing import List

from memory import embeddings, vector_store
from core.privacy import privacy_filter
from ingest import models
import os
from datetime import datetime


def creator(profiles: List[dict], name: str) -> dict:
    for p in profiles:
        if p["slug"] == name:
            return p
    return {"error": "unknown creator"}


def latest(episodes: List[dict], creator_slug: str, limit: int = 5) -> List[dict]:
    items = [e for e in episodes if e["creator"] == creator_slug]
    items.sort(key=lambda e: e.get("published_at") or "", reverse=True)
    return items[:limit]


def collabs(episodes: List[dict], creator_slug: str) -> List[str]:
    guests = []
    for e in episodes:
        if e["creator"] == creator_slug:
            guests.extend(e.get("guests", []))
    return sorted(set(guests))


def verify_profiles(candidates: List[dict]) -> List[dict]:
    return candidates


def context_query(store: vector_store.VectorStore, namespace: str, query: str) -> List[dict]:
    vec = embeddings.embed([query])[0]
    res = store.query(namespace, vec, top_k=3)
    out: List[dict] = []
    texts = []
    for hit in res:
        payload = hit.payload or {}
        text = payload.get("text", "")
        clean, _ = privacy_filter.filter_text(text, {})
        url = payload.get("source_url")
        start = payload.get("start")
        out.append({"text": clean, "url": url, "start": start})
        texts.append(clean)
    db_path = os.getenv("INGEST_DB_PATH")
    if db_path and texts:
        conn = models.connect(db_path)
        usage = models.UsageLog(
            id=None,
            call_id="ctx",
            content_ids=",".join(t.get("url", "") for t in out),
            policy_version="default",
            decisions="[]",
            redactions="{}",
            output_hash="",
            user_cmd="/context",
            channel_id="",
            ts=datetime.utcnow().isoformat(),
        )
        models.record_usage(conn, usage)
    return out


def ops_status(budget_remaining: float, cache_hits: int, breaker_open: bool) -> dict:
    """Return basic operational counters for tests."""

    return {
        "budget_remaining": budget_remaining,
        "cache_hits": cache_hits,
        "breaker_open": breaker_open,
    }


def ops_privacy_status(events: list[dict], policy_version: str) -> dict:
    return {"events": events, "policy_version": policy_version}


def ops_privacy_show(report: dict) -> dict:
    return report


__all__ = [
    "creator",
    "latest",
    "collabs",
    "verify_profiles",
    "context_query",
    "ops_status",
    "ops_privacy_status",
    "ops_privacy_show",
]
