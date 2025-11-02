"""Creator features for content analysis and automation.

This module provides high-level creator features including Live Clip Radar,
Repurposing Studio, and Episode Intelligence Pack.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .clip_radar_agent import LiveClipRadarAgent
from .clip_radar_models import (
    ChatMessage,
    ClipCandidate,
    ClipMetrics,
    ClipProcessingJob,
    ClipRadarResult,
    ClipStatus,
    MomentType,
    MonitoringConfig,
    PlatformType,
    SentimentScore,
    StreamInfo,
    StreamMarker,
    StreamStatus,
    ViralMoment,
)


if TYPE_CHECKING:
    from .episode_intelligence import EpisodeIntelligencePack
    from .intelligence_agent import EpisodeIntelligenceAgent

# Optional imports for ML-dependent features
# Catch all exceptions (not just ImportError) because ML dependencies may have broken dependency chains
try:
    from .episode_intelligence import EpisodeIntelligencePack
    from .intelligence_agent import EpisodeIntelligenceAgent
except Exception:
    # Graceful fallback when ML dependencies unavailable
    EpisodeIntelligencePack = None  # type: ignore[assignment,misc]
    EpisodeIntelligenceAgent = None  # type: ignore[assignment,misc]
from .intelligence_models import (
    AgendaItem,
    AnalysisMetrics,
    BrandSafetyAnalysis,
    ClaimStatus,
    DefamationRisk,
    EpisodeIntelligence,
    ExportTemplate,
    FactCheckableClaim,
    GuestInfo,
    IntelligenceConfig,
    IntelligenceResult,
    NotableQuotation,
    OutboundLink,
    RiskLevel,
    ThumbnailSuggestion,
)
from .live_clip_radar import LiveClipRadar
from .repurposing_agent import RepurposingAgent
from .repurposing_models import (
    AspectRatio,
    CaptionStyle,
    FFmpegConfig,
    PlatformHook,
    RepurposingConfig,
    RepurposingJob,
    RepurposingResult,
    VideoClip,
)
from .repurposing_models import (
    ClipCandidate as RepurposingClipCandidate,
)
from .repurposing_models import (
    ClipStatus as RepurposingClipStatus,
)
from .repurposing_models import (
    PlatformType as RepurposingPlatformType,
)
from .repurposing_studio import RepurposingStudio


__all__ = [
    "AgendaItem",
    "AnalysisMetrics",
    "AspectRatio",
    "BrandSafetyAnalysis",
    "CaptionStyle",
    "ChatMessage",
    "ClaimStatus",
    "ClipCandidate",
    "ClipMetrics",
    "ClipProcessingJob",
    "ClipRadarResult",
    "ClipStatus",
    "DefamationRisk",
    "EpisodeIntelligence",
    "EpisodeIntelligenceAgent",
    "EpisodeIntelligencePack",
    "ExportTemplate",
    "FFmpegConfig",
    "FactCheckableClaim",
    "GuestInfo",
    "IntelligenceConfig",
    "IntelligenceResult",
    "LiveClipRadar",
    "LiveClipRadarAgent",
    "MomentType",
    "MonitoringConfig",
    "NotableQuotation",
    "OutboundLink",
    "PlatformHook",
    "PlatformType",
    "RepurposingAgent",
    # Explicitly export repurposing aliases to avoid unused import warnings
    "RepurposingClipCandidate",
    "RepurposingClipStatus",
    "RepurposingConfig",
    "RepurposingJob",
    "RepurposingPlatformType",
    "RepurposingResult",
    "RepurposingStudio",
    "RiskLevel",
    "SentimentScore",
    "StreamInfo",
    "StreamMarker",
    "StreamStatus",
    "ThumbnailSuggestion",
    "VideoClip",
    "ViralMoment",
]
