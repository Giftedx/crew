from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class DegradationEvent:
    component: str
    event_type: str
    severity: str = "info"
    detail: str | None = None
    added_latency_ms: float | None = None
    ts_epoch: float = field(default_factory=lambda: time.time())


class DegradationReporter:
    def __init__(self, max_events: int = 1000) -> None:
        self._events: list[DegradationEvent] = []
        self._max = max(1, int(max_events))

    def record(
        self,
        *,
        component: str,
        event_type: str,
        severity: str = "info",
        detail: str | None = None,
        added_latency_ms: float | None = None,
    ) -> DegradationEvent:
        ev = DegradationEvent(
            component=component,
            event_type=event_type,
            severity=severity,
            detail=detail,
            added_latency_ms=added_latency_ms,
        )
        self._events.append(ev)
        if len(self._events) > self._max:
            # keep most recent
            self._events = self._events[-self._max :]
        return ev

    def snapshot(self) -> list[DegradationEvent]:
        return list(self._events)


_GLOBAL_REPORTER = DegradationReporter()


def get_degradation_reporter() -> DegradationReporter:
    return _GLOBAL_REPORTER


def record_degradation(
    *,
    component: str,
    event_type: str,
    severity: str = "info",
    detail: str | None = None,
    added_latency_ms: float | None = None,
) -> DegradationEvent:
    return _GLOBAL_REPORTER.record(
        component=component,
        event_type=event_type,
        severity=severity,
        detail=detail,
        added_latency_ms=added_latency_ms,
    )


__all__ = [
    "DegradationEvent",
    "DegradationReporter",
    "get_degradation_reporter",
    "record_degradation",
]
