from __future__ import annotations

import contextvars
import functools
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Generator


_tenant_ctx_var: contextvars.ContextVar[TenantContext | None] = contextvars.ContextVar("tenant_ctx", default=None)


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
    """Context manager that sets the active :class:`TenantContext`.

    Thread-safe and async-safe via contextvars. Automatically propagates
    to child async tasks and threads created with copy_context().
    """
    token = _tenant_ctx_var.set(ctx)
    try:
        yield ctx
    finally:
        _tenant_ctx_var.reset(token)


def current_tenant() -> TenantContext | None:
    """Get current tenant context (async-safe).

    Returns the active TenantContext or None. Safe to call from
    asyncio tasks, thread pool executors, and sync code.
    """
    return _tenant_ctx_var.get()


def require_tenant(strict: bool = False) -> TenantContext:
    """Get current tenant context, raising if not set.

    Args:
        strict: If True, always raise when ctx is None.
                If False (default), only raise in production/staging.

    Raises:
        RuntimeError: When context not set and strict mode active.
    """
    ctx = current_tenant()
    if ctx is None:
        import os

        env = os.getenv("ENVIRONMENT", "development").lower()
        if strict or env in {"production", "staging"}:
            raise RuntimeError("TenantContext required but not set (strict mode)")
    return ctx or TenantContext("default", "main")


def mem_ns(ctx: TenantContext, name: str) -> str:
    """Compose a memory namespace for the given tenant/workspace."""
    return f"{ctx.tenant_id}:{ctx.workspace_id}:{name}"


def run_with_tenant_context(func):
    """Decorator to copy current tenant context for ThreadPoolExecutor.

    Use when submitting to ThreadPoolExecutor:

        executor.submit(run_with_tenant_context(my_func), arg1, arg2)

    Context is automatically copied for asyncio.create_task().
    """
    ctx = current_tenant()

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if ctx:
            token = _tenant_ctx_var.set(ctx)
            try:
                return func(*args, **kwargs)
            finally:
                _tenant_ctx_var.reset(token)
        else:
            return func(*args, **kwargs)

    return wrapper
