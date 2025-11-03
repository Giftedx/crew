"""In-memory incident tracking used for tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from platform.time import default_utc_now
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import builtins
    from datetime import datetime


@dataclass
class Incident:
    id: int
    title: str
    severity: str
    status: str = "open"
    created_at: datetime = field(default_factory=default_utc_now)
    acknowledged_by: str | None = None
    resolved_at: datetime | None = None


class IncidentManager:
    """Minimal incident tracker."""

    def __init__(self) -> None:
        self._incidents: dict[int, Incident] = {}
        self._next_id = 1

    def open(self, title: str, severity: str = "minor") -> int:
        inc = Incident(id=self._next_id, title=title, severity=severity)
        self._incidents[self._next_id] = inc
        self._next_id += 1
        return inc.id

    def ack(self, incident_id: int, user: str) -> None:
        inc = self._incidents[incident_id]
        inc.status = "ack"
        inc.acknowledged_by = user

    def resolve(self, incident_id: int) -> None:
        inc = self._incidents[incident_id]
        inc.status = "resolved"
        inc.resolved_at = default_utc_now()

    def get(self, incident_id: int) -> Incident:
        return self._incidents[incident_id]

    def list(self) -> builtins.list[Incident]:
        return list(self._incidents.values())


manager = IncidentManager()
__all__ = ["Incident", "IncidentManager", "manager"]
