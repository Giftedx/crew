from __future__ import annotations

import logging

from fastapi import FastAPI


def register_archive_routes(app: FastAPI) -> None:
    """Optionally include the archive API router if available."""
    try:
        from archive.discord_store.api import api_router  # type: ignore

        if api_router is not None:
            try:
                app.include_router(api_router)
            except Exception as exc:
                logging.debug(f"Failed to include archive API router: {exc}")
    except Exception:  # pragma: no cover - optional dependency path
        pass


__all__ = ["register_archive_routes"]
