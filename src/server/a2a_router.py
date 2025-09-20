"""A2A Protocol adapter: JSON-RPC 2.0 endpoints and Agent Card.

This adapter exposes:
 - POST /a2a/jsonrpc : JSON-RPC 2.0 method dispatch for tools/actions (single or batch)
 - GET  /a2a/agent-card: Agent Card describing currently-enabled capabilities
 - GET  /a2a/skills: Minimal skills list with input schemas

Notes
- Uses dynamic tool registry resolution so feature flags toggled at runtime in tests
  are respected without process restart.
- Wraps tool calls with optional metrics and tracing if the observability layer is enabled.
- Honors optional API key auth via env flags.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, Response

# Local observability shims (defensive imports; fall back to no-ops in tests)
try:
    from obs import tracing  # type: ignore
except Exception:  # pragma: no cover

    class _NoTracing:  # type: ignore
        def start_span(self, _name: str):
            class _Span:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def set_attribute(self, *_args, **_kwargs):
                    pass

            return _Span()

    tracing = _NoTracing()  # type: ignore

try:
    from ultimate_discord_intelligence_bot.step_result import StepResult  # type: ignore
except Exception:  # pragma: no cover
    # Minimal stub for local tests if import path differs
    class StepResult:  # type: ignore
        def __init__(self, success: bool, data: Any | None = None, error: str | None = None):
            self.success = success
            self.data = data
            self.error = error

        @classmethod
        def ok(cls, data: Any | None = None):
            return cls(True, data=data)

        @classmethod
        def fail(cls, error: str, data: Any | None = None):
            return cls(False, data=data, error=error)

        def to_dict(self) -> dict[str, Any]:
            return {"status": "ok" if self.success else "error", "data": self.data, "error": self.error}


try:
    from ultimate_discord_intelligence_bot.tenancy.context import (
        TenantContext,
        with_tenant,
    )  # type: ignore
except Exception:  # pragma: no cover

    class TenantContext:  # type: ignore
        def __init__(self, tenant: str, workspace: str):
            self.tenant_id = tenant
            self.workspace_id = workspace

    from contextlib import contextmanager

    @contextmanager
    def with_tenant(_ctx: TenantContext):  # type: ignore
        yield _ctx


# Router
router = APIRouter(prefix="/a2a", tags=["a2a"])

# ---------------------------- Feature flags -----------------------------


def _is_enabled(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0").lower() in ("1", "true", "yes", "on")


def _api_key_ok(header_val: str | None) -> bool:
    if not _is_enabled("ENABLE_A2A_API_KEY", False):
        return True
    expected = os.getenv("A2A_API_KEY")
    if expected is None:
        return False
    allowed = {p.strip() for p in expected.split(",") if p.strip()}
    return header_val is not None and header_val in allowed


# -------------------------- Metrics helpers -----------------------------

try:
    from obs.metrics import get_metrics  # type: ignore

    _METRICS = get_metrics()
except Exception:  # pragma: no cover
    _METRICS = None


def _observe_tool_latency(tool: str, seconds: float, outcome: str) -> None:
    if _METRICS is None:
        return
    try:
        _METRICS.get_histogram("a2a_tool_latency_seconds", ["tool", "outcome"]).labels(tool, outcome).observe(seconds)
    except Exception:
        pass


def _inc_tool_runs(tool: str, outcome: str) -> None:
    if _METRICS is None:
        return
    try:
        _METRICS.get_counter("a2a_tool_runs_total", ["tool", "outcome"]).labels(tool, outcome).inc()
    except Exception:
        pass


def _observe_batch_size(n: int) -> None:
    if _METRICS is None:
        return
    try:
        _METRICS.get_histogram("a2a_jsonrpc_batch_size").observe(n)
    except Exception:
        pass


def _observe_request_latency(mode: str, seconds: float) -> None:
    if _METRICS is None:
        return
    try:
        _METRICS.get_histogram("a2a_jsonrpc_request_latency_seconds", ["mode"]).labels(mode).observe(seconds)
    except Exception:
        pass


# --------------------------- Tool registry ------------------------------

ToolFunc = Callable[..., StepResult]


def _load_tools() -> dict[str, ToolFunc]:  # pragma: no cover - resolved dynamically and tested via endpoints
    tools: dict[str, ToolFunc] = {}

    # Simple demo analyzer
    def _text_analyze(text: str) -> StepResult:
        text = str(text or "")
        words = text.split()
        data = {"length": len(text), "words": len(words), "preview": text[:64]}
        return StepResult.ok(data=data)

    tools["tools.text_analyze"] = _text_analyze

    # Optional skills based on flags; import lazily
    if _is_enabled("ENABLE_A2A_SKILL_SUMMARIZE", True):
        try:
            from ultimate_discord_intelligence_bot.tools.lc_summarize_tool import (
                summarize as lc_summarize,  # type: ignore
            )

            tools["tools.lc_summarize"] = lc_summarize  # type: ignore[assignment]
        except Exception:
            # Offline-safe fallback summarizer: pick first N sentences
            def _summarize(text: str, max_sentences: int = 3) -> StepResult:
                text = str(text or "").strip()
                import re

                # naive sentence split
                sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
                chosen = sentences[: max(1, int(max_sentences or 3))]
                summary = " ".join(chosen)
                data = {"summary": summary, "sentences": chosen, "count": len(chosen)}
                return StepResult.ok(data=data)

            tools["tools.lc_summarize"] = _summarize

    if _is_enabled("ENABLE_A2A_SKILL_RAG_OFFLINE", True):
        try:
            from ultimate_discord_intelligence_bot.tools.rag_offline_tool import rag_query  # type: ignore

            tools["tools.rag_query"] = rag_query  # type: ignore[assignment]
        except Exception:
            # Offline TF-IDF-lite fallback using Jaccard similarity
            def _rag_query(query: str, documents: list[str], top_k: int = 3) -> StepResult:
                if not isinstance(documents, list):
                    return StepResult.fail("Invalid params for tools.rag_query: documents must be a list", data={})
                q_tokens = {t.lower() for t in str(query or "").split() if t}
                hits: list[dict[str, Any]] = []
                for idx, doc in enumerate(documents):
                    d_tokens = {t.lower() for t in str(doc or "").split() if t}
                    inter = len(q_tokens & d_tokens)
                    union = len(q_tokens | d_tokens) or 1
                    score = inter / union
                    hits.append({"index": idx, "score": score, "snippet": str(doc)[:120]})
                hits.sort(key=lambda x: x["score"], reverse=True)
                hits = hits[: max(1, int(top_k or 3))]
                return StepResult.ok(data={"hits": hits, "count": len(hits)})

            tools["tools.rag_query"] = _rag_query

    if _is_enabled("ENABLE_A2A_SKILL_RAG_VECTOR", True):
        try:
            from ultimate_discord_intelligence_bot.tools.rag_vector_tool import rag_query_vs  # type: ignore

            tools["tools.rag_query_vs"] = rag_query_vs  # type: ignore[assignment]
        except Exception:
            pass

    if _is_enabled("ENABLE_A2A_SKILL_RAG_INGEST", False):
        try:
            from ultimate_discord_intelligence_bot.tools.rag_ingest_tool import rag_ingest  # type: ignore

            tools["tools.rag_ingest"] = rag_ingest  # type: ignore[assignment]
        except Exception:
            pass

    if _is_enabled("ENABLE_A2A_SKILL_RAG_INGEST_URL", False):
        try:
            from ultimate_discord_intelligence_bot.tools.rag_ingest_url_tool import rag_ingest_url  # type: ignore

            tools["tools.rag_ingest_url"] = rag_ingest_url  # type: ignore[assignment]
        except Exception:
            pass

    if _is_enabled("ENABLE_A2A_SKILL_RAG_HYBRID", True):
        try:
            from ultimate_discord_intelligence_bot.tools.rag_hybrid_tool import rag_hybrid  # type: ignore

            tools["tools.rag_hybrid"] = rag_hybrid  # type: ignore[assignment]
        except Exception:
            pass

    if _is_enabled("ENABLE_A2A_SKILL_RESEARCH_BRIEF", True):
        try:
            from ultimate_discord_intelligence_bot.tools.research_and_brief_tool import (
                research_and_brief,  # type: ignore
            )

            tools["tools.research_and_brief"] = research_and_brief  # type: ignore[assignment]
        except Exception:
            pass

    # Support both historical and current env flag names
    if _is_enabled("ENABLE_A2A_SKILL_RESEARCH_BRIEF_MULTI", False) or _is_enabled(
        "ENABLE_A2A_SKILL_RESEARCH_AND_BRIEF_MULTI", False
    ):
        try:
            from ultimate_discord_intelligence_bot.tools.research_and_brief_multi_tool import (
                research_and_brief_multi,
            )  # type: ignore

            tools["tools.research_and_brief_multi"] = research_and_brief_multi  # type: ignore[assignment]
        except Exception:
            # Offline-safe multi-agent fallback producing deterministic brief
            def _multi(
                query: str,
                sources_text: list[str] | None = None,
                max_items: int = 5,
                max_time: float | None = None,
                enable_alerts: bool = False,
            ) -> StepResult:
                q = str(query or "").strip()
                sources = [str(s) for s in (sources_text or [])]
                outline = [f"Overview: {q}"] + [
                    f"Point {i + 1}: {s[:60]}" for i, s in enumerate(sources[: max(0, int(max_items or 5))])
                ]
                key_findings = [s[:80] for s in sources[: max(0, int(max_items or 5))]]
                citations = [{"type": "source", "index": i} for i in range(len(key_findings))]
                risks = ["Limited sources", "Heuristic synthesis"]
                counts = {"sources": len(sources), "tokens_estimate": sum(len(s.split()) for s in sources)}
                meta = {"multi_agent": True, "quality_score": None, "execution_time": None}
                data = {
                    "outline": outline or ["Overview"],
                    "key_findings": key_findings or ["No sources provided"],
                    "citations": citations,
                    "risks": risks,
                    "counts": counts,
                    "meta": meta,
                }
                return StepResult.ok(data=data)

            tools["tools.research_and_brief_multi"] = _multi

    return tools


def _get_tools() -> dict[str, ToolFunc]:
    # Load tools on-demand to reflect runtime flag changes
    return _load_tools()


def _call_tool(method: str, params: dict[str, Any] | None) -> StepResult:
    fn = _get_tools().get(method)
    if fn is None:
        return StepResult.fail(f"Unknown method: {method}")
    try:
        params = params or {}
        return fn(**params)  # type: ignore[arg-type]
    except TypeError as te:
        return StepResult.fail(f"Invalid params for {method}: {te}")
    except Exception as exc:
        return StepResult.fail(f"Tool error: {exc}")


def _dispatch(method: str, params: dict[str, Any] | None) -> StepResult:
    """Dispatch a JSON-RPC request, supporting agent.execute wrapper."""
    if method == "agent.execute":
        skill = None
        args = None
        if isinstance(params, dict):
            skill = params.get("skill") or params.get("method") or params.get("tool")
            args = params.get("args") or params.get("params") or params.get("arguments")
        if not isinstance(skill, str):
            return StepResult.fail("Invalid params: missing 'skill' for agent.execute")
        if args is not None and not isinstance(args, dict):
            return StepResult.fail("Invalid params: 'args' must be an object")
        return _call_tool(skill, args if isinstance(args, dict) else {})
    return _call_tool(method, params)


def _tool_label(method: str, params: dict[str, Any] | None) -> str:
    if method == "agent.execute" and isinstance(params, dict):
        name = params.get("skill") or params.get("method") or params.get("tool")
        if isinstance(name, str) and name:
            return name
    return method


# ---------------------------- JSON-RPC API -------------------------------


def _jsonrpc_result(id_val: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_val, "result": result}


def _jsonrpc_error(id_val: Any, code: int, message: str, data: Any | None = None) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_val, "error": err}


def _sr_to_result(sr: StepResult) -> dict[str, Any]:
    # Normalise to a top-level mapping with status/data/error fields like StepResult.to_dict.
    # Ensure that payload appears under 'data' to keep JSON-RPC result shape consistent.
    d = sr.to_dict()
    # If StepResult produces a flat mapping, keep under 'data' key for RPC consistency
    payload = d
    if "status" in payload or "error" in payload:
        # StepResult.to_dict returns status/error combined with data; separate if needed
        payload = payload.get("data", payload)
    return {"status": "success" if sr.success else "error", "data": payload, "error": sr.error}


def _ctx_from_request(tenant_id: str | None, workspace_id: str | None) -> TenantContext | None:
    if tenant_id and workspace_id:
        return TenantContext(tenant_id, workspace_id)
    return None


@router.post("/jsonrpc")
async def jsonrpc_endpoint(
    request: Request,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    """Handle JSON-RPC 2.0 requests (single or batch)."""
    # Fallback header extraction in shim environments where Header aliasing may not fire
    if x_api_key is None and hasattr(request, "headers") and isinstance(request.headers, dict):
        x_api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    if not _api_key_ok(x_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Batch mode
    if isinstance(body, list):
        if len(body) == 0:
            return _jsonrpc_error(None, -32600, "Invalid Request: empty batch")
        _observe_batch_size(len(body))
        req_start = time.perf_counter()
        responses: list[dict[str, Any]] = []
        for item in body:
            if not isinstance(item, dict) or item.get("jsonrpc") != "2.0":
                responses.append(_jsonrpc_error(None, -32600, "Invalid Request"))
                continue
            method = item.get("method")
            id_val = item.get("id")
            params = item.get("params") if isinstance(item.get("params"), dict) else None
            if not isinstance(method, str):
                responses.append(_jsonrpc_error(id_val, -32600, "Invalid Request: method must be string"))
                continue

            tenant_id = x_tenant_id or (params.get("tenant_id") if params else None)
            workspace_id = x_workspace_id or (params.get("workspace_id") if params else None)
            ctx = _ctx_from_request(str(tenant_id) if tenant_id else None, str(workspace_id) if workspace_id else None)

            def _execute_one() -> dict[str, Any] | None:
                tool_name = _tool_label(method, params)
                t0 = time.perf_counter()
                with tracing.start_span("a2a.jsonrpc.tool") as span:  # type: ignore[attr-defined]
                    try:
                        span.set_attribute("tool", tool_name)
                        span.set_attribute("mode", "batch")
                    except Exception:
                        pass
                    sr = _dispatch(method, params)
                    try:
                        span.set_attribute("outcome", "success" if sr.success else "error")
                    except Exception:
                        pass
                dt = max(0.0, time.perf_counter() - t0)
                _observe_tool_latency(tool_name, dt, "success" if sr.success else "error")
                _inc_tool_runs(tool_name, "success" if sr.success else "error")

                if sr.success:
                    return _jsonrpc_result(id_val, _sr_to_result(sr)) if id_val is not None else None
                msg = sr.error or "error"
                code = -32603
                if isinstance(msg, str):
                    if msg.startswith("Unknown method"):
                        code = -32601
                    elif msg.startswith("Invalid params"):
                        code = -32602
                return _jsonrpc_error(id_val, code, msg, data=sr.data) if id_val is not None else None

            if ctx is not None:
                with with_tenant(ctx):
                    resp = _execute_one()
            else:
                resp = _execute_one()
            if resp is not None:
                responses.append(resp)
        _observe_request_latency("batch", max(0.0, time.perf_counter() - req_start))
        return responses

    # Single call
    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
        raise HTTPException(status_code=400, detail="Invalid JSON-RPC request")
    method = body.get("method")
    id_val = body.get("id")
    params = body.get("params") if isinstance(body.get("params"), dict) else None
    if not isinstance(method, str):
        return _jsonrpc_error(id_val, -32600, "Invalid Request: method must be string")

    tenant_id = x_tenant_id or (params.get("tenant_id") if params else None)
    workspace_id = x_workspace_id or (params.get("workspace_id") if params else None)
    ctx = _ctx_from_request(str(tenant_id) if tenant_id else None, str(workspace_id) if workspace_id else None)

    req_start = time.perf_counter()

    def _execute() -> StepResult:
        tool_name = _tool_label(method, params)
        t0 = time.perf_counter()
        with tracing.start_span("a2a.jsonrpc.tool") as span:  # type: ignore[attr-defined]
            try:
                span.set_attribute("tool", tool_name)
                span.set_attribute("mode", "single")
            except Exception:
                pass
            sr = _dispatch(method, params)
            try:
                span.set_attribute("outcome", "success" if sr.success else "error")
            except Exception:
                pass
        dt = max(0.0, time.perf_counter() - t0)
        _observe_tool_latency(tool_name, dt, "success" if sr.success else "error")
        _inc_tool_runs(tool_name, "success" if sr.success else "error")
        return sr

    if ctx is not None:
        with with_tenant(ctx):
            sr = _execute()
    else:
        sr = _execute()

    _observe_request_latency("single", max(0.0, time.perf_counter() - req_start))
    if sr.success:
        return _jsonrpc_result(id_val, _sr_to_result(sr))
    msg = sr.error or "error"
    code = -32603
    if isinstance(msg, str):
        if msg.startswith("Unknown method"):
            code = -32601
        elif msg.startswith("Invalid params"):
            code = -32602
    return _jsonrpc_error(id_val, code, msg, data=sr.data)


# ---------------------------- Streaming demo ----------------------------

if _is_enabled("ENABLE_A2A_STREAMING_DEMO", False):
    # Import locally to avoid failing when the lightweight FastAPI shim lacks StreamingResponse
    try:
        from fastapi.responses import StreamingResponse  # type: ignore
    except Exception:  # pragma: no cover - streaming demo optional
        StreamingResponse = None  # type: ignore

    if StreamingResponse is not None:  # type: ignore[truthy-bool]

        @router.get("/stream-demo")
        async def stream_demo(text: str = "processing") -> Response:
            async def gen():
                import asyncio

                for i in range(1, 4):
                    yield f"data: step {i}/3: {text}\n\n"
                    await asyncio.sleep(0.05)
                yield "data: done\n\n"

            return StreamingResponse(gen(), media_type="text/event-stream")
    else:
        # Provide a non-streaming fallback so the route exists if tests poke it while demo is enabled.
        @router.get("/stream-demo")
        async def stream_demo_fallback(text: str = "processing") -> Response:  # pragma: no cover - fallback
            payload = "".join([f"data: step {i}/3: {text}\n\n" for i in range(1, 4)]) + "data: done\n\n"
            return Response(payload, media_type="text/event-stream")


# ------------------------------ Discovery -------------------------------


def _skill_entries() -> list[dict[str, Any]]:
    tools_reg = _get_tools()
    skills: list[dict[str, Any]] = []

    if "tools.text_analyze" in tools_reg:
        skills.append(
            {
                "name": "tools.text_analyze",
                "description": "Analyze input text and return simple metrics (e.g., sentiment/keywords).",
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {"text": {"type": "string", "description": "Text to analyze"}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {"type": "object"},
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.lc_summarize" in tools_reg:
        skills.append(
            {
                "name": "tools.lc_summarize",
                "description": "Extractive summarization: selects key sentences to form a concise summary.",
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to summarize"},
                        "max_sentences": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3},
                    },
                    "required": ["text"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "summary": {"type": "string"},
                                "sentences": {"type": "array", "items": {"type": "string"}},
                                "count": {"type": "integer"},
                            },
                            "required": ["summary", "sentences"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.rag_query" in tools_reg:
        skills.append(
            {
                "name": "tools.rag_query",
                "description": "Rank a provided list of documents against a query using TF-IDF cosine.",
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "User query"},
                        "documents": {"type": "array", "items": {"type": "string"}, "description": "Docs to search"},
                        "top_k": {"type": "integer", "minimum": 1, "maximum": 25, "default": 3},
                    },
                    "required": ["query", "documents"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "hits": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "index": {"type": "integer"},
                                            "score": {"type": "number"},
                                            "snippet": {"type": "string"},
                                        },
                                        "required": ["index", "score", "snippet"],
                                    },
                                },
                                "count": {"type": "integer"},
                            },
                            "required": ["hits", "count"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.rag_query_vs" in tools_reg:
        skills.append(
            {
                "name": "tools.rag_query_vs",
                "description": "Query tenant-scoped vector index; optional offline fallback if documents provided.",
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "User query"},
                        "index": {"type": "string", "default": "memory", "description": "Logical index name"},
                        "top_k": {"type": "integer", "minimum": 1, "maximum": 25, "default": 3},
                        "documents": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional fallback docs",
                        },
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "hits": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "text": {"type": "string"},
                                            "score": {"type": "number"},
                                            "payload": {"type": "object"},
                                        },
                                    },
                                },
                                "count": {"type": "integer"},
                                "source": {"type": "string", "enum": ["vector", "offline"]},
                            },
                            "required": ["hits", "count", "source"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.rag_ingest" in tools_reg:
        skills.append(
            {
                "name": "tools.rag_ingest",
                "description": "Chunk and upsert provided texts into a tenant-scoped vector index.",
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "texts": {"type": "array", "items": {"type": "string"}},
                        "index": {"type": "string", "default": "memory"},
                        "chunk_size": {"type": "integer", "minimum": 50, "maximum": 2000, "default": 400},
                        "overlap": {"type": "integer", "minimum": 0, "maximum": 500, "default": 50},
                    },
                    "required": ["texts"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "inserted": {"type": "integer"},
                                "chunks": {"type": "integer"},
                                "index": {"type": "string"},
                                "tenant_scoped": {"type": "boolean"},
                            },
                            "required": ["inserted", "chunks", "index", "tenant_scoped"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.rag_ingest_url" in tools_reg:
        skills.append(
            {
                "name": "tools.rag_ingest_url",
                "description": "Fetch HTTPS URLs, strip HTML, chunk and upsert into a tenant-scoped vector index.",
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "urls": {"type": "array", "items": {"type": "string"}},
                        "index": {"type": "string", "default": "memory"},
                        "chunk_size": {"type": "integer", "minimum": 50, "maximum": 2000, "default": 400},
                        "overlap": {"type": "integer", "minimum": 0, "maximum": 500, "default": 50},
                        "max_bytes": {"type": "integer", "minimum": 1000, "maximum": 2000000, "default": 500000},
                    },
                    "required": ["urls"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "fetched": {"type": "integer"},
                                "inserted": {"type": "integer"},
                                "chunks": {"type": "integer"},
                                "index": {"type": "string"},
                                "tenant_scoped": {"type": "boolean"},
                            },
                            "required": ["fetched", "inserted", "chunks", "index", "tenant_scoped"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.rag_hybrid" in tools_reg:
        skills.append(
            {
                "name": "tools.rag_hybrid",
                "description": "Hybrid retrieval combining vector search with offline TF-IDF and optional reranker.",
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "index": {"type": "string", "default": "memory"},
                        "candidate_docs": {"type": "array", "items": {"type": "string"}},
                        "top_k": {"type": "integer", "minimum": 1, "maximum": 25, "default": 5},
                        "alpha": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.7},
                        "enable_rerank": {"type": ["boolean", "null"], "default": None},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "hits": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "text": {"type": "string"},
                                            "score": {"type": "number"},
                                            "source": {"type": "string"},
                                        },
                                    },
                                },
                                "count": {"type": "integer"},
                                "method": {"type": "string"},
                                "reranked": {"type": "boolean"},
                            },
                            "required": ["hits", "count", "method", "reranked"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.research_and_brief" in tools_reg:
        skills.append(
            {
                "name": "tools.research_and_brief",
                "description": "Synthesize outline and key findings from provided text sources (offline-safe).",
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "sources_text": {"type": ["array", "null"], "items": {"type": "string"}},
                        "max_items": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "outline": {"type": "array", "items": {"type": "string"}},
                                "key_findings": {"type": "array", "items": {"type": "string"}},
                                "citations": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {"type": {"type": "string"}, "index": {"type": "integer"}},
                                    },
                                },
                                "risks": {"type": "array", "items": {"type": "string"}},
                                "counts": {
                                    "type": "object",
                                    "properties": {
                                        "sources": {"type": "integer"},
                                        "tokens_estimate": {"type": "integer"},
                                    },
                                },
                            },
                            "required": ["outline", "key_findings", "citations", "risks", "counts"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.research_and_brief_multi" in tools_reg:
        skills.append(
            {
                "name": "tools.research_and_brief_multi",
                "description": "Multi-agent augmented research and brief with offline fallback; strict time limits.",
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "sources_text": {"type": ["array", "null"], "items": {"type": "string"}},
                        "max_items": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
                        "max_time": {"type": "number", "minimum": 5.0, "maximum": 300.0, "default": 60.0},
                        "enable_alerts": {"type": "boolean", "default": False},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "outline": {"type": "array", "items": {"type": "string"}},
                                "key_findings": {"type": "array", "items": {"type": "string"}},
                                "citations": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {"type": {"type": "string"}, "index": {"type": "integer"}},
                                    },
                                },
                                "risks": {"type": "array", "items": {"type": "string"}},
                                "counts": {
                                    "type": "object",
                                    "properties": {
                                        "sources": {"type": "integer"},
                                        "tokens_estimate": {"type": "integer"},
                                    },
                                },
                                "meta": {
                                    "type": "object",
                                    "properties": {
                                        "multi_agent": {"type": "boolean"},
                                        "quality_score": {"type": ["number", "null"]},
                                        "execution_time": {"type": ["number", "null"]},
                                    },
                                },
                            },
                            "required": ["outline", "key_findings", "citations", "risks", "counts", "meta"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    return skills


@router.get("/agent-card")
async def agent_card():
    return {
        "id": "crew-discord-intelligence",
        "name": "Crew Discord Intelligence A2A Adapter",
        "version": "0.1.0",
        "protocol": "A2A-JSONRPC",
        "transport": "https",
        "endpoints": {"rpc": "/a2a/jsonrpc"},
        "skills": _skill_entries(),
        "auth": {"type": "none" if not _is_enabled("ENABLE_A2A_API_KEY", False) else "apiKey"},
        "description": "A minimal A2A-compatible adapter exposing selected tools over JSON-RPC.",
    }


@router.get("/skills")
async def list_skills():
    out = []
    for name in sorted(_get_tools().keys()):
        schema = None
        if name == "tools.text_analyze":
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            }
        elif name == "tools.lc_summarize":
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "max_sentences": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3},
                },
                "required": ["text"],
            }
        elif name == "tools.rag_query":
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "documents": {"type": "array", "items": {"type": "string"}},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 25, "default": 3},
                },
                "required": ["query", "documents"],
            }
        elif name == "tools.rag_query_vs":
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "index": {"type": "string", "default": "memory"},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 25, "default": 3},
                    "documents": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["query"],
            }
        elif name == "tools.rag_ingest":
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "texts": {"type": "array", "items": {"type": "string"}},
                    "index": {"type": "string", "default": "memory"},
                    "chunk_size": {"type": "integer", "minimum": 50, "maximum": 2000, "default": 400},
                    "overlap": {"type": "integer", "minimum": 0, "maximum": 500, "default": 50},
                },
                "required": ["texts"],
            }
        elif name == "tools.rag_ingest_url":
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "urls": {"type": "array", "items": {"type": "string"}},
                    "index": {"type": "string", "default": "memory"},
                    "chunk_size": {"type": "integer", "minimum": 50, "maximum": 2000, "default": 400},
                    "overlap": {"type": "integer", "minimum": 0, "maximum": 500, "default": 50},
                    "max_bytes": {"type": "integer", "minimum": 1000, "maximum": 2000000, "default": 500000},
                },
                "required": ["urls"],
            }
        elif name == "tools.rag_hybrid":
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "index": {"type": "string", "default": "memory"},
                    "candidate_docs": {"type": "array", "items": {"type": "string"}},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 25, "default": 5},
                    "alpha": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.7},
                    "enable_rerank": {"type": ["boolean", "null"], "default": None},
                },
                "required": ["query"],
            }
        elif name == "tools.research_and_brief":
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "sources_text": {"type": ["array", "null"], "items": {"type": "string"}},
                    "max_items": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
                },
                "required": ["query"],
            }
        elif name == "tools.research_and_brief_multi":
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "sources_text": {"type": ["array", "null"], "items": {"type": "string"}},
                    "max_items": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
                    "max_time": {"type": "number", "minimum": 5.0, "maximum": 300.0, "default": 60.0},
                    "enable_alerts": {"type": "boolean", "default": False},
                },
                "required": ["query"],
            }
        out.append({"name": name, "input_schema": schema})
    return {"skills": out}


__all__ = ["router"]
