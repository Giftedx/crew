"""Role based access control helpers.

This module provides the `RBAC` class for enforcing permissions based on user roles
and checking Attribute-Based Access Control (ABAC) rules defined in configuration.
It serves as the central authorization mechanism for the platform.
"""

from __future__ import annotations

import functools
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, ParamSpec, TypeVar, cast

import yaml

from .events import log_security_event


# Risk tier ordering for comparison; lower index = lower risk level privilege.
_RISK_ORDER = ["low", "medium", "high"]

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "security.yaml"

# Some tests introspect ABAC rule mappings without constructing an RBAC instance first.
# Provide a module-level default so attribute access does not raise. Instance _load will
# overwrite this with file contents if present.
_abac_rules: dict[str, dict[str, Any]] = {}


P = ParamSpec("P")
R = TypeVar("R")


class RBAC:
    """Simple RBAC checker backed by a YAML config.

    Manages role-to-permission mappings and enforces access control policies.
    Supports both standard RBAC and an ABAC overlay for fine-grained control
    based on attributes like risk tier and channel.
    """

    def __init__(
        self,
        role_permissions: dict[str, set[str]] | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Create an :class:`RBAC` instance.

        Args:
            role_permissions: Optional in-memory map of roles to permission strings.
                If ``None``, the mapping is loaded from ``config_path``.
            config_path: Path to the YAML configuration file. Defaults to
                ``config/security.yaml`` relative to the module.
        """

        self._config_path = config_path or DEFAULT_CONFIG_PATH
        # Ensure attribute is defined for mypy across all code paths
        self._abac_rules: dict[str, dict[str, Any]] = {}
        if role_permissions is None:
            role_permissions = self._load()
        elif not hasattr(self, "_abac_rules"):
            # When role permissions supplied directly (tests), ensure ABAC rules map exists.
            self._abac_rules = {}
        self.role_permissions: dict[str, set[str]] = role_permissions

    def _load(self) -> dict[str, set[str]]:
        """Load role permissions from ``self._config_path``.

        Reads the configuration file to populate role permissions and ABAC rules.

        Returns:
            dict[str, set[str]]: A mapping of role names to sets of permissions.
        """
        if not self._config_path.exists():
            self._abac_rules = {}
            return {}
        data = yaml.safe_load(self._config_path.read_text()) or {}
        self._abac_rules = (data.get("abac") or {}).get("rules", {}) or {}
        return {role: set(perms) for role, perms in (data.get("role_permissions") or {}).items()}

    # --- ABAC helpers -----------------------------------------------------------------
    def _risk_tier_allows(self, required: str | None, provided: str | None) -> bool:
        """Check if the provided risk tier meets the required level.

        Args:
            required: The minimum risk tier required (low, medium, high).
            provided: The risk tier associated with the request context.

        Returns:
            bool: True if allowed, False otherwise.
        """
        if not required:
            return True
        if provided is None:
            return False
        try:
            return _RISK_ORDER.index(provided) >= _RISK_ORDER.index(required)
        except ValueError:
            return False

    def _abac_permits(self, perm: str, *, channel: str | None, risk_tier: str | None) -> bool:
        """Return True if ABAC overlay permits permission ``perm``.

        The ABAC rule schema (in ``config/security.yaml``) for a permission name can include:
        ``min_risk_tier``: lowest acceptable risk classification required.
        ``allowed_channels``: list of channel identifiers where the permission is valid.
        Unknown permissions or empty rule sets default to allow (RBAC governs base access).

        Args:
            perm: The permission string being checked.
            channel: The channel identifier (e.g., 'discord', 'web').
            risk_tier: The risk tier of the operation.

        Returns:
            bool: True if ABAC rules are satisfied.
        """
        rules = self._abac_rules.get(perm) or {}
        if not rules:
            return True
        if not self._risk_tier_allows(rules.get("min_risk_tier"), risk_tier):
            return False
        allowed_channels = rules.get("allowed_channels")
        return not (allowed_channels and channel not in allowed_channels)

    def has_perm(self, roles: Iterable[str], perm: str) -> bool:
        """Return ``True`` if any role grants ``perm``.

        Args:
            roles: A list of roles assigned to the user/actor.
            perm: The permission to check.

        Returns:
            bool: True if at least one role has the permission or a wildcard ('*').
        """
        for role in roles:
            perms = self.role_permissions.get(role, set())
            if "*" in perms or perm in perms:
                return True
        return False

    def require(self, perm: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Decorator enforcing ``perm`` based on a ``roles`` kwarg.

        Wraps a function to perform authorization checks before execution. It
        extracts security context (roles, actor, tenant, etc.) from kwargs,
        checks permissions, logs the access decision, and strips security
        metadata before calling the wrapped function.

        Args:
            perm: The permission string to require.

        Returns:
            Callable: A decorator that wraps the target function.
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                roles_obj = kwargs.get("roles", [])
                roles: Iterable[str] = roles_obj if isinstance(roles_obj, Iterable) else []
                actor = str(kwargs.get("actor", "unknown"))
                tenant = cast(
                    "str | None",
                    kwargs.get("tenant") if isinstance(kwargs.get("tenant"), str) else None,
                )
                workspace = cast(
                    "str | None",
                    kwargs.get("workspace") if isinstance(kwargs.get("workspace"), str) else None,
                )
                channel = cast(
                    "str | None",
                    kwargs.get("channel") if isinstance(kwargs.get("channel"), str) else None,
                )
                risk_tier = cast(
                    "str | None",
                    kwargs.get("risk_tier") if isinstance(kwargs.get("risk_tier"), str) else None,
                )

                # First evaluate base RBAC.
                if not self.has_perm(roles, perm):
                    log_security_event(
                        actor=actor,
                        action="rbac",
                        resource=perm,
                        decision="deny",
                        reason="missing_permission",
                        tenant=tenant,
                        workspace=workspace,
                    )
                    raise PermissionError(f"missing permission '{perm}'")
                # Then evaluate ABAC overlay if rules exist.
                if not self._abac_permits(perm, channel=channel, risk_tier=risk_tier):
                    log_security_event(
                        actor=actor,
                        action="abac",
                        resource=perm,
                        decision="deny",
                        reason="attribute_mismatch",
                        tenant=tenant,
                        workspace=workspace,
                        channel=channel,
                        risk_tier=risk_tier,
                    )
                    raise PermissionError(f"ABAC denial for '{perm}'")
                # drop security metadata before invoking the wrapped function
                for key in (
                    "roles",
                    "actor",
                    "tenant",
                    "workspace",
                    "channel",
                    "risk_tier",
                ):
                    kwargs.pop(key, None)
                return func(*args, **kwargs)

            return wrapper

        return decorator
