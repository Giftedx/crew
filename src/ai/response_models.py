"""Pydantic models for structured LLM responses.

This module defines all response schemas used with Instructor for type-safe,
validated LLM outputs. All models include field validators and comprehensive
documentation for clarity.

Architecture:
- All models inherit from BaseModel (Pydantic v2)
- Field validators ensure data quality and consistency
- Models map directly to analysis tool outputs
- Designed for use with instructor.from_openai() wrapping

Usage:
    from ai.response_models import FallacyAnalysisResult
    from ai.structured_outputs import InstructorClientFactory

    client = InstructorClientFactory.create_client()
    result = client.chat.completions.create(
        model="gpt-4",
        response_model=FallacyAnalysisResult,
        messages=[{"role": "user", "content": "Analyze this..."}]
    )
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ====== Enums ======


class SeverityLevel(str, Enum):
    """Severity classification for detected issues."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    """Confidence rating for analysis results."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FallacyType(str, Enum):
    """Common logical fallacy types detected in content."""

    AD_HOMINEM = "ad_hominem"
    STRAW_MAN = "straw_man"
    FALSE_DILEMMA = "false_dilemma"
    SLIPPERY_SLOPE = "slippery_slope"
    APPEAL_TO_AUTHORITY = "appeal_to_authority"
    APPEAL_TO_EMOTION = "appeal_to_emotion"
    HASTY_GENERALIZATION = "hasty_generalization"
    RED_HERRING = "red_herring"
    CIRCULAR_REASONING = "circular_reasoning"
    FALSE_CAUSE = "false_cause"
    BANDWAGON = "bandwagon"
    TU_QUOQUE = "tu_quoque"
    NO_TRUE_SCOTSMAN = "no_true_scotsman"
    LOADED_QUESTION = "loaded_question"
    APPEAL_TO_NATURE = "appeal_to_nature"
    APPEAL_TO_TRADITION = "appeal_to_tradition"
    PERSONAL_INCREDULITY = "personal_incredulity"
    COMPOSITION_DIVISION = "composition_division"
    MIDDLE_GROUND = "middle_ground"
    BURDEN_OF_PROOF = "burden_of_proof"
    AMBIGUITY = "ambiguity"
    GAMBLER_FALLACY = "gambler_fallacy"
    OTHER = "other"


class PerspectiveType(str, Enum):
    """Ideological or analytical perspectives identified in content."""

    PROGRESSIVE = "progressive"
    CONSERVATIVE = "conservative"
    LIBERTARIAN = "libertarian"
    AUTHORITARIAN = "authoritarian"
    NEUTRAL = "neutral"
    TECHNOCRATIC = "technocratic"
    POPULIST = "populist"
    ANARCHIST = "anarchist"
    CENTRIST = "centrist"
    SOCIALIST = "socialist"
    CAPITALIST = "capitalist"
    ENVIRONMENTALIST = "environmentalist"
    NATIONALIST = "nationalist"
    GLOBALIST = "globalist"
    RELIGIOUS = "religious"
    SECULAR = "secular"
    OTHER = "other"


