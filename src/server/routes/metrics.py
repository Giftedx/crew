from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Response
from obs import metrics


def register_metrics_endpoint(app: FastAPI, settings: Any) -> None:
    """Register Prometheus metrics exposition endpoint if enabled.

    This mirrors the prior inline behavior in server.app, including:
    - env fallback for enable flag
    - coercion of pydantic FieldInfo default
    - storing the path on app.state for middleware exclusions
    """

    try:
        enable_prom = getattr(settings, "enable_prometheus_endpoint", False)
        if not enable_prom:
            import os as _os

            enable_prom = _os.getenv("ENABLE_PROMETHEUS_ENDPOINT", "0").lower() in (
                "1",
                "true",
                "yes",
                "on",
            )
        if not enable_prom:
            return

        path = getattr(settings, "prometheus_endpoint_path", "/metrics")
        # Pydantic FieldInfo may leak through if Settings not fully instantiated; coerce to str
        try:
            from pydantic.fields import FieldInfo  # type: ignore

            if isinstance(path, FieldInfo):  # type: ignore
                path = getattr(path, "default", "/metrics")  # type: ignore
        except Exception:  # pragma: no cover - pydantic absent
            pass

        @app.get(str(path))
        def _metrics():
            data = metrics.render()
            return Response(data, status_code=200, media_type="text/plain; version=0.0.4")

        # Persist metrics path to application state for middleware
        try:  # pragma: no cover - defensive
            app.state.metrics_path = str(path)  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            app._metrics_path = str(path)
    except Exception as exc:  # pragma: no cover - defensive
        logging.debug("metrics endpoint registration skipped: %s", exc)


__all__ = ["register_metrics_endpoint"]
