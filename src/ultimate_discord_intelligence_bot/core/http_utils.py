"""Compatibility shim to expose platform.http under the package namespace.

Tests import `ultimate_discord_intelligence_bot.core.http_utils`; the actual
implementation lives in `platform/http/`. This module re-exports
the public API for test and runtime compatibility.
"""

from __future__ import annotations

from platform.http.http_utils import (
    cached_get,
    resilient_delete,
    resilient_get,
    resilient_get_result,
    resilient_post,
    resilient_post_result,
    retrying_delete,
    retrying_get,
    retrying_post,
)


__all__ = [
    "cached_get",
    "resilient_delete",
    "resilient_get",
    "resilient_get_result",
    "resilient_post",
    "resilient_post_result",
    "retrying_delete",
    "retrying_get",
    "retrying_post",
]
