"""FastMCP HTTP & Cache server (read-only, allowlisted).

Tools:
- http_get(url, params=None, use_cache=True, ttl_seconds=None, max_bytes=10000)

Resources:
- httpcfg://allowlist – current allowed hostnames

Security:
- Only HTTPS URLs allowed via core.http_utils.validate_public_https_url
- Domain must be present in MCP_HTTP_ALLOWLIST (comma-separated hostnames)
- Response text truncated to max_bytes to avoid payload blowups
"""

from __future__ import annotations

from typing import Any

try:
    from fastmcp import FastMCP  # type: ignore
except Exception as exc:  # pragma: no cover
    raise SystemExit("FastMCP is required for the HTTP MCP server. Install with 'pip install .[mcp]'.") from exc


http_mcp = FastMCP("HTTP & Cache Server")


def _allowed_hosts() -> set[str]:
    try:
        import os

        raw = os.getenv("MCP_HTTP_ALLOWLIST", "")
        if not raw.strip():
            return set()
        hosts = {h.strip().lower() for h in raw.split(",") if h.strip()}
        return {h for h in hosts if h}
    except Exception:
        return set()


def _validate_url(url: str) -> tuple[bool, str | None]:
    try:
        from core.http_utils import validate_public_https_url  # type: ignore

        validate_public_https_url(url)
        return True, None
    except Exception as exc:
        return False, str(exc)


def _hostname(url: str) -> str:
    try:
        from urllib.parse import urlparse

        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


@http_mcp.tool
def http_get(
    url: str,
    params: dict[str, Any] | None = None,
    use_cache: bool = True,
    ttl_seconds: int | None = None,
    max_bytes: int = 10000,
) -> dict:
    """Perform an allowlisted HTTPS GET; optionally use shared cache.

    Returns: {status, length, text}
    """

    ok, err = _validate_url(url)
    if not ok:
        return {"error": f"invalid_url:{err}"}
    host = _hostname(url)
    allow = _allowed_hosts()
    if host not in allow:
        return {"error": f"domain_not_allowed:{host}", "allowlist": sorted(allow)}

    try:
        if use_cache:
            from core.http_utils import cached_get as _get  # type: ignore

            resp = _get(url, params=params, ttl_seconds=ttl_seconds)
        else:
            from core.http_utils import resilient_get as _get  # type: ignore

            resp = _get(url, params=params)
        status = int(getattr(resp, "status_code", 0))
        text = str(getattr(resp, "text", ""))
        clipped = text[: max(0, int(max_bytes))]
        return {"status": status, "length": len(text), "text": clipped}
    except Exception as exc:
        return {"error": str(exc)}


@http_mcp.tool
def http_json_get(
    url: str,
    params: dict[str, Any] | None = None,
    use_cache: bool = True,
    ttl_seconds: int | None = None,
    max_bytes: int = 20000,
) -> dict:
    """Allowlisted HTTPS GET and parse JSON body (truncated before parse to avoid extreme payloads)."""

    ok, err = _validate_url(url)
    if not ok:
        return {"error": f"invalid_url:{err}"}
    host = _hostname(url)
    allow = _allowed_hosts()
    if host not in allow:
        return {"error": f"domain_not_allowed:{host}", "allowlist": sorted(allow)}

    try:
        if use_cache:
            from core.http_utils import cached_get as _get  # type: ignore

            resp = _get(url, params=params, ttl_seconds=ttl_seconds)
        else:
            from core.http_utils import resilient_get as _get  # type: ignore

            resp = _get(url, params=params)
        status = int(getattr(resp, "status_code", 0))
        text = str(getattr(resp, "text", ""))[: max(0, int(max_bytes))]
        try:
            import json as _json

            data = _json.loads(text) if text else {}
        except Exception:
            data = {"raw": text}
        return {"status": status, "data": data}
    except Exception as exc:
        return {"error": str(exc)}


@http_mcp.resource("httpcfg://allowlist")
def allowlist_resource() -> list[str]:
    return sorted(_allowed_hosts())


@http_mcp.resource("httpcfg://example-header")
def example_header() -> dict:
    """Small illustrative config snippet showing how to set an allowlist.

    Not a live config endpoint; purely an example for clients.
    """

    return {"env": {"MCP_HTTP_ALLOWLIST": "api.github.com,raw.githubusercontent.com"}}


__all__ = ["http_mcp", "http_get", "http_json_get", "allowlist_resource", "example_header"]
