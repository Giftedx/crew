import importlib
import types


MODULES = [
    "mcp_server.server",  # core aggregator (may be FastMCP optional)
    "mcp_server.memory_server",
    "mcp_server.routing_server",
    "mcp_server.obs_server",
    "mcp_server.kg_server",
    "mcp_server.ingest_server",
    "mcp_server.http_server",
    "mcp_server.a2a_bridge_server",
]


def test_mcp_modules_import_safely():
    """All MCP modules should import without raising, even if FastMCP isn't installed.

    Each module should expose a top-level MCP-like object (attribute endswith '_mcp') with .tool and .resource
    attributes that are callable decorators. We don't call .run() here.
    """

    for modname in MODULES:
        mod = importlib.import_module(modname)
        assert isinstance(mod, types.ModuleType)
        # Find an attr named like '*_mcp'
        mcp_like = None
        for attr in dir(mod):
            if attr.endswith("_mcp"):
                mcp_like = getattr(mod, attr)
                break
        if mcp_like is None and modname.endswith(".server") and hasattr(mod, "mcp"):
            mcp_like = mod.mcp
        assert mcp_like is not None, f"No MCP object found in {modname}"
        # Verify decorators exist
        assert hasattr(mcp_like, "tool"), f"{modname} MCP object missing .tool"
        assert hasattr(mcp_like, "resource"), f"{modname} MCP object missing .resource"
        # tool/resource should be callables returning decorators
        deco = mcp_like.tool
        res = mcp_like.resource
        assert callable(deco), f"{modname}.tool not callable"
        assert callable(res), f"{modname}.resource not callable"
