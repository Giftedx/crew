from __future__ import annotations

import contextlib
import logging
import time
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from fastapi import FastAPI, Request


def register_pilot_route(app: FastAPI, settings: Any) -> None:
    try:
        import os as _os

        if _os.getenv("ENABLE_LANGGRAPH_PILOT_API", "0").lower() not in (
            "1",
            "true",
            "yes",
            "on",
        ):
            return

        try:
            from graphs.langgraph_pilot import run_ingest_analysis_pilot  # type: ignore

            @app.get("/pilot/run")
            def _pilot_run(request: Request) -> dict:
                """Trigger the pilot with minimal stub functions.

                Query params 'tenant' and 'workspace' are optional and default
                to 'default'/'main' when not supplied.
                """

                def _ingest(job: dict) -> dict:
                    """Simulate ingest step returning logical vector namespace.

                    Uses VectorStore.namespace for consistency with memory layer so that
                    downstream components (if wired later) can rely on identical formatting.
                    """
                    t = job.get("tenant", "default")
                    w = job.get("workspace", "main")
                    if not isinstance(t, str):
                        t = "default"
                    if not isinstance(w, str):
                        w = "main"
                    try:
                        from memory.vector_store import (
                            VectorStore,  # local import to avoid heavy deps at import time
                        )

                        ns = VectorStore.namespace(t, w, "pilot")
                    except Exception:  # pragma: no cover - fallback if import fails
                        ns = f"{t}:{w}:pilot"
                    return {"chunks": 2, "namespace": ns}

                def _analyze(ctx: dict) -> dict:
                    n = int(ctx.get("chunks", 0))
                    return {"insights": n * 2}

                def _segment(ctx: dict) -> dict:
                    n = int(ctx.get("chunks", 0))
                    return {"segments": n * 4}

                def _embed(ctx: dict) -> dict:
                    segs = int(ctx.get("segments", 0))
                    return {"embeddings": max(segs, 1)}

                q = getattr(request, "query_params", {}) if request is not None else {}
                tenant_val = q.get("tenant", "default") if isinstance(q, dict) else "default"
                workspace_val = q.get("workspace", "main") if isinstance(q, dict) else "main"
                enable_segment = q.get("enable_segment") in ("1", "true", "yes", "on") if isinstance(q, dict) else False
                enable_embed = q.get("enable_embed") in ("1", "true", "yes", "on") if isinstance(q, dict) else False
                if not isinstance(tenant_val, str):
                    tenant_val = "default"
                if not isinstance(workspace_val, str):
                    workspace_val = "main"
                job = {"tenant": tenant_val, "workspace": workspace_val}
                seg_fn = _segment if enable_segment else None
                emb_fn = _embed if enable_embed else None
                t0 = time.perf_counter()
                out = run_ingest_analysis_pilot(job, _ingest, _analyze, segment_fn=seg_fn, embed_fn=emb_fn)
                with contextlib.suppress(Exception):
                    out["duration_seconds"] = max(0.0, time.perf_counter() - t0)
                return out
        except Exception as exc:  # pragma: no cover - optional path
            logging.debug("pilot api wiring skipped: %s", exc)
    except Exception:  # pragma: no cover - environment access issues
        pass


__all__ = ["register_pilot_route"]
