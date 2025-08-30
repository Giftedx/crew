from __future__ import annotations

import threading
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass

_thread_local = threading.local()


@dataclass
class TenantContext:
    """Holds identifiers required to scope operations to a tenant."""

    tenant_id: str
    workspace_id: str
    routing_profile_id: str | None = None
    budget_id: str | None = None
    policy_binding_id: str | None = None
    flags: dict[str, str] | None = None


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
