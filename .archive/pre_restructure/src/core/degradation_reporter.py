"""Degradation / fallback reporting helper.

This module provides a very small API for recording *structured* degradation
signals (fallbacks, partial failures, timeouts) in a consistent manner. It is
feature‑flag gated via ``ENABLE_DEGRADATION_REPORTER`` so can be enabled in
staging first without overhead concerns in production.

Design principles:
 - Zero mandatory dependency on prometheus_client; metrics module supplies no‑ops if absent.
 - Tenant aware: all events automatically label tenant/workspace using ``obs.metrics.label_ctx``.
 - Low cardinality: caller supplies a short ``event_type`` token (e.g. "transcription_fallback") and ``component``;
   free‑form detail strings are stored only in an in‑memory ring buffer (not as metric labels) to avoid label explosion.
 - Bounded memory: ring buffer size default 500 events (configurable) – oldest events are dropped.
 - Optional latency attribution: if an added_latency_ms numeric value is supplied it feeds a histogram.

Future extensions (not yet implemented – keep surface minimal initially):
 - Exporter to structured log JSON lines.
 - Periodic flush to external store (persisted incidents).
 - Aggregation of repetitive events into compaction records.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import RLock
from time import time

from obs import metrics


try:  # Primary path: use the core settings facade (backed by SecureConfig)
    from core.settings import get_settings as _core_get_settings
except Exception:  # pragma: no cover - fallback in limited environments
    _core_get_settings = None


def _load_legacy_settings():
    """Load legacy Settings as a fallback when the core settings facade is unavailable."""
    try:
        from ultimate_discord_intelligence_bot.settings import Settings  # type: ignore

        return Settings()
    except Exception:  # pragma: no cover - minimal default fallback for tests

        class _DefaultSettings:
            enable_degradation_reporter = False

        return _DefaultSettings()


def get_settings():
    """
    Prefer the shared ``core.settings`` facade so feature flags and other configuration
    stay consistent across the codebase. Fall back to the legacy
    ``ultimate_discord_intelligence_bot.settings.Settings`` implementation when running
    in stripped-down test environments that may not have the core facade wired up yet.
    """
    if _core_get_settings is not None:
        return _core_get_settings()
    return _load_legacy_settings()


__all__ = [
    "DegradationEvent",
    "DegradationReporter",
    "get_degradation_reporter",
    "get_settings",
    "record_degradation",
]


@dataclass(slots=True)
class DegradationEvent:
    ts_epoch: float
    component: str
    event_type: str
    severity: str
    detail: str | None
    added_latency_ms: float | None


class DegradationReporter:
    def __init__(self, max_events: int = 500) -> None:
        self._max = max_events
        self._events: deque[DegradationEvent] = deque(maxlen=max_events)
        self._lock = RLock()

    def record(
        self,
        component: str,
        event_type: str,
        severity: str = "info",
        *,
        detail: str | None = None,
        added_latency_ms: float | None = None,
    ) -> None:
        """Record a degradation event.

        Parameters
        ----------
        component: short stable identifier (e.g. "ingest", "rerank", "vector_store")
        event_type: low cardinality token (snake_case) describing category
        severity: one of info|warn|error|critical (free form but prefer these)
        detail: optional human readable explanation (NOT placed in metric labels)
        added_latency_ms: optional numeric latency impact; feeds a histogram
        """
        settings = get_settings()
        if not getattr(settings, "enable_degradation_reporter", False):  # fast path exit
            return
        evt = DegradationEvent(time(), component, event_type, severity, detail, added_latency_ms)
        with self._lock:
            self._events.append(evt)
        # Metrics - rely on label_ctx for tenant/workspace tagging
        lbl = metrics.label_ctx()
        metrics.DEGRADATION_EVENTS.labels(lbl["tenant"], lbl["workspace"], component, event_type, severity).inc()
        if added_latency_ms is not None:
            metrics.DEGRADATION_IMPACT_LATENCY.labels(lbl["tenant"], lbl["workspace"], component, event_type).observe(
                added_latency_ms
            )

    def snapshot(self) -> list[DegradationEvent]:  # cheap copy for diagnostics/tests
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


_singleton: DegradationReporter | None = None
_singleton_lock = RLock()


def get_degradation_reporter() -> DegradationReporter:
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:  # double-checked
                _singleton = DegradationReporter()
    return _singleton


def record_degradation(
    component: str,
    event_type: str,
    severity: str = "info",
    *,
    detail: str | None = None,
    added_latency_ms: float | None = None,
) -> None:
    """Convenience wrapper to record via the process singleton."""
    get_degradation_reporter().record(
        component=component,
        event_type=event_type,
        severity=severity,
        detail=detail,
        added_latency_ms=added_latency_ms,
    )
