"""StepResult-aware HTTP wrappers for enhanced error handling and observability.

Provides alternative HTTP functions that return StepResult instead of raw Response
objects, enabling structured error handling, retry logic, and observability integration.
"""

from __future__ import annotations

import logging
from platform.core.step_result import ErrorCategory, StepResult
from typing import TYPE_CHECKING, Any

from .requests_wrappers import (
    ResponseLike,
)
from .requests_wrappers import (
    resilient_get as _resilient_get,
)
from .requests_wrappers import (
    resilient_post as _resilient_post,
)


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


logger = logging.getLogger(__name__)


def _response_to_step_result(
    response: ResponseLike | Exception,
    url: str,
    method: str,
) -> StepResult:
    """Convert HTTP response or exception to StepResult.

    Args:
        response: Response object or exception
        url: Request URL
        method: HTTP method (GET, POST, etc.)

    Returns:
        StepResult with response data or error information
    """
    if isinstance(response, Exception):
        error_msg = str(response)
        error_lower = error_msg.lower()

        # Categorize exception
        if "timeout" in error_lower or "timed out" in error_lower:
            category = ErrorCategory.TIMEOUT
        elif any(word in error_lower for word in ("connection", "network", "ssl", "certificate")):
            category = ErrorCategory.NETWORK
        else:
            category = ErrorCategory.NETWORK

        return StepResult.fail(
            error=f"{method} {url} failed: {error_msg}",
            error_category=category,
            retryable=True,
            url=url,
            method=method,
        )

    try:
        status_code = response.status_code

        # Success range (2xx)
        if 200 <= status_code < 300:
            # Try to parse JSON
            try:
                data = response.json()
            except Exception:
                data = response.text

            return StepResult.ok(
                response=data,
                status_code=status_code,
                url=url,
                method=method,
                headers=dict(response.__dict__.get("headers", {})),
            )

        # Client errors (4xx)
        if 400 <= status_code < 500:
            if status_code == 404:
                category = ErrorCategory.NOT_FOUND
            elif status_code == 401:
                category = ErrorCategory.AUTHENTICATION
            elif status_code == 403:
                category = ErrorCategory.AUTHORIZATION
            elif status_code == 429:
                category = ErrorCategory.RATE_LIMIT
            else:
                category = ErrorCategory.VALIDATION

            return StepResult.fail(
                error=f"{method} {url} returned {status_code}: {response.text[:200]}",
                error_category=category,
                retryable=(status_code == 429),
                status_code=status_code,
                url=url,
                method=method,
                response_text=response.text[:500],
            )

        # Server errors (5xx)
        if 500 <= status_code < 600:
            if status_code == 503:
                category = ErrorCategory.SERVICE_UNAVAILABLE
            elif status_code == 504:
                category = ErrorCategory.TIMEOUT
            else:
                category = ErrorCategory.SERVICE_UNAVAILABLE

            return StepResult.fail(
                error=f"{method} {url} server error {status_code}",
                error_category=category,
                retryable=True,
                status_code=status_code,
                url=url,
                method=method,
                response_text=response.text[:500],
            )

        # Other status codes
        return StepResult.fail(
            error=f"{method} {url} unexpected status {status_code}",
            error_category=ErrorCategory.NETWORK,
            retryable=False,
            status_code=status_code,
            url=url,
            method=method,
        )

    except Exception as e:
        return StepResult.fail(
            error=f"Failed to process {method} {url} response: {e}",
            error_category=ErrorCategory.PROCESSING,
            retryable=False,
            url=url,
            method=method,
            exception=str(e),
        )


def resilient_post_result(
    url: str,
    *,
    json_payload: Any | None = None,
    headers: Mapping[str, str] | None = None,
    files: Mapping[str, Any] | None = None,
    timeout_seconds: int | None = None,
    allow_legacy_timeout_fallback: bool = True,
    request_fn: Callable[..., Any] | None = None,
) -> StepResult:
    """POST request returning StepResult for structured error handling.

    Args:
        url: Target URL
        json_payload: JSON body
        headers: HTTP headers
        files: File attachments
        timeout_seconds: Request timeout
        allow_legacy_timeout_fallback: Fallback for timeout parameter
        request_fn: Optional custom request function

    Returns:
        StepResult with response data or error information
    """
    try:
        response = _resilient_post(
            url,
            json_payload=json_payload,
            headers=headers,
            files=files,
            timeout_seconds=timeout_seconds,
            allow_legacy_timeout_fallback=allow_legacy_timeout_fallback,
            request_fn=request_fn,
        )
        return _response_to_step_result(response, url, "POST")
    except Exception as e:
        return _response_to_step_result(e, url, "POST")


def resilient_get_result(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: int | None = None,
    allow_legacy_timeout_fallback: bool = True,
    request_fn: Callable[..., Any] | None = None,
    stream: bool | None = None,
) -> StepResult:
    """GET request returning StepResult for structured error handling.

    Args:
        url: Target URL
        params: Query parameters
        headers: HTTP headers
        timeout_seconds: Request timeout
        allow_legacy_timeout_fallback: Fallback for timeout parameter
        request_fn: Optional custom request function
        stream: Enable streaming response

    Returns:
        StepResult with response data or error information
    """
    try:
        response = _resilient_get(
            url,
            params=params,
            headers=headers,
            timeout_seconds=timeout_seconds,
            allow_legacy_timeout_fallback=allow_legacy_timeout_fallback,
            request_fn=request_fn,
            stream=stream,
        )
        return _response_to_step_result(response, url, "GET")
    except Exception as e:
        return _response_to_step_result(e, url, "GET")


__all__ = [
    "resilient_get_result",
    "resilient_post_result",
]
