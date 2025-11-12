"""Compatibility shim for logfire_config in ultimate_discord_intelligence_bot.obs

This module re-exports the logfire_config API from platform.observability.logfire_config
to preserve the historical import path.
"""

from platform.observability.logfire_config import setup_logfire


__all__ = ["setup_logfire"]
