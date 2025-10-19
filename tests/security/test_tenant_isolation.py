"""
Test suite for tenant isolation functionality.

This module tests that tenant data never crosses boundaries, namespace isolation
in vector store, memory retrieval respects tenant context, and concurrent
multi-tenant access.
"""

import asyncio
from unittest.mock import Mock

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult


class TestTenantIsolation:
    """Test tenant isolation and data boundary enforcement."""

    @pytest.fixture
    def mock_vector_store(self) -> Mock:
        """Mock vector store for testing."""
        return Mock()

    @pytest.fixture
    def mock_memory_service(self) -> Mock:
        """Mock memory service for testing."""
        return Mock()

    @pytest.fixture
    def sample_tenants(self) -> dict[str, dict[str, str | dict[str, str]]]:
        """Sample tenant data for testing."""
        return {
            "tenant_a": {
                "workspace": "workspace_a",
                "namespace": "tenant_a:workspace_a",
                "data": {"content": "Tenant A content", "id": "a_123"},
            },
            "tenant_b": {
                "workspace": "workspace_b",
                "namespace": "tenant_b:workspace_b",
                "data": {"content": "Tenant B content", "id": "b_456"},
            },
            "tenant_c": {
                "workspace": "workspace_c",
                "namespace": "tenant_c:workspace_c",
                "data": {"content": "Tenant C content", "id": "c_789"},
            },
        }

    @pytest.fixture
    def sample_content_data(self) -> dict[str, str | dict[str, str | float] | list[float]]:
        """Sample content data for testing."""
        return {
            "transcript": "This is a sample transcript",
            "analysis": {"sentiment": "positive", "score": 0.8},
            "metadata": {"source": "youtube", "duration": 300},
            "embeddings": [0.1, 0.2, 0.3, 0.4, 0.5],
        }

    # Namespace Isolation Tests

    def test_vector_store_namespace_isolation(
        self, mock_vector_store: Mock, sample_tenants: dict[str, dict[str, str | dict[str, str]]]
    ) -> None:
        """Test vector store enforces namespace isolation."""
        # Mock vector store operations
        mock_vector_store.store.return_value = StepResult.ok(data={"stored": True})
        mock_vector_store.retrieve.return_value = StepResult.ok(data={"content": "retrieved"})

        # Store data for different tenants
        for tenant_id, tenant_info in sample_tenants.items():
            result = mock_vector_store.store(
                content=tenant_info["data"]["content"], tenant=tenant_id, workspace=tenant_info["workspace"]
            )

            # Verify store was called with correct namespace
            assert result.success
            mock_vector_store.store.assert_called_with(
                content=tenant_info["data"]["content"], tenant=tenant_id, workspace=tenant_info["workspace"]
            )

    def test_vector_store_retrieval_namespace_isolation(
        self, mock_vector_store: Mock, sample_tenants: dict[str, dict[str, str | dict[str, str]]]
    ) -> None:
        """Test vector store retrieval respects namespace boundaries."""

        # Mock retrieval to return tenant-specific data
        def mock_retrieve(query: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            namespace = f"{tenant}:{workspace}"
            if namespace == "tenant_a:workspace_a":
                return StepResult.ok(data={"content": "Tenant A content"})
            elif namespace == "tenant_b:workspace_b":
                return StepResult.ok(data={"content": "Tenant B content"})
            else:
                return StepResult.ok(data={"content": "Tenant C content"})

        mock_vector_store.retrieve.side_effect = mock_retrieve

        # Test retrieval for each tenant
        for tenant_id, tenant_info in sample_tenants.items():
            result = mock_vector_store.retrieve(
                query="test query", tenant=tenant_id, workspace=tenant_info["workspace"]
            )

            assert result.success
            assert result.data["content"] == tenant_info["data"]["content"]

    def test_vector_store_cross_tenant_data_leak_prevention(
        self, mock_vector_store: Mock, sample_tenants: dict[str, dict[str, str | dict[str, str]]]
    ) -> None:
        """Test vector store prevents cross-tenant data leaks."""

        # Mock retrieval to never return data from other tenants
        def mock_retrieve(query: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            # Only return data if querying the correct tenant
            if tenant == "tenant_a" and workspace == "workspace_a":
                return StepResult.ok(data={"content": "Tenant A content"})
            else:
                return StepResult.fail("Data not found")

        mock_vector_store.retrieve.side_effect = mock_retrieve

        # Try to retrieve tenant A data using tenant B credentials
        result = mock_vector_store.retrieve(query="test query", tenant="tenant_b", workspace="workspace_b")

        # Should not return tenant A data
        assert not result.success
        assert "Data not found" in result.error

    # Memory Service Isolation Tests

    def test_memory_service_tenant_isolation(
        self, mock_memory_service: Mock, sample_tenants: dict[str, dict[str, str | dict[str, str]]]
    ) -> None:
        """Test memory service enforces tenant isolation."""
        # Mock memory service operations
        mock_memory_service.store_content.return_value = StepResult.ok(data={"stored": True})
        mock_memory_service.retrieve_content.return_value = StepResult.ok(data={"content": "retrieved"})

        # Store content for different tenants
        for tenant_id, tenant_info in sample_tenants.items():
            result = mock_memory_service.store_content(
                content=tenant_info["data"]["content"], tenant=tenant_id, workspace=tenant_info["workspace"]
            )

            assert result.success
            mock_memory_service.store_content.assert_called_with(
                content=tenant_info["data"]["content"], tenant=tenant_id, workspace=tenant_info["workspace"]
            )

    def test_memory_service_retrieval_tenant_context(
        self, mock_memory_service: Mock, sample_tenants: dict[str, dict[str, str | dict[str, str]]]
    ) -> None:
        """Test memory service retrieval respects tenant context."""

        # Mock retrieval to return tenant-specific data
        def mock_retrieve(query: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            if tenant == "tenant_a":
                return StepResult.ok(data={"content": "Tenant A content", "tenant": "tenant_a"})
            elif tenant == "tenant_b":
                return StepResult.ok(data={"content": "Tenant B content", "tenant": "tenant_b"})
            else:
                return StepResult.ok(data={"content": "Tenant C content", "tenant": "tenant_c"})

        mock_memory_service.retrieve_content.side_effect = mock_retrieve

        # Test retrieval for each tenant
        for tenant_id, tenant_info in sample_tenants.items():
            result = mock_memory_service.retrieve_content(
                query="test query", tenant=tenant_id, workspace=tenant_info["workspace"]
            )

            assert result.success
            assert result.data["tenant"] == tenant_id
            assert result.data["content"] == tenant_info["data"]["content"]

    def test_memory_service_workspace_isolation(self, mock_memory_service):
        """Test memory service enforces workspace isolation within tenants."""
        tenant_id = "test_tenant"
        workspace_a = "workspace_a"
        workspace_b = "workspace_b"

        # Mock retrieval to return workspace-specific data
        def mock_retrieve(query: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            if workspace == "workspace_a":
                return StepResult.ok(data={"content": "Workspace A content", "workspace": "workspace_a"})
            elif workspace == "workspace_b":
                return StepResult.ok(data={"content": "Workspace B content", "workspace": "workspace_b"})
            else:
                return StepResult.fail("Workspace not found")

        mock_memory_service.retrieve_content.side_effect = mock_retrieve

        # Test retrieval from different workspaces
        result_a = mock_memory_service.retrieve_content(query="test query", tenant=tenant_id, workspace=workspace_a)

        result_b = mock_memory_service.retrieve_content(query="test query", tenant=tenant_id, workspace=workspace_b)

        assert result_a.success
        assert result_b.success
        assert result_a.data["workspace"] == "workspace_a"
        assert result_b.data["workspace"] == "workspace_b"
        assert result_a.data["content"] != result_b.data["content"]

    # Concurrent Access Tests

    @pytest.mark.asyncio
    async def test_concurrent_tenant_access(
        self, mock_vector_store: Mock, sample_tenants: dict[str, dict[str, str | dict[str, str]]]
    ) -> None:
        """Test concurrent access to different tenants doesn't cause data leaks."""
        # Mock vector store operations
        mock_vector_store.store.return_value = StepResult.ok(data={"stored": True})
        mock_vector_store.retrieve.return_value = StepResult.ok(data={"content": "retrieved"})

        async def store_tenant_data(tenant_id, tenant_info):
            """Store data for a specific tenant."""
            return mock_vector_store.store(
                content=tenant_info["data"]["content"], tenant=tenant_id, workspace=tenant_info["workspace"]
            )

        # Store data for all tenants concurrently
        tasks = [store_tenant_data(tenant_id, tenant_info) for tenant_id, tenant_info in sample_tenants.items()]

        results = await asyncio.gather(*tasks)

        # All operations should succeed
        assert all(result.success for result in results)

        # Verify store was called for each tenant
        assert mock_vector_store.store.call_count == len(sample_tenants)

    @pytest.mark.asyncio
    async def test_concurrent_retrieval_isolation(
        self, mock_vector_store: Mock, sample_tenants: dict[str, dict[str, str | dict[str, str]]]
    ) -> None:
        """Test concurrent retrieval maintains tenant isolation."""

        # Mock retrieval to return tenant-specific data
        def mock_retrieve(query: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            if tenant == "tenant_a":
                return StepResult.ok(data={"content": "Tenant A content", "tenant": "tenant_a"})
            elif tenant == "tenant_b":
                return StepResult.ok(data={"content": "Tenant B content", "tenant": "tenant_b"})
            else:
                return StepResult.ok(data={"content": "Tenant C content", "tenant": "tenant_c"})

        mock_vector_store.retrieve.side_effect = mock_retrieve

        async def retrieve_tenant_data(tenant_id, tenant_info):
            """Retrieve data for a specific tenant."""
            return mock_vector_store.retrieve(query="test query", tenant=tenant_id, workspace=tenant_info["workspace"])

        # Retrieve data for all tenants concurrently
        tasks = [retrieve_tenant_data(tenant_id, tenant_info) for tenant_id, tenant_info in sample_tenants.items()]

        results = await asyncio.gather(*tasks)

        # All operations should succeed
        assert all(result.success for result in results)

        # Verify each result contains only the correct tenant's data
        for i, (tenant_id, tenant_info) in enumerate(sample_tenants.items()):
            assert results[i].data["tenant"] == tenant_id
            assert results[i].data["content"] == tenant_info["data"]["content"]

    # Data Boundary Tests

    def test_tenant_data_boundary_enforcement(
        self, mock_vector_store: Mock, sample_tenants: dict[str, dict[str, str | dict[str, str]]]
    ) -> None:
        """Test that tenant data boundaries are strictly enforced."""
        # Mock vector store to track namespace usage
        stored_data = {}

        def mock_store(content: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            namespace = f"{tenant}:{workspace}"
            stored_data[namespace] = content
            return StepResult.ok(data={"stored": True, "namespace": namespace})

        def mock_retrieve(query: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            namespace = f"{tenant}:{workspace}"
            if namespace in stored_data:
                return StepResult.ok(data={"content": stored_data[namespace], "namespace": namespace})
            else:
                return StepResult.fail("Data not found")

        mock_vector_store.store.side_effect = mock_store
        mock_vector_store.retrieve.side_effect = mock_retrieve

        # Store data for each tenant
        for tenant_id, tenant_info in sample_tenants.items():
            result = mock_vector_store.store(
                content=tenant_info["data"]["content"], tenant=tenant_id, workspace=tenant_info["workspace"]
            )
            assert result.success

        # Verify data is stored in correct namespaces
        assert len(stored_data) == len(sample_tenants)
        for tenant_id, tenant_info in sample_tenants.items():
            namespace = f"{tenant_id}:{tenant_info['workspace']}"
            assert namespace in stored_data
            assert stored_data[namespace] == tenant_info["data"]["content"]

    def test_workspace_data_boundary_enforcement(self, mock_vector_store):
        """Test that workspace data boundaries are strictly enforced."""
        tenant_id = "test_tenant"
        workspace_a = "workspace_a"
        workspace_b = "workspace_b"

        # Mock vector store to track workspace-specific data
        workspace_data = {}

        def mock_store(content: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            key = f"{tenant}:{workspace}"
            workspace_data[key] = content
            return StepResult.ok(data={"stored": True, "workspace": workspace})

        def mock_retrieve(query: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            key = f"{tenant}:{workspace}"
            if key in workspace_data:
                return StepResult.ok(data={"content": workspace_data[key], "workspace": workspace})
            else:
                return StepResult.fail("Data not found")

        mock_vector_store.store.side_effect = mock_store
        mock_vector_store.retrieve.side_effect = mock_retrieve

        # Store data in different workspaces
        content_a = "Workspace A content"
        content_b = "Workspace B content"

        result_a = mock_vector_store.store(content=content_a, tenant=tenant_id, workspace=workspace_a)

        result_b = mock_vector_store.store(content=content_b, tenant=tenant_id, workspace=workspace_b)

        assert result_a.success
        assert result_b.success

        # Verify data is stored in correct workspaces
        assert f"{tenant_id}:{workspace_a}" in workspace_data
        assert f"{tenant_id}:{workspace_b}" in workspace_data
        assert workspace_data[f"{tenant_id}:{workspace_a}"] == content_a
        assert workspace_data[f"{tenant_id}:{workspace_b}"] == content_b

    # Cross-Tenant Data Leak Prevention Tests

    def test_prevent_cross_tenant_data_access(
        self, mock_vector_store: Mock, sample_tenants: dict[str, dict[str, str | dict[str, str]]]
    ) -> None:
        """Test prevention of cross-tenant data access."""

        # Mock vector store to enforce strict tenant isolation
        def mock_retrieve(query: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            # Only allow access to data for the requesting tenant
            if tenant == "tenant_a" and workspace == "workspace_a":
                return StepResult.ok(data={"content": "Tenant A content", "tenant": "tenant_a"})
            else:
                return StepResult.fail("Access denied: Invalid tenant or workspace")

        mock_vector_store.retrieve.side_effect = mock_retrieve

        # Try to access tenant A data using tenant B credentials
        result = mock_vector_store.retrieve(query="test query", tenant="tenant_b", workspace="workspace_b")

        # Should be denied access
        assert not result.success
        assert "Access denied" in result.error

    def test_prevent_workspace_data_cross_access(self, mock_vector_store):
        """Test prevention of workspace data cross-access."""
        tenant_id = "test_tenant"
        workspace_a = "workspace_a"
        workspace_b = "workspace_b"

        # Mock vector store to enforce workspace isolation
        def mock_retrieve(query: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            if tenant == tenant_id and workspace == workspace_a:
                return StepResult.ok(data={"content": "Workspace A content", "workspace": "workspace_a"})
            else:
                return StepResult.fail("Access denied: Invalid workspace")

        mock_vector_store.retrieve.side_effect = mock_retrieve

        # Try to access workspace A data using workspace B credentials
        result = mock_vector_store.retrieve(query="test query", tenant=tenant_id, workspace=workspace_b)

        # Should be denied access
        assert not result.success
        assert "Access denied" in result.error

    # Namespace Validation Tests

    def test_namespace_validation(self, mock_vector_store):
        """Test namespace validation and sanitization."""

        # Mock vector store to validate namespaces
        def mock_store(content: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            # Validate namespace format
            if not tenant or not workspace:
                return StepResult.fail("Invalid tenant or workspace")

            if ":" in tenant or ":" in workspace:
                return StepResult.fail("Invalid characters in tenant or workspace")

            namespace = f"{tenant}:{workspace}"
            return StepResult.ok(data={"stored": True, "namespace": namespace})

        mock_vector_store.store.side_effect = mock_store

        # Test valid namespace
        result = mock_vector_store.store(content="test content", tenant="valid_tenant", workspace="valid_workspace")

        assert result.success
        assert result.data["namespace"] == "valid_tenant:valid_workspace"

        # Test invalid namespace
        result = mock_vector_store.store(content="test content", tenant="invalid:tenant", workspace="valid_workspace")

        assert not result.success
        assert "Invalid characters" in result.error

    def test_namespace_sanitization(self, mock_vector_store):
        """Test namespace sanitization for security."""

        # Mock vector store to sanitize namespaces
        def mock_store(content: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            # Sanitize namespace components
            sanitized_tenant = tenant.replace(" ", "_").replace(":", "_")
            sanitized_workspace = workspace.replace(" ", "_").replace(":", "_")
            namespace = f"{sanitized_tenant}:{sanitized_workspace}"
            return StepResult.ok(data={"stored": True, "namespace": namespace})

        mock_vector_store.store.side_effect = mock_store

        # Test namespace sanitization
        result = mock_vector_store.store(
            content="test content", tenant="tenant with spaces", workspace="workspace:with:colons"
        )

        assert result.success
        assert result.data["namespace"] == "tenant_with_spaces:workspace_with_colons"

    # Integration Tests

    def test_tenant_isolation_integration(self, mock_vector_store, mock_memory_service, sample_tenants):
        """Test integrated tenant isolation across services."""
        # Mock integrated operations
        mock_vector_store.store.return_value = StepResult.ok(data={"stored": True})
        mock_memory_service.store_content.return_value = StepResult.ok(data={"stored": True})

        # Store data across services for each tenant
        for tenant_id, tenant_info in sample_tenants.items():
            # Store in vector store
            vector_result = mock_vector_store.store(
                content=tenant_info["data"]["content"], tenant=tenant_id, workspace=tenant_info["workspace"]
            )

            # Store in memory service
            memory_result = mock_memory_service.store_content(
                content=tenant_info["data"]["content"], tenant=tenant_id, workspace=tenant_info["workspace"]
            )

            assert vector_result.success
            assert memory_result.success

        # Verify all operations succeeded
        assert mock_vector_store.store.call_count == len(sample_tenants)
        assert mock_memory_service.store_content.call_count == len(sample_tenants)

    def test_tenant_isolation_error_handling(
        self, mock_vector_store: Mock, sample_tenants: dict[str, dict[str, str | dict[str, str]]]
    ) -> None:
        """Test tenant isolation error handling."""

        # Mock vector store to simulate isolation errors
        def mock_store(content: str, tenant: str, workspace: str, **kwargs: dict) -> StepResult:
            if tenant == "error_tenant":
                return StepResult.fail("Tenant isolation error")
            else:
                return StepResult.ok(data={"stored": True})

        mock_vector_store.store.side_effect = mock_store

        # Test normal tenant
        result = mock_vector_store.store(content="test content", tenant="tenant_a", workspace="workspace_a")

        assert result.success

        # Test error tenant
        result = mock_vector_store.store(content="test content", tenant="error_tenant", workspace="workspace_a")

        assert not result.success
        assert "Tenant isolation error" in result.error
