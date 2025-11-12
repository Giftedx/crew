"""Compatibility shim for core.http_utils.

Re-exports from platform.http for backward compatibility.
"""

from platform.http.http_utils import (
    resilient_get,
    resilient_post,
    retrying_get,
    retrying_post,
)


__all__ = ["resilient_get", "resilient_post", "retrying_get", "retrying_post"]
