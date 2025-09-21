"""FastMCP Memory server (read-only) exposing vector search and namespace info.

Tools:
- vs_search(tenant, workspace, name, query, k=5, min_score=None)
- vs_list_namespaces(tenant, workspace)
- vs_samples(tenant, workspace, name, probe="", n=3)

Resources:
- memory://{tenant}/{workspace}/{name}/stats

Implementation notes:
- Uses VectorStore with logical namespaces via VectorStore.namespace.
- Embeddings via memory.embeddings.embed.
- Avoids write operations; returns redacted/capped payloads.
"""

from __future__ import annotations

from typing import Any

try:
    from fastmcp import FastMCP  # type: ignore
except Exception as exc:  # pragma: no cover
    raise SystemExit("FastMCP is required for the memory MCP server. Install with 'pip install .[mcp]'.") from exc

# Defer memory imports to function scope to keep import ordering simple for linters.


memory_mcp = FastMCP("Memory Server")


def _ns(tenant: str, workspace: str, name: str) -> str:
    # Defensive normalization to strings
    t = str(tenant or "default")
    w = str(workspace or "main")
    n = str(name or "memory")
    # Local import to avoid import-order lint issues at module level
    from memory import vector_store

    return vector_store.VectorStore.namespace(t, w, n)


def _sanitize_hit(payload: dict[str, Any]) -> dict[str, Any]:
    # Redact heavy fields and limit text size
    out = dict(payload or {})
    text = out.get("text")
    if isinstance(text, str) and len(text) > 800:
        out["text"] = text[:800] + "…"
    # Drop known noisy keys if present
    for k in ["embedding", "raw", "full_text", "transcript"]:
        if k in out:
            out.pop(k, None)
    return out


@memory_mcp.tool
def vs_search(tenant: str, workspace: str, name: str, query: str, k: int = 5, min_score: float | None = None) -> dict:
    """Vector similarity search over a logical namespace.

    Returns: { "namespace": str, "hits": [{"score": float, "payload": dict}] }
    """

    namespace = _ns(tenant, workspace, name)
    from memory import embeddings, vector_store

    v = embeddings.embed([query])[0]
    store = vector_store.VectorStore()
    try:
        res = store.query(namespace, v, top_k=max(1, min(int(k), 50)))
    except Exception as exc:
        return {"namespace": namespace, "hits": [], "error": str(exc)}
    hits: list[dict[str, Any]] = []
    for r in res:
        score = float(getattr(r, "score", 0.0))
        if (min_score is not None) and (score < float(min_score)):
            continue
        payload = _sanitize_hit(getattr(r, "payload", {}) or {})
        hits.append({"score": score, "payload": payload})
    return {"namespace": namespace, "hits": hits}


@memory_mcp.tool
def vs_list_namespaces(tenant: str, workspace: str) -> dict:
    """List available logical memory namespaces for a tenant/workspace.

    Uses the physical naming convention (":" -> "__") to reconstruct logical names.
    Returns: { "namespaces": ["tenant:workspace:name", ...], "names": ["name", ...] }
    """

    from memory import vector_store

    store = vector_store.VectorStore()
    client = store.client
    try:
        cols = client.get_collections().collections
    except Exception as exc:
        return {"namespaces": [], "names": [], "error": str(exc)}
    prefix = f"{tenant}__{workspace}__"
    logical = []
    short_names: set[str] = set()
    for c in cols:
        pname = getattr(c, "name", "")
        if not isinstance(pname, str) or not pname.startswith(prefix):
            continue
        ns = pname.replace("__", ":")
        parts = ns.split(":", 2)
        if len(parts) == 3:
            short_names.add(parts[2])
        logical.append(ns)
    return {"namespaces": sorted(logical), "names": sorted(short_names)}


@memory_mcp.tool
def vs_samples(tenant: str, workspace: str, name: str, probe: str = "", n: int = 3) -> dict:
    """Return a small sample of payloads by querying with a probe string.

    This uses a vector query with an optional probe (empty string allowed).
    Returns: { "namespace": str, "samples": [payload, ...] }
    """

    namespace = _ns(tenant, workspace, name)
    from memory import embeddings, vector_store

    v = embeddings.embed([probe])[0]
    store = vector_store.VectorStore()
    try:
        res = store.query(namespace, v, top_k=max(1, min(int(n), 10)))
    except Exception as exc:
        return {"namespace": namespace, "samples": [], "error": str(exc)}
    samples: list[dict[str, Any]] = []
    for r in res:
        payload = _sanitize_hit(getattr(r, "payload", {}) or {})
        samples.append(payload)
    return {"namespace": namespace, "samples": samples}


@memory_mcp.resource("memory://{tenant}/{workspace}/{name}/stats")
def memory_stats(tenant: str, workspace: str, name: str) -> dict:
    """Basic collection statistics for the namespace (best-effort)."""

    ns = _ns(tenant, workspace, name)
    physical = ns.replace(":", "__")
    from memory import vector_store

    store = vector_store.VectorStore()
    client = store.client
    info: dict[str, Any] = {"namespace": ns, "collection": physical}
    try:
        c = client.get_collection(physical)
        # DummyClient returns attributes below; qdrant returns richer models
        vectors_count = getattr(c, "vectors_count", None)
        info["vectors_count"] = int(vectors_count) if vectors_count is not None else None
        cfg = getattr(c, "config", None)
        if cfg and getattr(cfg, "params", None):
            params = cfg.params
            vectors = getattr(params, "vectors", None)
            if vectors is not None:
                info["distance"] = getattr(getattr(vectors, "distance", None), "value", None)
                info["dimension"] = getattr(vectors, "size", None)
    except Exception:
        # Best-effort; missing collection or fields
        ...
    return info


__all__ = ["memory_mcp", "vs_search", "vs_list_namespaces", "vs_samples", "memory_stats"]