class ContentQuality(str, Enum):
    """Quality assessment for content."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    VERY_POOR = "very_poor"


class ContentType(str, Enum):
    """Types of content for classification and routing."""

    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    TECHNOLOGY = "technology"
    DISCUSSION = "discussion"
    POLITICAL = "political"
    SCIENTIFIC = "scientific"
    BUSINESS = "business"
    SPORTS = "sports"
    GENERAL = "general"
    OTHER = "other"


# ====== Core Analysis Models ======


class FallacyInstance(BaseModel):
    """A single detected logical fallacy instance."""

    fallacy_type: FallacyType = Field(..., description="Type of logical fallacy detected")
    quote: str = Field(..., description="Exact quote containing the fallacy", min_length=1, max_length=1000)
    explanation: str = Field(
        ..., description="Why this is a fallacy and how it undermines the argument", min_length=10, max_length=2000
    )
    severity: SeverityLevel = Field(..., description="Impact severity of this fallacy")
    confidence: ConfidenceLevel = Field(..., description="Confidence in this detection")
    line_number: int | None = Field(default=None, description="Approximate line/timestamp if available", ge=0)

    @field_validator("quote")
    @classmethod
    def validate_quote(cls, v: str) -> str:
        """Ensure quote is meaningful and not just whitespace."""
        if not v.strip():
            raise ValueError("Quote cannot be empty or whitespace")
        return v.strip()

    @field_validator("explanation")
    @classmethod
    def validate_explanation(cls, v: str) -> str:
        """Ensure explanation provides value."""
        if len(v.strip()) < 10:
            raise ValueError("Explanation must be at least 10 characters")
        return v.strip()


class PerspectiveInstance(BaseModel):
    """A single identified ideological or analytical perspective."""

    perspective_type: PerspectiveType = Field(..., description="Type of perspective detected")
    evidence: str = Field(
        ..., description="Supporting evidence for this perspective identification", min_length=10, max_length=2000
    )
    confidence: ConfidenceLevel = Field(..., description="Confidence in this identification")
    prominence: float = Field(
        ..., description="How prominently this perspective is expressed (0.0-1.0)", ge=0.0, le=1.0
    )
    bias_indicators: list[str] = Field(
        default_factory=list,
        description="Specific language or framing indicating bias",
        max_length=10,
    )

    @field_validator("evidence")
    @classmethod
    def validate_evidence(cls, v: str) -> str:
        """Ensure evidence is substantive."""
        if len(v.strip()) < 10:
            raise ValueError("Evidence must be at least 10 characters")
        return v.strip()

    @field_validator("bias_indicators")
    @classmethod
    def validate_bias_indicators(cls, v: list[str]) -> list[str]:
        """Clean and validate bias indicators."""
        return [indicator.strip() for indicator in v if indicator.strip()]


class FallacyAnalysisResult(BaseModel):
    """Complete fallacy analysis result with detected instances and summary."""

    fallacies: list[FallacyInstance] = Field(
        default_factory=list,
        description="All detected logical fallacies",
        max_length=50,
    )
    overall_quality: ContentQuality = Field(..., description="Overall argument quality assessment")
    credibility_score: float = Field(
        ..., description="Content credibility score (0.0-1.0, higher is better)", ge=0.0, le=1.0
    )
    summary: str = Field(
        ..., description="High-level summary of fallacy patterns and argument quality", min_length=20, max_length=3000
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations for improvement",
        max_length=10,
    )
    key_issues: list[str] = Field(
        default_factory=list,
        description="Most critical issues to address",
        max_length=5,
    )

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: str) -> str:
        """Ensure summary is meaningful."""
        if len(v.strip()) < 20:
            raise ValueError("Summary must be at least 20 characters")
        return v.strip()

    @model_validator(mode="after")
    def validate_consistency(self) -> FallacyAnalysisResult:
        """Ensure credibility score aligns with detected fallacies."""
        if len(self.fallacies) > 10 and self.credibility_score > 0.5:
            raise ValueError("High fallacy count should result in lower credibility score")
        if len(self.fallacies) == 0 and self.credibility_score < 0.7:
            raise ValueError("No fallacies should result in higher credibility score")
        return self


class PerspectiveAnalysisResult(BaseModel):
    """Complete perspective analysis result with identified viewpoints and bias assessment."""

    perspectives: list[PerspectiveInstance] = Field(
        default_factory=list,
        description="All identified perspectives",
        max_length=20,
    )
    dominant_perspective: PerspectiveType | None = Field(
        default=None, description="Most prominent perspective if any clearly dominates"
    )
    bias_score: float = Field(
        ..., description="Overall bias level (0.0-1.0, higher indicates more bias)", ge=0.0, le=1.0
    )
    balance_score: float = Field(
        ..., description="Viewpoint balance (0.0-1.0, higher is more balanced)", ge=0.0, le=1.0
    )
    framing_analysis: str = Field(
        ..., description="Analysis of how content is framed and what's emphasized", min_length=20, max_length=3000
    )
    omitted_perspectives: list[PerspectiveType] = Field(
        default_factory=list,
        description="Perspectives conspicuously absent",
        max_length=10,
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Suggestions for more balanced coverage",
        max_length=10,
    )

    @field_validator("framing_analysis")
    @classmethod
    def validate_framing(cls, v: str) -> str:
        """Ensure framing analysis is substantive."""
        if len(v.strip()) < 20:
            raise ValueError("Framing analysis must be at least 20 characters")
        return v.strip()

    @model_validator(mode="after")
    def validate_balance_consistency(self) -> PerspectiveAnalysisResult:
        """Ensure bias and balance scores are inversely correlated."""
        if self.bias_score > 0.7 and self.balance_score > 0.5:
            raise ValueError("High bias should correlate with low balance")
        if len(self.perspectives) > 5 and self.balance_score < 0.3:
            raise ValueError("Many perspectives should indicate better balance")
        return self


# ====== Content Routing Models ======


class ContentRoutingDecision(BaseModel):
    """Decision on whether content should proceed through pipeline."""

    should_process: bool = Field(..., description="Whether content meets quality threshold for processing")
    confidence: ConfidenceLevel = Field(..., description="Confidence in this routing decision")
    reasoning: str = Field(..., description="Explanation for the routing decision", min_length=20, max_length=2000)
    quality_indicators: dict[str, float] = Field(
        default_factory=dict,
        description="Quality metrics (0.0-1.0) for various aspects",
    )
    suggested_action: str = Field(
        ...,
        description="Recommended next step (process, skip, flag_for_review, etc.)",
        min_length=3,
        max_length=100,
    )
    estimated_value: float = Field(
        ..., description="Estimated value of processing this content (0.0-1.0)", ge=0.0, le=1.0
    )

    @field_validator("quality_indicators")
    @classmethod
    def validate_quality_indicators(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure all quality indicators are in valid range."""
        for key, value in v.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Quality indicator '{key}' must be between 0.0 and 1.0, got {value}")
        return v

    @model_validator(mode="after")
    def validate_decision_consistency(self) -> ContentRoutingDecision:
        """Ensure routing decision aligns with quality metrics."""
        avg_quality = (
            sum(self.quality_indicators.values()) / len(self.quality_indicators) if self.quality_indicators else 0.5
        )
        if self.should_process and avg_quality < 0.3:
            raise ValueError("Low quality metrics should result in should_process=False")
        if not self.should_process and avg_quality > 0.7:
            raise ValueError("High quality metrics should result in should_process=True")
        return self


