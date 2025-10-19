"""
Data models for Live Clip Radar feature.
Provides models for viral moment detection, clip generation, and stream monitoring.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PlatformType(str, Enum):
    """Supported platforms for Live Clip Radar."""

    YOUTUBE = "youtube"
    TWITCH = "twitch"


class MomentType(str, Enum):
    """Types of viral moments detected."""

    CHAT_VELOCITY = "chat_velocity"
    SENTIMENT_FLIP = "sentiment_flip"
    LAUGHTER = "laughter"
    EMOTIONAL_PEAK = "emotional_peak"
    CONTROVERSY = "controversy"
    BREAKING_NEWS = "breaking_news"


class ClipStatus(str, Enum):
    """Status of clip generation."""

    DETECTED = "detected"
    PROCESSING = "processing"
    GENERATED = "generated"
    PUBLISHED = "published"
    FAILED = "failed"


class StreamStatus(str, Enum):
    """Status of stream monitoring."""

    OFFLINE = "offline"
    ONLINE = "online"
    MONITORING = "monitoring"
    ERROR = "error"


@dataclass
class ChatMessage:
    """Chat message from live stream."""

    message_id: str
    user_id: str
    username: str
    message: str
    timestamp: datetime
    platform: PlatformType
    channel_id: str
    stream_id: str
    emotes: list[str] = field(default_factory=list)
    badges: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SentimentScore:
    """Sentiment analysis result."""

    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    label: str  # "positive", "negative", "neutral"
    keywords: list[str] = field(default_factory=list)


@dataclass
class ViralMoment:
    """Detected viral moment."""

    moment_id: str
    moment_type: MomentType
    timestamp: datetime
    platform: PlatformType
    channel_id: str
    stream_id: str
    confidence: float  # 0.0 to 1.0
    trigger_message: ChatMessage | None = None
    context_messages: list[ChatMessage] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    description: str = ""
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class ClipCandidate:
    """Generated clip candidate."""

    clip_id: str
    moment_id: str
    title: str
    description: str
    start_time: float  # seconds from stream start
    end_time: float  # seconds from stream start
    duration: float  # clip duration in seconds
    platform: PlatformType
    stream_id: str
    channel_id: str
    status: ClipStatus
    viral_moment: ViralMoment
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class StreamMarker:
    """Stream marker created for viral moment."""

    marker_id: str
    platform: PlatformType
    stream_id: str
    timestamp: float  # seconds from stream start
    description: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StreamInfo:
    """Information about a live stream."""

    stream_id: str
    channel_id: str
    platform: PlatformType
    title: str
    description: str
    status: StreamStatus
    started_at: datetime
    viewer_count: int
    language: str
    category: str
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Configuration for stream monitoring."""

    platform: PlatformType
    channel_id: str
    enabled: bool = True
    detection_sensitivity: float = 0.7  # 0.0 to 1.0
    chat_velocity_threshold: float = 3.0  # multiplier for baseline
    sentiment_flip_threshold: float = 0.5  # sentiment change threshold
    laughter_keywords: list[str] = field(default_factory=lambda: ["lol", "lmao", "haha", "😂", "🤣"])
    min_clip_duration: float = 30.0  # minimum clip duration in seconds
    max_clip_duration: float = 90.0  # maximum clip duration in seconds
    auto_generate_clips: bool = True
    auto_create_markers: bool = True
    notification_webhook: str | None = None


@dataclass
class ClipRadarResult:
    """Result from Live Clip Radar operation."""

    success: bool
    moments_detected: int = 0
    clips_generated: int = 0
    markers_created: int = 0
    errors: list[str] = field(default_factory=list)
    processing_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# Pydantic models for API serialization
class ChatMessageModel(BaseModel):
    """Pydantic model for ChatMessage."""

    message_id: str
    user_id: str
    username: str
    message: str
    timestamp: datetime
    platform: PlatformType
    channel_id: str
    stream_id: str
    emotes: list[str] = Field(default_factory=list)
    badges: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class SentimentScoreModel(BaseModel):
    """Pydantic model for SentimentScore."""

    score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    label: str
    keywords: list[str] = Field(default_factory=list)


