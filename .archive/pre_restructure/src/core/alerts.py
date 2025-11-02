"""Simple in-memory alert manager used by ops tools."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AlertManager:
    """Store alert messages for later retrieval.

    This lightweight helper keeps alerts in memory so that tests and ops
    commands can retrieve and clear them.  A production system would route
    alerts to external services instead.
    """

    events: list[str] = field(default_factory=list)

    def record(self, message: str) -> None:
        """Record an alert ``message``."""

        self.events.append(message)

    def drain(self) -> list[str]:
        """Return and clear all pending alerts."""

        out = list(self.events)
        self.events.clear()
        return out


alerts = AlertManager()

__all__ = ["AlertManager", "alerts"]
