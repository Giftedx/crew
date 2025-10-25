"""Web automation tools for browser interactions."""

from __future__ import annotations

try:
    from ultimate_discord_intelligence_bot.tools.web.playwright_automation_tool import PlaywrightAutomationTool
    __all__ = ["PlaywrightAutomationTool"]
except ImportError:
    __all__ = []