class ViralMomentModel(BaseModel):
    """Pydantic model for ViralMoment."""

    moment_id: str
    moment_type: MomentType
    timestamp: datetime
    platform: PlatformType
    channel_id: str
    stream_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    trigger_message: ChatMessageModel | None = None
    context_messages: list[ChatMessageModel] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    description: str = ""
    detected_at: datetime

    class Config:
        use_enum_values = True


class ClipCandidateModel(BaseModel):
    """Pydantic model for ClipCandidate."""

    clip_id: str
    moment_id: str
    title: str
    description: str
    start_time: float = Field(ge=0.0)
    end_time: float = Field(ge=0.0)
    duration: float = Field(ge=0.0)
    platform: PlatformType
    stream_id: str
    channel_id: str
    status: ClipStatus
    viral_moment: ViralMomentModel
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True


class StreamMarkerModel(BaseModel):
    """Pydantic model for StreamMarker."""

    marker_id: str
    platform: PlatformType
    stream_id: str
    timestamp: float = Field(ge=0.0)
    description: str
    created_at: datetime

    class Config:
        use_enum_values = True


class StreamInfoModel(BaseModel):
    """Pydantic model for StreamInfo."""

    stream_id: str
    channel_id: str
    platform: PlatformType
    title: str
    description: str
    status: StreamStatus
    started_at: datetime
    viewer_count: int = Field(ge=0)
    language: str
    category: str
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class MonitoringConfigModel(BaseModel):
    """Pydantic model for MonitoringConfig."""

    platform: PlatformType
    channel_id: str
    enabled: bool = True
    detection_sensitivity: float = Field(ge=0.0, le=1.0, default=0.7)
    chat_velocity_threshold: float = Field(ge=1.0, default=3.0)
    sentiment_flip_threshold: float = Field(ge=0.0, le=1.0, default=0.5)
    laughter_keywords: list[str] = Field(default_factory=lambda: ["lol", "lmao", "haha", "😂", "🤣"])
    min_clip_duration: float = Field(ge=10.0, default=30.0)
    max_clip_duration: float = Field(ge=30.0, default=90.0)
    auto_generate_clips: bool = True
    auto_create_markers: bool = True
    notification_webhook: str | None = None

    class Config:
        use_enum_values = True


class ClipRadarResultModel(BaseModel):
    """Pydantic model for ClipRadarResult."""

    success: bool
    moments_detected: int = Field(ge=0, default=0)
    clips_generated: int = Field(ge=0, default=0)
    markers_created: int = Field(ge=0, default=0)
    errors: list[str] = Field(default_factory=list)
    processing_time: float = Field(ge=0.0, default=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


# Additional models for clip generation and processing
@dataclass
class ClipProcessingJob:
    """Job for processing a clip candidate."""

    job_id: str
    clip_candidate: ClipCandidate
    status: ClipStatus
    progress: float = 0.0  # 0.0 to 1.0
    error_message: str | None = None
    output_path: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ClipMetrics:
    """Metrics for a generated clip."""

    clip_id: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float = 0.0
    click_through_rate: float = 0.0
    retention_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class ClipProcessingJobModel(BaseModel):
    """Pydantic model for ClipProcessingJob."""

    job_id: str
    clip_candidate: ClipCandidateModel
    status: ClipStatus
    progress: float = Field(ge=0.0, le=1.0, default=0.0)
    error_message: str | None = None
    output_path: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True


class ClipMetricsModel(BaseModel):
    """Pydantic model for ClipMetrics."""

    clip_id: str
    views: int = Field(ge=0, default=0)
    likes: int = Field(ge=0, default=0)
    comments: int = Field(ge=0, default=0)
    shares: int = Field(ge=0, default=0)
    engagement_rate: float = Field(ge=0.0, default=0.0)
    click_through_rate: float = Field(ge=0.0, default=0.0)
    retention_rate: float = Field(ge=0.0, default=0.0)
    last_updated: datetime

    class Config:
        use_enum_values = True
