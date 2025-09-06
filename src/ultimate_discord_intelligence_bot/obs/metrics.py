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


class _Metric(Protocol):  # pragma: no cover - structural typing helper
    def inc(self, *args: Any, **kwargs: Any) -> None: ...
    def observe(self, *args: Any, **kwargs: Any) -> None: ...


class _NoOpMetric:  # pragma: no cover - trivial
    def inc(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        return None

    def observe(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        return None


class _MetricsFacade:
    def __init__(self, backend: Any | None) -> None:
        self._backend = backend

    def counter(self, name: str, labels: dict[str, str] | None = None) -> _Metric:
        labels = labels or {}
        try:
            if self._backend and hasattr(self._backend, "CounterFactory"):
                factory = getattr(self._backend, "CounterFactory")
                ctr = factory(name, f"auto-generated counter: {name}", list(labels.keys()))
                return ctr.labels(*labels.values())  # type: ignore[return-value]
        except Exception as exc:  # pragma: no cover - fallback
            logging.getLogger(__name__).debug("counter backend failure: %s", exc)
        return _NoOpMetric()

    def histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        labels = labels or {}
        try:
            if self._backend and hasattr(self._backend, "HistogramFactory"):
                factory = getattr(self._backend, "HistogramFactory")
                hist = factory(name, f"auto-generated histogram: {name}", list(labels.keys()))
                hist = hist.labels(*labels.values())
                hist.observe(value)
                return
        except Exception:  # pragma: no cover - fallback
            return


@lru_cache(maxsize=1)
def get_metrics() -> _MetricsFacade:
    # Delayed import to avoid hard dependency at module import time.
    try:  # pragma: no cover - normal path
        import obs.metrics as backend  # type: ignore  # noqa: WPS433,E402,PLC0415 (intentional lazy import for optional dependency)

        return _MetricsFacade(backend)
    except Exception as exc:  # pragma: no cover - fallback path
        logging.getLogger(__name__).debug("metrics backend import failed: %s", exc)
        return _MetricsFacade(None)


__all__ = ["get_metrics"]
