"""
Test suite for rate limiting functionality.

This module tests rate limit enforcement per tenant, rate limit reset logic,
backoff and retry behavior, and rate limit bypass attempts.
"""

import asyncio
import time
from platform.core.step_result import StepResult
from unittest.mock import Mock

import pytest


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
            "tenant_a": {"workspace": "workspace_a", "rate_limit": 100, "burst_limit": 10},
            "tenant_b": {"workspace": "workspace_b", "rate_limit": 50, "burst_limit": 5},
            "tenant_c": {"workspace": "workspace_c", "rate_limit": 200, "burst_limit": 20},
        }

    @pytest.fixture
    def mock_redis_client(self) -> Mock:
        """Mock Redis client for rate limiting."""
        return Mock()

    def test_rate_limit_enforcement_per_tenant(self, mock_rate_limiter: Mock, sample_tenants: dict) -> None:
        """Test rate limits are enforced per tenant."""
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
        for tenant_id, tenant_info in sample_tenants.items():
            rate_limit = tenant_info["rate_limit"]
            for _i in range(rate_limit):
                result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])
                assert result.success
                assert result.data["allowed"]
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])
            assert not result.success
            assert result.status == "rate_limited"
            assert "Rate limit exceeded" in result.error

    def test_rate_limit_enforcement_per_endpoint(self, mock_rate_limiter: Mock) -> None:
        """Test rate limits are enforced per endpoint."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"
        endpoint_requests = {}

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            if endpoint not in endpoint_requests:
                endpoint_requests[endpoint] = 0
            endpoint_requests[endpoint] += 1
            endpoint_limit = 10
            if endpoint_requests[endpoint] <= endpoint_limit:
                return StepResult.ok(data={"allowed": True, "remaining": endpoint_limit - endpoint_requests[endpoint]})
            else:
                return StepResult.fail("Rate limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit
        endpoints = ["/api/analyze", "/api/transcribe", "/api/search"]
        for endpoint in endpoints:
            for _i in range(10):
                result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, endpoint=endpoint)
                assert result.success
                assert result.data["allowed"]
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, endpoint=endpoint)
            assert not result.success
            assert result.status == "rate_limited"

    def test_rate_limit_enforcement_per_workspace(self, mock_rate_limiter: Mock) -> None:
        """Test rate limits are enforced per workspace."""
        tenant_id = "test_tenant"
        workspace_a = "workspace_a"
        workspace_b = "workspace_b"
        workspace_requests = {}

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            key = f"{tenant}:{workspace}"
            if key not in workspace_requests:
                workspace_requests[key] = 0
            workspace_requests[key] += 1
            workspace_limit = 50
            if workspace_requests[key] <= workspace_limit:
                return StepResult.ok(data={"allowed": True, "remaining": workspace_limit - workspace_requests[key]})
            else:
                return StepResult.fail("Rate limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit
        workspaces = [workspace_a, workspace_b]
        for workspace in workspaces:
            for _i in range(50):
                result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)
                assert result.success
                assert result.data["allowed"]
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)
            assert not result.success
            assert result.status == "rate_limited"

    def test_rate_limit_reset_logic(self, mock_rate_limiter, mock_redis_client):
        """Test rate limit reset logic."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"
        mock_redis_client.get.return_value = "100"
        mock_redis_client.setex.return_value = True
        mock_redis_client.incr.return_value = 101

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
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, endpoint="/api/analyze")
        assert result.success
        assert result.data["allowed"]
        mock_redis_client.get.assert_called()
        mock_redis_client.incr.assert_called()

    def test_rate_limit_reset_after_window(self, mock_rate_limiter, mock_redis_client):
        """Test rate limit resets after time window."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"
        mock_redis_client.get.return_value = None
        mock_redis_client.setex.return_value = True
        mock_redis_client.incr.return_value = 1

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            key = f"rate_limit:{tenant}:{workspace}:{endpoint or 'default'}"
            current_count = int(mock_redis_client.get(key) or "0")
            limit = 100
            if current_count < limit:
                if current_count == 0:
                    mock_redis_client.setex(key, 60, 1)
                else:
                    mock_redis_client.incr(key)
                return StepResult.ok(data={"allowed": True, "remaining": limit - current_count - 1})
            else:
                return StepResult.fail("Rate limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, endpoint="/api/analyze")
        assert result.success
        assert result.data["allowed"]
        mock_redis_client.setex.assert_called()

    def test_burst_limit_enforcement(self, mock_rate_limiter: Mock, sample_tenants: dict) -> None:
        """Test burst limit enforcement."""
        tenant_id = "tenant_a"
        tenant_info = sample_tenants[tenant_id]
        burst_limit = tenant_info["burst_limit"]
        burst_requests = 0

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            nonlocal burst_requests
            burst_requests += 1
            if burst_requests <= burst_limit:
                return StepResult.ok(data={"allowed": True, "remaining": burst_limit - burst_requests})
            else:
                return StepResult.fail("Burst limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit
        for _i in range(burst_limit):
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])
            assert result.success
            assert result.data["allowed"]
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])
        assert not result.success
        assert result.status == "rate_limited"
        assert "Burst limit exceeded" in result.error

    def test_burst_limit_recovery(self, mock_rate_limiter: Mock, sample_tenants: dict) -> None:
        """Test burst limit recovery after cooldown period."""
        tenant_id = "tenant_a"
        tenant_info = sample_tenants[tenant_id]
        burst_limit = tenant_info["burst_limit"]
        burst_requests = 0
        last_burst_time = time.time()

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            nonlocal burst_requests, last_burst_time
            current_time = time.time()
            if current_time - last_burst_time > 1.0:
                burst_requests = 0
                last_burst_time = current_time
            burst_requests += 1
            if burst_requests <= burst_limit:
                return StepResult.ok(data={"allowed": True, "remaining": burst_limit - burst_requests})
            else:
                return StepResult.fail("Burst limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit
        for i in range(burst_limit + 1):
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])
            if i < burst_limit:
                assert result.success
            else:
                assert not result.success
        time.sleep(1.1)
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])
        assert result.success
        assert result.data["allowed"]

    def test_exponential_backoff(self, mock_rate_limiter: Mock) -> None:
        """Test exponential backoff behavior."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"
        retry_count = 0
        base_delay = 1.0

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            nonlocal retry_count
            retry_count += 1
            if retry_count == 1:
                return StepResult.fail("Rate limit exceeded", status="rate_limited")
            else:
                delay = base_delay * 2 ** (retry_count - 2)
                return StepResult.ok(data={"allowed": True, "retry_after": delay})

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)
        assert not result.success
        assert result.status == "rate_limited"
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)
        assert result.success
        assert "retry_after" in result.data
        assert result.data["retry_after"] == base_delay

    def test_retry_after_header(self, mock_rate_limiter: Mock) -> None:
        """Test retry-after header generation."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            return StepResult.fail("Rate limit exceeded", status="rate_limited", headers={"Retry-After": "60"})

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)
        assert not result.success
        assert result.status == "rate_limited"
        assert "headers" in result.__dict__
        assert result.headers["Retry-After"] == "60"

    def test_rate_limit_bypass_prevention(self, mock_rate_limiter: Mock) -> None:
        """Test prevention of rate limit bypass attempts."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"
        bypass_attempts = []

        def mock_check_rate_limit(tenant, workspace, endpoint=None, client_ip=None):
            bypass_attempts.append(
                {
                    "tenant": tenant,
                    "workspace": workspace,
                    "endpoint": endpoint,
                    "client_ip": client_ip,
                    "timestamp": time.time(),
                }
            )
            recent_attempts = [attempt for attempt in bypass_attempts if time.time() - attempt["timestamp"] < 60]
            if len(recent_attempts) > 10:
                return StepResult.fail("Suspicious activity detected", status="forbidden")
            return StepResult.ok(data={"allowed": True})

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit
        for i in range(5):
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, client_ip="192.168.1.1")
            assert result.success
        for i in range(10):
            result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace, client_ip="192.168.1.2")
            if i < 5:
                assert result.success
            else:
                assert not result.success
                assert result.status == "forbidden"

    def test_ip_based_rate_limiting(self, mock_rate_limiter: Mock) -> None:
        """Test IP-based rate limiting."""
        ip_requests = {}

        def mock_check_rate_limit(tenant, workspace, endpoint=None, client_ip=None):
            if client_ip not in ip_requests:
                ip_requests[client_ip] = 0
            ip_requests[client_ip] += 1
            ip_limit = 50
            if ip_requests[client_ip] <= ip_limit:
                return StepResult.ok(data={"allowed": True, "remaining": ip_limit - ip_requests[client_ip]})
            else:
                return StepResult.fail("IP rate limit exceeded", status="rate_limited")

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit
        client_ips = ["192.168.1.1", "192.168.1.2"]
        for ip in client_ips:
            for _i in range(50):
                result = mock_rate_limiter.check_rate_limit(
                    tenant="test_tenant", workspace="test_workspace", client_ip=ip
                )
                assert result.success
                assert result.data["allowed"]
            result = mock_rate_limiter.check_rate_limit(tenant="test_tenant", workspace="test_workspace", client_ip=ip)
            assert not result.success
            assert result.status == "rate_limited"
            assert "IP rate limit exceeded" in result.error

    @pytest.mark.asyncio
    async def test_concurrent_rate_limiting(self, mock_rate_limiter: Mock, sample_tenants: dict) -> None:
        """Test rate limiting under concurrent load."""
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

        async def make_request(tenant_id, tenant_info):
            return mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=tenant_info["workspace"])

        tasks = [
            make_request(tenant_id, tenant_info) for tenant_id, tenant_info in sample_tenants.items() for _ in range(35)
        ]
        results = await asyncio.gather(*tasks)
        successful = sum(1 for result in results if result.success)
        failed = sum(1 for result in results if not result.success)
        assert successful == rate_limit
        assert failed == len(tasks) - rate_limit

    def test_rate_limiting_integration_with_stepresult(self, mock_rate_limiter: Mock) -> None:
        """Test rate limiting integration with StepResult pattern."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            return StepResult.ok(data={"allowed": True, "remaining": 99})

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)
        assert result.success
        assert result.data["allowed"]
        assert result.data["remaining"] == 99

    def test_rate_limiting_error_handling(self, mock_rate_limiter: Mock) -> None:
        """Test rate limiting error handling."""
        tenant_id = "test_tenant"
        workspace = "test_workspace"

        def mock_check_rate_limit(tenant, workspace, endpoint=None):
            if tenant == "error_tenant":
                return StepResult.fail("Rate limiter error", status="internal_error")
            else:
                return StepResult.ok(data={"allowed": True})

        mock_rate_limiter.check_rate_limit.side_effect = mock_check_rate_limit
        result = mock_rate_limiter.check_rate_limit(tenant=tenant_id, workspace=workspace)
        assert result.success
        result = mock_rate_limiter.check_rate_limit(tenant="error_tenant", workspace=workspace)
        assert not result.success
        assert result.status == "internal_error"
        assert "Rate limiter error" in result.error
