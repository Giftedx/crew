"""Project-local metrics accessor wrapper.

Provides a stable import path ``ultimate_discord_intelligence_bot.obs.metrics``
that delegates to the top-level ``obs.metrics`` module (which owns the actual
Prometheus integration).  Tools should only import ``get_metrics`` from here
to avoid direct dependency on internal implementation details.

Design:
 - Lazy delegation: resolve underlying factories on first call.
 - Safe fallbacks: if the global module is unavailable, return inert no-op
   objects whose methods can be called safely.
 - Low cardinality: this wrapper does not enrich labels; callers must ensure
   labels remain low cardinality (tenant/workspace handled centrally where
   applicable by the underlying metrics layer or omitted entirely here).
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Protocol


class _Metric(Protocol):
    def inc(self, *args: Any, **kwargs: Any) -> None: ...

    def observe(self, *args: Any, **kwargs: Any) -> None: ...

    def set(self, *args: Any, **kwargs: Any) -> None: ...

    def add(self, *args: Any, **kwargs: Any) -> None: ...


class _NoOpMetric:
    def inc(self, *args: Any, **kwargs: Any) -> None:
        return None

    def observe(self, *args: Any, **kwargs: Any) -> None:
        return None

    def set(self, *args: Any, **kwargs: Any) -> None:
        return None

    def add(self, *args: Any, **kwargs: Any) -> None:
        return None


class _MetricsFacade:
    def __init__(self, backend: Any | None) -> None:
        self._backend = backend

    def _wrap_counter(self, labeled: Any) -> _Metric:
        if labeled is None:
            return _NoOpMetric()
        if not hasattr(labeled, "add"):
            try:
                labeled.add = labeled.inc
            except Exception:
                return _NoOpMetric()
        if not hasattr(labeled, "set"):
            labeled.set = lambda *a, **k: None
        if not hasattr(labeled, "observe"):
            labeled.observe = lambda *a, **k: None
        return labeled

    def counter(self, name: str, *_, labels: dict[str, str] | None = None, **__) -> _Metric:
        labels = labels or {}
        try:
            if self._backend and hasattr(self._backend, "CounterFactory"):
                factory = self._backend.CounterFactory
                ctr = factory(name, f"auto-generated counter: {name}", list(labels.keys()))
                labeled = ctr.labels(*labels.values())
                return self._wrap_counter(labeled)
        except Exception as exc:
            logging.getLogger(__name__).debug("counter backend failure: %s", exc)
        return _NoOpMetric()

    def gauge(self, name: str, *_, labels: dict[str, str] | None = None, **__) -> _Metric:
        labels = labels or {}
        try:
            if self._backend and hasattr(self._backend, "GaugeFactory"):
                factory = self._backend.GaugeFactory
                g = factory(name, f"auto-generated gauge: {name}", list(labels.keys()))
                labeled = g.labels(*labels.values())
                if not hasattr(labeled, "add"):
                    labeled.add = lambda v, *_a, **_k: labeled.inc(v) if hasattr(labeled, "inc") else None
                if not hasattr(labeled, "observe"):
                    labeled.observe = lambda *a, **k: None
                return labeled
        except Exception as exc:
            logging.getLogger(__name__).debug("gauge backend failure: %s", exc)
        return _NoOpMetric()

    def histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        labels = labels or {}
        try:
            if self._backend and hasattr(self._backend, "HistogramFactory"):
                factory = self._backend.HistogramFactory
                hist = factory(name, f"auto-generated histogram: {name}", list(labels.keys()))
                hist = hist.labels(*labels.values())
                hist.observe(value)
                return
        except Exception:
            return


@lru_cache(maxsize=1)
def get_metrics() -> _MetricsFacade:
    try:
        import platform.observability.metrics as backend

        return _MetricsFacade(backend)
    except Exception as exc:
        logging.getLogger(__name__).debug("metrics backend import failed: %s", exc)
        return _MetricsFacade(None)


__all__ = ["get_metrics"]
