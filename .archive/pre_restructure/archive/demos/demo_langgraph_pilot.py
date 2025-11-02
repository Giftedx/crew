#!/usr/bin/env python3

"""Demo runner for the LangGraph pilot orchestration stub.

Runs a minimal ingest→analysis flow via run_ingest_analysis_pilot and prints a
compact summary so you can validate metrics and dashboards quickly.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

from src.graphs.langgraph_pilot import run_ingest_analysis_pilot


def _ingest(job: dict):
    # Simulate making transcript chunks and a namespace
    return {
        "chunks": 2,
        "namespace": f"{job.get('tenant', 'default')}:{job.get('workspace', 'main')}:demo",
    }


def _analyze(ctx: dict):
    # Simulate simple analysis over chunks
    n = int(ctx.get("chunks", 0))
    return {"insights": n * 2, "analyzed_at": datetime.now(UTC).isoformat()}


def main():
    job = {
        "tenant": os.getenv("DEMO_TENANT", "default"),
        "workspace": os.getenv("DEMO_WORKSPACE", "main"),
    }
    enable_segment = os.getenv("DEMO_ENABLE_SEGMENT", "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    enable_embed = os.getenv("DEMO_ENABLE_EMBED", "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    def _segment(ctx: dict):
        n = int(ctx.get("chunks", 0))
        return {"segments": n * 4}

    def _embed(ctx: dict):
        segs = int(ctx.get("segments", 0))
        return {"embeddings": max(segs, 1)}

    res = run_ingest_analysis_pilot(
        job,
        _ingest,
        _analyze,
        segment_fn=_segment if enable_segment else None,
        embed_fn=_embed if enable_embed else None,
    )
    print("LangGraph Pilot Demo Result:\n" + json.dumps(res, indent=2))
    # Friendly summary including timing and orchestrator
    dur = res.get("duration_seconds")
    orch = res.get("orchestrator")
    if isinstance(dur, (int, float)):
        print(f"\nSummary: orchestrator={orch}, duration_seconds={dur:.4f}")
    else:
        print(f"\nSummary: orchestrator={orch}")
    print("\nHints:")
    if os.getenv("ENABLE_LANGGRAPH_PILOT") in ("1", "true", "yes", "on"):
        print(" - Pilot enabled: expect pipeline step completion metric for step=langgraph_pilot.")
    else:
        print(" - Pilot disabled: expect degradation event fallback_sequential.")
    print(" - Check your Prometheus /metrics endpoint and Grafana dashboard panels.")


if __name__ == "__main__":
    main()
