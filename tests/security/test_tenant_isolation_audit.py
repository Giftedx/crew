"""Comprehensive tests for tenant isolation audit framework."""

from unittest.mock import patch

from src.core.security.tenant_isolation_audit import (
    IsolationAuditResult,
    IsolationViolation,
    TenantIsolationAuditor,
    audit_tenant_isolation,
    test_namespace_isolation,
    validate_tenant_context,
)
from src.ultimate_discord_intelligence_bot.tenancy import TenantContext


class TestTenantIsolationAuditor:
    """Test tenant isolation auditor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.auditor = TenantIsolationAuditor()

        # Create test tenant contexts
        self.tenant1 = TenantContext(
            tenant_id="tenant1",
            workspace_id="workspace1",
            routing_profile_id="profile1",
            budget_id="budget1",
            policy_binding_id="policy1",
            flags={"feature1": "enabled"},
        )

        self.tenant2 = TenantContext(
            tenant_id="tenant2",
            workspace_id="workspace2",
            routing_profile_id="profile2",
            budget_id="budget2",
            policy_binding_id="policy2",
            flags={"feature2": "enabled"},
        )

    def test_namespace_isolation_clean(self):
        """Test namespace isolation when tenants are properly isolated."""
        violations = self.auditor.audit_namespace_isolation(self.tenant1, self.tenant2)

        # Should have no violations for properly isolated tenants
        assert len(violations) == 0, "Properly isolated tenants should have no violations"

    def test_namespace_isolation_violation(self):
        """Test namespace isolation when tenants have identical namespaces."""
        # Create tenants with identical IDs (violation scenario)
        tenant1_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")
        tenant2_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")

        violations = self.auditor.audit_namespace_isolation(tenant1_duplicate, tenant2_duplicate)

        # Should detect namespace collision
        assert len(violations) > 0, "Identical tenants should have namespace violations"
        assert any(v.violation_type == "namespace_collision" for v in violations)

    def test_data_access_isolation(self):
        """Test data access isolation between tenants."""
        violations = self.auditor.audit_data_access_isolation(self.tenant1, self.tenant2)

        # Should have no violations for properly isolated tenants
        assert len(violations) == 0, "Properly isolated tenants should have no data access violations"

    def test_configuration_isolation(self):
        """Test configuration isolation between tenants."""
        violations = self.auditor.audit_configuration_isolation(self.tenant1, self.tenant2)

        # Should have no violations for properly isolated tenants
        assert len(violations) == 0, "Properly isolated tenants should have no configuration violations"

    def test_resource_isolation(self):
        """Test resource isolation between tenants."""
        violations = self.auditor.audit_resource_isolation(self.tenant1, self.tenant2)

        # Should have no violations for properly isolated tenants
        assert len(violations) == 0, "Properly isolated tenants should have no resource violations"

    def test_security_boundaries(self):
        """Test security boundaries between tenants."""
        violations = self.auditor.audit_security_boundaries(self.tenant1, self.tenant2)

        # Should have no violations for properly isolated tenants
        assert len(violations) == 0, "Properly isolated tenants should have no security boundary violations"

    def test_tenant_context_validation_valid(self):
        """Test tenant context validation with valid context."""
        violations = self.auditor.audit_tenant_context_validation(self.tenant1)

        # Should have no violations for valid tenant context
        assert len(violations) == 0, "Valid tenant context should have no violations"

    def test_tenant_context_validation_invalid_tenant_id(self):
        """Test tenant context validation with invalid tenant ID."""
        invalid_tenant = TenantContext(
            tenant_id="",  # Empty tenant ID
            workspace_id="workspace1",
        )

        violations = self.auditor.audit_tenant_context_validation(invalid_tenant)

        # Should detect invalid tenant ID
        assert len(violations) > 0, "Invalid tenant ID should have violations"
        assert any(v.violation_type == "invalid_tenant_id" for v in violations)

    def test_tenant_context_validation_invalid_workspace_id(self):
        """Test tenant context validation with invalid workspace ID."""
        invalid_tenant = TenantContext(
            tenant_id="tenant1",
            workspace_id="",  # Empty workspace ID
        )

        violations = self.auditor.audit_tenant_context_validation(invalid_tenant)

        # Should detect invalid workspace ID
        assert len(violations) > 0, "Invalid workspace ID should have violations"
        assert any(v.violation_type == "invalid_workspace_id" for v in violations)

    def test_tenant_context_validation_dangerous_chars(self):
        """Test tenant context validation with dangerous characters."""
        dangerous_tenant = TenantContext(
            tenant_id="tenant/../etc",  # Path traversal attempt
            workspace_id="workspace1",
        )

        violations = self.auditor.audit_tenant_context_validation(dangerous_tenant)

        # Should detect dangerous characters
        assert len(violations) > 0, "Dangerous characters should have violations"
        assert any(v.violation_type == "dangerous_tenant_id" for v in violations)

    def test_memory_namespace_isolation(self):
        """Test memory namespace isolation for a single tenant."""
        violations = self.auditor.audit_memory_namespace_isolation(self.tenant1)

        # Should have no violations for valid tenant
        assert len(violations) == 0, "Valid tenant should have no namespace violations"

    def test_cross_tenant_access_clean(self):
        """Test cross-tenant access with properly isolated tenants."""
        tenants = [self.tenant1, self.tenant2]
        violations = self.auditor.audit_cross_tenant_access(tenants)

        # Should have no violations for properly isolated tenants
        assert len(violations) == 0, "Properly isolated tenants should have no cross-tenant violations"

    def test_cross_tenant_access_violations(self):
        """Test cross-tenant access with violations."""
        # Create tenants with identical IDs
        tenant1_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")
        tenant2_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")

        tenants = [tenant1_duplicate, tenant2_duplicate]
        violations = self.auditor.audit_cross_tenant_access(tenants)

        # Should detect violations
        assert len(violations) > 0, "Identical tenants should have cross-tenant violations"

    def test_comprehensive_audit_clean(self):
        """Test comprehensive audit with clean tenants."""
        tenants = [self.tenant1, self.tenant2]
        result = self.auditor.run_comprehensive_audit(tenants)

        assert isinstance(result, IsolationAuditResult)
        assert result.total_violations == 0, "Clean tenants should have no violations"
        assert result.audit_time > 0, "Audit should take some time"
        assert len(result.recommendations) == 0, "Clean tenants should have no recommendations"

    def test_comprehensive_audit_violations(self):
        """Test comprehensive audit with violations."""
        # Create tenants with violations
        tenant1_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")
        tenant2_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")

        tenants = [tenant1_duplicate, tenant2_duplicate]
        result = self.auditor.run_comprehensive_audit(tenants)

        assert isinstance(result, IsolationAuditResult)
        assert result.total_violations > 0, "Violating tenants should have violations"
        assert result.audit_time > 0, "Audit should take some time"
        assert len(result.recommendations) > 0, "Violating tenants should have recommendations"

    def test_audit_summary_clean(self):
        """Test audit summary with clean tenants."""
        tenants = [self.tenant1, self.tenant2]
        self.auditor.run_comprehensive_audit(tenants)
        summary = self.auditor.get_audit_summary()

        assert summary["status"] == "clean"
        assert summary["violations"] == 0

    def test_audit_summary_violations(self):
        """Test audit summary with violations."""
        # Create tenants with violations
        tenant1_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")
        tenant2_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")

        tenants = [tenant1_duplicate, tenant2_duplicate]
        self.auditor.run_comprehensive_audit(tenants)
        summary = self.auditor.get_audit_summary()

        assert summary["status"] == "violations_found"
        assert summary["total_violations"] > 0
        assert "severity_breakdown" in summary
        assert "violation_types" in summary

    def test_violation_severity_levels(self):
        """Test violation severity levels."""
        # Create violations with different severity levels
        violations = [
            IsolationViolation(
                violation_type="test_low",
                description="Low severity test",
                severity="low",
                tenant_id="tenant1",
                workspace_id="workspace1",
                affected_resource="test",
                details={},
            ),
            IsolationViolation(
                violation_type="test_medium",
                description="Medium severity test",
                severity="medium",
                tenant_id="tenant1",
                workspace_id="workspace1",
                affected_resource="test",
                details={},
            ),
            IsolationViolation(
                violation_type="test_high",
                description="High severity test",
                severity="high",
                tenant_id="tenant1",
                workspace_id="workspace1",
                affected_resource="test",
                details={},
            ),
            IsolationViolation(
                violation_type="test_critical",
                description="Critical severity test",
                severity="critical",
                tenant_id="tenant1",
                workspace_id="workspace1",
                affected_resource="test",
                details={},
            ),
        ]

        self.auditor.violations = violations
        summary = self.auditor.get_audit_summary()

        assert summary["severity_breakdown"]["low"] == 1
        assert summary["severity_breakdown"]["medium"] == 1
        assert summary["severity_breakdown"]["high"] == 1
        assert summary["severity_breakdown"]["critical"] == 1

    def test_recommendations_generation(self):
        """Test recommendations generation."""
        # Create violations with different types
        violations = [
            IsolationViolation(
                violation_type="namespace_collision",
                description="Namespace collision test",
                severity="critical",
                tenant_id="tenant1",
                workspace_id="workspace1",
                affected_resource="namespace",
                details={},
            ),
            IsolationViolation(
                violation_type="data_access",
                description="Data access test",
                severity="high",
                tenant_id="tenant1",
                workspace_id="workspace1",
                affected_resource="data",
                details={},
            ),
        ]

        self.auditor.violations = violations
        result = self.auditor.run_comprehensive_audit([self.tenant1, self.tenant2])

        assert len(result.recommendations) > 0, "Should generate recommendations for violations"
        assert any("namespace" in rec.lower() for rec in result.recommendations), "Should recommend namespace fixes"
        assert any("data access" in rec.lower() for rec in result.recommendations), "Should recommend data access fixes"


class TestConvenienceFunctions:
    """Test convenience functions for tenant isolation audit."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tenant1 = TenantContext(tenant_id="tenant1", workspace_id="workspace1")

        self.tenant2 = TenantContext(tenant_id="tenant2", workspace_id="workspace2")

    def test_audit_tenant_isolation_clean(self):
        """Test audit_tenant_isolation with clean tenants."""
        tenants = [self.tenant1, self.tenant2]
        result = audit_tenant_isolation(tenants)

        assert result.success, "Clean tenants should pass audit"
        assert "audit_result" in result.data

    def test_audit_tenant_isolation_violations(self):
        """Test audit_tenant_isolation with violations."""
        # Create tenants with violations
        tenant1_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")
        tenant2_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")

        tenants = [tenant1_duplicate, tenant2_duplicate]
        result = audit_tenant_isolation(tenants)

        assert not result.success, "Violating tenants should fail audit"
        assert "audit_result" in result.data

    def test_validate_tenant_context_valid(self):
        """Test validate_tenant_context with valid context."""
        result = validate_tenant_context(self.tenant1)

        assert result.success, "Valid tenant context should pass validation"
        assert result.data["status"] == "valid"

    def test_validate_tenant_context_invalid(self):
        """Test validate_tenant_context with invalid context."""
        invalid_tenant = TenantContext(
            tenant_id="",  # Empty tenant ID
            workspace_id="workspace1",
        )

        result = validate_tenant_context(invalid_tenant)

        assert not result.success, "Invalid tenant context should fail validation"
        assert "violations" in result.data

    def test_test_namespace_isolation_clean(self):
        """Test test_namespace_isolation with clean tenants."""
        result = test_namespace_isolation(self.tenant1, self.tenant2)

        assert result.success, "Clean tenants should pass namespace isolation test"
        assert result.data["status"] == "isolated"

    def test_test_namespace_isolation_violations(self):
        """Test test_namespace_isolation with violations."""
        # Create tenants with identical IDs
        tenant1_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")
        tenant2_duplicate = TenantContext(tenant_id="same_tenant", workspace_id="same_workspace")

        result = test_namespace_isolation(tenant1_duplicate, tenant2_duplicate)

        assert not result.success, "Identical tenants should fail namespace isolation test"
        assert "violations" in result.data

    def test_audit_tenant_isolation_exception(self):
        """Test audit_tenant_isolation with exception."""
        with patch("src.core.security.tenant_isolation_audit.TenantIsolationAuditor") as mock_auditor:
            mock_auditor.side_effect = Exception("Test exception")

            result = audit_tenant_isolation([self.tenant1])

            assert not result.success, "Exception should cause audit to fail"
            assert "Test exception" in result.error

    def test_validate_tenant_context_exception(self):
        """Test validate_tenant_context with exception."""
        with patch("src.core.security.tenant_isolation_audit.TenantIsolationAuditor") as mock_auditor:
            mock_auditor.side_effect = Exception("Test exception")

            result = validate_tenant_context(self.tenant1)

            assert not result.success, "Exception should cause validation to fail"
            assert "Test exception" in result.error

    def test_test_namespace_isolation_exception(self):
        """Test test_namespace_isolation with exception."""
        with patch("src.core.security.tenant_isolation_audit.TenantIsolationAuditor") as mock_auditor:
            mock_auditor.side_effect = Exception("Test exception")

            result = test_namespace_isolation(self.tenant1, self.tenant2)

            assert not result.success, "Exception should cause test to fail"
            assert "Test exception" in result.error
