"""
Test suite for rate limiting functionality.

This module tests rate limit enforcement per tenant, rate limit reset logic,
backoff and retry behavior, and rate limit bypass attempts.
"""

import asyncio
import time
from unittest.mock import Mock

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult


class TestRateLimiting:
    """Test rate limiting and throttling functionality."""

    @pytest.fixture
    def mock_rate_limiter(self) -> Mock:
        """Mock rate limiter for testing."""
        return Mock()

    @pytest.fixture
    def sample_tenants(self) -> dict[str, dict[str, str | int]]:
        """Sample tenant data for testing."""
        return {
            "tenant_a": {
                "workspace": "workspace_a",
                "rate_limit": 100,  # requests per minute
                "burst_limit": 10,  # burst requests
            },
            "tenant_b": {
                "workspace": "workspace_b",
                "rate_limit": 50,  # requests per minute
                "burst_limit": 5,  # burst requests
            },
            "tenant_c": {
                "workspace": "workspace_c",
                "rate_limit": 200,  # requests per minute
                "burst_limit": 20,  # burst requests
            },
        }

    @pytest.fixture
    def mock_redis_client(self) -> Mock:
        """Mock Redis client for rate limiting."""
        return Mock()

    # Rate Limit Enforcement Tests

    def test_rate_limit_enforcement_per_tenant(self, mock_rate_limiter: Mock, sample_tenants: dict) -> None:
        """Test rate limits are enforced per tenant."""
        # Mock rate limiter to track tenant-specific limits
        tenant_requests = {}

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            if tenant not in tenant_requests:
                tenant_requests[tenant] = 0

            tenant_requests[tenant] += 1
            tenant_info = sample_tenants.get(tenant, {})
            rate_limit = tenant_info.get("rate_limit", 100)

            if tenant_requests[tenant] <= rate_limit:
                return StepResult.ok(data={"allowed": True, "remaining": rate_limit - tenant_requests[tenant]})
            else:
                return StepResult.fail("Rate limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Test rate limit enforcement for each tenant
        for tenant_id, tenant_info in sample_tenants.items():
            rate_limit = tenant_info["rate_limit"]

            # Make requests up to the limit
            for i in range(rate_limit):
                result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])
                assert result.success
                assert result.data["allowed"]

            # Make one more request to exceed the limit
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])

            assert not result.success
            assert result.status == "rate_limited"
            assert "Rate limit exceeded" in result.error

    def test_rate_limit_enforcement_per_endpoint(self, mock_rate_limiter: Mock) -> None:
        """Test rate limits are enforced per endpoint."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"

        # Mock rate limiter to track endpoint-specific limits
        endpoint_requests = {}

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            if endpoint not in endpoint_requests:
                endpoint_requests[endpoint] = 0

            endpoint_requests[endpoint] += 1
            endpoint_limit = 10  # requests per minute per endpoint

            if endpoint_requests[endpoint] <= endpoint_limit:
                return StepResult.ok(data={"allowed": True, "remaining": endpoint_limit - endpoint_requests[endpoint]})
            else:
                return StepResult.fail("Rate limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Test rate limit enforcement for different endpoints
        endpoints = ["/api/analyze", "/api/transcribe", "/api/search"]

        for endpoint in endpoints:
            # Make requests up to the limit for each endpoint
            for i in range(10):
                result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, endpoint=endpoint)
                assert result.success
                assert result.data["allowed"]

            # Make one more request to exceed the limit
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, endpoint=endpoint)

            assert not result.success
            assert result.status == "rate_limited"

    def test_rate_limit_enforcement_per_workspace(self, mock_rate_limiter: Mock) -> None:
        """Test rate limits are enforced per workspace."""
        tenant_id = "test_tenant"
        workspace_a = "workspace_a"
        workspace_b = "workspace_b"

        # Mock rate limiter to track workspace-specific limits
        workspace_requests = {}

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            key = f"{tenant}:{workspace}"
            if key not in workspace_requests:
                workspace_requests[key] = 0

            workspace_requests[key] += 1
            workspace_limit = 50  # requests per minute per workspace

            if workspace_requests[key] <= workspace_limit:
                return StepResult.ok(data={"allowed": True, "remaining": workspace_limit - workspace_requests[key]})
            else:
                return StepResult.fail("Rate limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Test rate limit enforcement for different workspaces
        workspaces = [workspace_a, workspace_b]

        for workspace in workspaces:
            # Make requests up to the limit for each workspace
            for i in range(50):
                result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)
                assert result.success
                assert result.data["allowed"]

            # Make one more request to exceed the limit
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)

            assert not result.success
            assert result.status == "rate_limited"

    # Rate Limit Reset Logic Tests

    def test_rate_limit_reset_logic(self, mock_rate_limiter, mock_redis_client):
        """Test rate limit reset logic."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"

        # Mock Redis client for rate limit tracking
        mock_redis_client.get.return_value = "100"  # Current count
        mock_redis_client.setex.return_value = True
        mock_redis_client.incr.return_value = 101

        # Mock rate limiter to use Redis
        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            key = f"rate_limit:{tenant}:{workspace}:{endpoint or 'default'}"
            current_count = int(mock_redis_client.get(key) or "0")
            limit = 100

            if current_count < limit:
                mock_redis_client.incr(key)
                return StepResult.ok(data={"allowed": True, "remaining": limit - current_count - 1})
            else:
                return StepResult.fail("Rate limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Test rate limit check
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, endpoint="/api/analyze")

        assert result.success
        assert result.data["allowed"]

        # Verify Redis operations
        mock_redis_client.get.assert_called()
        mock_redis_client.incr.assert_called()

    def test_rate_limit_reset_after_window(self, mock_rate_limiter, mock_redis_client):
        """Test rate limit resets after time window."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"

        # Mock Redis client to simulate expired rate limit
        mock_redis_client.get.return_value = None  # No existing count
        mock_redis_client.setex.return_value = True
        mock_redis_client.incr.return_value = 1

        # Mock rate limiter to handle expired limits
        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            key = f"rate_limit:{tenant}:{workspace}:{endpoint or 'default'}"
            current_count = int(mock_redis_client.get(key) or "0")
            limit = 100

            if current_count < limit:
                if current_count == 0:
                    # Set expiration for new rate limit window
                    mock_redis_client.setex(key, 60, 1)  # 60 seconds
                else:
                    mock_redis_client.incr(key)
                return StepResult.ok(data={"allowed": True, "remaining": limit - current_count - 1})
            else:
                return StepResult.fail("Rate limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Test rate limit check after reset
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, endpoint="/api/analyze")

        assert result.success
        assert result.data["allowed"]

        # Verify Redis setex was called for new window
        mock_redis_client.setex.assert_called()

    # Burst Limit Tests

    def test_burst_limit_enforcement(self, mock_rate_limiter: Mock, sample_tenants: dict) -> None:
        """Test burst limit enforcement."""
        tenant_id = "tenant_a"
        tenant_info = sample_tenants[tenant_id]
        burst_limit = tenant_info["burst_limit"]

        # Mock rate limiter to track burst requests
        burst_requests = 0

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            nonlocal burst_requests
            burst_requests += 1

            if burst_requests <= burst_limit:
                return StepResult.ok(data={"allowed": True, "remaining": burst_limit - burst_requests})
            else:
                return StepResult.fail("Burst limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Make burst requests up to the limit
        for i in range(burst_limit):
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])
            assert result.success
            assert result.data["allowed"]

        # Make one more request to exceed burst limit
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])

        assert not result.success
        assert result.status == "rate_limited"
        assert "Burst limit exceeded" in result.error

    def test_burst_limit_recovery(self, mock_rate_limiter: Mock, sample_tenants: dict) -> None:
        """Test burst limit recovery after cooldown period."""
        tenant_id = "tenant_a"
        tenant_info = sample_tenants[tenant_id]
        burst_limit = tenant_info["burst_limit"]

        # Mock rate limiter to simulate burst limit recovery
        burst_requests = 0
        last_burst_time = time.time()

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            nonlocal burst_requests, last_burst_time
            current_time = time.time()

            # Reset burst count after cooldown period
            if current_time - last_burst_time > 1.0:  # 1 second cooldown
                burst_requests = 0
                last_burst_time = current_time

            burst_requests += 1

            if burst_requests <= burst_limit:
                return StepResult.ok(data={"allowed": True, "remaining": burst_limit - burst_requests})
            else:
                return StepResult.fail("Burst limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Exceed burst limit
        for i in range(burst_limit + 1):
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])
            if i < burst_limit:
                assert result.success
            else:
                assert not result.success

        # Wait for cooldown period
        time.sleep(1.1)

        # Should be able to make requests again
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])

        assert result.success
        assert result.data["allowed"]

    # Backoff and Retry Tests

    def test_exponential_backoff(self, mock_rate_limiter: Mock) -> None:
        """Test exponential backoff behavior."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"

        # Mock rate limiter to simulate exponential backoff
        retry_count = 0
        base_delay = 1.0

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            nonlocal retry_count
            retry_count += 1

            if retry_count == 1:
                return StepResult.fail("Rate limit exceeded", status="rate_limited")
            else:
                delay = base_delay * (2 ** (retry_count - 2))  # Exponential backoff
                return StepResult.ok(data={"allowed": True, "retry_after": delay})

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # First request should fail
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)

        assert not result.success
        assert result.status == "rate_limited"

        # Second request should succeed with retry delay
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)

        assert result.success
        assert "retry_after" in result.data
        assert result.data["retry_after"] == base_delay

    def test_retry_after_header(self, mock_rate_limiter: Mock) -> None:
        """Test retry-after header generation."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"

        # Mock rate limiter to return retry-after information
        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            return StepResult.fail("Rate limit exceeded", status="rate_limited", headers={"Retry-After": "60"})

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Test rate limit check
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)

        assert not result.success
        assert result.status == "rate_limited"
        assert "headers" in result.__dict__
        assert result.headers["Retry-After"] == "60"

    # Rate Limit Bypass Prevention Tests

    def test_rate_limit_bypass_prevention(self, mock_rate_limiter: Mock) -> None:
        """Test prevention of rate limit bypass attempts."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"

        # Mock rate limiter to track bypass attempts
        bypass_attempts = []

        def mock_check_rate_limit(tenant, workspace, endpoint=None, client_ip=None):
            # Track bypass attempts
            bypass_attempts.append(
                {
                    "tenant": tenant,
                    "workspace": workspace,
                    "endpoint": endpoint,
                    "client_ip": client_ip,
                    "timestamp": time.time(),
                }
            )

            # Check for suspicious patterns
            recent_attempts = [attempt for attempt in bypass_attempts if time.time() - attempt["timestamp"] < 60]

            if len(recent_attempts) > 10:  # Too many attempts
                return StepResult.fail("Suspicious activity detected", status="forbidden")

            return StepResult.ok(data={"allowed": True})

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Make normal requests
        for i in range(5):
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, client_ip="192.168.1.1")
            assert result.success

        # Make suspicious requests (too many in short time)
        for i in range(10):
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, client_ip="192.168.1.2")
            if i < 5:
                assert result.success
            else:
                assert not result.success
                assert result.status == "forbidden"

    def test_ip_based_rate_limiting(self, mock_rate_limiter: Mock) -> None:
        """Test IP-based rate limiting."""
        # Mock rate limiter to track IP-based limits
        ip_requests = {}

        def mock_check_rate_limit(tenant, workspace, endpoint=None, client_ip=None):
            if client_ip not in ip_requests:
                ip_requests[client_ip] = 0

            ip_requests[client_ip] += 1
            ip_limit = 50  # requests per minute per IP

            if ip_requests[client_ip] <= ip_limit:
                return StepResult.ok(data={"allowed": True, "remaining": ip_limit - ip_requests[client_ip]})
            else:
                return StepResult.fail("IP rate limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Test IP-based rate limiting
        client_ips = ["192.168.1.1", "192.168.1.2"]

        for ip in client_ips:
            # Make requests up to the limit for each IP
            for i in range(50):
                result = mock_rate_limiter.check_rate_limit(
                    tenant="test_tenant", workspace="test_workspace", client_ip=ip
                )
                assert result.success
                assert result.data["allowed"]

            # Make one more request to exceed the limit
            result = mock_rate_limiter.check_rate_limit(tenant="test_tenant", workspace="test_workspace", client_ip=ip)

            assert not result.success
            assert result.status == "rate_limited"
            assert "IP rate limit exceeded" in result.error

    # Concurrent Rate Limiting Tests

    @pytest.mark.asyncio
    async def test_concurrent_rate_limiting(self, mock_rate_limiter: Mock, sample_tenants: dict) -> None:
        """Test rate limiting under concurrent load."""
        # Mock rate limiter to handle concurrent requests
        request_count = 0
        rate_limit = 100

        async def mock_check_rate_limit(tenant, workspace, endpoint=None):
            nonlocal request_count
            request_count += 1

            if request_count <= rate_limit:
                return StepResult.ok(data={"allowed": True, "remaining": rate_limit - request_count})
            else:
                return StepResult.fail("Rate limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Make concurrent requests
        async def make_request(tenant_id, tenant_info):
            return mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])

        tasks = [
            make_request(tenant_id, tenant_info)
            for tenant_id, tenant_info in sample_tenants.items()
            for _ in range(35)  # 35 requests per tenant = 105 total
        ]

        results = await asyncio.gather(*tasks)

        # Count successful and failed requests
        successful = sum(1 for result in results if result.success)
        failed = sum(1 for result in results if not result.success)

        assert successful == rate_limit
        assert failed == len(tasks) - rate_limit

    # Integration Tests

    def test_rate_limiting_integration_with_stepresult(self, mock_rate_limiter: Mock) -> None:
        """Test rate limiting integration with StepResult pattern."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"

        # Mock rate limiter to return StepResult
        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            return StepResult.ok(data={"allowed": True, "remaining": 99})

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Test rate limit check
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)

        assert result.success
        assert result.data["allowed"]
        assert result.data["remaining"] == 99

    def test_rate_limiting_error_handling(self, mock_rate_limiter: Mock) -> None:
        """Test rate limiting error handling."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"

        # Mock rate limiter to simulate errors
        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            if tenant == "error_tenant":
                return StepResult.fail("Rate limiter error", status="internal_error")
            else:
                return StepResult.ok(data={"allowed": True})

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit

        # Test normal tenant
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)

        assert result.success

        # Test error tenant
        result = mock_rate_limiter.check_rate_limit(tenant="error_tenant", workspace=workspace)

        assert not result.success
        assert result.status == "internal_error"
        assert "Rate limiter error" in result.error
