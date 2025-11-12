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

import contextlib
import time
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from .a2a_discovery import attach_discovery_routes as _attach_discovery
from .a2a_metrics import inc_tool_runs as _inc_tool_runs
from .a2a_metrics import observe_batch_size as _observe_batch_size
from .a2a_metrics import observe_request_latency as _observe_request_latency
from .a2a_metrics import observe_tool_latency as _observe_tool_latency
from .a2a_streaming import attach_streaming_demo as _attach_streaming_demo
from .a2a_tools import api_key_ok as _api_key_ok
from .a2a_tools import get_tools as _get_tools


try:
    from ultimate_discord_intelligence_bot.obs import tracing
except Exception:

    class _NoTracing:
        def start_span(self, _name: str):
            class _Span:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def set_attribute(self, *_args, **_kwargs):
                    pass

            return _Span()

    tracing = _NoTracing()
try:
    from ultimate_discord_intelligence_bot.step_result import StepResult
except Exception:

    class StepResult:
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
    from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant
except Exception:

    class TenantContext:
        def __init__(self, tenant: str, workspace: str):
            self.tenant_id = tenant
            self.workspace_id = workspace

    from contextlib import contextmanager

    @contextmanager
    def with_tenant(_ctx: TenantContext):
        yield _ctx


router = APIRouter(prefix="/a2a", tags=["a2a"])
"Tool registry lives in a2a_tools; keep an adapter name for clarity in this module."


def _call_tool(method: str, params: dict[str, Any] | None) -> StepResult:
    fn = _get_tools().get(method)
    if fn is None:
        return StepResult.fail(f"Unknown method: {method}")
    try:
        params = params or {}
        return fn(**params)
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
        if args is not None and (not isinstance(args, dict)):
            return StepResult.fail("Invalid params: 'args' must be an object")
        return _call_tool(skill, args if isinstance(args, dict) else {})
    return _call_tool(method, params)


def _tool_label(method: str, params: dict[str, Any] | None) -> str:
    if method == "agent.execute" and isinstance(params, dict):
        name = params.get("skill") or params.get("method") or params.get("tool")
        if isinstance(name, str) and name:
            return name
    return method


def _jsonrpc_result(id_val: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_val, "result": result}


def _jsonrpc_error(id_val: Any, code: int, message: str, data: Any | None = None) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_val, "error": err}


def _sr_to_result(sr: StepResult) -> dict[str, Any]:
    d = sr.to_dict()
    payload = d
    if "status" in payload or "error" in payload:
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
    if x_api_key is None and hasattr(request, "headers") and isinstance(request.headers, dict):
        x_api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    if not _api_key_ok(x_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc
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

            def _execute_one(
                method_name: str = method, method_params: dict[str, Any] | None = params, request_id: Any = id_val
            ) -> dict[str, Any] | None:
                tool_name = _tool_label(method_name, method_params)
                t0 = time.perf_counter()
                with tracing.start_span("a2a.jsonrpc.tool") as span:
                    try:
                        span.set_attribute("tool", tool_name)
                        span.set_attribute("mode", "batch")
                    except Exception:
                        pass
                    sr = _dispatch(method_name, method_params)
                    with contextlib.suppress(Exception):
                        span.set_attribute("outcome", "success" if sr.success else "error")
                dt = max(0.0, time.perf_counter() - t0)
                _observe_tool_latency(tool_name, dt, "success" if sr.success else "error")
                _inc_tool_runs(tool_name, "success" if sr.success else "error")
                if sr.success:
                    return _jsonrpc_result(request_id, _sr_to_result(sr)) if request_id is not None else None
                msg = sr.error or "error"
                code = -32603
                if isinstance(msg, str):
                    if msg.startswith("Unknown method"):
                        code = -32601
                    elif msg.startswith("Invalid params"):
                        code = -32602
                return _jsonrpc_error(request_id, code, msg, data=sr.data) if request_id is not None else None

            if ctx is not None:
                with with_tenant(ctx):
                    resp = _execute_one()
            else:
                resp = _execute_one()
            if resp is not None:
                responses.append(resp)
        _observe_request_latency("batch", max(0.0, time.perf_counter() - req_start))
        return responses
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

    def _execute(method_name: str = method, method_params: dict[str, Any] | None = params) -> StepResult:
        tool_name = _tool_label(method_name, method_params)
        t0 = time.perf_counter()
        with tracing.start_span("a2a.jsonrpc.tool") as span:
            try:
                span.set_attribute("tool", tool_name)
                span.set_attribute("mode", "single")
            except Exception:
                pass
            sr = _dispatch(method_name, method_params)
            with contextlib.suppress(Exception):
                span.set_attribute("outcome", "success" if sr.success else "error")
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


_attach_streaming_demo(router)
_attach_discovery(router)
__all__ = ["router"]
