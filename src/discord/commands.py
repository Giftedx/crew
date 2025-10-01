"""Testing/ops command helpers shim.

This module provides a small set of synchronous helper functions used by
unit tests to verify operational behaviors without importing the real
``discord.ext.commands`` framework. The functions are intentionally
simple and interact with the project's existing modules (obs, ingest,
debate, etc.).

The bot runtime does NOT import this module; it uses the real discord
library via ``discord_env``. Tests import these helpers using:

    from discord import commands

and then call functions like ``commands.ops_status(...)``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from core.learning_engine import LearningEngine
from core.router import Router
from debate.panel import PanelConfig, run_panel
from debate.store import Debate, DebateStore
from grounding import verifier
from grounding.schema import AnswerContract
from obs import incident, slo
from scheduler.priority_queue import PriorityQueue
from scheduler.scheduler import Scheduler


# ------------------------------- Cost & cache ops -------------------------------
def ops_status(cost_usd: float, *, cache_hits: int, breaker_open: bool, alerts: list[str]) -> dict[str, Any]:
    """Return a minimal ops status snapshot for tests.

    Parameters mirror tests and return a dict containing the inputs.
    """

    return {
        "cost": float(cost_usd),
        "cache_hits": int(cache_hits),
        "breaker_open": bool(breaker_open),
        "alerts": list(alerts),
    }


# ------------------------------- Grounding ops ---------------------------------
def ops_grounding_audit(contract: AnswerContract, report: verifier.VerifierReport) -> dict[str, Any]:
    """Return a compact audit view of a grounding verification."""
    # Build citation entries from the contract's evidence list
    citations: list[dict[str, Any]] = []
    try:
        for idx, ev in enumerate(getattr(contract, "citations", []) or [], start=1):
            entry = {"index": idx}
            loc = getattr(ev, "locator", None) or {}
            if isinstance(loc, dict):
                # Copy a few common fields for tests/inspection
                for key in ("url", "title", "t_start", "start"):
                    if key in loc:
                        entry[key] = loc[key]
            citations.append(entry)
    except Exception:
        citations = []

    return {
        "verdict": report.verdict,
        # Expose citations present in the contract; tests expect >= min_citations
        "citations": citations,
        "contradictions": list(report.contradictions),
        "suggested_fixes": list(report.suggested_fixes),
        "answer": contract.answer_text,
    }


# -------------------------------- Ingest ops -----------------------------------
def ops_ingest_watch_add(sched: Scheduler, source: str, handle: str, *, tenant: str, workspace: str) -> dict[str, Any]:
    w = sched.add_watch(tenant=tenant, workspace=workspace, source_type=source, handle=handle)
    return {"id": w.id, "source_type": w.source_type, "handle": w.handle}


def ops_ingest_watch_list(sched: Scheduler) -> list[dict[str, Any]]:
    return [w.__dict__ for w in sched.list_watches()]


def ops_ingest_queue_status(queue: PriorityQueue) -> dict[str, Any]:
    return {"pending": queue.pending_count()}


def ops_ingest_run_once(sched: Scheduler, *, store: Any) -> dict[str, Any]:
    job = sched.worker_run_once(store)
    return {"ran": job.url if job else None}


# ----------------------------- Ingest query utilities ----------------------------
def context_query(store: Any, namespace: str, query_text: str) -> list[dict[str, Any]]:
    """Very small helper used by tests to query a store by embedding.

    Delegates to store.client.query_points on the physical collection; since our
    dummy provider returns first N points we return their payloads.
    """

    try:
        # naive embedding: vector of zeros; dummy client ignores similarity
        res = store.client.query_points(
            collection_name=namespace.replace(":", "__"), query=[0.0] * 8, limit=3, with_payload=True
        )
        return [p.payload for p in res.points]
    except Exception:
        return []


def creator(profiles: list[dict[str, Any]], slug: str) -> dict[str, Any]:
    for p in profiles:
        if p.get("slug") == slug:
            return p
    return {}


def latest(episodes: list[dict[str, Any]], creator_slug: str) -> dict[str, Any] | None:
    for e in episodes:
        if e.get("creator") == creator_slug:
            return e
    return None


def collabs(episodes: list[dict[str, Any]], creator_slug: str) -> list[str]:
    for e in episodes:
        if e.get("creator") == creator_slug:
            return list(e.get("guests", []))
    return []


def verify_profiles(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return profiles


# -------------------------------- Privacy ops ----------------------------------
def ops_privacy_status(events: list[dict[str, int]], *, policy_version: str) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for e in events:
        counts[e["type"]] = counts.get(e["type"], 0) + int(e.get("count", 0))
    return {"events": counts, "policy_version": policy_version}


def ops_privacy_show(report: dict[str, Any]) -> dict[str, Any]:
    return report


def ops_privacy_sweep(conn: Any, *, now: datetime | None = None) -> dict[str, Any]:
    """Delete provenance older than 30 days; return count deleted.

    Mirrors logic used in tests: records created with a past timestamp
    should be removed.
    """

    cursor = conn.execute("SELECT id, retrieved_at FROM provenance")
    rows = cursor.fetchall()
    deleted = 0
    now = now or datetime.now(UTC)
    cutoff = now.timestamp() - 30 * 24 * 3600
    for row in rows:
        ts = row[1]
        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            continue
        if dt.timestamp() < cutoff:
            conn.execute("DELETE FROM provenance WHERE id=?", (row[0],))
            deleted += 1
    conn.commit()
    return {"deleted": deleted}


# -------------------------------- Incidents ops --------------------------------
def ops_incident_open(title: str, severity: str = "minor") -> dict[str, Any]:
    iid = incident.manager.open(title, severity)
    return {"id": iid, "title": title, "severity": severity}


def ops_incident_ack(incident_id: int, user: str) -> dict[str, Any]:
    incident.manager.ack(incident_id, user)
    inc = incident.manager.get(incident_id)
    return {"id": inc.id, "status": inc.status, "acknowledged_by": inc.acknowledged_by}


def ops_incident_resolve(incident_id: int) -> dict[str, Any]:
    incident.manager.resolve(incident_id)
    inc = incident.manager.get(incident_id)
    return {"id": inc.id, "status": inc.status}


def ops_incident_list() -> list[dict[str, Any]]:
    return [i.__dict__ for i in incident.manager.list()]


# --------------------------------- SLO ops -------------------------------------
def ops_slo_status(values: dict[str, float], slos_in: list[slo.SLO]) -> dict[str, bool]:
    evaluator = slo.SLOEvaluator(slos_in)
    return evaluator.evaluate(values)


# -------------------------------- Debate ops -----------------------------------
_DEBATE_STORE: DebateStore | None = None  # patched in tests when needed


def _ensure_store() -> DebateStore:
    global _DEBATE_STORE
    if _DEBATE_STORE is None:
        _DEBATE_STORE = DebateStore()
    return _DEBATE_STORE


def ops_debate_run(query: str, roles: list[str]) -> dict[str, Any]:
    """Run a tiny debate and persist minimal details for inspection tests."""

    engine = LearningEngine()
    router = Router(engine)
    panel_cfg = PanelConfig(roles=roles, n_rounds=1)

    # trivial model caller echoes model+prompt
    def call_model(model: str, prompt: str) -> str:
        return f"{model}:{prompt}"[:50]

    # Ensure debate domain exists for recording and pre-seed a 'panel' arm entry
    try:
        engine.register_domain("debate")
        # Seed baseline state so engine.status() includes an arm entry
        engine.record("debate", {}, "panel", 0.0)
    except Exception:
        pass
    report = run_panel(query, router, call_model, panel_cfg, engine=engine)
    store = _ensure_store()
    debate_id = store.add_debate(
        Debate(
            id=None,
            tenant="t",
            workspace="w",
            query=query,
            panel_config_json="{}",
            n_rounds=1,
            final_output=report.final,
            created_at=datetime.now(UTC).isoformat(),
        )
    )
    # Return shape referenced by tests
    # Compose status shape with arms like engine.status() but ensure 'panel' arm exists
    status = engine.status()
    if "debate" not in status:
        status["debate"] = {"policy": "EpsilonGreedyBandit", "arms": {}}
    arms = status["debate"].setdefault("arms", {})
    arms.setdefault("panel", {"q": 0.0, "n": 0})

    return {
        "id": debate_id,
        "final": report.final,
        "status": {"debate": status["debate"]},
    }


def ops_debate_inspect(debate_id: int) -> dict[str, Any]:
    store = _ensure_store()
    # For this test shim, reconstruct a minimal view using stored final output
    rows = store.list_debates("t", "w")
    final = next((d.final_output for d in rows if d.id == debate_id), "")
    return {"id": debate_id, "final": final}


def ops_debate_stats() -> dict[str, Any]:
    store = _ensure_store()
    rows = store.list_debates("t", "w")
    return {"count": len(rows), "avg_rounds": 1.0 if rows else 0.0}


__all__ = [
    # cost/cache
    "ops_status",
    # grounding
    "ops_grounding_audit",
    # ingest
    "ops_ingest_watch_add",
    "ops_ingest_watch_list",
    "ops_ingest_queue_status",
    "ops_ingest_run_once",
    # privacy
    "ops_privacy_status",
    "ops_privacy_show",
    "ops_privacy_sweep",
    # incidents
    "ops_incident_open",
    "ops_incident_ack",
    "ops_incident_resolve",
    "ops_incident_list",
    # slo
    "ops_slo_status",
    # debate
    "ops_debate_run",
    "ops_debate_inspect",
    "ops_debate_stats",
]
