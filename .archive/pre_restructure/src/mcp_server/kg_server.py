"""FastMCP Grounding & KG server (read-only).

Tools:
- kg_query(tenant, entity, depth=1) -> small subgraph (nodes, edges)
- kg_timeline(tenant, entity) -> ordered events mentioning the entity

Resources:
- policy://{key} -> subset of config/policy.yaml by top-level key (or "full")
- grounding://profiles -> contents of config/grounding.yaml

Notes:
- Uses the SQLite-backed KGStore with default path (in-memory unless the app wires persistence).
- Read-only and size-capped; returns empty sets when data is unavailable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable


try:
    from fastmcp import FastMCP  # type: ignore

    _FASTMCP_AVAILABLE = True
except Exception:  # pragma: no cover
    FastMCP = None  # type: ignore
    _FASTMCP_AVAILABLE = False


class _StubMCP:  # pragma: no cover - used when FastMCP not installed
    def __init__(self, _name: str):
        self.name = _name

    def tool(self, fn: Callable | None = None, /, **_kw):
        def _decorator(f: Callable):
            return f

        return _decorator if fn is None else fn

    def resource(self, *_a, **_k):
        def _decorator(f: Callable):
            return f

        return _decorator

    def run(self) -> None:
        raise RuntimeError("FastMCP not available; install '.[mcp]' to run this server")


kg_mcp = FastMCP("Grounding & KG Server") if _FASTMCP_AVAILABLE else _StubMCP("Grounding & KG Server")


def _open_store():
    # Default ephemeral store; production setups should wire a persistent path.
    try:
        from kg.store import KGStore  # type: ignore

        return KGStore()
    except Exception:  # pragma: no cover
        return None


def _kg_query_impl(tenant: str, entity: str, depth: int = 1) -> dict:
    """Return a small subgraph around the given entity name.

    Output shape: { nodes: [{id,type,name}], edges: [{src,dst,type}] }
    """

    store = _open_store()
    if store is None:
        return {"nodes": [], "edges": [], "error": "kg_store_unavailable"}
    try:
        nodes = store.query_nodes(tenant, type="entity", name=str(entity))
        if not nodes:
            return {"nodes": [], "edges": []}
        root = nodes[0]
        # Collect neighbor ids up to depth
        neighbor_ids = set(store.neighbors(int(root.id or 0), max(0, int(depth))))
        include_ids = {int(root.id or 0)} | {int(x) for x in neighbor_ids}
        # Build node list
        out_nodes: list[dict[str, Any]] = []
        for nid in include_ids:
            n = store.get_node(nid)
            if n is None:
                continue
            out_nodes.append({"id": int(n.id or 0), "type": n.type, "name": n.name})
        # Build edges: gather direct edges from each included src
        out_edges: list[dict[str, Any]] = []
        for src in list(include_ids):
            for e in store.query_edges(src_id=src):
                if (e.dst_id in include_ids) and len(out_edges) < 200:
                    out_edges.append({"src": int(e.src_id), "dst": int(e.dst_id), "type": e.type})
        return {"nodes": out_nodes[:200], "edges": out_edges[:400]}
    except Exception as exc:
        return {"nodes": [], "edges": [], "error": str(exc)}


def _kg_timeline_impl(tenant: str, entity: str) -> dict:
    """Return timeline events for an entity (best-effort; may be empty)."""

    store = _open_store()
    if store is None:
        return {"events": [], "error": "kg_store_unavailable"}
    try:
        from kg.reasoner import timeline  # type: ignore

        events = timeline(store, entity_name=str(entity), tenant=str(tenant))
        out = [{"node_id": int(e.node_id), "name": e.name, "timestamp": float(e.timestamp)} for e in events]
        return {"events": out[:200]}
    except Exception as exc:
        return {"events": [], "error": str(exc)}


# Plain callables for direct imports
def kg_query(tenant: str, entity: str, depth: int = 1) -> dict:
    return _kg_query_impl(tenant, entity, depth)


def kg_timeline(tenant: str, entity: str) -> dict:
    return _kg_timeline_impl(tenant, entity)


# MCP-decorated wrappers with distinct names
@kg_mcp.tool
def kg_query_tool(tenant: str, entity: str, depth: int = 1) -> dict:  # pragma: no cover
    return _kg_query_impl(tenant, entity, depth)


@kg_mcp.tool
def kg_timeline_tool(tenant: str, entity: str) -> dict:  # pragma: no cover
    return _kg_timeline_impl(tenant, entity)


@kg_mcp.resource("policy://{key}")
def policy_resource(key: str) -> Any:
    """Return subset of config/policy.yaml by key, or full file when key == 'full'."""

    try:
        import yaml  # type: ignore

        with open("config/policy.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if key == "full":
            return data
        if key in data:
            return data.get(key)
        return {"error": f"unknown_key:{key}"}
    except Exception as exc:
        return {"error": str(exc)}


@kg_mcp.tool
def policy_keys_tool() -> dict:  # pragma: no cover - MCP wrapper
    """List top-level keys from config/policy.yaml for quick discovery."""

    try:
        import yaml  # type: ignore

        with open("config/policy.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        keys = sorted([str(k) for k in data]) if isinstance(data, dict) else []
        return {"keys": keys}
    except Exception as exc:
        return {"keys": [], "error": str(exc)}


# Plain callable for tests
def policy_keys() -> dict:
    try:
        import yaml  # type: ignore

        with open("config/policy.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        keys = sorted([str(k) for k in data]) if isinstance(data, dict) else []
        return {"keys": keys}
    except Exception as exc:
        return {"keys": [], "error": str(exc)}


@kg_mcp.resource("grounding://profiles")
def grounding_profiles() -> Any:
    """Return config/grounding.yaml contents."""

    try:
        import yaml  # type: ignore

        with open("config/grounding.yaml", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:
        return {"error": str(exc)}


__all__ = [
    "grounding_profiles",
    "kg_mcp",
    "kg_query",
    "kg_query_tool",
    "kg_timeline",
    "kg_timeline_tool",
    "policy_keys",
    "policy_keys_tool",
    "policy_resource",
]
