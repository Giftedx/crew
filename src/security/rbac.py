"""Role based access control helpers."""

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
    """Simple RBAC checker backed by a YAML config."""

    def __init__(
        self,
        role_permissions: dict[str, set[str]] | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Create an :class:`RBAC` instance.

        Parameters
        ----------
        role_permissions:
            Optional in-memory map of roles to permission strings. When
            ``None`` the mapping is loaded from ``config_path``.
        config_path:
            Path to the YAML configuration file. Defaults to
            ``config/security.yaml`` within the repository.
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

        Also caches the ABAC rules section (if present) for attribute overlay checks.
        """
        if not self._config_path.exists():
            self._abac_rules = {}
            return {}
        data = yaml.safe_load(self._config_path.read_text()) or {}
        self._abac_rules = (data.get("abac") or {}).get("rules", {}) or {}
        return {role: set(perms) for role, perms in (data.get("role_permissions") or {}).items()}

    # --- ABAC helpers -----------------------------------------------------------------
    def _risk_tier_allows(self, required: str | None, provided: str | None) -> bool:
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
        """
        rules = self._abac_rules.get(perm) or {}
        if not rules:
            return True
        if not self._risk_tier_allows(rules.get("min_risk_tier"), risk_tier):
            return False
        allowed_channels = rules.get("allowed_channels")
        return not (allowed_channels and channel not in allowed_channels)

    def has_perm(self, roles: Iterable[str], perm: str) -> bool:
        """Return ``True`` if any role grants ``perm``."""
        for role in roles:
            perms = self.role_permissions.get(role, set())
            if "*" in perms or perm in perms:
                return True
        return False

    def require(self, perm: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Decorator enforcing ``perm`` based on a ``roles`` kwarg.

        The wrapped function signature is preserved using ``ParamSpec`` so
        downstream call sites retain their type information.
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                roles_obj = kwargs.get("roles", [])
                roles: Iterable[str] = roles_obj if isinstance(roles_obj, Iterable) else []
                actor = str(kwargs.get("actor", "unknown"))
                tenant = cast(str | None, kwargs.get("tenant") if isinstance(kwargs.get("tenant"), str) else None)
                workspace = cast(
                    str | None,
                    kwargs.get("workspace") if isinstance(kwargs.get("workspace"), str) else None,
                )
                channel = cast(str | None, kwargs.get("channel") if isinstance(kwargs.get("channel"), str) else None)
                risk_tier = cast(
                    str | None,
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
                for key in ("roles", "actor", "tenant", "workspace", "channel", "risk_tier"):
                    kwargs.pop(key, None)
                return func(*args, **kwargs)

            return wrapper

        return decorator
