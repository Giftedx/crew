"""Backward compatibility shim for deprecated crew module.

This module provides compatibility for tests and legacy code importing
from ultimate_discord_intelligence_bot.crew. New code should import
from ultimate_discord_intelligence_bot.crew_core instead.

Migration:
    # Old (still works):
    from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew

    # New (recommended):
    from ultimate_discord_intelligence_bot.crew_core import UltimateDiscordIntelligenceBotCrew, get_crew
"""

from __future__ import annotations

import warnings

from ultimate_discord_intelligence_bot.crew_core import UltimateDiscordIntelligenceBotCrew, get_crew


warnings.warn(
    "ultimate_discord_intelligence_bot.crew is deprecated. "
    "Import from ultimate_discord_intelligence_bot.crew_core instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Backward compatibility: alias get_crew as create_crew
create_crew = get_crew

__all__ = ["UltimateDiscordIntelligenceBotCrew", "create_crew"]
