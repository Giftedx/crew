"""Validation helpers for HTTP operations."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


def validate_public_https_url(url: str) -> str:
    """Validate HTTPS URL that is not private/loopback.

    Accepts hostnames or globally routable IPs.
    """
    if not url or not isinstance(url, str) or not url.strip():
        raise ValueError(f"URL cannot be empty or None (got: '{url}')")

    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"URL must use https (got: '{parsed.scheme}' for URL: '{url}')")
    if not parsed.hostname:
        raise ValueError("URL must include a host")
    host = parsed.hostname
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return url
    if not ip.is_global:
        raise ValueError("IP must be globally routable")
    return url


__all__ = ["validate_public_https_url"]
