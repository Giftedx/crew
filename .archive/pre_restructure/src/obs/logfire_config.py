"""Logfire initialization and instrumentation helpers.

This module safely initializes Logfire observability when enabled in settings,
without imposing runtime dependencies when disabled. It guards all imports so
that environments without logfire/opentelemetry continue to function normally.

Feature flag: ENABLE_LOGFIRE (default: false)
Required: LOGFIRE_TOKEN (if sending to SaaS) unless LOGFIRE_SEND_TO_LOGFIRE=false

Usage:
    from obs.logfire_config import setup_logfire
    setup_logfire(app)  # app is a FastAPI instance (optional)
"""

from __future__ import annotations

import logging
from typing import Any

from core.secure_config import get_config


logger = logging.getLogger(__name__)


def setup_logfire(app: Any | None = None) -> bool:
    """Initialize Logfire if enabled.

    Args:
        app: Optional FastAPI app to instrument

    Returns:
        True if Logfire initialized, False otherwise
    """
    cfg = get_config()
    if not getattr(cfg, "enable_logfire", False):
        logger.debug("Logfire disabled via feature flag")
        return False

    try:
        import logfire
    except Exception as exc:  # pragma: no cover - import guard
        logger.warning("Logfire requested but not available: %s", exc)
        return False

    try:
        # Configure Logfire
        kwargs: dict[str, Any] = {
            "project_name": getattr(cfg, "logfire_project_name", "discord-intelligence-bot"),
            "service_version": getattr(cfg, "logfire_service_version", None),
            "send_to_logfire": getattr(cfg, "logfire_send_to_logfire", True),
        }
        token = getattr(cfg, "logfire_token", None)
        if token:
            kwargs["token"] = token
        elif kwargs.get("send_to_logfire"):
            logger.warning("LOGFIRE_TOKEN not set; disabling send_to_logfire to avoid errors")
            kwargs["send_to_logfire"] = False

        logfire.configure(**kwargs)

        # Instrument libraries
        try:
            if app is not None:
                logfire.instrument_fastapi(app)
        except Exception as exc:
            logger.debug("FastAPI instrumentation skipped: %s", exc)
        try:
            logfire.instrument_httpx()
        except Exception as exc:
            logger.debug("httpx instrumentation skipped: %s", exc)

        logger.info("Logfire initialized (send_to_logfire=%s)", kwargs.get("send_to_logfire"))
        return True
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning("Failed to initialize Logfire: %s", exc)
        return False


__all__ = ["setup_logfire"]
