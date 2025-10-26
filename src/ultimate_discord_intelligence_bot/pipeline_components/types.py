"""Shared types for the content pipeline implementation."""

from __future__ import annotations

from typing import Any, TypedDict


class PipelineRunResult(TypedDict, total=False):
    """Structured response returned by the content pipeline."""

    status: str
    download: dict[str, Any]
    drive: dict[str, Any]
    transcription: dict[str, Any]
    analysis: dict[str, Any]
    fallacy: dict[str, Any]
    perspective: dict[str, Any]
    memory: dict[str, Any]
    discord: dict[str, Any]
    step: str
    error: str
    rate_limit_exceeded: bool
    status_code: int
    # Optional observability and metrics fields
    observability: dict[str, Any]
    processing_type: str
    quality_score: float
    exit_checkpoint: str | None
    exit_reason: str | None
    exit_confidence: float | None
    time_saved_estimate: float | str
