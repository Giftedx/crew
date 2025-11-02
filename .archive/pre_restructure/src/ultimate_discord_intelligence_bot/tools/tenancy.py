"""Tenancy utilities for tool isolation."""

from __future__ import annotations

from contextvars import ContextVar


# Context variables for tenant isolation
current_tenant: ContextVar[str | None] = ContextVar("current_tenant", default=None)
current_workspace: ContextVar[str | None] = ContextVar("current_workspace", default=None)


def set_tenant_context(tenant: str, workspace: str) -> None:
    """Set the current tenant and workspace context."""
    current_tenant.set(tenant)
    current_workspace.set(workspace)


def get_tenant_context() -> tuple[str, str]:
    """Get the current tenant and workspace context."""
    tenant = current_tenant.get()
    workspace = current_workspace.get()

    if not tenant or not workspace:
        raise ValueError("Tenant context not set")

    return tenant, workspace


def clear_tenant_context() -> None:
    """Clear the current tenant and workspace context."""
    current_tenant.set(None)
    current_workspace.set(None)


# Memory namespace utilities
def mem_ns(tenant: str, workspace: str) -> str:
    """Generate a memory namespace for tenant isolation."""
    return f"{tenant}:{workspace}"


def get_memory_key(key: str, tenant: str, workspace: str) -> str:
    """Generate a memory key with tenant isolation."""
    return f"{mem_ns(tenant, workspace)}:{key}"
