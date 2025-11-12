"""Integration tests for HTTP facade retry, circuit breaker, and backoff behavior.

These tests verify end-to-end behavior under various failure scenarios including:
- Network timeouts and connection errors
- Rate limiting (429) with retry-after headers
- Transient server errors (500, 502, 503, 504)
- Circuit breaker state transitions
- Exponential backoff timing
"""

from __future__ import annotations

import time
from platform.http import http_utils
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
import requests


if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def mock_session() -> Generator[Mock, None, None]:
    """Provide a mocked requests session."""
    with patch("requests.Session") as mock:
        yield mock.return_value


class TestHTTPRetryBehavior:
    """Test retry behavior under various failure conditions."""

    def test_retry_on_connection_error(self, mock_session: Mock) -> None:
        """Verify retry on connection errors with exponential backoff."""
        mock_session.get.side_effect = [
            requests.exceptions.ConnectionError("Connection refused"),
            requests.exceptions.ConnectionError("Connection refused"),
            Mock(status_code=200, text="success"),
        ]

        start = time.time()
        response = http_utils.retrying_get("https://example.com", max_retries=3)
        elapsed = time.time() - start

        assert response is not None
        assert response.status_code == 200
        assert mock_session.get.call_count == 3
        # Verify exponential backoff (should take at least base_delay * 2)
        assert elapsed >= 0.3  # Base backoff for connection errors

    def test_retry_on_500_series_errors(self, mock_session: Mock) -> None:
        """Verify retry on transient server errors."""
        mock_session.post.side_effect = [
            Mock(status_code=502, text="Bad Gateway"),
            Mock(status_code=503, text="Service Unavailable"),
            Mock(status_code=200, json=lambda: {"success": True}),
        ]

        response = http_utils.retrying_post(
            "https://api.example.com/endpoint",
            json_payload={"test": "data"},
            max_retries=3,
        )

        assert response is not None
        assert response.status_code == 200
        assert mock_session.post.call_count == 3

    def test_no_retry_on_400_series_errors(self, mock_session: Mock) -> None:
        """Verify no retry on client errors (except 429)."""
        mock_session.get.return_value = Mock(status_code=404, text="Not Found")

        response = http_utils.retrying_get("https://example.com/missing", max_retries=3)

        assert response is not None
        assert response.status_code == 404
        assert mock_session.get.call_count == 1  # No retries

    def test_retry_with_rate_limit_backoff(self, mock_session: Mock) -> None:
        """Verify respect for rate limit headers."""
        mock_session.get.side_effect = [
            Mock(status_code=429, headers={"Retry-After": "2"}, text="Rate limited"),
            Mock(status_code=200, text="success"),
        ]

        start = time.time()
        response = http_utils.retrying_get("https://api.example.com/endpoint")
        elapsed = time.time() - start

        assert response is not None
        assert response.status_code == 200
        assert mock_session.get.call_count == 2
        # Verify backoff respected retry-after header
        assert elapsed >= 2.0

    def test_max_retries_exhausted(self, mock_session: Mock) -> None:
        """Verify behavior when max retries are exhausted."""
        mock_session.post.side_effect = requests.exceptions.Timeout("Request timeout")

        response = http_utils.retrying_post(
            "https://slow.example.com",
            json_payload={"data": "test"},
            max_retries=2,
        )

        assert response is None
        assert mock_session.post.call_count == 3  # Initial + 2 retries


class TestCircuitBreakerIntegration:
    """Test circuit breaker state transitions and behavior."""

    def test_circuit_breaker_opens_after_threshold(self) -> None:
        """Verify circuit breaker opens after consecutive failures."""
        with patch("requests.Session") as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")

            # Make multiple failing requests
            for _ in range(5):
                response = http_utils.resilient_get("https://failing.example.com")
                assert response is None

            # Circuit should now be open - subsequent requests fail fast
            start = time.time()
            response = http_utils.resilient_get("https://failing.example.com")
            elapsed = time.time() - start

            assert response is None
            # Should fail fast (< 100ms) without actual request
            assert elapsed < 0.1

    def test_circuit_breaker_half_open_recovery(self) -> None:
        """Verify circuit breaker transitions to half-open and recovers."""
        with patch("requests.Session") as mock_session_class:
            mock_session = mock_session_class.return_value

            # Initial failures to open circuit
            mock_session.get.side_effect = [
                requests.exceptions.ConnectionError("Failed"),
            ] * 5

            for _ in range(5):
                http_utils.resilient_get("https://recovering.example.com")

            # Wait for circuit to enter half-open state
            time.sleep(5)

            # Next request should succeed and close circuit
            mock_session.get.side_effect = None
            mock_session.get.return_value = Mock(status_code=200, text="recovered")

            response = http_utils.resilient_get("https://recovering.example.com")
            assert response is not None
            assert response.status_code == 200


