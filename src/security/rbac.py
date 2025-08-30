"""Role based access control helpers."""

from __future__ import annotations

import functools
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import ParamSpec, TypeVar

import yaml

from .events import log_security_event

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "security.yaml"


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
        if role_permissions is None:
            role_permissions = self._load()
        self.role_permissions: dict[str, set[str]] = role_permissions

    def _load(self) -> dict[str, set[str]]:
        """Load role permissions from ``self._config_path``."""
        if not self._config_path.exists():
            return {}
        data = yaml.safe_load(self._config_path.read_text()) or {}
        return {role: set(perms) for role, perms in (data.get("role_permissions") or {}).items()}

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
                if not self.has_perm(roles, perm):
                    log_security_event(
                        actor=str(kwargs.get("actor", "unknown")),
                        action="rbac",
                        resource=perm,
                        decision="deny",
                        reason="missing_permission",
                        tenant=kwargs.get("tenant"),  # type: ignore[arg-type]
                        workspace=kwargs.get("workspace"),  # type: ignore[arg-type]
                    )
                    raise PermissionError(f"missing permission '{perm}'")
                # drop security metadata before invoking the wrapped function
                for key in ("roles", "actor", "tenant", "workspace"):
                    kwargs.pop(key, None)
                return func(*args, **kwargs)
            return wrapper

        return decorator
