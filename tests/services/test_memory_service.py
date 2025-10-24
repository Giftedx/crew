"""Tests for MemoryService."""

from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.services.memory_service import MemoryService
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


class TestMemoryService:
    """Test cases for MemoryService."""

    @pytest.fixture
    def memory_service(self, mock_qdrant_client, mock_redis_client):
        """Create MemoryService instance."""
        return MemoryService(qdrant_client=mock_qdrant_client, redis_client=mock_redis_client)

    @pytest.fixture
    def test_tenant_context(self):
        """Create test tenant context."""
        return TenantContext(tenant="test_tenant", workspace="test_workspace")

    def test_memory_service_initialization(self, memory_service):
        """Test memory service initialization."""
        assert memory_service is not None
        assert hasattr(memory_service, "store_content")
        assert hasattr(memory_service, "search_content")
        assert hasattr(memory_service, "update_content")
        assert hasattr(memory_service, "delete_content")

    def test_store_content(self, memory_service, test_tenant_context):
        """Test content storage."""
        content = "Test content for storage"

        result = memory_service.store_content(content=content, tenant_context=test_tenant_context)

        assert isinstance(result, StepResult)
        assert result.success
        assert "id" in result.data

    def test_search_content(self, memory_service, test_tenant_context):
        """Test content search."""
        query = "test query"

        result = memory_service.search_content(query=query, tenant_context=test_tenant_context)

        assert isinstance(result, StepResult)
        assert result.success
        assert "results" in result.data

    def test_update_content(self, memory_service, test_tenant_context):
        """Test content update."""
        content_id = "test_id"
        updated_content = "Updated content"

        result = memory_service.update_content(
            content_id=content_id,
            content=updated_content,
            tenant_context=test_tenant_context,
        )

        assert isinstance(result, StepResult)
        assert result.success

    def test_delete_content(self, memory_service, test_tenant_context):
        """Test content deletion."""
        content_id = "test_id"

        result = memory_service.delete_content(content_id=content_id, tenant_context=test_tenant_context)

        assert isinstance(result, StepResult)
        assert result.success

    def test_tenant_isolation(self, memory_service):
        """Test tenant isolation."""
        tenant1 = TenantContext(tenant="tenant1", workspace="workspace1")
        tenant2 = TenantContext(tenant="tenant2", workspace="workspace2")

        # Store content for tenant1
        result1 = memory_service.store_content(content="Content for tenant1", tenant_context=tenant1)

        # Store content for tenant2
        result2 = memory_service.store_content(content="Content for tenant2", tenant_context=tenant2)

        assert result1.success
        assert result2.success
        assert result1.data["id"] != result2.data["id"]

    def test_error_handling(self, memory_service, test_tenant_context):
        """Test error handling."""
        with patch.object(memory_service, "_store_in_qdrant", side_effect=Exception("Test error")):
            result = memory_service.store_content(content="Test content", tenant_context=test_tenant_context)

            assert isinstance(result, StepResult)
            assert not result.success
            assert "error" in result.data

    def test_performance(self, memory_service, test_tenant_context, performance_benchmark):
        """Test performance."""
        content = "Test content for performance testing"

        performance_benchmark.start()

        result = memory_service.store_content(content=content, tenant_context=test_tenant_context)

        elapsed_time = performance_benchmark.stop()

        assert result.success
        assert elapsed_time < 1.0  # Should complete within 1 second
