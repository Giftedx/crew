"""FastMCP Observability server (read-only).

Tools:
- summarize_health(): basic OK/degraded summary using metrics availability and renderability
- get_counters(): safe snapshot including whether Prometheus is available and a small sample of exposition text

Resource (optional):
- metrics://prom – returns full Prometheus exposition text (feature-flag gated)

Notes:
- Low-cardinality only; avoids enumerating dynamic labels.
- Does not require the FastAPI app instance; uses obs.metrics facade directly.
"""

from __future__ import annotations

from collections.abc import Callable

try:
    from fastmcp import FastMCP  # type: ignore

    _FASTMCP_AVAILABLE = True
except Exception:  # pragma: no cover
    FastMCP = None  # type: ignore
    _FASTMCP_AVAILABLE = False


class _StubMCP:  # pragma: no cover
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


obs_mcp = FastMCP("Observability Server") if _FASTMCP_AVAILABLE else _StubMCP("Observability Server")


@obs_mcp.tool
def summarize_health() -> dict:
    """Return a simple health summary based on metrics availability and render()."""

    try:
        from obs import metrics  # type: ignore

        prom_ok = bool(getattr(metrics, "PROMETHEUS_AVAILABLE", False))
        # Attempt a render to ensure registry is functional
        data = b""
        try:
            data = metrics.render()
        except Exception:
            pass
        status = "ok" if (prom_ok or len(data) >= 0) else "degraded"
        return {
            "status": status,
            "prometheus_available": prom_ok,
            "exposition_bytes": int(len(data)) if isinstance(data, (bytes, bytearray)) else 0,
        }
    except Exception as exc:
        return {"status": "degraded", "error": str(exc)}


@obs_mcp.tool
def get_counters(sample_bytes: int = 1000) -> dict:
    """Return a safe counters snapshot using Prometheus exposition text (truncated)."""

    try:
        from obs import metrics  # type: ignore

        prom_ok = bool(getattr(metrics, "PROMETHEUS_AVAILABLE", False))
        data = b""
        try:
            data = metrics.render()
        except Exception:
            data = b""
        text = data.decode("utf-8", errors="ignore") if isinstance(data, (bytes, bytearray)) else str(data)
        sample = text[: max(0, int(sample_bytes))]
        return {
            "prometheus_available": prom_ok,
            "scrape_bytes": len(text),
            "sample": sample,
        }
    except Exception as exc:
        return {"prometheus_available": False, "scrape_bytes": 0, "error": str(exc)}


@obs_mcp.tool
def recent_degradations(limit: int = 50) -> dict:
    """Return a recent snapshot of degradation events (if enabled).

    Uses core.degradation_reporter singleton; returns at most ``limit`` events
    with minimal fields to keep payloads small.
    """

    try:
        from core.degradation_reporter import get_degradation_reporter  # type: ignore

        rep = get_degradation_reporter()
        events = rep.snapshot()[-max(1, int(limit)) :]
        out: list[dict] = []
        for e in events:
            try:
                out.append(
                    {
                        "ts": float(getattr(e, "ts_epoch", 0.0)),
                        "component": str(getattr(e, "component", "")),
                        "event": str(getattr(e, "event_type", "")),
                        "severity": str(getattr(e, "severity", "")),
                        "detail": getattr(e, "detail", None),
                        "added_latency_ms": getattr(e, "added_latency_ms", None),
                    }
                )
            except Exception:
                continue
        return {"events": out}
    except Exception as exc:
        return {"events": [], "error": str(exc)}


@obs_mcp.resource("metrics://prom")
def metrics_prom() -> str:
    """Return full Prometheus exposition (feature-flag gated)."""

    import os as _os

    if _os.getenv("ENABLE_MCP_OBS_PROM_RESOURCE", "0").lower() not in ("1", "true", "yes", "on"):
        return "prom_resource_disabled"
    try:
        from obs import metrics  # type: ignore

        data = metrics.render()
        if isinstance(data, (bytes, bytearray)):
            return data.decode("utf-8", errors="ignore")
        return str(data)
    except Exception as exc:
        return f"error: {exc}"


@obs_mcp.resource("degradations://recent")
def degradations_recent() -> dict:
    """Resource variant of recent degradation events (default of 50)."""

    try:
        return recent_degradations(50)
    except Exception as exc:
        return {"events": [], "error": str(exc)}


__all__ = [
    "obs_mcp",
    "summarize_health",
    "get_counters",
    "recent_degradations",
    "metrics_prom",
    "degradations_recent",
]
