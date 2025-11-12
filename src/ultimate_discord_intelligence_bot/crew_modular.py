"""DEPRECATED: crew_modular shim.

This module exists for backward compatibility. The modular crew implementation
was consolidated into ``ultimate_discord_intelligence_bot.crew_core``.
Import from ``crew_core`` going forward.
"""

from __future__ import annotations

from .crew_core import UltimateDiscordIntelligenceBotCrew, get_crew


__all__ = ["UltimateDiscordIntelligenceBotCrew", "get_crew"]
