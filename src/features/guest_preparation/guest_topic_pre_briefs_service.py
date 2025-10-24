"""Compatibility wrapper for moved module.

This module re-exports the unified implementation under
`ultimate_discord_intelligence_bot.features.guest_preparation`.
"""

from __future__ import annotations

from ultimate_discord_intelligence_bot.features.guest_preparation.guest_topic_pre_briefs_service import (
    ArgumentAnalysis,
    AudienceReactionPrediction,
    GuestTopicPreBriefsResult,
    GuestTopicPreBriefsService,
    InterviewPreparationBrief,
    get_guest_topic_pre_briefs_service,
)


__all__ = [
    "ArgumentAnalysis",
    "AudienceReactionPrediction",
    "GuestTopicPreBriefsResult",
    "GuestTopicPreBriefsService",
    "InterviewPreparationBrief",
    "get_guest_topic_pre_briefs_service",
]