class TestBackoffTiming:
    """Test exponential backoff timing behavior."""

    def test_exponential_backoff_progression(self, mock_session: Mock) -> None:
        """Verify backoff delays increase exponentially."""
        mock_session.get.side_effect = [
            Mock(status_code=503),
            Mock(status_code=503),
            Mock(status_code=503),
            Mock(status_code=200, text="success"),
        ]

        start = time.time()
        response = http_utils.retrying_get(
            "https://example.com",
            max_retries=3,
            base_delay=0.5,
        )
        elapsed = time.time() - start

        assert response is not None
        assert response.status_code == 200
        # Verify cumulative backoff: 0.5 + 1.0 + 2.0 = 3.5s minimum
        assert elapsed >= 3.5

    def test_connection_error_special_backoff(self, mock_session: Mock) -> None:
        """Verify connection errors use scaled backoff."""
        mock_session.post.side_effect = [
            requests.exceptions.ConnectionError("Connection refused"),
            Mock(status_code=200, json=lambda: {"success": True}),
        ]

        start = time.time()
        response = http_utils.retrying_post(
            "https://example.com",
            json_payload={"test": "data"},
            base_delay=0.5,
        )
        elapsed = time.time() - start

        assert response is not None
        # Connection errors use 3x backoff multiplier
        assert elapsed >= 1.5  # 0.5 * 3


class TestCacheInteraction:
    """Test interaction between retry logic and caching."""

    def test_cached_get_skips_retry_on_cache_hit(self) -> None:
        """Verify cache hits bypass retry logic."""
        with patch("core.http_utils.cached_get") as mock_cached:
            mock_cached.return_value = Mock(status_code=200, text="cached")

            start = time.time()
            response = http_utils.cached_get("https://example.com/cached")
            elapsed = time.time() - start

            assert response is not None
            assert elapsed < 0.1  # Should be nearly instantaneous
            mock_cached.assert_called_once()

    def test_failed_requests_not_cached(self, mock_session: Mock) -> None:
        """Verify failed responses are not cached."""
        mock_session.get.side_effect = [
            Mock(status_code=500, text="error"),
            Mock(status_code=200, text="success"),
        ]

        # First request fails
        response1 = http_utils.retrying_get("https://example.com/endpoint")
        assert response1 is None or response1.status_code >= 500

        # Second request should make actual HTTP call (not cached)
        response2 = http_utils.retrying_get("https://example.com/endpoint")
        assert response2 is not None
        assert response2.status_code == 200
        assert mock_session.get.call_count >= 2


@pytest.mark.slow
class TestRealWorldScenarios:
    """Test realistic failure scenarios with timing."""

    def test_cascading_failure_recovery(self, mock_session: Mock) -> None:
        """Verify recovery from cascading failures across multiple endpoints."""
        # Simulate dependent service calls with varying failure modes
        mock_session.get.side_effect = [
            # First endpoint: timeout then success
            requests.exceptions.Timeout("Timeout"),
            Mock(status_code=200, json=lambda: {"token": "abc123"}),
            # Second endpoint: rate limit then success
            Mock(status_code=429, headers={"Retry-After": "1"}),
            Mock(status_code=200, json=lambda: {"data": "result"}),
        ]

        # Call chain
        token_response = http_utils.retrying_get("https://auth.example.com/token")
        assert token_response is not None

        data_response = http_utils.retrying_get("https://api.example.com/data")
        assert data_response is not None

        assert mock_session.get.call_count == 4

    def test_partial_failure_graceful_degradation(self, mock_session: Mock) -> None:
        """Verify graceful degradation when some requests fail."""
        mock_session.get.side_effect = [
            Mock(status_code=200, json=lambda: {"service": "A", "status": "ok"}),
            requests.exceptions.ConnectionError("Service B unavailable"),
            Mock(status_code=200, json=lambda: {"service": "C", "status": "ok"}),
        ]

        results = []
        for endpoint in ["service-a", "service-b", "service-c"]:
            response = http_utils.resilient_get(f"https://api.example.com/{endpoint}")
            results.append(response)

        # Verify partial success
        assert results[0] is not None
        assert results[1] is None  # Failed service
        assert results[2] is not None
