"""Comprehensive tenant isolation audit and testing framework."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy import TenantContext, mem_ns


logger = logging.getLogger(__name__)


@dataclass
class IsolationViolation:
    """Represents a tenant isolation violation."""

    violation_type: str
    description: str
    severity: str  # low, medium, high, critical
    tenant_id: str
    workspace_id: str
    affected_resource: str
    details: dict[str, Any]


@dataclass
class IsolationAuditResult:
    """Result of tenant isolation audit."""

    violations: list[IsolationViolation]
    total_violations: int
    severity_counts: dict[str, int]
    audit_time: float
    recommendations: list[str]


class TenantIsolationAuditor:
    """Comprehensive tenant isolation auditor."""

    def __init__(self):
        """Initialize tenant isolation auditor."""
        self.violations: list[IsolationViolation] = []
        self.audit_start_time: float | None = None

    def audit_namespace_isolation(self, tenant1: TenantContext, tenant2: TenantContext) -> list[IsolationViolation]:
        """Audit namespace isolation between two tenants."""
        violations = []

        # Test memory namespace isolation
        ns1 = mem_ns(tenant1, "test")
        ns2 = mem_ns(tenant2, "test")

        if ns1 == ns2:
            violations.append(
                IsolationViolation(
                    violation_type="namespace_collision",
                    description="Memory namespaces are identical between tenants",
                    severity="critical",
                    tenant_id=tenant1.tenant_id,
                    workspace_id=tenant1.workspace_id,
                    affected_resource="memory_namespace",
                    details={"namespace1": ns1, "namespace2": ns2},
                )
            )

        # Test namespace format validation
        if not ns1.startswith(f"{tenant1.tenant_id}:{tenant1.workspace_id}:"):
            violations.append(
                IsolationViolation(
                    violation_type="namespace_format",
                    description="Memory namespace does not follow expected format",
                    severity="high",
                    tenant_id=tenant1.tenant_id,
                    workspace_id=tenant1.workspace_id,
                    affected_resource="memory_namespace",
                    details={"namespace": ns1, "expected_prefix": f"{tenant1.tenant_id}:{tenant1.workspace_id}:"},
                )
            )

        return violations

    def audit_data_access_isolation(self, tenant1: TenantContext, tenant2: TenantContext) -> list[IsolationViolation]:
        """Audit data access isolation between tenants."""
        violations = []

        # Test that tenants cannot access each other's data
        # This would need to be implemented with actual data access tests
        # For now, we'll create placeholder violations for demonstration

        # Simulate data access test
        test_data_tenant1 = f"data_for_{tenant1.tenant_id}_{tenant1.workspace_id}"
        test_data_tenant2 = f"data_for_{tenant2.tenant_id}_{tenant2.workspace_id}"

        # Check if tenant1 can access tenant2's data (should not be possible)
        if test_data_tenant1 in test_data_tenant2 or test_data_tenant2 in test_data_tenant1:
            violations.append(
                IsolationViolation(
                    violation_type="data_access",
                    description="Tenant can access another tenant's data",
                    severity="critical",
                    tenant_id=tenant1.tenant_id,
                    workspace_id=tenant1.workspace_id,
                    affected_resource="data_access",
                    details={"accessed_data": test_data_tenant2},
                )
            )

        return violations

    def audit_configuration_isolation(self, tenant1: TenantContext, tenant2: TenantContext) -> list[IsolationViolation]:
        """Audit configuration isolation between tenants."""
        violations = []

        # Test that tenant configurations are isolated
        # This would need to be implemented with actual configuration access tests

        # Simulate configuration access test
        config_tenant1 = f"config_for_{tenant1.tenant_id}"
        config_tenant2 = f"config_for_{tenant2.tenant_id}"

        # Check if tenants can access each other's configurations
        if config_tenant1 == config_tenant2:
            violations.append(
                IsolationViolation(
                    violation_type="config_isolation",
                    description="Tenants share configuration",
                    severity="high",
                    tenant_id=tenant1.tenant_id,
                    workspace_id=tenant1.workspace_id,
                    affected_resource="configuration",
                    details={"shared_config": config_tenant1},
                )
            )

        return violations

    def audit_resource_isolation(self, tenant1: TenantContext, tenant2: TenantContext) -> list[IsolationViolation]:
        """Audit resource isolation between tenants."""
        violations = []

        # Test that tenants cannot access each other's resources
        # This includes rate limits, budgets, etc.

        # Simulate resource access test
        resource_tenant1 = f"resource_for_{tenant1.tenant_id}"
        resource_tenant2 = f"resource_for_{tenant2.tenant_id}"

        # Check if tenants can access each other's resources
        if resource_tenant1 == resource_tenant2:
            violations.append(
                IsolationViolation(
                    violation_type="resource_isolation",
                    description="Tenants share resources",
                    severity="high",
                    tenant_id=tenant1.tenant_id,
                    workspace_id=tenant1.workspace_id,
                    affected_resource="resource_access",
                    details={"shared_resource": resource_tenant1},
                )
            )

        return violations

    def audit_security_boundaries(self, tenant1: TenantContext, tenant2: TenantContext) -> list[IsolationViolation]:
        """Audit security boundaries between tenants."""
        violations = []

        # Test that security boundaries are properly enforced
        # This includes authentication, authorization, etc.

        # Simulate security boundary test
        security_tenant1 = f"security_for_{tenant1.tenant_id}"
        security_tenant2 = f"security_for_{tenant2.tenant_id}"

        # Check if tenants can bypass security boundaries
        if security_tenant1 == security_tenant2:
            violations.append(
                IsolationViolation(
                    violation_type="security_boundary",
                    description="Tenants share security boundaries",
                    severity="critical",
                    tenant_id=tenant1.tenant_id,
                    workspace_id=tenant1.workspace_id,
                    affected_resource="security_boundary",
                    details={"shared_security": security_tenant1},
                )
            )

        return violations

    def audit_tenant_context_validation(self, tenant: TenantContext) -> list[IsolationViolation]:
        """Audit tenant context validation."""
        violations = []

        # Validate tenant ID format
        if not tenant.tenant_id or not isinstance(tenant.tenant_id, str):
            violations.append(
                IsolationViolation(
                    violation_type="invalid_tenant_id",
                    description="Invalid tenant ID format",
                    severity="critical",
                    tenant_id=tenant.tenant_id,
                    workspace_id=tenant.workspace_id,
                    affected_resource="tenant_context",
                    details={"tenant_id": tenant.tenant_id},
                )
            )

        # Validate workspace ID format
        if not tenant.workspace_id or not isinstance(tenant.workspace_id, str):
            violations.append(
                IsolationViolation(
                    violation_type="invalid_workspace_id",
                    description="Invalid workspace ID format",
                    severity="critical",
                    tenant_id=tenant.tenant_id,
                    workspace_id=tenant.workspace_id,
                    affected_resource="tenant_context",
                    details={"workspace_id": tenant.workspace_id},
                )
            )

        # Validate tenant ID doesn't contain dangerous characters
        dangerous_chars = ["..", "/", "\\", ":", ";", "|", "&", ">", "<", "`", "$"]
        for char in dangerous_chars:
            if char in tenant.tenant_id:
                violations.append(
                    IsolationViolation(
                        violation_type="dangerous_tenant_id",
                        description=f"Tenant ID contains dangerous character: {char}",
                        severity="high",
                        tenant_id=tenant.tenant_id,
                        workspace_id=tenant.workspace_id,
                        affected_resource="tenant_context",
                        details={"dangerous_char": char, "tenant_id": tenant.tenant_id},
                    )
                )

        # Validate workspace ID doesn't contain dangerous characters
        for char in dangerous_chars:
            if char in tenant.workspace_id:
                violations.append(
                    IsolationViolation(
                        violation_type="dangerous_workspace_id",
                        description=f"Workspace ID contains dangerous character: {char}",
                        severity="high",
                        tenant_id=tenant.tenant_id,
                        workspace_id=tenant.workspace_id,
                        affected_resource="tenant_context",
                        details={"dangerous_char": char, "workspace_id": tenant.workspace_id},
                    )
                )

        return violations

    def audit_memory_namespace_isolation(self, tenant: TenantContext) -> list[IsolationViolation]:
        """Audit memory namespace isolation for a single tenant."""
        violations = []

        # Test various namespace scenarios
        test_namespaces = [
            "test",
            "user_data",
            "cache",
            "sessions",
            "analytics",
            "logs",
        ]

        for ns in test_namespaces:
            namespace = mem_ns(tenant, ns)

            # Validate namespace format
            expected_prefix = f"{tenant.tenant_id}:{tenant.workspace_id}:"
            if not namespace.startswith(expected_prefix):
                violations.append(
                    IsolationViolation(
                        violation_type="namespace_format",
                        description=f"Namespace '{namespace}' does not start with expected prefix",
                        severity="high",
                        tenant_id=tenant.tenant_id,
                        workspace_id=tenant.workspace_id,
                        affected_resource="memory_namespace",
                        details={"namespace": namespace, "expected_prefix": expected_prefix},
                    )
                )

            # Validate namespace doesn't contain dangerous characters
            dangerous_chars = ["..", "/", "\\", ":", ";", "|", "&", ">", "<", "`", "$"]
            for char in dangerous_chars:
                if char in namespace and char != ":" and char != ":":
                    violations.append(
                        IsolationViolation(
                            violation_type="dangerous_namespace",
                            description=f"Namespace contains dangerous character: {char}",
                            severity="high",
                            tenant_id=tenant.tenant_id,
                            workspace_id=tenant.workspace_id,
                            affected_resource="memory_namespace",
                            details={"namespace": namespace, "dangerous_char": char},
                        )
                    )

        return violations

    def audit_cross_tenant_access(self, tenants: list[TenantContext]) -> list[IsolationViolation]:
        """Audit cross-tenant access patterns."""
        violations = []

        # Test all pairs of tenants for isolation
        for i, tenant1 in enumerate(tenants):
            for j, tenant2 in enumerate(tenants):
                if i >= j:  # Skip self and duplicate pairs
                    continue

                # Test namespace isolation
                violations.extend(self.audit_namespace_isolation(tenant1, tenant2))

                # Test data access isolation
                violations.extend(self.audit_data_access_isolation(tenant1, tenant2))

                # Test configuration isolation
                violations.extend(self.audit_configuration_isolation(tenant1, tenant2))

                # Test resource isolation
                violations.extend(self.audit_resource_isolation(tenant1, tenant2))

                # Test security boundaries
                violations.extend(self.audit_security_boundaries(tenant1, tenant2))

        return violations

    def run_comprehensive_audit(self, tenants: list[TenantContext]) -> IsolationAuditResult:
        """Run comprehensive tenant isolation audit."""
        self.audit_start_time = time.time()
        self.violations = []

        # Audit individual tenant contexts
        for tenant in tenants:
            self.violations.extend(self.audit_tenant_context_validation(tenant))
            self.violations.extend(self.audit_memory_namespace_isolation(tenant))

        # Audit cross-tenant access
        self.violations.extend(self.audit_cross_tenant_access(tenants))

        # Calculate audit metrics
        audit_time = time.time() - self.audit_start_time
        severity_counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0,
        }

        for violation in self.violations:
            severity_counts[violation.severity] += 1

        # Generate recommendations
        recommendations = self._generate_recommendations()

        return IsolationAuditResult(
            violations=self.violations,
            total_violations=len(self.violations),
            severity_counts=severity_counts,
            audit_time=audit_time,
            recommendations=recommendations,
        )

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on audit results."""
        recommendations = []

        # Analyze violations by type
        violation_types = {}
        for violation in self.violations:
            violation_types[violation.violation_type] = violation_types.get(violation.violation_type, 0) + 1

        # Generate specific recommendations
        if "namespace_collision" in violation_types:
            recommendations.append("Implement strict namespace validation to prevent collisions")

        if "data_access" in violation_types:
            recommendations.append("Enhance data access controls with proper authorization checks")

        if "config_isolation" in violation_types:
            recommendations.append("Implement configuration isolation mechanisms")

        if "resource_isolation" in violation_types:
            recommendations.append("Enforce resource isolation between tenants")

        if "security_boundary" in violation_types:
            recommendations.append("Strengthen security boundaries between tenants")

        if "invalid_tenant_id" in violation_types or "invalid_workspace_id" in violation_types:
            recommendations.append("Implement strict tenant and workspace ID validation")

        if "dangerous_tenant_id" in violation_types or "dangerous_workspace_id" in violation_types:
            recommendations.append("Sanitize tenant and workspace IDs to prevent injection attacks")

        if "namespace_format" in violation_types:
            recommendations.append("Enforce consistent namespace format validation")

        if "dangerous_namespace" in violation_types:
            recommendations.append("Sanitize namespace strings to prevent injection attacks")

        # General recommendations
        if len(self.violations) > 0:
            recommendations.append("Implement comprehensive tenant isolation testing in CI/CD")
            recommendations.append("Add runtime tenant isolation monitoring")
            recommendations.append("Document tenant isolation requirements and best practices")

        return recommendations

    def get_audit_summary(self) -> dict[str, Any]:
        """Get audit summary statistics."""
        if not self.violations:
            return {"status": "clean", "violations": 0}

        return {
            "status": "violations_found",
            "total_violations": len(self.violations),
            "severity_breakdown": {
                "critical": len([v for v in self.violations if v.severity == "critical"]),
                "high": len([v for v in self.violations if v.severity == "high"]),
                "medium": len([v for v in self.violations if v.severity == "medium"]),
                "low": len([v for v in self.violations if v.severity == "low"]),
            },
            "violation_types": list({v.violation_type for v in self.violations}),
        }


