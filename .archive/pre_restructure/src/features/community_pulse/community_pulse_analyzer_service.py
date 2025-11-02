"""Compatibility wrapper for moved module.

This module re-exports the unified implementation under
`ultimate_discord_intelligence_bot.features.community_pulse`.
"""

from __future__ import annotations

from ultimate_discord_intelligence_bot.features.community_pulse.community_pulse_analyzer_service import (
    CommunityPulseAnalyzerService,
    get_community_pulse_analyzer_service,
)


__all__ = [
    "CommunityPulseAnalyzerService",
    "get_community_pulse_analyzer_service",
]
