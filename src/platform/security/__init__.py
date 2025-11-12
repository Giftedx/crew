"""Security utilities for the Crew repository.

This package exposes lightweight, import-safe symbols by default. Heavy or
optional dependencies (e.g., content moderation backends) are imported lazily
or guarded so that unrelated functionality (like logging or metrics) can run in
minimal environments used by tests.
"""

from __future__ import annotations

from typing import Optional


try:  # Prefer to expose Moderation if available, but don't hard fail at import time
    from .moderation import Moderation  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - optional dependency path
    Moderation = None  # type: ignore[assignment]

from .net_guard import is_safe_url
from .rate_limit import TokenBucket
from .rbac import RBAC
from .secrets import get_secret, rotate_secret
from .signing import (
    build_signature_headers,
    sign_message,
    verify_signature,
    verify_signature_headers,
)
from .validate import (
    validate_filename,
    validate_mime,
    validate_path,
    validate_url,
)


__all__ = [
    "RBAC",
    "TokenBucket",
    "build_signature_headers",
    "get_secret",
    "is_safe_url",
    "rotate_secret",
    "sign_message",
    "validate_filename",
    "validate_mime",
    "validate_path",
    "validate_url",
    "verify_signature",
    "verify_signature_headers",
]

# Only include Moderation in __all__ when available
if isinstance(Moderation, type):  # pragma: no cover - import-time condition
    __all__.append("Moderation")
