from __future__ import annotations

"""Compatibility wrapper for moved module.

This module re-exports the unified implementation under
`ultimate_discord_intelligence_bot.features.guest_preparation`.
"""

from ultimate_discord_intelligence_bot.features.guest_preparation.guest_topic_pre_briefs_service import (
    ArgumentAnalysis,
    AudienceReactionPrediction,
    GuestTopicPreBriefsResult,
    GuestTopicPreBriefsService,
    InterviewPreparationBrief,
    get_guest_topic_pre_briefs_service,
)

__all__ = [
    "GuestTopicPreBriefsService",
    "get_guest_topic_pre_briefs_service",
    "ArgumentAnalysis",
    "AudienceReactionPrediction",
    "InterviewPreparationBrief",
    "GuestTopicPreBriefsResult",
]
