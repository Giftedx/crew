"""Tests for StepResult-aware HTTP wrappers."""

from __future__ import annotations

import pytest

from platform.core.step_result import ErrorCategory
from platform.http.step_result_wrappers import resilient_get_result, resilient_post_result


class MockResponse:
    """Mock HTTP response."""

    def __init__(self, status_code: int, text: str = "", json_data: dict | None = None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data
        self.headers = {}

    def json(self):
        if self._json_data is not None:
            return self._json_data
        raise ValueError("No JSON")

    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            raise Exception(f"HTTP {self.status_code}")


def test_resilient_get_result_success_json():
    """Test successful GET with JSON response."""

    def mock_get(*args, **kwargs):
        return MockResponse(200, json_data={"result": "success"})

    result = resilient_get_result(
        "https://example.com/api",
        request_fn=mock_get,
    )

    assert result.success
    assert result["response"] == {"result": "success"}
    assert result["status_code"] == 200
    assert result["method"] == "GET"


def test_resilient_get_result_success_text():
    """Test successful GET with text response."""

    def mock_get(*args, **kwargs):
        return MockResponse(200, text="Hello World")

    result = resilient_get_result(
        "https://example.com/api",
        request_fn=mock_get,
    )

    assert result.success
    assert result["response"] == "Hello World"
    assert result["status_code"] == 200


def test_resilient_post_result_success():
    """Test successful POST."""

    def mock_post(*args, **kwargs):
        return MockResponse(201, json_data={"id": 123})

    result = resilient_post_result(
        "https://example.com/api",
        json_payload={"data": "test"},
        request_fn=mock_post,
    )

    assert result.success
    assert result["response"] == {"id": 123}
    assert result["status_code"] == 201
    assert result["method"] == "POST"


def test_resilient_get_result_404():
    """Test 404 Not Found error."""

    def mock_get(*args, **kwargs):
        return MockResponse(404, text="Not Found")

    result = resilient_get_result(
        "https://example.com/api/missing",
        request_fn=mock_get,
    )

    assert not result.success
    assert result.error_category == ErrorCategory.NOT_FOUND
    assert result["status_code"] == 404
    assert not result.retryable


def test_resilient_get_result_401():
    """Test 401 Unauthorized error."""

    def mock_get(*args, **kwargs):
        return MockResponse(401, text="Unauthorized")

    result = resilient_get_result(
        "https://example.com/api",
        request_fn=mock_get,
    )

    assert not result.success
    assert result.error_category == ErrorCategory.AUTHENTICATION
    assert result["status_code"] == 401
    assert not result.retryable


def test_resilient_get_result_429():
    """Test 429 Rate Limit error."""

    def mock_get(*args, **kwargs):
        return MockResponse(429, text="Too Many Requests")

    result = resilient_get_result(
        "https://example.com/api",
        request_fn=mock_get,
    )

    assert not result.success
    assert result.error_category == ErrorCategory.RATE_LIMIT
    assert result["status_code"] == 429
    assert result.retryable  # Rate limits should be retryable


def test_resilient_get_result_503():
    """Test 503 Service Unavailable error."""

    def mock_get(*args, **kwargs):
        return MockResponse(503, text="Service Unavailable")

    result = resilient_get_result(
        "https://example.com/api",
        request_fn=mock_get,
    )

    assert not result.success
    assert result.error_category == ErrorCategory.SERVICE_UNAVAILABLE
    assert result["status_code"] == 503
    assert result.retryable  # 5xx should be retryable


def test_resilient_get_result_timeout_exception():
    """Test timeout exception handling."""

    def mock_get(*args, **kwargs):
        raise TimeoutError("Request timed out")

    result = resilient_get_result(
        "https://example.com/api",
        request_fn=mock_get,
    )

    assert not result.success
    assert result.error_category == ErrorCategory.TIMEOUT
    assert result.retryable
    assert "timed out" in result.error.lower()


def test_resilient_post_result_connection_error():
    """Test connection error handling."""

    def mock_post(*args, **kwargs):
        raise ConnectionError("Network unreachable")

    result = resilient_post_result(
        "https://example.com/api",
        json_payload={"test": "data"},
        request_fn=mock_post,
    )

    assert not result.success
    assert result.error_category == ErrorCategory.NETWORK
    assert result.retryable
    assert "network" in result.error.lower()


def test_resilient_get_result_with_params():
    """Test GET with query parameters."""

    captured_args = {}

    def mock_get(*args, **kwargs):
        captured_args.update(kwargs)
        return MockResponse(200, json_data={"ok": True})

    result = resilient_get_result(
        "https://example.com/api",
        params={"key": "value"},
        request_fn=mock_get,
    )

    assert result.success
    assert captured_args.get("params") == {"key": "value"}


def test_resilient_post_result_with_headers():
    """Test POST with custom headers."""

    captured_args = {}

    def mock_post(*args, **kwargs):
        captured_args.update(kwargs)
        return MockResponse(200, json_data={"ok": True})

    result = resilient_post_result(
        "https://example.com/api",
        headers={"Authorization": "Bearer token"},
        request_fn=mock_post,
    )

    assert result.success
    assert captured_args.get("headers") == {"Authorization": "Bearer token"}


def test_resilient_get_result_500_error():
    """Test 500 Internal Server Error."""

    def mock_get(*args, **kwargs):
        return MockResponse(500, text="Internal Server Error")

    result = resilient_get_result(
        "https://example.com/api",
        request_fn=mock_get,
    )

    assert not result.success
    assert result.error_category == ErrorCategory.SERVICE_UNAVAILABLE
    assert result["status_code"] == 500
    assert result.retryable
