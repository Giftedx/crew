"""FastMCP A2A Bridge server (limited surface).

Tools:
- a2a_call(method, params): invoke selected A2A tools (names must start with 'tools.')

Resources:
- a2a://skills - list of tool names currently available via A2A
- a2a://skills_full - detailed skills entries (schemas) when available

Guards:
- Only methods with prefix 'tools.' are allowed
- Errors are returned as structured dicts; no exceptions are raised for recoverable issues
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from collections.abc import Callable
try:
    from fastmcp import FastMCP
    _FASTMCP_AVAILABLE = True
except Exception:
    FastMCP = None
    _FASTMCP_AVAILABLE = False

class _StubMCP:

    def __init__(self, _name: str):
        self.name = _name

    def tool(self, fn: Callable | None=None, /, **_kw):

        def _decorator(f: Callable):
            return f
        return _decorator if fn is None else fn

    def resource(self, *_a, **_k):

        def _decorator(f: Callable):
            return f
        return _decorator

    def run(self) -> None:
        raise RuntimeError("FastMCP not available; install '.[mcp]' to run this server")
a2a_mcp = FastMCP('A2A Bridge Server') if _FASTMCP_AVAILABLE else _StubMCP('A2A Bridge Server')

def _get_tools() -> dict[str, Any]:
    try:
        from server import a2a_router as _a2a
        return _a2a._get_tools()
    except Exception:
        return {}

def _to_result(obj: Any) -> dict[str, Any]:
    try:
        if hasattr(obj, 'to_dict'):
            d = obj.to_dict()
            if isinstance(d, dict):
                return d
        if isinstance(obj, dict):
            return {'status': obj.get('status', 'ok'), 'data': obj.get('data', obj), 'error': obj.get('error')}
        return {'status': 'ok', 'data': obj, 'error': None}
    except Exception as exc:
        return {'status': 'error', 'error': str(exc), 'data': None}

def _a2a_call_impl(method: str, params: dict[str, Any] | None=None) -> dict:
    """Call an A2A tool by name (must start with 'tools.')."""
    name = str(method or '').strip()
    if not name.startswith('tools.'):
        return {'status': 'error', 'error': 'forbidden_method', 'data': {'method': name}}
    tools = _get_tools()
    fn = tools.get(name)
    if fn is None:
        return {'status': 'error', 'error': f'unknown_method:{name}'}
    try:
        payload = params if isinstance(params, dict) else {}
        result = fn(**payload)
        return _to_result(result)
    except TypeError as te:
        return {'status': 'error', 'error': f'invalid_params:{te}'}
    except Exception as exc:
        return {'status': 'error', 'error': str(exc)}

def a2a_call(method: str, params: dict[str, Any] | None=None) -> dict:
    return _a2a_call_impl(method, params)

@a2a_mcp.tool
def a2a_call_tool(method: str, params: dict[str, Any] | None=None) -> dict:
    return _a2a_call_impl(method, params)

@a2a_mcp.resource('a2a://skills')
def skills_simple() -> list[str]:
    return sorted(_get_tools().keys())

@a2a_mcp.resource('a2a://skills_full')
def skills_full() -> Any:
    try:
        from server import a2a_router as _a2a
        return _a2a._skill_entries()
    except Exception as exc:
        return {'error': str(exc)}
__all__ = ['a2a_call', 'a2a_call_tool', 'a2a_mcp', 'skills_full', 'skills_simple']