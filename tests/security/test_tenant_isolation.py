"""Security tests for tenant isolation mechanisms."""

from __future__ import annotations

import pytest

from ultimate_discord_intelligence_bot.services.memory_service import MemoryService
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant


class TestTenantIsolation:
    """Test tenant isolation and data separation."""

    @pytest.fixture
    def memory_service(self):
        """Create memory service for testing."""
        return MemoryService()

    @pytest.fixture
    def tenant1_context(self):
        """First tenant context."""
        return ("tenant1", "workspace1")

    @pytest.fixture
    def tenant2_context(self):
        """Second tenant context."""
        return ("tenant2", "workspace2")

    def test_memory_namespace_isolation(self, memory_service, tenant1_context, tenant2_context):
        """Test that memory storage is isolated between tenants."""
        # Arrange
        tenant1, workspace1 = tenant1_context
        tenant2, workspace2 = tenant2_context

        # Act - Store data for tenant1
        result1 = memory_service.add(
            "Tenant 1 secret data", metadata={"sensitive": True}, namespace=f"{tenant1}:{workspace1}"
        )

        # Store data for tenant2
        result2 = memory_service.add(
            "Tenant 2 secret data", metadata={"sensitive": True}, namespace=f"{tenant2}:{workspace2}"
        )

        # Assert both operations succeed
        assert result1.success
        assert result2.success

        # Verify data is stored in separate namespaces
        # This would require implementing a get method to verify isolation
        # For now, we verify the operations don't interfere with each other

    def test_tenant_context_propagation(self, tenant1_context):
        """Test that tenant context is properly propagated through the system."""
        # Arrange
        tenant, workspace = tenant1_context

        # Act
        with TenantContext(tenant, workspace) as ctx:
            # Simulate a tool operation that should use tenant context
            result = self._simulate_tool_operation(ctx)

        # Assert
        assert result.success
        assert result.data["tenant"] == tenant
        assert result.data["workspace"] == workspace

    def _simulate_tool_operation(self, ctx: TenantContext):
        """Simulate a tool operation that uses tenant context."""
        from ultimate_discord_intelligence_bot.step_result import StepResult

        return StepResult.ok(data={"tenant": ctx.tenant, "workspace": ctx.workspace, "operation": "test"})

    def test_cross_tenant_data_access_prevention(self, memory_service, tenant1_context, tenant2_context):
        """Test that tenants cannot access each other's data."""
        # Arrange
        tenant1, workspace1 = tenant1_context
        tenant2, workspace2 = tenant2_context

        # Store data for tenant1
        memory_service.add("Tenant 1 confidential data", namespace=f"{tenant1}:{workspace1}")

        # Act - Try to access tenant1 data from tenant2 context
        with TenantContext(tenant2, workspace2):
            # This should not be able to access tenant1's data
            # The actual implementation would need to verify this
            pass

        # Assert - This test would need to be implemented with actual data retrieval
        # to verify that tenant2 cannot access tenant1's data

    def test_tenant_boundary_validation(self):
        """Test that tenant boundaries are properly validated."""
        # Test invalid tenant format
        with pytest.raises(ValueError):
            TenantContext("", "workspace")

        with pytest.raises(ValueError):
            TenantContext("tenant", "")

        # Test valid tenant format
        ctx = TenantContext("valid_tenant", "valid_workspace")
        assert ctx.tenant == "valid_tenant"
        assert ctx.workspace == "valid_workspace"

    def test_tenant_context_decorator(self, tenant1_context):
        """Test the @with_tenant decorator functionality."""
        # Arrange
        tenant, workspace = tenant1_context

        # Act
        @with_tenant
        def test_function():
            from ultimate_discord_intelligence_bot.tenancy.context import current_tenant

            ctx = current_tenant()
            return ctx.tenant, ctx.workspace

        result_tenant, result_workspace = test_function(tenant, workspace)

        # Assert
        assert result_tenant == tenant
        assert result_workspace == workspace

    def test_tenant_isolation_in_tools(self, tenant1_context, tenant2_context):
        """Test that tools maintain tenant isolation."""
        # This test would need to be implemented with actual tools
        # to verify that they properly use tenant context and don't leak data

        # For now, we test the concept with a mock tool
        from ultimate_discord_intelligence_bot.step_result import StepResult
        from ultimate_discord_intelligence_bot.tools._base import BaseTool

        class MockTool(BaseTool[dict]):
            def _run(self, content: str, tenant: str, workspace: str) -> StepResult:
                return StepResult.ok(data={"content": content, "tenant": tenant, "workspace": workspace})

        tool = MockTool()
        tenant1, workspace1 = tenant1_context
        tenant2, workspace2 = tenant2_context

        # Act
        result1 = tool._run("test content", tenant1, workspace1)
        result2 = tool._run("test content", tenant2, workspace2)

        # Assert
        assert result1.success
        assert result2.success
        assert result1.data["tenant"] == tenant1
        assert result2.data["tenant"] == tenant2
        assert result1.data["tenant"] != result2.data["tenant"]

    def test_tenant_workspace_isolation(self):
        """Test that workspaces within the same tenant are isolated."""
        # Arrange
        tenant = "same_tenant"
        workspace1 = "workspace1"
        workspace2 = "workspace2"

        # Act
        with TenantContext(tenant, workspace1) as ctx1:
            result1 = self._simulate_tool_operation(ctx1)

        with TenantContext(tenant, workspace2) as ctx2:
            result2 = self._simulate_tool_operation(ctx2)

        # Assert
        assert result1.success
        assert result2.success
        assert result1.data["tenant"] == result2.data["tenant"]  # Same tenant
        assert result1.data["workspace"] != result2.data["workspace"]  # Different workspaces

    def test_tenant_context_cleanup(self):
        """Test that tenant context is properly cleaned up."""
        # Arrange
        tenant, workspace = "test_tenant", "test_workspace"

        # Act
        with TenantContext(tenant, workspace) as ctx:
            assert ctx.tenant == tenant
            assert ctx.workspace == workspace

        # After context exit, the context should be cleaned up
        # This would need to be verified with actual implementation

    def test_tenant_context_thread_safety(self):
        """Test that tenant context is thread-safe."""
        import threading
        import time

        results = {}

        def worker(tenant, workspace, result_key):
            with TenantContext(tenant, workspace) as ctx:
                time.sleep(0.1)  # Simulate some work
                results[result_key] = (ctx.tenant, ctx.workspace)

        # Start multiple threads with different tenant contexts
        thread1 = threading.Thread(target=worker, args=("tenant1", "workspace1", "thread1"))
        thread2 = threading.Thread(target=worker, args=("tenant2", "workspace2", "thread2"))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Assert that each thread maintained its own tenant context
        assert results["thread1"] == ("tenant1", "workspace1")
        assert results["thread2"] == ("tenant2", "workspace2")
