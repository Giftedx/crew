"""Minimal FastMCP server exposing a few safe utility tools/resources.

This module is optional and only used when the `mcp` extra is installed:

    uv pip install .[mcp]

Entry point: `crew_mcp` (configured in pyproject).

It provides:
 - tools: health_check, echo, get_config_flag
 - resource: settings://service_name

Safe defaults only; integrates lightly with existing core/settings.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
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

    def mount(self, *_a, **_k):
        return None

    def run(self, *args, **kwargs) -> None:
        raise RuntimeError("FastMCP not available; install '.[mcp]' to run this server")
try:
    from platform.config.settings import Settings
    _settings = Settings()
    SERVER_NAME = getattr(_settings, 'service_name', 'Crew MCP Server')
except Exception:
    SERVER_NAME = 'Crew MCP Server'
mcp = FastMCP(SERVER_NAME) if _FASTMCP_AVAILABLE else _StubMCP(SERVER_NAME)

@mcp.tool
def health_check() -> str:
    """Return a simple OK string indicating the server is alive."""
    return 'ok'

@mcp.tool
def echo(message: str, uppercase: bool=False) -> str:
    """Echo the provided message back to the caller.

    Args:
        message: Text to echo back
        uppercase: If true, returns the message uppercased
    """
    return message.upper() if uppercase else message

@mcp.tool
def get_config_flag(name: str, default: str | None=None) -> str | None:
    """Read a simple configuration flag from environment or Settings.

    Tries Settings first (attribute by name), then falls back to environment
    variables using the same key. Returns the provided default if missing.
    """
    try:
        from platform.config.settings import Settings
        s = Settings()
        if hasattr(s, name):
            val = getattr(s, name)
            return str(val) if val is not None else None
    except Exception:
        pass
    try:
        import os
        val = os.getenv(name)
        if val is not None:
            return val
    except Exception:
        pass
    return default

@mcp.resource('settings://service_name')
def service_name() -> str:
    """Expose the current service name as a read-only resource."""
    return SERVER_NAME
try:
    import os as _os
    if _os.getenv('ENABLE_MCP_MEMORY', '0').lower() in ('1', 'true', 'yes', 'on'):
        try:
            from mcp_server.memory_server import memory_mcp
            mcp.mount(memory_mcp, prefix='memory')
        except Exception:
            pass
    if _os.getenv('ENABLE_MCP_ROUTER', '0').lower() in ('1', 'true', 'yes', 'on'):
        try:
            from mcp_server.routing_server import routing_mcp
            mcp.mount(routing_mcp, prefix='router')
        except Exception:
            pass
    if _os.getenv('ENABLE_MCP_OBS', '0').lower() in ('1', 'true', 'yes', 'on'):
        try:
            from mcp_server.obs_server import obs_mcp
            mcp.mount(obs_mcp, prefix='obs')
        except Exception:
            pass
    if _os.getenv('ENABLE_MCP_KG', '0').lower() in ('1', 'true', 'yes', 'on'):
        try:
            from mcp_server.kg_server import kg_mcp
            mcp.mount(kg_mcp, prefix='kg')
        except Exception:
            pass
    if _os.getenv('ENABLE_MCP_INGEST', '0').lower() in ('1', 'true', 'yes', 'on'):
        try:
            from mcp_server.ingest_server import ingest_mcp
            mcp.mount(ingest_mcp, prefix='ingest')
        except Exception:
            pass
    if _os.getenv('ENABLE_MCP_HTTP', '0').lower() in ('1', 'true', 'yes', 'on'):
        try:
            from mcp_server.http_server import http_mcp
            mcp.mount(http_mcp, prefix='http')
        except Exception:
            pass
    if _os.getenv('ENABLE_MCP_A2A', '0').lower() in ('1', 'true', 'yes', 'on'):
        try:
            from mcp_server.a2a_bridge_server import a2a_mcp
            mcp.mount(a2a_mcp, prefix='a2a')
        except Exception:
            pass
    if _os.getenv('ENABLE_MCP_CREWAI', '0').lower() in ('1', 'true', 'yes', 'on'):
        try:
            from mcp_server.crewai_server import crewai_mcp
            mcp.mount(crewai_mcp, prefix='crewai')
        except Exception:
            pass
except Exception:
    pass

def main(argv: list[str] | None=None) -> int:
    """Run the FastMCP server using stdio by default.

    Use environment variables FASTMCP_HOST/PORT and transport args for HTTP/SSE if desired.
    """
    argv = argv or []
    if any((arg in {'-h', '--help'} for arg in argv)):
        print('Usage: python -m mcp_server.server [--transport stdio|http]')
        return 0
    try:
        _m = globals().get('mcp')
        if _m is None:
            import sys as _sys
            print("FastMCP not available. Install optional extra: pip install '.[mcp]'", file=_sys.stderr)
            return 2
        _m.run()
        return 0
    except Exception as exc:
        import sys as _sys
        print(f'MCP server failed to start: {exc}', file=_sys.stderr)
        return 1
if __name__ == '__main__':
    raise SystemExit(main())