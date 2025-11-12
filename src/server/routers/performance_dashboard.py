"""Performance Dashboard API Router for Week 4 Phase 2 Week 3.

Provides REST endpoints for performance metrics, including:
- Pipeline performance (bypass rates, exit rates, time savings)
- Content type routing statistics
- Early exit checkpoint analytics
- Quality filtering trends
- Overall optimization impact
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field


try:
    from ultimate_discord_intelligence_bot.obs import metrics
except ImportError:
    metrics = None


class PerformanceMetrics(BaseModel):
    """Overall performance metrics."""

    total_processed: int = Field(..., description="Total items processed")
    quality_bypassed: int = Field(..., description="Items bypassed by quality filtering")
    early_exits: int = Field(..., description="Items that exited early at checkpoints")
    full_processing: int = Field(..., description="Items with full processing")
    bypass_rate: float = Field(..., description="Overall bypass rate (0-1)")
    early_exit_rate: float = Field(..., description="Overall early exit rate (0-1)")
    avg_time_savings: float = Field(..., description="Average time savings percentage")
    total_time_saved_hours: float = Field(..., description="Total time saved in hours")


class ContentTypeStats(BaseModel):
    """Statistics for a specific content type."""

    content_type: str = Field(..., description="Content type name")
    count: int = Field(..., description="Number of items processed")
    bypass_rate: float = Field(..., description="Bypass rate for this content type")
    avg_quality_score: float = Field(..., description="Average quality score")
    avg_processing_time: float = Field(..., description="Average processing time (seconds)")


class CheckpointStats(BaseModel):
    """Statistics for an early exit checkpoint."""

    checkpoint_name: str = Field(..., description="Checkpoint name")
    exit_count: int = Field(..., description="Number of exits at this checkpoint")
    exit_rate: float = Field(..., description="Exit rate at this checkpoint")
    top_exit_reasons: list[dict[str, Any]] = Field(..., description="Most common exit reasons")
    avg_confidence: float = Field(..., description="Average exit confidence")


class QualityTrend(BaseModel):
    """Quality metrics trend data."""

    timestamp: datetime = Field(..., description="Data point timestamp")
    avg_quality_score: float = Field(..., description="Average quality score")
    coherence_score: float = Field(..., description="Average coherence")
    completeness_score: float = Field(..., description="Average completeness")
    informativeness_score: float = Field(..., description="Average informativeness")
    items_processed: int = Field(..., description="Items in this time window")


class DashboardResponse(BaseModel):
    """Complete dashboard data response."""

    overall_metrics: PerformanceMetrics
    content_type_breakdown: list[ContentTypeStats]
    checkpoint_analytics: list[CheckpointStats]
    quality_trends: list[QualityTrend]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


router = APIRouter(prefix="/api/performance", tags=["performance"], responses={404: {"description": "Not found"}})
_metrics_store: dict[str, Any] = {
    "total_processed": 0,
    "quality_bypassed": 0,
    "early_exits": 0,
    "full_processing": 0,
    "content_types": {},
    "checkpoints": {},
    "quality_history": [],
    "time_savings": [],
}


@router.get("/", response_model=DashboardResponse)
async def get_dashboard_data(
    hours: int = Query(24, description="Hours of data to retrieve", ge=1, le=168),
) -> DashboardResponse:
    """
    Get complete performance dashboard data.

    Args:
        hours: Number of hours of historical data to retrieve (default: 24)

    Returns:
        Complete dashboard metrics and trends
    """
    total = _metrics_store["total_processed"]
    bypassed = _metrics_store["quality_bypassed"]
    exits = _metrics_store["early_exits"]
    full = _metrics_store["full_processing"]
    bypass_rate = bypassed / total if total > 0 else 0.0
    exit_rate = exits / total if total > 0 else 0.0
    time_savings_list = _metrics_store["time_savings"]
    avg_savings = sum(time_savings_list) / len(time_savings_list) if time_savings_list else 0.0
    estimated_baseline_time = total * 10.0 / 60.0
    total_saved = estimated_baseline_time * avg_savings
    overall = PerformanceMetrics(
        total_processed=total,
        quality_bypassed=bypassed,
        early_exits=exits,
        full_processing=full,
        bypass_rate=bypass_rate,
        early_exit_rate=exit_rate,
        avg_time_savings=avg_savings,
        total_time_saved_hours=total_saved,
    )
    content_types = []
    for ct_name, ct_data in _metrics_store["content_types"].items():
        content_types.append(
            ContentTypeStats(
                content_type=ct_name,
                count=ct_data["count"],
                bypass_rate=ct_data["bypass_rate"],
                avg_quality_score=ct_data["avg_quality"],
                avg_processing_time=ct_data["avg_time"],
            )
        )
    checkpoints = []
    for cp_name, cp_data in _metrics_store["checkpoints"].items():
        checkpoints.append(
            CheckpointStats(
                checkpoint_name=cp_name,
                exit_count=cp_data["exit_count"],
                exit_rate=cp_data["exit_rate"],
                top_exit_reasons=cp_data["top_reasons"],
                avg_confidence=cp_data["avg_confidence"],
            )
        )
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    quality_trends = [QualityTrend(**qt) for qt in _metrics_store["quality_history"] if qt["timestamp"] >= cutoff_time]
    return DashboardResponse(
        overall_metrics=overall,
        content_type_breakdown=content_types,
        checkpoint_analytics=checkpoints,
        quality_trends=quality_trends,
    )


@router.get("/metrics/summary", response_model=PerformanceMetrics)
async def get_metrics_summary() -> PerformanceMetrics:
    """Get overall performance metrics summary."""
    total = _metrics_store["total_processed"]
    bypassed = _metrics_store["quality_bypassed"]
    exits = _metrics_store["early_exits"]
    full = _metrics_store["full_processing"]
    bypass_rate = bypassed / total if total > 0 else 0.0
    exit_rate = exits / total if total > 0 else 0.0
    time_savings_list = _metrics_store["time_savings"]
    avg_savings = sum(time_savings_list) / len(time_savings_list) if time_savings_list else 0.0
    estimated_baseline_time = total * 10.0 / 60.0
    total_saved = estimated_baseline_time * avg_savings
    return PerformanceMetrics(
        total_processed=total,
        quality_bypassed=bypassed,
        early_exits=exits,
        full_processing=full,
        bypass_rate=bypass_rate,
        early_exit_rate=exit_rate,
        avg_time_savings=avg_savings,
        total_time_saved_hours=total_saved,
    )


@router.get("/content-types", response_model=list[ContentTypeStats])
async def get_content_type_stats() -> list[ContentTypeStats]:
    """Get performance statistics broken down by content type."""
    return [
        ContentTypeStats(
            content_type=ct_name,
            count=ct_data["count"],
            bypass_rate=ct_data["bypass_rate"],
            avg_quality_score=ct_data["avg_quality"],
            avg_processing_time=ct_data["avg_time"],
        )
        for ct_name, ct_data in _metrics_store["content_types"].items()
    ]


@router.get("/checkpoints", response_model=list[CheckpointStats])
async def get_checkpoint_stats() -> list[CheckpointStats]:
    """Get early exit checkpoint analytics."""
    return [
        CheckpointStats(
            checkpoint_name=cp_name,
            exit_count=cp_data["exit_count"],
            exit_rate=cp_data["exit_rate"],
            top_exit_reasons=cp_data["top_reasons"],
            avg_confidence=cp_data["avg_confidence"],
        )
        for cp_name, cp_data in _metrics_store["checkpoints"].items()
    ]


@router.get("/quality-trends", response_model=list[QualityTrend])
async def get_quality_trends(
    hours: int = Query(24, description="Hours of historical data", ge=1, le=168),
) -> list[QualityTrend]:
    """Get quality metrics trends over time."""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    return [QualityTrend(**qt) for qt in _metrics_store["quality_history"] if qt["timestamp"] >= cutoff_time]


@router.post("/record")
async def record_pipeline_result(
    processing_type: str,
    content_type: str | None = None,
    quality_score: float | None = None,
    processing_time: float | None = None,
    exit_checkpoint: str | None = None,
    exit_reason: str | None = None,
    exit_confidence: float | None = None,
    time_saved_pct: float | None = None,
) -> dict[str, str]:
    """
    Record a pipeline processing result for dashboard metrics.

    This endpoint should be called by the pipeline after each item is processed.

    Args:
        processing_type: Type of processing (full, lightweight, early_exit)
        content_type: Content type classification
        quality_score: Quality assessment score (0-1)
        processing_time: Actual processing time in seconds
        exit_checkpoint: Checkpoint name if early exit
        exit_reason: Reason for early exit
        exit_confidence: Confidence of early exit decision
        time_saved_pct: Estimated time savings percentage

    Returns:
        Confirmation message
    """
    _metrics_store["total_processed"] += 1
    if processing_type == "lightweight":
        _metrics_store["quality_bypassed"] += 1
    elif processing_type == "early_exit":
        _metrics_store["early_exits"] += 1
    elif processing_type == "full":
        _metrics_store["full_processing"] += 1
    if content_type:
        if content_type not in _metrics_store["content_types"]:
            _metrics_store["content_types"][content_type] = {
                "count": 0,
                "total_quality": 0.0,
                "total_time": 0.0,
                "bypassed": 0,
            }
        ct_data = _metrics_store["content_types"][content_type]
        ct_data["count"] += 1
        if quality_score is not None:
            ct_data["total_quality"] += quality_score
            ct_data["avg_quality"] = ct_data["total_quality"] / ct_data["count"]
        if processing_time is not None:
            ct_data["total_time"] += processing_time
            ct_data["avg_time"] = ct_data["total_time"] / ct_data["count"]
        if processing_type in ("lightweight", "early_exit"):
            ct_data["bypassed"] += 1
        ct_data["bypass_rate"] = ct_data["bypassed"] / ct_data["count"]
    if exit_checkpoint:
        if exit_checkpoint not in _metrics_store["checkpoints"]:
            _metrics_store["checkpoints"][exit_checkpoint] = {"exit_count": 0, "total_confidence": 0.0, "reasons": {}}
        cp_data = _metrics_store["checkpoints"][exit_checkpoint]
        cp_data["exit_count"] += 1
        if exit_confidence is not None:
            cp_data["total_confidence"] += exit_confidence
            cp_data["avg_confidence"] = cp_data["total_confidence"] / cp_data["exit_count"]
        if exit_reason:
            cp_data["reasons"][exit_reason] = cp_data["reasons"].get(exit_reason, 0) + 1
        cp_data["exit_rate"] = cp_data["exit_count"] / _metrics_store["total_processed"]
        cp_data["top_reasons"] = [
            {"reason": reason, "count": count}
            for reason, count in sorted(cp_data["reasons"].items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    if quality_score is not None:
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        hour_entry = next((qt for qt in _metrics_store["quality_history"] if qt["timestamp"] == current_hour), None)
        if hour_entry is None:
            hour_entry = {
                "timestamp": current_hour,
                "total_quality": 0.0,
                "total_coherence": 0.0,
                "total_completeness": 0.0,
                "total_informativeness": 0.0,
                "items_processed": 0,
                "avg_quality_score": 0.0,
                "coherence_score": 0.0,
                "completeness_score": 0.0,
                "informativeness_score": 0.0,
            }
            _metrics_store["quality_history"].append(hour_entry)
        hour_entry["total_quality"] += quality_score
        hour_entry["items_processed"] += 1
        hour_entry["avg_quality_score"] = hour_entry["total_quality"] / hour_entry["items_processed"]
    if time_saved_pct is not None:
        _metrics_store["time_savings"].append(time_saved_pct)
    return {"status": "recorded", "processing_type": processing_type}


@router.delete("/reset")
async def reset_metrics() -> dict[str, str]:
    """
    Reset all performance metrics (for testing/debugging).

    ⚠️ This should be protected in production!
    """
    _metrics_store.clear()
    _metrics_store.update(
        {
            "total_processed": 0,
            "quality_bypassed": 0,
            "early_exits": 0,
            "full_processing": 0,
            "content_types": {},
            "checkpoints": {},
            "quality_history": [],
            "time_savings": [],
        }
    )
    return {"status": "reset", "message": "All metrics cleared"}
