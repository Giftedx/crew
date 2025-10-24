"""Pydantic models for structured LLM responses in tools.

These models ensure consistent, validated outputs from LLM calls,
reducing parsing errors by 15x through automatic validation and retries.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, validator


class AnalysisStatus(str, Enum):
    """Analysis completion status."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class SentimentScore(BaseModel):
    """Sentiment analysis result."""

    label: str = Field(description="Sentiment label: positive, negative, neutral")
    score: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")

    @validator("label")
    def validate_label(cls, v):
        allowed = ["positive", "negative", "neutral"]
        if v.lower() not in allowed:
            raise ValueError(f"Label must be one of: {allowed}")
        return v.lower()


class TextAnalysisResult(BaseModel):
    """Structured result from text analysis tool."""

    status: AnalysisStatus
    sentiment: SentimentScore
    key_phrases: list[str] = Field(default_factory=list, max_length=10, description="Top 10 key phrases extracted")
    word_count: int = Field(ge=0, description="Total word count")
    language_detected: str = Field(default="en", description="ISO 639-1 language code")
    readability_score: float | None = Field(None, ge=0.0, le=100.0, description="Flesch reading ease score")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "sentiment": {"label": "positive", "score": 0.85},
                "key_phrases": [
                    "artificial intelligence",
                    "machine learning",
                    "data science",
                ],
                "word_count": 1250,
                "language_detected": "en",
                "readability_score": 65.5,
            }
        }


class ClaimType(str, Enum):
    """Types of factual claims."""

    FACTUAL = "factual"
    OPINION = "opinion"
    PREDICTION = "prediction"
    STATISTIC = "statistic"


class ExtractedClaim(BaseModel):
    """A single extracted claim with verification info."""

    claim_text: str = Field(description="The exact claim text")
    claim_type: ClaimType
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")
    context: str = Field(description="Surrounding context for the claim")
    requires_verification: bool = Field(description="Whether claim needs fact-checking")


class ClaimExtractionResult(BaseModel):
    """Structured result from claim extraction tool."""

    status: AnalysisStatus
    claims: list[ExtractedClaim] = Field(default_factory=list, max_length=20, description="Extracted claims")
    total_sentences: int = Field(ge=0, description="Total sentences processed")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "claims": [
                    {
                        "claim_text": "AI will replace 40% of jobs by 2030",
                        "claim_type": "prediction",
                        "confidence": 0.9,
                        "context": "According to recent studies, AI will replace 40% of jobs by 2030.",
                        "requires_verification": True,
                    }
                ],
                "total_sentences": 15,
            }
        }


class LogicalFallacyType(str, Enum):
    """Types of logical fallacies."""

    AD_HOMINEM = "ad_hominem"
    STRAW_MAN = "straw_man"
    FALSE_DICHOTOMY = "false_dichotomy"
    SLIPPERY_SLOPE = "slippery_slope"
    APPEAL_TO_AUTHORITY = "appeal_to_authority"
    CIRCULAR_REASONING = "circular_reasoning"
    RED_HERRING = "red_herring"
    HASTY_GENERALIZATION = "hasty_generalization"
    NONE_DETECTED = "none_detected"


class DetectedFallacy(BaseModel):
    """A detected logical fallacy."""

    fallacy_type: LogicalFallacyType
    explanation: str = Field(description="Why this is considered a fallacy")
    text_excerpt: str = Field(description="The specific text exhibiting the fallacy")
    severity: float = Field(ge=0.0, le=1.0, description="Severity score")


class LogicalFallacyResult(BaseModel):
    """Structured result from logical fallacy detection."""

    status: AnalysisStatus
    fallacies: list[DetectedFallacy] = Field(default_factory=list, max_length=10, description="Detected fallacies")
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall logical consistency score")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "fallacies": [
                    {
                        "fallacy_type": "ad_hominem",
                        "explanation": "Attack on person rather than argument",
                        "text_excerpt": "You can't trust John because he's a terrible person",
                        "severity": 0.8,
                    }
                ],
                "overall_score": 0.7,
            }
        }


class PerspectiveType(str, Enum):
    """Types of alternative perspectives."""

    COUNTERARGUMENT = "counterargument"
    ALTERNATIVE_INTERPRETATION = "alternative_interpretation"
    DIFFERENT_CONTEXT = "different_context"
    OPPOSING_VIEWPOINT = "opposing_viewpoint"


