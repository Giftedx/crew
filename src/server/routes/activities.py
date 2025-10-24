from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from fastapi import FastAPI, Request


def register_activities_echo(app: FastAPI, settings: Any) -> None:
    try:
        import os as _os

        if _os.getenv("ENABLE_ACTIVITIES_ECHO", "0").lower() not in (
            "1",
            "true",
            "yes",
            "on",
        ):
            return

        @app.get("/activities/echo")
        def _activities_echo(request: Request) -> dict:
            """Return basic request information for debugging client wiring.

            Includes method, url path, query params, selected headers, and client info.
            Avoids echoing bodies to keep responses lightweight and safe by default.
            """

            interesting = [
                "origin",
                "referer",
                "user-agent",
                "accept",
                "accept-language",
                "x-forwarded-for",
                "cf-connecting-ip",
            ]
            headers = {k: v for k, v in request.headers.items() if k.lower() in interesting}
            client_host = None
            try:
                if request.client:
                    client_host = request.client.host
            except Exception:
                client_host = None
            return {
                "method": request.method,
                "path": request.url.path,
                "query": dict(getattr(request, "query_params", {}) or {}),
                "headers": headers,
                "client": client_host,
                "component": "activities-echo",
            }
    except Exception as exc:  # pragma: no cover - optional path
        logging.debug("activities echo wiring skipped: %s", exc)


__all__ = ["register_activities_echo"]
