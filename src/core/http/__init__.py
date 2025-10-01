"""HTTP utilities package.

This package contains modularized components previously in ``core.http_utils``.

Public API is re-exported here and from ``core.http_utils`` for backward
compatibility. New code should prefer ``core.http`` imports.
"""
# isort: skip_file

from .cache import cached_get
from .config import (
    DEFAULT_HTTP_RETRY_ATTEMPTS,
    DEFAULT_RATE_LIMIT_RETRY,
    HTTP_RATE_LIMITED,
    HTTP_SUCCESS_NO_CONTENT,
    REQUEST_TIMEOUT_SECONDS,
    get_request_timeout,
)
from .requests_wrappers import resilient_get, resilient_post
from .retry import (
    get_circuit_breaker_status,
    http_request_with_retry,
    is_circuit_breaker_enabled,
    is_retry_enabled,
    reset_circuit_breakers,
    retrying_get,
    retrying_post,
)
from .retry_config import reset_retry_config_cache, resolve_retry_attempts
from .validators import validate_public_https_url

__all__ = [
    "REQUEST_TIMEOUT_SECONDS",
    "get_request_timeout",
    "HTTP_SUCCESS_NO_CONTENT",
    "HTTP_RATE_LIMITED",
    "DEFAULT_RATE_LIMIT_RETRY",
    "DEFAULT_HTTP_RETRY_ATTEMPTS",
    "validate_public_https_url",
    "resilient_post",
    "resilient_get",
    "http_request_with_retry",
    "retrying_post",
    "retrying_get",
    "is_retry_enabled",
    "resolve_retry_attempts",
    "is_circuit_breaker_enabled",
    "get_circuit_breaker_status",
    "reset_circuit_breakers",
    "cached_get",
    "reset_retry_config_cache",
]
