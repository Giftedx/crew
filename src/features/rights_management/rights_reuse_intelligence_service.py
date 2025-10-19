from __future__ import annotations

"""Compatibility wrapper for moved module.

This module re-exports the unified implementation under
`ultimate_discord_intelligence_bot.features.rights_management`.
"""

from ultimate_discord_intelligence_bot.features.rights_management.rights_reuse_intelligence_service import (
    ContentFragment,
    LicenseInfo,
    ReuseAnalysis,
    RightsReuseIntelligenceService,
    get_rights_reuse_intelligence_service,
)

__all__ = [
    "RightsReuseIntelligenceService",
    "get_rights_reuse_intelligence_service",
    "ContentFragment",
    "LicenseInfo",
    "ReuseAnalysis",
]
