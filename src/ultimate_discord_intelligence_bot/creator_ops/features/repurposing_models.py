"""
Data models for the Repurposing Studio feature.
Defines structures for video clips, platform-specific hooks, and metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PlatformType(str, Enum):
    """Supported platforms for repurposing."""

    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK = "tiktok"
    INSTAGRAM_REELS = "instagram_reels"
    X = "x"


class AspectRatio(str, Enum):
    """Supported aspect ratios for different platforms."""

    VERTICAL_9_16 = "9:16"  # TikTok, Instagram Reels, YouTube Shorts
    SQUARE_1_1 = "1:1"  # Instagram Posts
    LANDSCAPE_16_9 = "16:9"  # YouTube, X


class ClipStatus(str, Enum):
    """Status of clip processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VideoClip:
    """Represents a video clip extracted from an episode."""

    clip_id: str
    episode_id: str
    title: str
    description: str
    start_time: float
    end_time: float
    duration: float
    aspect_ratio: AspectRatio
    resolution: str
    file_path: str
    thumbnail_path: str
    captions_path: str
    status: ClipStatus
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlatformHook:
    """Platform-specific hook for a clip."""

    platform: PlatformType
    hook_text: str
    hashtags: list[str]
    mentions: list[str]
    call_to_action: str
    trending_topics: list[str]
    optimal_posting_time: str | None = None
    engagement_tips: list[str] = field(default_factory=list)


@dataclass
class RepurposingJob:
    """Represents a repurposing job for an episode."""

    job_id: str
    episode_id: str
    episode_title: str
    episode_duration: float
    target_platforms: list[PlatformType]
    clip_count: int
    status: ClipStatus
    created_at: datetime
    updated_at: datetime
    clips: list[VideoClip] = field(default_factory=list)
    hooks: list[PlatformHook] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClipCandidate:
    """Represents a candidate segment for clip creation."""

    start_time: float
    end_time: float
    duration: float
    transcript_segment: str
    speakers: list[str]
    topics: list[str]
    sentiment_score: float
    engagement_score: float
    viral_potential: float
    reason: str


@dataclass
class FFmpegConfig:
    """Configuration for FFmpeg processing."""

    input_file: str
    output_file: str
    start_time: float
    end_time: float
    aspect_ratio: AspectRatio
    resolution: str
    fps: int = 30
    bitrate: str = "2000k"
    audio_bitrate: str = "128k"
    filters: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class CaptionStyle:
    """Style configuration for captions."""

    font_family: str = "Arial"
    font_size: int = 24
    font_color: str = "white"
    background_color: str = "black"
    background_opacity: float = 0.7
    position: str = "bottom"
    margin: int = 20
    max_lines: int = 2
    fade_in_duration: float = 0.5
    fade_out_duration: float = 0.5


@dataclass
class RepurposingConfig:
    """Configuration for repurposing process."""

    min_clip_duration: float = 15.0
    max_clip_duration: float = 60.0
    target_clip_count: int = 5
    aspect_ratios: dict[PlatformType, AspectRatio] = field(
        default_factory=lambda: {
            PlatformType.YOUTUBE_SHORTS: AspectRatio.VERTICAL_9_16,
            PlatformType.TIKTOK: AspectRatio.VERTICAL_9_16,
            PlatformType.INSTAGRAM_REELS: AspectRatio.VERTICAL_9_16,
            PlatformType.X: AspectRatio.LANDSCAPE_16_9,
        }
    )
    resolutions: dict[PlatformType, str] = field(
        default_factory=lambda: {
            PlatformType.YOUTUBE_SHORTS: "1080x1920",
            PlatformType.TIKTOK: "1080x1920",
            PlatformType.INSTAGRAM_REELS: "1080x1920",
            PlatformType.X: "1920x1080",
        }
    )
    caption_style: CaptionStyle = field(default_factory=CaptionStyle)
    include_speaker_labels: bool = True
    include_timestamps: bool = False
    auto_generate_hooks: bool = True
    optimize_for_platform: bool = True


@dataclass
class RepurposingResult:
    """Result of repurposing process."""

    job_id: str
    success: bool
    clips_created: int
    total_duration: float
    platforms_targeted: list[PlatformType]
    output_files: list[str]
    error_message: str | None = None
    processing_time: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