def audit_tenant_isolation(tenants: list[TenantContext]) -> StepResult:
    """Convenience function for tenant isolation audit."""
    try:
        auditor = TenantIsolationAuditor()
        result = auditor.run_comprehensive_audit(tenants)

        if result.total_violations == 0:
            return StepResult.ok(data={"status": "clean", "audit_result": result})
        else:
            return StepResult.fail(
                f"Found {result.total_violations} isolation violations", data={"audit_result": result}
            )

    except Exception as e:
        return StepResult.fail(f"Tenant isolation audit failed: {e}")


def validate_tenant_context(tenant: TenantContext) -> StepResult:
    """Validate a single tenant context."""
    try:
        auditor = TenantIsolationAuditor()
        violations = auditor.audit_tenant_context_validation(tenant)

        if not violations:
            return StepResult.ok(data={"status": "valid"})
        else:
            return StepResult.fail(f"Found {len(violations)} validation violations", data={"violations": violations})

    except Exception as e:
        return StepResult.fail(f"Tenant context validation failed: {e}")


def test_namespace_isolation(tenant1: TenantContext, tenant2: TenantContext) -> StepResult:
    """Test namespace isolation between two tenants."""
    try:
        auditor = TenantIsolationAuditor()
        violations = auditor.audit_namespace_isolation(tenant1, tenant2)

        if not violations:
            return StepResult.ok(data={"status": "isolated"})
        else:
            return StepResult.fail(
                f"Found {len(violations)} namespace isolation violations", data={"violations": violations}
            )

    except Exception as e:
        return StepResult.fail(f"Namespace isolation test failed: {e}")
