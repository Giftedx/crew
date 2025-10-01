from __future__ import annotations

import logging

from fastapi import FastAPI


def register_alert_routes(app: FastAPI) -> None:
    try:
        from ops.alert_adapter import alert_router

        app.include_router(alert_router)
    except Exception as exc:  # pragma: no cover - optional path
        logging.debug("alert router wiring skipped: %s", exc)


__all__ = ["register_alert_routes"]
