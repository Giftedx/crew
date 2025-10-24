"""Compatibility wrapper for moved module.

This module re-exports the unified implementation under
`ultimate_discord_intelligence_bot.features.rights_management`.
"""

from __future__ import annotations

from ultimate_discord_intelligence_bot.features.rights_management.rights_reuse_intelligence_service import (
    ContentFragment,
    LicenseInfo,
    ReuseAnalysis,
    RightsReuseIntelligenceService,
    get_rights_reuse_intelligence_service,
)


__all__ = [
    "ContentFragment",
    "LicenseInfo",
    "ReuseAnalysis",
    "RightsReuseIntelligenceService",
    "get_rights_reuse_intelligence_service",
]
