"""Scoped Discord bot core class (optional-dependency safe).

This module must import cleanly even when discord.py is not installed.
Command and event registrations are isolated in registrar modules.
"""

from __future__ import annotations

import logging
from typing import Any


try:  # optional dependency
    import discord
    from discord.ext import commands

    _DISCORD_AVAILABLE = True
except Exception:  # pragma: no cover - CI safe
    _DISCORD_AVAILABLE = False
    discord = None
    commands = None

from .registrars.analytics import register_analytics_commands
from .registrars.dev import register_dev_commands
from .registrars.events import register_events
from .registrars.openai import register_openai_commands
from .registrars.ops import register_ops_commands
from .registrars.system import register_system_commands
from .timeline import TimelineManager


log = logging.getLogger(__name__)


class ScopedCommandBot:
    """Discord bot with strictly scoped command interface."""

    def __init__(self) -> None:
        self.timeline_manager = TimelineManager()
        self.analysis_results_cache: dict[str, Any] = {}
        self.system_metrics: dict[str, Any] = {}

        if _DISCORD_AVAILABLE:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True
            self.bot = commands.Bot(
                command_prefix="!",
                intents=intents,
                description="Ultimate Discord Intelligence Bot - Scoped",
            )
            self._register_scoped_commands()
        else:
            self.bot = None  # type: ignore

    def _register_scoped_commands(self) -> None:
        if not self.bot:
            return
        register_system_commands(self)
        register_ops_commands(self)
        register_dev_commands(self)
        register_analytics_commands(self)
        register_openai_commands(self)
        register_events(self)

    async def start(self, token: str) -> None:
        if not _DISCORD_AVAILABLE or not self.bot:
            log.warning("Discord not available; cannot start bot")
            return
        await self.bot.start(token)


__all__ = ["ScopedCommandBot"]
