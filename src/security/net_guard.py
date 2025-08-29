"""Utilities to guard against unsafe network requests.

The helpers here perform lightweight URL validation to reduce the risk of
server-side request forgery (SSRF). Only basic checks are performed; callers
should layer additional validation as needed for their context.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


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
    return list({info[4][0] for info in infos})


def _is_private(host: str) -> bool:
    """Return ``True`` if ``host`` resolves to any non-public IP."""
    try:
        ips = [ipaddress.ip_address(host)]
    except ValueError:
        resolved = _resolve_host(host)
        if not resolved:
            return True
        ips = [ipaddress.ip_address(ip) for ip in resolved]
    for ip in ips:
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_multicast:
            return True
    return False


def is_safe_url(url: str, allowed_schemes: set[str] | None = None) -> bool:
    """Return True if ``url`` uses a public host and allowed scheme."""
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
    if _is_private(host):
        return False
    return True
