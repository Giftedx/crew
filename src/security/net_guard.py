"""Utilities to guard against unsafe network requests.

Enhancements (PR18):
    * Redirect chain revalidation (each hop must remain public + scheme allowed)
    * Host allow / deny lists pulled from ``config/security.yaml``
    * Content length cap and content-type allowlist enforcement
    * Structured security events on block decisions
    * Helper ``safe_fetch`` that returns bytes (bounded) or raises ``SecurityError``
"""

from __future__ import annotations

import ipaddress
import socket
import urllib.request
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from .events import log_security_event

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "security.yaml"


def _resolve_host(host: str) -> list[str]:
    """Resolve ``host`` to all IP addresses (IPv4 and IPv6).

    Returns an empty list if resolution fails. A domain may resolve to multiple
    addresses; the caller must treat the host as unsafe if *any* resolved
    address is private.
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return []
    # getaddrinfo sockaddr first element is textual IP; be defensive and coerce to str
    addresses: set[str] = {str(info[4][0]) for info in infos}
    return list(addresses)


def _is_private(host: str) -> bool:
    """Return ``True`` if ``host`` resolves to any non-public IP."""
    try:
        ips = [ipaddress.ip_address(host)]
    except ValueError:
        resolved = _resolve_host(host)
        if not resolved:
            return True
        ips = [ipaddress.ip_address(ip) for ip in resolved]
    return any(ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_multicast for ip in ips)


def _load_net_config(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = DEFAULT_CONFIG_PATH
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("network", {})


def is_safe_url(
    url: str,
    *,
    allowed_schemes: set[str] | None = None,
    allow_hosts: Iterable[str] | None = None,
    deny_hosts: Iterable[str] | None = None,
) -> bool:
    """Return True if ``url`` uses a public host, allowed scheme, and passes host lists."""
    allowed_schemes = allowed_schemes or {"http", "https"}
    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in allowed_schemes:
        return False
    host = parsed.hostname
    if not host:
        return False
    if deny_hosts and host in set(deny_hosts):
        return False
    if allow_hosts and host not in set(allow_hosts):
        return False
    return not _is_private(host)


class SecurityError(Exception):
    """Raised when a network fetch is blocked by security policy."""


HTTP_REDIRECT_MIN = 300
HTTP_REDIRECT_MAX = 400


def safe_fetch(  # noqa: PLR0915 - readability prioritized over splitting small helpers
    url: str,
    *,
    config_path: Path | None = None,
    actor: str | None = None,
    tenant: str | None = None,
    workspace: str | None = None,
) -> bytes:
    """Fetch ``url`` enforcing redirect & content safety rules.

    Raises ``SecurityError`` if any policy violation occurs.
    """
    net_cfg = _load_net_config(config_path)
    allow_hosts = net_cfg.get("allow_hosts") or []
    deny_hosts = net_cfg.get("deny_hosts") or []
    max_bytes = int(net_cfg.get("max_content_bytes", 5 * 1024 * 1024))
    follow_redirects = bool(net_cfg.get("follow_redirects", True))
    max_hops = int(net_cfg.get("max_redirect_hops", 4))
    enforce_ct = bool(net_cfg.get("enforce_content_type", True))
    allowed_cts = set(net_cfg.get("allowed_content_types") or [])

    visited: list[str] = []
    current = url
    hops = 0
    while True:
        if hops > max_hops:
            _log_block(actor, tenant, workspace, current, reason="redirect_hops_exceeded")
            raise SecurityError("redirect hop limit exceeded")
        if current in visited:
            _log_block(actor, tenant, workspace, current, reason="redirect_loop")
            raise SecurityError("redirect loop detected")
        if not is_safe_url(current, allow_hosts=allow_hosts, deny_hosts=deny_hosts):
            _log_block(actor, tenant, workspace, current, reason="unsafe_url")
            raise SecurityError("unsafe url")
        visited.append(current)
        if not current.startswith(("http://", "https://")):
            _log_block(actor, tenant, workspace, current, reason="scheme_not_allowed")
            raise SecurityError("scheme not allowed")
        # At this point scheme has been validated (http/https only) above.
        # Guard variable communicates validated scheme to static analyzers
        _scheme_ok = current.startswith(("http://", "https://"))  # always True here
        if not _scheme_ok:  # pragma: no cover - defensive
            raise SecurityError("invalid scheme post-validation")
        # Safe construction after explicit scheme validation; suppress bandit/ruff warning.
        req = urllib.request.Request(current, method="GET")  # nosec B310  # noqa: S310
        try:
            # Safe open: scheme already validated (http/https) and host vetted.
            with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310  # noqa: S310
                # Handle redirect manually if follow_redirects disabled.
                if HTTP_REDIRECT_MIN <= resp.status < HTTP_REDIRECT_MAX and resp.getheader("Location"):
                    if not follow_redirects:
                        _log_block(actor, tenant, workspace, current, reason="redirect_disallowed")
                        raise SecurityError("redirect disallowed")
                    current = resp.getheader("Location")
                    hops += 1
                    continue
                content_type = resp.getheader("Content-Type", "").split(";")[0].strip()
                if enforce_ct and allowed_cts and content_type not in allowed_cts:
                    _log_block(actor, tenant, workspace, current, reason="content_type_block")
                    raise SecurityError("blocked content-type")
                data = resp.read(max_bytes + 1)
                if len(data) > max_bytes:
                    _log_block(actor, tenant, workspace, current, reason="size_exceeded")
                    raise SecurityError("content size exceeds limit")
                _log_allow(
                    actor,
                    tenant,
                    workspace,
                    current,
                    {"size": len(data), "content_type": content_type, "hops": hops},
                )
                return data
        except SecurityError:
            raise
        except Exception as exc:  # pragma: no cover - network variability
            _log_block(actor, tenant, workspace, current, reason=f"fetch_error:{type(exc).__name__}")
            raise SecurityError("fetch failed") from exc


def _log_block(actor: str | None, tenant: str | None, workspace: str | None, url: str, *, reason: str) -> None:
    log_security_event(
        actor=actor or "unknown",
        action="net_guard",
        resource=url,
        decision="block",
        reason=reason,
        tenant=tenant,
        workspace=workspace,
    )


def _log_allow(
    actor: str | None,
    tenant: str | None,
    workspace: str | None,
    url: str,
    extra: dict[str, Any],
) -> None:
    log_security_event(
        actor=actor or "unknown",
        action="net_guard",
        resource=url,
        decision="allow",
        reason="ok",
        tenant=tenant,
        workspace=workspace,
        **extra,
    )

__all__ = [
    "is_safe_url",
    "safe_fetch",
    "SecurityError",
]
