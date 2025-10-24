"""Task output schemas for validation and type safety."""

from typing import Any


# Task output schemas for validation
# This provides type safety and validation for task outputs
TASK_OUTPUT_SCHEMAS: dict[str, Any] = {
    "content_analysis": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
            "topics": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["summary", "sentiment", "confidence"],
    },
    "fact_check": {
        "type": "object",
        "properties": {
            "claim": {"type": "string"},
            "verdict": {"type": "string", "enum": ["true", "false", "misleading", "unverified"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "sources": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["claim", "verdict", "confidence"],
    },
    "transcription": {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "timestamps": {"type": "array", "items": {"type": "object"}},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "language": {"type": "string"},
        },
        "required": ["text", "confidence"],
    },
}
