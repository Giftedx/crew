"""Compatibility shim for logging in ultimate_discord_intelligence_bot.obs

This module re-exports the logging API from platform.observability.logging
to preserve the historical import path.
"""

from platform.observability.logging import JsonLogger, logger


__all__ = ["JsonLogger", "logger"]
