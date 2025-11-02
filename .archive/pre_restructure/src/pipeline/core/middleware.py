from __future__ import annotations

from typing import Any, Protocol


class Middleware(Protocol):
    """Middleware hooks around Step execution.

    Hooks are optional; implement what's needed. Keep low-cardinality labels.
    """

    def before(self, context: dict[str, Any]) -> None:
        """Called before step.run."""
        ...

    def after(self, context: dict[str, Any], result: dict[str, Any]) -> None:
        """Called after step.run with result."""
        ...

    def on_error(self, context: dict[str, Any], error: Exception) -> None:
        """Called when step.run raises; MUST NOT raise."""
        ...
