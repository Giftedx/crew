from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Generator


_thread_local = threading.local()


@dataclass(init=False)
class TenantContext:
    """Holds identifiers required to scope operations to a tenant."""

    tenant_id: str
    workspace_id: str
    routing_profile_id: str | None = None
    budget_id: str | None = None
    policy_binding_id: str | None = None
    flags: dict[str, str] | None = None

    def __init__(
        self,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        *,
        # Backward-compatible aliases expected by tests
        tenant: str | None = None,
        workspace: str | None = None,
        routing_profile_id: str | None = None,
        budget_id: str | None = None,
        policy_binding_id: str | None = None,
        flags: dict[str, str] | None = None,
    ) -> None:
        # Prefer explicit ids; fall back to alias names for compatibility
        self.tenant_id = tenant_id or tenant or "default"
        self.workspace_id = workspace_id or workspace or "main"
        self.routing_profile_id = routing_profile_id
        self.budget_id = budget_id
        self.policy_binding_id = policy_binding_id
        self.flags = flags

    # Alias properties for ergonomic access in legacy code/tests
    @property
    def tenant(self) -> str:
        return self.tenant_id

    @property
    def workspace(self) -> str:
        return self.workspace_id


@contextmanager
def with_tenant(ctx: TenantContext) -> Generator[TenantContext, None, None]:
    """Context manager that sets the active :class:`TenantContext`."""

    prev = getattr(_thread_local, "tenant_ctx", None)
    _thread_local.tenant_ctx = ctx
    try:
        yield ctx
    finally:
        _thread_local.tenant_ctx = prev


def current_tenant() -> TenantContext | None:
    return getattr(_thread_local, "tenant_ctx", None)


def require_tenant() -> TenantContext:
    ctx = current_tenant()
    if ctx is None:
        raise RuntimeError("TenantContext required but not set")
    return ctx


def mem_ns(ctx: TenantContext, name: str) -> str:
    """Compose a memory namespace for the given tenant/workspace."""

    return f"{ctx.tenant_id}:{ctx.workspace_id}:{name}"
