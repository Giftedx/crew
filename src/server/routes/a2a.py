from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from fastapi import FastAPI


def register_a2a_router(app: FastAPI, settings: Any) -> None:
    try:
        import os as _os

        if _os.getenv("ENABLE_A2A_API", "0").lower() in ("1", "true", "yes", "on"):
            try:
                from server.a2a_router import router as a2a_router  # type: ignore

                app.include_router(a2a_router)
            except Exception as exc:  # pragma: no cover - optional path
                logging.debug("a2a router wiring skipped: %s", exc)
    except Exception:  # pragma: no cover - environment access issues
        pass


__all__ = ["register_a2a_router"]