class ContentTypeClassification(BaseModel):
    """Content type classification result for routing optimization."""

    primary_type: ContentType = Field(..., description="Primary content type detected")
    confidence: float = Field(..., description="Confidence in classification (0.0-1.0)", ge=0.0, le=1.0)
    secondary_types: list[ContentType] = Field(
        default_factory=list,
        description="Secondary content types if content is multi-faceted",
        max_length=3,
    )
    recommended_pipeline: str = Field(
        ...,
        description="Recommended processing pipeline (deep_analysis, fast_summary, light_analysis, standard_pipeline)",
        min_length=5,
        max_length=50,
    )
    processing_flags: dict[str, bool] = Field(
        default_factory=dict,
        description="Boolean flags for enabling/disabling specific processing steps",
    )
    quality_score: float = Field(..., description="Overall content quality score (0.0-1.0)", ge=0.0, le=1.0)
    estimated_processing_time: float = Field(..., description="Estimated processing time in seconds", ge=0.0, le=3600.0)
    recommendations: list[str] = Field(
        default_factory=list,
        description="Processing recommendations based on content type",
        max_length=5,
    )

    @field_validator("secondary_types")
    @classmethod
    def validate_secondary_types_unique(cls, v: list[ContentType], info) -> list[ContentType]:
        """Ensure secondary types don't include primary type."""
        # Note: info.data['primary_type'] may not be available during parsing,
        # so we'll validate this in model_validator instead
        if len(v) != len(set(v)):
            raise ValueError("Secondary types must be unique")
        return v

    @model_validator(mode="after")
    def validate_type_consistency(self) -> ContentTypeClassification:
        """Ensure secondary types don't duplicate primary type."""
        if self.primary_type in self.secondary_types:
            raise ValueError(f"Secondary types cannot include primary type: {self.primary_type}")
        return self


# ====== General Analysis Models ======


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result for content."""

    polarity: float = Field(..., description="Sentiment polarity (-1.0 to 1.0, negative to positive)", ge=-1.0, le=1.0)
    subjectivity: float = Field(
        ..., description="Objectivity vs subjectivity (0.0-1.0, objective to subjective)", ge=0.0, le=1.0
    )
    dominant_emotion: str | None = Field(default=None, description="Primary emotional tone if detected")
    intensity: float = Field(..., description="Emotional intensity (0.0-1.0)", ge=0.0, le=1.0)
    confidence: ConfidenceLevel = Field(..., description="Confidence in sentiment analysis")


class KeyTopic(BaseModel):
    """A key topic or theme identified in content."""

    topic: str = Field(..., description="Topic or theme name", min_length=2, max_length=200)
    relevance: float = Field(..., description="Topic relevance score (0.0-1.0)", ge=0.0, le=1.0)
    keywords: list[str] = Field(default_factory=list, description="Associated keywords", max_length=20)
    context: str | None = Field(default=None, description="Contextual information about this topic", max_length=1000)

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: list[str]) -> list[str]:
        """Clean and validate keywords."""
        return [kw.strip().lower() for kw in v if kw.strip()]


class ComprehensiveAnalysis(BaseModel):
    """Complete multi-faceted analysis combining all analysis types."""

    fallacy_analysis: FallacyAnalysisResult | None = Field(
        default=None, description="Logical fallacy detection results"
    )
    perspective_analysis: PerspectiveAnalysisResult | None = Field(
        default=None, description="Ideological perspective identification"
    )
    sentiment: SentimentAnalysis | None = Field(default=None, description="Sentiment and emotional tone analysis")
    key_topics: list[KeyTopic] = Field(default_factory=list, description="Main topics and themes", max_length=15)
    executive_summary: str = Field(
        ..., description="High-level summary synthesizing all analyses", min_length=50, max_length=5000
    )
    actionable_insights: list[str] = Field(
        default_factory=list, description="Key takeaways and recommendations", max_length=10
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (processing time, model version, etc.)",
    )

    @field_validator("executive_summary")
    @classmethod
    def validate_executive_summary(cls, v: str) -> str:
        """Ensure executive summary is comprehensive."""
        if len(v.strip()) < 50:
            raise ValueError("Executive summary must be at least 50 characters")
        return v.strip()


__all__ = [
    # Core models
    "ComprehensiveAnalysis",
    # Enums
    "ConfidenceLevel",
    "ContentQuality",
    # Routing
    "ContentRoutingDecision",
    # Core models
    "FallacyAnalysisResult",
    "FallacyInstance",
    "FallacyType",
    # General
    "KeyTopic",
    "PerspectiveAnalysisResult",
    "PerspectiveInstance",
    "PerspectiveType",
    "SentimentAnalysis",
    "SeverityLevel",
]
