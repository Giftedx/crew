"""Crew tool that invokes MCP server tools directly by module import.

This avoids transport dependencies (stdio/http) and makes MCP utilities
available inside Crew agents universally. Only known safe tool functions
from each MCP module are exposed.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

_SAFE_REGISTRY: dict[str, tuple[str, list[str]]] = {
    # namespace: (module_path, [allowed function names])
    "obs": (
        "mcp_server.obs_server",
        ["summarize_health", "get_counters", "recent_degradations"],
    ),
    "http": (
        "mcp_server.http_server",
        ["http_get", "http_json_get"],
    ),
    "ingest": (
        "mcp_server.ingest_server",
        [
            "extract_metadata",
            "list_channel_videos",
            "fetch_transcript_local",
            "summarize_subtitles",
        ],
    ),
    "kg": (
        "mcp_server.kg_server",
        ["kg_query", "kg_timeline", "policy_keys"],
    ),
    "router": (
        "mcp_server.routing_server",
        ["estimate_cost", "route_completion", "choose_embedding_model"],
    ),
    "memory": (
        "mcp_server.memory_server",
        ["vs_search", "vs_list_namespaces", "vs_samples"],
    ),
    "a2a": (
        "mcp_server.a2a_bridge_server",
        ["a2a_call"],
    ),
    "crewai": (
        "mcp_server.crewai_server",
        ["list_available_crews", "get_crew_status", "execute_crew", "get_agent_performance", "abort_crew_execution"],
    ),
}


class MCPCallTool(BaseTool[StepResult]):
    name: str = "MCP Call Tool"
    description: str = "Call a safe MCP server tool by namespace and name (no transport; direct import)."

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def _resolve(self, namespace: str, name: str) -> Callable[..., Any] | None:
        entry = _SAFE_REGISTRY.get(str(namespace))
        if not entry:
            return None
        module_path, allowed = entry
        if name not in allowed:
            return None
        try:  # import lazily to keep startup fast
            mod = __import__(module_path, fromlist=["__all__"])  # type: ignore
            fn = getattr(mod, name, None)
            return fn if callable(fn) else None
        except Exception:
            return None

    def run(self, namespace: str, name: str, params: dict[str, Any] | None = None) -> StepResult:
        ns = str(namespace or "").strip()
        nm = str(name or "").strip()
        if not ns or not nm:
            return StepResult.fail("namespace and name are required")
        fn = self._resolve(ns, nm)
        if fn is None:
            return StepResult.fail(f"unknown_or_forbidden: {ns}.{nm}")
        try:
            payload = params if isinstance(params, dict) else {}
            result = fn(**payload) if payload else fn()
            # Emit metrics
            try:
                self._metrics.counter("tool_runs_total", labels={"tool": "mcp_call", "ns": ns, "name": nm}).inc()
            except Exception:
                ...
            if isinstance(result, dict):
                return StepResult.ok(result=result)
            # Wrap non-dict returns
            return StepResult.ok(result={"value": result})
        except TypeError as te:
            return StepResult.fail(f"invalid_params: {te}")
        except Exception as exc:
            return StepResult.fail(str(exc))


__all__ = ["MCPCallTool"]
