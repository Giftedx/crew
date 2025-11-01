from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterable


class PluginPermissionError(Exception):
    """Raised when a plugin attempts to use a capability without permission."""


class PermissionGuard:
    """Simple guard that checks a plugin's required scopes against grants."""

    def __init__(self, granted_scopes: Iterable[str]):
        self._granted: set[str] = set(granted_scopes)

    def require(self, scopes: Iterable[str]) -> None:
        missing = set(scopes) - self._granted
        if missing:
            raise PluginPermissionError(f"Missing permission(s): {', '.join(sorted(missing))}")
