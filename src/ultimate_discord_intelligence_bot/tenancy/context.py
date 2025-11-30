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
    """Holds identifiers required to scope operations to a tenant.

    This class provides the context necessary for multi-tenancy, including
    tenant and workspace IDs, as well as optional configuration overrides.

    Attributes:
        tenant_id (str): The unique identifier for the tenant.
        workspace_id (str): The identifier for the workspace within the tenant.
        routing_profile_id (str | None): Optional ID for a specific routing profile.
        budget_id (str | None): Optional ID for a budget configuration.
        policy_binding_id (str | None): Optional ID for policy enforcement.
        flags (dict[str, str] | None): Dictionary of feature flags or settings.
    """

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
        """Initialize the TenantContext.

        Args:
            tenant_id (str | None): Unique tenant identifier. Defaults to 'default'.
            workspace_id (str | None): Workspace identifier. Defaults to 'main'.
            tenant (str | None): Alias for tenant_id (legacy support).
            workspace (str | None): Alias for workspace_id (legacy support).
            routing_profile_id (str | None): Routing profile identifier.
            budget_id (str | None): Budget configuration identifier.
            policy_binding_id (str | None): Policy binding identifier.
            flags (dict[str, str] | None): Feature flags dictionary.
        """
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
        """Alias for tenant_id.

        Returns:
            str: The tenant identifier.
        """
        return self.tenant_id

    @property
    def workspace(self) -> str:
        """Alias for workspace_id.

        Returns:
            str: The workspace identifier.
        """
        return self.workspace_id


@contextmanager
def with_tenant(ctx: TenantContext) -> Generator[TenantContext, None, None]:
    """Context manager that sets the active :class:`TenantContext`.

    This context manager ensures that the provided TenantContext is set for
    the duration of the block and reset afterwards. It uses `contextvars` to
    be thread-safe and async-safe, automatically propagating to child async
    tasks.

    Args:
        ctx (TenantContext): The tenant context to activate.

    Yields:
        TenantContext: The active tenant context.
    """
    token = _tenant_ctx_var.set(ctx)
    try:
        yield ctx
    finally:
        _tenant_ctx_var.reset(token)


def current_tenant() -> TenantContext | None:
    """Get current tenant context (async-safe).

    Retrieves the currently active TenantContext from the context variable.
    Safe to call from asyncio tasks, thread pool executors, and synchronous code.

    Returns:
        TenantContext | None: The active TenantContext, or None if not set.
    """
    return _tenant_ctx_var.get()


def require_tenant(strict: bool = False) -> TenantContext:
    """Get current tenant context, raising if not set.

    Retrieves the active TenantContext. If no context is set, it checks the
    environment configuration. In 'production' or 'staging' environments (or
    if `strict` is True), it raises a RuntimeError. Otherwise, it returns a
    default context ('default'/'main').

    Args:
        strict (bool): If True, always raise RuntimeError when ctx is None,
            regardless of environment. Defaults to False.

    Raises:
        RuntimeError: When context not set and strict mode is active or
            environment is production/staging.

    Returns:
        TenantContext: The active or default TenantContext.
    """
    ctx = current_tenant()
    if ctx is None:
        import os

        env = os.getenv("ENVIRONMENT", "development").lower()
        if strict or env in {"production", "staging"}:
            raise RuntimeError("TenantContext required but not set (strict mode)")
    return ctx or TenantContext("default", "main")


def mem_ns(ctx: TenantContext, name: str) -> str:
    """Compose a memory namespace for the given tenant/workspace.

    Creates a standardized namespace string by combining the tenant ID,
    workspace ID, and the provided name.

    Args:
        ctx (TenantContext): The tenant context to use.
        name (str): The specific name or suffix for the namespace.

    Returns:
        str: The composed namespace string (e.g., "tenant:workspace:name").
    """
    return f"{ctx.tenant_id}:{ctx.workspace_id}:{name}"


def run_with_tenant_context(func):
    """Decorator to copy current tenant context for ThreadPoolExecutor.

    Ensures that the current tenant context is captured and reapplied when
    the decorated function is executed, which is useful when offloading tasks
    to a ThreadPoolExecutor where context variables are not automatically
    propagated.

    Usage:
        executor.submit(run_with_tenant_context(my_func), arg1, arg2)

    Note:
        Context is automatically copied for `asyncio.create_task()`, so this
        decorator is primarily for thread pools.

    Args:
        func (callable): The function to decorate.

    Returns:
        callable: The wrapped function that runs within the captured context.
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
