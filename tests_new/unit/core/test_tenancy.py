"""Tests for tenancy context."""

import pytest

from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


class TestTenancyContext:
    """Test cases for TenantContext."""

    def test_tenant_context_initialization(self):
        """Test tenant context initialization."""
        tenant = "test_tenant"
        workspace = "test_workspace"

        context = TenantContext(tenant=tenant, workspace=workspace)

        assert context.tenant == tenant
        assert context.workspace == workspace

    def test_tenant_context_equality(self):
        """Test tenant context equality."""
        context1 = TenantContext(tenant="tenant1", workspace="workspace1")
        context2 = TenantContext(tenant="tenant1", workspace="workspace1")
        context3 = TenantContext(tenant="tenant2", workspace="workspace1")

        assert context1 == context2
        assert context1 != context3

    def test_tenant_context_hash(self):
        """Test tenant context hashing."""
        context1 = TenantContext(tenant="tenant1", workspace="workspace1")
        context2 = TenantContext(tenant="tenant1", workspace="workspace1")
        context3 = TenantContext(tenant="tenant2", workspace="workspace1")

        assert hash(context1) == hash(context2)
        assert hash(context1) != hash(context3)

    def test_tenant_context_string_representation(self):
        """Test tenant context string representation."""
        context = TenantContext(tenant="test_tenant", workspace="test_workspace")

        assert str(context) == "test_tenant:test_workspace"
        assert repr(context) == "TenantContext(tenant='test_tenant', workspace='test_workspace')"

    def test_tenant_context_namespace(self):
        """Test tenant context namespace generation."""
        context = TenantContext(tenant="test_tenant", workspace="test_workspace")

        namespace = context.get_namespace()
        assert namespace == "test_tenant:test_workspace"

    def test_tenant_context_validation(self):
        """Test tenant context validation."""
        # Valid context
        context = TenantContext(tenant="valid_tenant", workspace="valid_workspace")
        assert context.is_valid()

        # Invalid context - empty tenant
        context = TenantContext(tenant="", workspace="valid_workspace")
        assert not context.is_valid()

        # Invalid context - empty workspace
        context = TenantContext(tenant="valid_tenant", workspace="")
        assert not context.is_valid()

        # Invalid context - None values
        context = TenantContext(tenant=None, workspace="valid_workspace")
        assert not context.is_valid()

    def test_tenant_context_isolation(self):
        """Test tenant context isolation."""
        context1 = TenantContext(tenant="tenant1", workspace="workspace1")
        context2 = TenantContext(tenant="tenant2", workspace="workspace2")

        # Different tenants should be isolated
        assert context1.tenant != context2.tenant
        assert context1.workspace != context2.workspace
        assert context1 != context2

    def test_tenant_context_serialization(self):
        """Test tenant context serialization."""
        context = TenantContext(tenant="test_tenant", workspace="test_workspace")

        # Test to_dict
        data = context.to_dict()
        assert data["tenant"] == "test_tenant"
        assert data["workspace"] == "test_workspace"

        # Test from_dict
        new_context = TenantContext.from_dict(data)
        assert new_context.tenant == "test_tenant"
        assert new_context.workspace == "test_workspace"
        assert new_context == context

    def test_tenant_context_immutability(self):
        """Test tenant context immutability."""
        context = TenantContext(tenant="test_tenant", workspace="test_workspace")

        # Should not be able to modify tenant or workspace
        with pytest.raises(AttributeError):
            context.tenant = "new_tenant"

        with pytest.raises(AttributeError):
            context.workspace = "new_workspace"

    def test_tenant_context_defaults(self):
        """Test tenant context default values."""
        context = TenantContext()

        assert context.tenant == "default"
        assert context.workspace == "default"

    def test_tenant_context_validation_rules(self):
        """Test tenant context validation rules."""
        # Test valid tenant names
        valid_tenants = ["tenant1", "tenant_2", "tenant-3", "tenant.4"]
        for tenant in valid_tenants:
            context = TenantContext(tenant=tenant, workspace="workspace")
            assert context.is_valid()

        # Test invalid tenant names
        invalid_tenants = ["", "tenant with spaces", "tenant@invalid", "tenant#invalid"]
        for tenant in invalid_tenants:
            context = TenantContext(tenant=tenant, workspace="workspace")
            assert not context.is_valid()

    def test_tenant_context_workspace_validation(self):
        """Test tenant context workspace validation."""
        # Test valid workspace names
        valid_workspaces = ["workspace1", "workspace_2", "workspace-3", "workspace.4"]
        for workspace in valid_workspaces:
            context = TenantContext(tenant="tenant", workspace=workspace)
            assert context.is_valid()

        # Test invalid workspace names
        invalid_workspaces = [
            "",
            "workspace with spaces",
            "workspace@invalid",
            "workspace#invalid",
        ]
        for workspace in invalid_workspaces:
            context = TenantContext(tenant="tenant", workspace=workspace)
            assert not context.is_valid()

    def test_tenant_context_comparison(self):
        """Test tenant context comparison."""
        context1 = TenantContext(tenant="tenant1", workspace="workspace1")
        context2 = TenantContext(tenant="tenant1", workspace="workspace1")
        context3 = TenantContext(tenant="tenant2", workspace="workspace1")
        context4 = TenantContext(tenant="tenant1", workspace="workspace2")

        assert context1 == context2
        assert context1 != context3
        assert context1 != context4
        assert context3 != context4

    def test_tenant_context_sorting(self):
        """Test tenant context sorting."""
        contexts = [
            TenantContext(tenant="tenant3", workspace="workspace3"),
            TenantContext(tenant="tenant1", workspace="workspace1"),
            TenantContext(tenant="tenant2", workspace="workspace2"),
        ]

        sorted_contexts = sorted(contexts)

        assert sorted_contexts[0].tenant == "tenant1"
        assert sorted_contexts[1].tenant == "tenant2"
        assert sorted_contexts[2].tenant == "tenant3"

    def test_tenant_context_set_operations(self):
        """Test tenant context set operations."""
        context1 = TenantContext(tenant="tenant1", workspace="workspace1")
        context2 = TenantContext(tenant="tenant1", workspace="workspace1")
        context3 = TenantContext(tenant="tenant2", workspace="workspace2")

        context_set = {context1, context2, context3}

        # Should only have 2 unique contexts
        assert len(context_set) == 2
        assert context1 in context_set
        assert context2 in context_set
        assert context3 in context_set