class AlternativePerspective(BaseModel):
    """An alternative perspective or counterargument."""

    perspective_type: PerspectiveType
    title: str = Field(description="Brief title for this perspective")
    description: str = Field(description="Detailed explanation of the perspective")
    supporting_points: list[str] = Field(default_factory=list, max_length=5, description="Key supporting points")
    strength: float = Field(ge=0.0, le=1.0, description="Strength of this perspective")


class PerspectiveSynthesisResult(BaseModel):
    """Structured result from perspective synthesis tool."""

    status: AnalysisStatus
    original_summary: str = Field(description="Summary of the original content")
    perspectives: list[AlternativePerspective] = Field(
        default_factory=list, max_length=5, description="Alternative perspectives"
    )
    synthesis: str = Field(description="Balanced synthesis of different viewpoints")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "original_summary": "The article argues for increased AI regulation",
                "perspectives": [
                    {
                        "perspective_type": "counterargument",
                        "title": "Innovation Concern",
                        "description": "Heavy regulation might stifle AI innovation",
                        "supporting_points": [
                            "Slower development",
                            "Competitive disadvantage",
                        ],
                        "strength": 0.8,
                    }
                ],
                "synthesis": "While regulation is important for safety, it must be balanced with innovation needs",
            }
        }


class MemoryStorageEntry(BaseModel):
    """Entry for memory storage."""

    content: str = Field(description="Content to store")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    importance_score: float = Field(ge=0.0, le=1.0, description="Importance score for retrieval")
    tags: list[str] = Field(default_factory=list, max_length=10, description="Content tags")


class MemoryStorageResult(BaseModel):
    """Structured result from memory storage operation."""

    status: AnalysisStatus
    entry_id: str | None = Field(None, description="Unique identifier for stored entry")
    stored_count: int = Field(ge=0, description="Number of entries stored")
    namespace: str = Field(description="Storage namespace used")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "entry_id": "mem_12345",
                "stored_count": 1,
                "namespace": "default:main:discussion",
            }
        }


class FactCheckVeracity(str, Enum):
    """Fact check veracity levels."""

    TRUE = "true"
    MOSTLY_TRUE = "mostly_true"
    MIXED = "mixed"
    MOSTLY_FALSE = "mostly_false"
    FALSE = "false"
    UNVERIFIABLE = "unverifiable"


class FactCheckSource(BaseModel):
    """Source used for fact checking."""

    url: str = Field(description="Source URL")
    title: str = Field(description="Source title")
    credibility_score: float = Field(ge=0.0, le=1.0, description="Source credibility score")


class FactCheckResult(BaseModel):
    """Structured result from fact checking."""

    status: AnalysisStatus
    claim: str = Field(description="The claim being fact-checked")
    veracity: FactCheckVeracity
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the assessment")
    explanation: str = Field(description="Explanation of the verdict")
    sources: list[FactCheckSource] = Field(default_factory=list, max_length=5, description="Sources consulted")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "claim": "The Earth is round",
                "veracity": "true",
                "confidence": 0.99,
                "explanation": "Overwhelming scientific evidence confirms the Earth's spherical shape",
                "sources": [
                    {
                        "url": "https://nasa.gov/earth-shape",
                        "title": "NASA: Earth's Shape",
                        "credibility_score": 0.95,
                    }
                ],
            }
        }


class TrustLevel(str, Enum):
    """Trust levels for content assessment."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class TrustworthinessMetrics(BaseModel):
    """Trustworthiness assessment metrics."""

    source_credibility: float = Field(ge=0.0, le=1.0, description="Source credibility score")
    fact_accuracy: float = Field(ge=0.0, le=1.0, description="Factual accuracy score")
    bias_level: float = Field(ge=0.0, le=1.0, description="Bias level (0 = unbiased, 1 = highly biased)")
    transparency: float = Field(ge=0.0, le=1.0, description="Transparency and disclosure score")


class TrustworthinessResult(BaseModel):
    """Structured result from trustworthiness assessment."""

    status: AnalysisStatus
    overall_trust_level: TrustLevel
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall trustworthiness score")
    metrics: TrustworthinessMetrics
    reasoning: str = Field(description="Explanation of the assessment")
    red_flags: list[str] = Field(default_factory=list, max_length=10, description="Identified concerns")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "overall_trust_level": "medium",
                "overall_score": 0.65,
                "metrics": {
                    "source_credibility": 0.7,
                    "fact_accuracy": 0.8,
                    "bias_level": 0.4,
                    "transparency": 0.6,
                },
                "reasoning": "Generally reliable source with some bias detected",
                "red_flags": ["Potential selection bias in examples"],
            }
        }
