"""Tenancy utilities for tool isolation."""

from __future__ import annotations

from contextvars import ContextVar

from ..step_result import ErrorCategory, StepResult


# Context variables for tenant isolation
current_tenant: ContextVar[str | None] = ContextVar("current_tenant", default=None)
current_workspace: ContextVar[str | None] = ContextVar("current_workspace", default=None)


def set_tenant_context(tenant: str, workspace: str) -> StepResult:
    """Set the current tenant and workspace context.

    Returns StepResult for compliance with tooling conventions.
    """
    current_tenant.set(tenant)
    current_workspace.set(workspace)
    return StepResult.ok(tenant=tenant, workspace=workspace)


def get_tenant_context() -> StepResult:
    """Get the current tenant and workspace context as StepResult."""
    tenant = current_tenant.get()
    workspace = current_workspace.get()
    if not tenant or not workspace:
        return StepResult.fail("Tenant context not set", error_category=ErrorCategory.VALIDATION)
    return StepResult.ok(tenant=tenant, workspace=workspace)


def clear_tenant_context() -> StepResult:
    """Clear the current tenant and workspace context."""
    current_tenant.set(None)
    current_workspace.set(None)
    return StepResult.ok(cleared=True)


# Memory namespace utilities
def mem_ns(tenant: str, workspace: str) -> StepResult:
    """Generate a memory namespace for tenant isolation as StepResult."""
    return StepResult.ok(namespace=f"{tenant}:{workspace}")


def get_memory_key(key: str, tenant: str, workspace: str) -> StepResult:
    """Generate a memory key with tenant isolation as StepResult."""
    ns = f"{tenant}:{workspace}"
    return StepResult.ok(key=f"{ns}:{key}")
