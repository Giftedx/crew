"""Crew tool that invokes MCP server tools directly by module import.

This avoids transport dependencies (stdio/http) and makes MCP utilities
available inside Crew agents universally. Only known safe tool functions
from each MCP module are exposed.
"""
from __future__ import annotations
import contextlib
from typing import TYPE_CHECKING, Any
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ._base import BaseTool
if TYPE_CHECKING:
    from collections.abc import Callable
_SAFE_REGISTRY: dict[str, tuple[str, list[str]]] = {'obs': ('mcp_server.obs_server', ['summarize_health', 'get_counters', 'recent_degradations']), 'http': ('mcp_server.http_server', ['http_get', 'http_json_get']), 'ingest': ('mcp_server.ingest_server', ['extract_metadata', 'list_channel_videos', 'fetch_transcript_local', 'summarize_subtitles']), 'kg': ('mcp_server.kg_server', ['kg_query', 'kg_timeline', 'policy_keys']), 'router': ('mcp_server.routing_server', ['estimate_cost', 'route_completion', 'choose_embedding_model']), 'multimodal': ('mcp_server.multimodal_server', ['analyze_image', 'analyze_video', 'analyze_audio', 'analyze_content_auto', 'get_visual_sentiment', 'extract_content_themes']), 'memory': ('mcp_server.memory_server', ['vs_search', 'vs_list_namespaces', 'vs_samples']), 'a2a': ('mcp_server.a2a_bridge_server', ['a2a_call']), 'crewai': ('mcp_server.crewai_server', ['list_available_crews', 'get_crew_status', 'execute_crew', 'get_agent_performance', 'abort_crew_execution'])}

class MCPCallTool(BaseTool[StepResult]):
    name: str = 'MCP Call Tool'
    description: str = 'Call a safe MCP server tool by namespace and name (no transport; direct import).'

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
        try:
            mod = __import__(module_path, fromlist=['__all__'])
            fn = getattr(mod, name, None)
            return fn if callable(fn) else None
        except Exception:
            return None

    def run(self, namespace: str, name: str, params: dict[str, Any] | None=None) -> StepResult:
        ns = str(namespace or '').strip()
        nm = str(name or '').strip()
        if not ns or not nm:
            return StepResult.fail('namespace and name are required')
        fn = self._resolve(ns, nm)
        if fn is None:
            return StepResult.fail(f'unknown_or_forbidden: {ns}.{nm}')
        try:
            payload = params if isinstance(params, dict) else {}
            result = fn(**payload) if payload else fn()
            with contextlib.suppress(Exception):
                self._metrics.counter('tool_runs_total', labels={'tool': 'mcp_call', 'ns': ns, 'name': nm}).inc()
            if isinstance(result, dict):
                return StepResult.ok(result=result)
            return StepResult.ok(result={'value': result})
        except TypeError as te:
            return StepResult.fail(f'invalid_params: {te}')
        except Exception as exc:
            return StepResult.fail(str(exc))
__all__ = ['MCPCallTool']