from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from fastapi import FastAPI


def register_a2a_router(app: FastAPI, settings: Any) -> None:
    try:
        import os as _os

        flag = getattr(settings, "enable_a2a_api", None)
        enabled = None
        if flag is not None:
            enabled = bool(flag)
        if enabled is None:
            enabled = _os.getenv("ENABLE_A2A_API", "0").lower() in ("1", "true", "yes", "on")
        if enabled:
            try:
                from server.a2a_router import router as a2a_router  # type: ignore

                app.include_router(a2a_router)
            except Exception as exc:  # pragma: no cover - optional path
                logging.debug("a2a router wiring skipped: %s", exc)
        else:
            logging.debug("A2A router disabled by settings/env")
    except Exception:  # pragma: no cover - environment access issues
        pass


__all__ = ["register_a2a_router"]
