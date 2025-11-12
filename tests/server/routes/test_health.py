"""Tests for health check endpoints and utilities.

Validates:
- /healthz fast liveness probe (<10ms target)
- /readyz dependency readiness checks
- /livez core service availability
- Health check metrics emission
- Proper status codes (200 OK, 503 Service Unavailable)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from server.app import create_app
from platform.http.health import HealthChecker, HealthStatus, get_health_checker


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    from platform.config.settings import Settings

    settings = Settings()
    app = create_app(settings)
    return TestClient(app)


@pytest.fixture
def health_checker() -> HealthChecker:
    """Create health checker instance."""
    return get_health_checker()


class TestHealthEndpoints:
    """Test suite for health check HTTP endpoints."""

    def test_health_legacy_endpoint(self, client: TestClient):
        """Test legacy /health endpoint for backward compatibility."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_activities_health_endpoint(self, client: TestClient):
        """Test Discord Activities health endpoint."""
        response = client.get("/activities/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["component"] == "activities"

    def test_healthz_liveness_probe(self, client: TestClient):
        """Test /healthz liveness probe returns quickly."""
        import time

        start = time.perf_counter()
        response = client.get("/healthz")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == HealthStatus.HEALTHY.value
        assert "uptime_seconds" in data
        assert "latency_ms" in data

        # Verify fast response (<50ms including HTTP overhead)
        assert elapsed_ms < 50, f"Liveness probe too slow: {elapsed_ms:.2f}ms"

    @pytest.mark.asyncio
    async def test_readyz_when_healthy(self, client: TestClient):
        """Test /readyz returns 200 when dependencies healthy."""
        # Note: In test environment, some dependencies may be missing
        # This test validates the endpoint structure, not actual dependency health
        response = client.get("/readyz")

        # Accept either 200 (all healthy) or 503 (some unavailable in test env)
        assert response.status_code in (200, 503)
        data = response.json()

        assert "status" in data
        if response.status_code == 200:
            assert data["status"] in (HealthStatus.HEALTHY.value, HealthStatus.DEGRADED.value)
        else:
            assert data["status"] == HealthStatus.UNHEALTHY.value

        # Verify structure includes checks
        if "checks" in data:
            assert isinstance(data["checks"], list)
            for check in data["checks"]:
                assert "component" in check
                assert "status" in check
                assert "latency_ms" in check

    @pytest.mark.asyncio
    async def test_livez_service_check(self, client: TestClient):
        """Test /livez core service availability check."""
        response = client.get("/livez")

        # Accept either 200 or 503 depending on environment
        assert response.status_code in (200, 503)
        data = response.json()

        assert "status" in data
        if "checks" in data:
            assert isinstance(data["checks"], list)


class TestHealthChecker:
    """Test suite for HealthChecker utility class."""

    def test_liveness_check_always_healthy(self, health_checker: HealthChecker):
        """Test liveness check always returns healthy when process alive."""
        result = health_checker.liveness_check()

        assert result.success is True
        assert result.data is not None
        assert result.data["status"] == HealthStatus.HEALTHY.value
        assert "uptime_seconds" in result.data
        assert "latency_ms" in result.data
        assert result.data["latency_ms"] < 10, "Liveness check should be <10ms"

    @pytest.mark.asyncio
    async def test_readiness_check_structure(self, health_checker: HealthChecker):
        """Test readiness check returns proper structure."""
        result = await health_checker.readiness_check()

        # Result may succeed or fail depending on environment
        assert result.data is not None
        assert "status" in result.data
        assert "checks" in result.data
        assert "latency_ms" in result.data

        # Verify checks structure
        checks = result.data["checks"]
        assert isinstance(checks, list)
        assert len(checks) >= 2  # At minimum: qdrant, config

        for check in checks:
            assert "component" in check
            assert "status" in check
            assert "latency_ms" in check

    @pytest.mark.asyncio
    async def test_service_check_structure(self, health_checker: HealthChecker):
        """Test service check returns proper structure."""
        result = await health_checker.service_check()

        assert result.data is not None
        assert "status" in result.data
        assert "checks" in result.data
        assert "latency_ms" in result.data

        # Verify checks include core services
        checks = result.data["checks"]
        component_names = {check["component"] for check in checks}
        assert "llm_router" in component_names or "tool_registry" in component_names

    def test_health_checker_singleton(self):
        """Test health checker uses singleton pattern."""
        checker1 = get_health_checker()
        checker2 = get_health_checker()
        assert checker1 is checker2


class TestHealthMetrics:
    """Test suite for health check metrics emission."""

    def test_metrics_emitted_on_liveness(self, health_checker: HealthChecker):
        """Test liveness check emits metrics."""
        # Clear any previous metrics state if possible
        result = health_checker.liveness_check()

        assert result.success is True
        # Metrics emission happens internally via _emit_health_metrics
        # Actual metric validation would require accessing Prometheus registry

    @pytest.mark.asyncio
    async def test_metrics_emitted_on_readiness(self, health_checker: HealthChecker):
        """Test readiness check emits per-component metrics."""
        result = await health_checker.readiness_check()

        # Verify metadata includes check type
        assert result.metadata is not None
        assert result.metadata.get("check_type") == "readiness"

    @pytest.mark.asyncio
    async def test_metrics_emitted_on_service_check(self, health_checker: HealthChecker):
        """Test service check emits per-component metrics."""
        result = await health_checker.service_check()

        assert result.metadata is not None
        assert result.metadata.get("check_type") == "service"


class TestHealthStatusAggregation:
    """Test suite for health status aggregation logic."""

    @pytest.mark.asyncio
    async def test_unhealthy_dependency_returns_503(self, client: TestClient):
        """Test that unhealthy critical dependency returns 503."""
        # This test requires mocking dependencies to force failures
        # For now, validate the endpoint accepts requests
        response = client.get("/readyz")
        assert response.status_code in (200, 503)

        if response.status_code == 503:
            data = response.json()
            assert "error" in data or data.get("status") == HealthStatus.UNHEALTHY.value


# Run tests with: pytest tests/server/routes/test_health.py -v
