"""Compatibility shim for legacy ai.response_models imports.

DEPRECATED: This module provides backward compatibility for code using the old
`ai.response_models` import path. New code should import directly from
`platform.rl.response_models` instead.

This shim will be removed in a future release after all imports are migrated.
"""

# Re-export everything from the canonical location
from platform.rl.response_models import (
    ComprehensiveAnalysis,
    ConfidenceLevel,
    ContentQuality,
    ContentRoutingDecision,
    ContentType,
    ContentTypeClassification,
    FallacyAnalysisResult,
    FallacyInstance,
    FallacyType,
    KeyTopic,
    PerspectiveAnalysisResult,
    PerspectiveInstance,
    PerspectiveType,
    SentimentAnalysis,
    SeverityLevel,
)


__all__ = [
    "ComprehensiveAnalysis",
    "ConfidenceLevel",
    "ContentQuality",
    "ContentRoutingDecision",
    "ContentType",
    "ContentTypeClassification",
    "FallacyAnalysisResult",
    "FallacyInstance",
    "FallacyType",
    "KeyTopic",
    "PerspectiveAnalysisResult",
    "PerspectiveInstance",
    "PerspectiveType",
    "SentimentAnalysis",
    "SeverityLevel",
]
