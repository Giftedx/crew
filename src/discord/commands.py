"""Minimal Discord command helpers used in tests.

These functions are intentionally lightweight; they operate directly on
in-memory stores and return plain dictionaries that mimic Discord
responses. A full bot wiring is outside the scope of the tests but the
interfaces make later integration straightforward.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any, TypedDict

from core.learning_engine import LearningEngine
from core.privacy import privacy_filter, retention
from core.router import Router
from debate.panel import PanelConfig, run_panel
from debate.store import Debate, DebateStore
from grounding.schema import AnswerContract
from grounding.verifier import VerifierReport
from ingest import models
from memory import api as memory_api
from memory import embeddings, vector_store
from memory.store import MemoryStore
from obs import incident, slo
from scheduler import PriorityQueue, Scheduler

_DEBATE_STORE = DebateStore()


class CreatorProfile(TypedDict, total=False):
    slug: str
    name: str
    bio: str
    error: str


class EpisodeRecord(TypedDict, total=False):
    id: str
    creator: str
    guests: list[str]
    published_at: str


class ContextHit(TypedDict, total=False):
    text: str
    url: str | None
    start: float | None


class DebateSummary(TypedDict, total=False):
    id: int
    final: str
    status: dict[str, Any]
    error: str


class DebateInspection(TypedDict, total=False):
    id: int
    query: str
    final: str
    error: str


class DebateStats(TypedDict):
    count: int
    avg_rounds: float


class OpsStatus(TypedDict):
    budget_remaining: float
    cache_hits: int
    breaker_open: bool
    alerts: list[str]


class PrivacyEvents(TypedDict):
    events: dict[str, int]
    policy_version: str


class MemoryHit(TypedDict):
    id: int
    text: str
    score: float


class EvalRunResult(TypedDict):
    id: int
    report: dict[str, Any]


class WatchAddResult(TypedDict):
    id: int | None
    handle: str


def creator(profiles: list[CreatorProfile], name: str) -> CreatorProfile:
    for p in profiles:
        if p["slug"] == name:
            return p
    return {"error": "unknown creator"}


def latest(episodes: list[EpisodeRecord], creator_slug: str, limit: int = 5) -> list[EpisodeRecord]:
    items = [e for e in episodes if e["creator"] == creator_slug]
    items.sort(key=lambda e: e.get("published_at") or "", reverse=True)
    return items[:limit]


def collabs(episodes: list[EpisodeRecord], creator_slug: str) -> list[str]:
    guests = []
    for e in episodes:
        if e["creator"] == creator_slug:
            guests.extend(e.get("guests", []))
    return sorted(set(guests))


def verify_profiles(candidates: list[CreatorProfile]) -> list[CreatorProfile]:
    return candidates


def context_query(store: vector_store.VectorStore, namespace: str, query: str) -> list[ContextHit]:
    vec = embeddings.embed([query])[0]
    res = store.query(namespace, vec, top_k=3)
    out: list[ContextHit] = []
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
            # ensure url is a string (TypedDict allows None)
            content_ids=",".join((t.get("url") or "") for t in out),
            policy_version="default",
            decisions="[]",
            redactions="{}",
            output_hash="",
            user_cmd="/context",
            channel_id="",
            ts=datetime.now(UTC).isoformat(),
        )
        models.record_usage(conn, usage)
    return out


def ops_debate_run(query: str, roles: list[str]) -> DebateSummary:
    """Run a simple debate and persist the result."""

    engine = LearningEngine()
    engine.register_domain("debate")
    router = Router(engine)
    cfg = PanelConfig(roles=roles)
    report = run_panel(query, router, lambda m, p: f"{m}:{p}"[:100], cfg, engine=router.engine, reward=1.0)
    debate = Debate(
        id=None,
        tenant="t",
        workspace="w",
        query=query,
        panel_config_json="{}",
        n_rounds=cfg.n_rounds,
        final_output=report.final,
        created_at=datetime.now(UTC).isoformat(),
    )
    debate_id = _DEBATE_STORE.add_debate(debate)
    return {"id": debate_id, "final": report.final, "status": router.engine.status()}


def ops_debate_inspect(debate_id: int) -> DebateInspection:
    for row in _DEBATE_STORE.list_debates("t", "w"):
        if row.id == debate_id:
            return {"id": row.id, "query": row.query, "final": row.final_output}
    return {"error": "not found"}


def ops_debate_stats() -> DebateStats:
    """Return basic counts and averages for debates.

    This helper aggregates over persisted debates for a single default
    tenant/workspace pair. It allows ops to sanity check debate usage
    without needing direct database access.

    Returns
    -------
    dict
        ``{"count": int, "avg_rounds": float}``
    """

    rows = _DEBATE_STORE.list_debates("t", "w")
    if not rows:
        return {"count": 0, "avg_rounds": 0.0}
    count = len(rows)
    avg_rounds = sum(r.n_rounds for r in rows) / count
    return {"count": count, "avg_rounds": avg_rounds}


def ops_status(
    budget_remaining: float,
    cache_hits: int,
    breaker_open: bool,
    alerts: list[str] | None = None,
) -> OpsStatus:
    """Return basic operational counters and pending alerts for tests."""

    return {
        "budget_remaining": budget_remaining,
        "cache_hits": cache_hits,
        "breaker_open": breaker_open,
        "alerts": alerts or [],
    }


def ops_privacy_status(events: list[dict[str, Any]], policy_version: str) -> PrivacyEvents:
    """Summarise recent privacy events for ops.

    Parameters
    ----------
    events:
        A list of event dicts with ``type`` and ``count`` keys.
    policy_version:
        The currently active policy version string.
    """

    totals: dict[str, int] = {}
    for ev in events:
        typ = ev.get("type", "unknown")
        totals[typ] = totals.get(typ, 0) + int(ev.get("count", 1))
    return {"events": totals, "policy_version": policy_version}


def ops_privacy_show(report: PrivacyEvents) -> PrivacyEvents:
    return report


def ops_privacy_sweep(conn: Any, *, tenant: str | None = None, now: datetime | None = None) -> dict[str, int]:
    """Run the retention sweeper and return number of deleted rows."""

    deleted = retention.sweep(conn, tenant=tenant, now=now)
    return {"deleted": deleted}


# ------------------------------------------------------------------ memory ops
def ops_memory_find(
    mstore: MemoryStore,
    vstore: vector_store.VectorStore,
    tenant: str,
    workspace: str,
    query: str,
) -> list[MemoryHit]:
    hits = memory_api.retrieve(mstore, vstore, tenant=tenant, workspace=workspace, query=query)
    return [{"id": h.id, "text": h.text, "score": h.score} for h in hits]


def ops_memory_pin(mstore: MemoryStore, item_id: int, pinned: bool = True) -> dict[str, bool]:
    memory_api.pin(mstore, item_id, pinned)
    return {"pinned": pinned}


def ops_memory_prune(mstore: MemoryStore, tenant: str) -> dict[str, int]:
    deleted = memory_api.prune(mstore, tenant=tenant)
    return {"deleted": deleted}


def ops_memory_stats(mstore: MemoryStore, tenant: str, workspace: str) -> dict[str, int]:
    items = mstore.search_keyword(tenant, workspace, "", limit=1000)
    return {
        "total": len(items),
        "pinned": sum(i.pinned for i in items),
        "archived": sum(i.archived for i in items),
    }


def ops_memory_archive(
    mstore: MemoryStore,
    item_id: int,
    tenant: str,
    workspace: str,
) -> dict[str, bool]:
    memory_api.archive(mstore, item_id, tenant=tenant, workspace=workspace)
    return {"archived": True}


def ops_grounding_audit(contract: AnswerContract, report: VerifierReport) -> dict[str, Any]:
    """Return a concise summary of the grounding artefacts."""

    return {
        "answer": contract.answer_text,
        "citations": [asdict(c) for c in contract.citations],
        "verdict": report.verdict,
    }


_EVAL_HISTORY: list[dict[str, Any]] = []


def ops_eval_run(
    model_func: Callable[[str, dict[str, Any]], tuple[str, dict[str, float]]], dataset_dir: str
) -> EvalRunResult:
    """Run the golden evaluation suite using ``model_func``.

    ``model_func`` should follow the signature expected by ``eval.runner.run``.
    The report is stored in an in-memory history for later inspection.
    """

    from eval.runner import run  # noqa: PLC0415 - lazy import avoids heavy deps unless evaluation is invoked

    report = run(dataset_dir, model_func)
    _EVAL_HISTORY.append(report)
    return {"id": len(_EVAL_HISTORY), "report": report}


def ops_eval_latest(n: int = 1) -> list[dict[str, Any]]:
    """Return the last ``n`` evaluation reports."""

    return _EVAL_HISTORY[-n:]


def ops_eval_diff(a: int, b: int) -> dict[str, float]:
    """Return quality deltas between runs ``a`` and ``b`` (1-indexed)."""

    ra = _EVAL_HISTORY[a - 1]
    rb = _EVAL_HISTORY[b - 1]
    diff: dict[str, float] = {}
    for task in ra:
        diff[task] = rb.get(task, {}).get("quality", 0.0) - ra.get(task, {}).get("quality", 0.0)
    return diff


__all__ = [
    "creator",
    "latest",
    "collabs",
    "verify_profiles",
    "context_query",
    "ops_status",
    "ops_privacy_status",
    "ops_privacy_show",
    "ops_privacy_sweep",
    "ops_grounding_audit",
    "ops_eval_run",
    "ops_eval_latest",
    "ops_eval_diff",
    "ops_ingest_watch_add",
    "ops_ingest_watch_list",
    "ops_ingest_queue_status",
    "ops_ingest_run_once",
    "ops_incident_open",
    "ops_incident_ack",
    "ops_incident_resolve",
    "ops_incident_list",
    "ops_slo_status",
]


# ----------------------------------------------------------------- ingest ops
def ops_ingest_watch_add(  # noqa: PLR0913 - explicit params map 1:1 to watch schema; dict packing would hurt type safety & clarity
    sched: Scheduler,
    source_type: str,
    handle: str,
    tenant: str,
    workspace: str,
    label: str | None = None,
) -> WatchAddResult:
    """Register a new watchlist entry."""

    watch = sched.add_watch(
        tenant=tenant,
        workspace=workspace,
        source_type=source_type,
        handle=handle,
        label=label,
    )
    return {"id": watch.id, "handle": watch.handle}


def ops_ingest_watch_list(sched: Scheduler, tenant: str | None = None) -> list[dict[str, Any]]:
    """Return all watchlists for ``tenant``."""

    return [w.__dict__ for w in sched.list_watches(tenant)]


def ops_ingest_queue_status(queue: PriorityQueue) -> dict[str, int]:
    """Return basic queue metrics."""

    return {"pending": queue.pending_count()}


def ops_ingest_run_once(sched: Scheduler, store: vector_store.VectorStore) -> dict[str, bool]:
    """Process a single queued ingest job."""

    job = sched.worker_run_once(store)
    return {"ran": bool(job)}


# ------------------------------------------------------------ observability ops
def ops_incident_open(title: str, severity: str = "minor") -> dict[str, int]:
    """Open a new incident."""

    inc_id = incident.manager.open(title, severity)
    return {"id": inc_id}


def ops_incident_ack(incident_id: int, user: str) -> dict[str, str]:
    """Acknowledge an incident."""

    incident.manager.ack(incident_id, user)
    return {"status": "ack"}


def ops_incident_resolve(incident_id: int) -> dict[str, str]:
    """Resolve an incident."""

    incident.manager.resolve(incident_id)
    return {"status": "resolved"}


def ops_incident_list() -> list[dict[str, Any]]:
    """Return all incidents."""

    return [i.__dict__ for i in incident.manager.list()]


def ops_slo_status(values: dict[str, Any], slos: list[slo.SLO]) -> dict[str, Any]:
    """Evaluate metrics against SLOs."""

    evaluator = slo.SLOEvaluator(slos)
    return evaluator.evaluate(values)
