"""HTTP configuration and constants.

Contains timeout resolution and shared constants. Pulled from the legacy
``core.http_utils`` module.
"""

from __future__ import annotations

import os
from typing import Any

# Import secure config for centralized settings
_config: Any | None = None
try:
    from core.secure_config import get_config

    _config = get_config()
except Exception:  # pragma: no cover - fallback for import cycles in init
    _config = None


def get_request_timeout() -> int:
    """Resolve HTTP request timeout with precedence.

    1) Environment variable ``HTTP_TIMEOUT``
    2) Secure config ``http_timeout``
    3) Default 15 seconds
    """
    raw = os.getenv("HTTP_TIMEOUT")
    if raw is not None and str(raw).strip() != "":
        try:
            return int(raw)
        except ValueError:
            ...
    if _config and getattr(_config, "http_timeout", None):
        try:
            return int(_config.http_timeout)
        except Exception:
            ...
    return 15


# Exported constants
REQUEST_TIMEOUT_SECONDS = get_request_timeout()
HTTP_SUCCESS_NO_CONTENT = 204
HTTP_RATE_LIMITED = 429
DEFAULT_RATE_LIMIT_RETRY = 60
DEFAULT_HTTP_RETRY_ATTEMPTS = 3

__all__ = [
    "REQUEST_TIMEOUT_SECONDS",
    "get_request_timeout",
    "HTTP_SUCCESS_NO_CONTENT",
    "HTTP_RATE_LIMITED",
    "DEFAULT_RATE_LIMIT_RETRY",
    "DEFAULT_HTTP_RETRY_ATTEMPTS",
]
