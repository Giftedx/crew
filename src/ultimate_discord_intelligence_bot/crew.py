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

from domains.orchestration.crew import UltimateDiscordIntelligenceBotCrew, get_crew


# Backward compatibility constants
RAW_SNIPPET_MAX_LEN = 160

warnings.warn(
    "ultimate_discord_intelligence_bot.crew is deprecated. Import from ultimate_discord_intelligence_bot.crew_core instead.",
    DeprecationWarning,
    stacklevel=2,
)
create_crew = get_crew
__all__ = ["RAW_SNIPPET_MAX_LEN", "UltimateDiscordIntelligenceBotCrew", "create_crew"]
