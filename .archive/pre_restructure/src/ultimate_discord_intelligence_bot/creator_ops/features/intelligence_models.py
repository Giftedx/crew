"""
Data models for the Episode Intelligence Pack feature.
Defines structures for structured show notes, analysis, and export formats.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    """Risk assessment levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClaimStatus(str, Enum):
    """Status of fact-checkable claims."""

    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    MISLEADING = "misleading"
    FALSE = "false"


@dataclass
class AgendaItem:
    """Represents an agenda item with timestamp."""

    title: str
    start_time: float
    end_time: float
    duration: float
    description: str
    speakers: list[str]
    topics: list[str]
    key_points: list[str] = field(default_factory=list)


@dataclass
class GuestInfo:
    """Information about a guest or participant."""

    name: str
    role: str
    bio: str
    first_mentioned: float
    total_speaking_time: float
    segments: int
    key_contributions: list[str] = field(default_factory=list)
    social_links: dict[str, str] = field(default_factory=dict)
    expertise_areas: list[str] = field(default_factory=list)


@dataclass
class FactCheckableClaim:
    """Represents a fact-checkable claim made during the episode."""

    claim_id: str
    text: str
    speaker: str
    timestamp: float
    context: str
    claim_type: str  # "statistical", "historical", "scientific", "personal", etc.
    status: ClaimStatus
    confidence: float  # 0-1 confidence in the claim
    sources_mentioned: list[str] = field(default_factory=list)
    verification_notes: str = ""
    risk_assessment: RiskLevel = RiskLevel.LOW


@dataclass
class NotableQuotation:
    """Represents a notable quotation from the episode."""

    quote_id: str
    text: str
    speaker: str
    timestamp: float
    context: str
    significance: str
    topics: list[str] = field(default_factory=list)
    sentiment: float = 0.0  # -1 to 1
    viral_potential: float = 0.0  # 0 to 1


@dataclass
class OutboundLink:
    """Represents an outbound link mentioned in the episode."""

    url: str
    title: str
    description: str
    mentioned_by: str
    timestamp: float
    context: str
    link_type: str  # "website", "social", "product", "article", etc.
    domain: str
    is_affiliate: bool = False
    is_sponsored: bool = False


@dataclass
class ThumbnailSuggestion:
    """Represents a suggested thumbnail for the episode."""

    timestamp: float
    frame_url: str
    description: str
    engagement_score: float
    visual_elements: list[str] = field(default_factory=list)
    text_overlay: str = ""
    recommended: bool = False


@dataclass
class BrandSafetyAnalysis:
    """Brand safety analysis for the episode."""

    overall_score: float  # 1-5, 5 being most advertiser-friendly
    toxicity_score: float  # 0-1, 1 being most toxic
    controversy_score: float  # 0-1, 1 being most controversial
    advertiser_friendliness: str  # "safe", "caution", "unsafe"
    flagged_segments: list[dict[str, Any]] = field(default_factory=list)
    content_warnings: list[str] = field(default_factory=list)
    brand_mentions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DefamationRisk:
    """Defamation risk assessment."""

    risk_level: RiskLevel
    risk_score: float  # 0-1
    flagged_statements: list[dict[str, Any]] = field(default_factory=list)
    individuals_mentioned: list[str] = field(default_factory=list)
    organizations_mentioned: list[str] = field(default_factory=list)
    unverified_claims: list[FactCheckableClaim] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class EpisodeIntelligence:
    """Complete episode intelligence pack."""

    episode_id: str
    episode_title: str
    episode_duration: float
    created_at: datetime
    updated_at: datetime

    # Core content
    agenda: list[AgendaItem] = field(default_factory=list)
    guests: list[GuestInfo] = field(default_factory=list)
    claims: list[FactCheckableClaim] = field(default_factory=list)
    quotations: list[NotableQuotation] = field(default_factory=list)
    links: list[OutboundLink] = field(default_factory=list)
    thumbnail_suggestions: list[ThumbnailSuggestion] = field(default_factory=list)

    # Analysis
    brand_safety: BrandSafetyAnalysis | None = None
    defamation_risk: DefamationRisk | None = None

    # Metadata
    total_speakers: int = 0
    total_segments: int = 0
    average_sentiment: float = 0.0
    top_topics: list[str] = field(default_factory=list)
    key_insights: list[str] = field(default_factory=list)

    # Export info
    export_formats: list[str] = field(default_factory=list)  # ["markdown", "json", "html"]
    file_paths: dict[str, str] = field(default_factory=dict)


@dataclass
class IntelligenceConfig:
    """Configuration for intelligence pack generation."""

    include_agenda: bool = True
    include_guests: bool = True
    include_claims: bool = True
    include_quotations: bool = True
    include_links: bool = True
    include_thumbnails: bool = True
    include_brand_safety: bool = True
    include_defamation_risk: bool = True

    # Analysis parameters
    min_claim_confidence: float = 0.7
    min_quotation_length: int = 20
    max_agenda_items: int = 20
    max_thumbnail_suggestions: int = 5

    # Export options
    export_markdown: bool = True
    export_json: bool = True
    export_html: bool = False

    # Risk assessment
    defamation_threshold: float = 0.7
    brand_safety_threshold: float = 3.0  # Below this is not advertiser-friendly


@dataclass
class IntelligenceResult:
    """Result of intelligence pack generation."""

    episode_id: str
    success: bool
    intelligence_pack: EpisodeIntelligence | None = None
    processing_time: float | None = None
    error_message: str | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportTemplate:
    """Template for exporting intelligence packs."""

    format: str  # "markdown", "json", "html"
    template_path: str
    output_path: str
    custom_fields: dict[str, Any] = field(default_factory=dict)
    styling: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisMetrics:
    """Metrics for intelligence pack analysis quality."""

    total_segments_analyzed: int
    claims_identified: int
    quotations_extracted: int
    links_found: int
    speakers_identified: int
    topics_detected: int

    # Quality scores
    agenda_accuracy: float = 0.0
    guest_info_completeness: float = 0.0
    claim_verification_rate: float = 0.0
    quotation_relevance: float = 0.0

    # Processing metrics
    analysis_duration: float = 0.0
    model_versions: dict[str, str] = field(default_factory=dict)
    confidence_scores: dict[str, float] = field(default_factory=dict)
