"""Dashboard metrics recorder - sends pipeline results to performance dashboard API."""

from __future__ import annotations

import logging

from core.http_utils import resilient_post
from core.secure_config import get_config


logger = logging.getLogger(__name__)


async def record_pipeline_metrics(
    processing_type: str,
    content_type: str | None = None,
    quality_score: float | None = None,
    processing_time: float | None = None,
    exit_checkpoint: str | None = None,
    exit_reason: str | None = None,
    exit_confidence: float | None = None,
    time_saved_pct: float | None = None,
) -> None:
    """
    Record pipeline metrics to the performance dashboard.

    This is a fire-and-forget async call that sends metrics to the dashboard API.
    Failures are logged but don't affect pipeline execution.

    Args:
        processing_type: Type of processing (full, lightweight, early_exit)
        content_type: Content type classification
        quality_score: Quality assessment score (0-1)
        processing_time: Actual processing time in seconds
        exit_checkpoint: Checkpoint name if early exit
        exit_reason: Reason for early exit
        exit_confidence: Confidence of early exit decision
        time_saved_pct: Estimated time savings percentage
    """
    # Check if dashboard recording is enabled
    enable_dashboard = get_config("ENABLE_DASHBOARD_METRICS", "0") == "1"
    if not enable_dashboard:
        return

    # Get dashboard API URL
    dashboard_url = get_config("DASHBOARD_API_URL", "http://localhost:8000")
    endpoint = f"{dashboard_url}/api/performance/record"

    # Build payload
    payload = {"processing_type": processing_type}

    if content_type is not None:
        payload["content_type"] = content_type
    if quality_score is not None:
        payload["quality_score"] = quality_score
    if processing_time is not None:
        payload["processing_time"] = processing_time
    if exit_checkpoint is not None:
        payload["exit_checkpoint"] = exit_checkpoint
    if exit_reason is not None:
        payload["exit_reason"] = exit_reason
    if exit_confidence is not None:
        payload["exit_confidence"] = exit_confidence
    if time_saved_pct is not None:
        payload["time_saved_pct"] = time_saved_pct

    try:
        # Fire and forget - don't await
        await resilient_post(endpoint, json_payload=payload, timeout_seconds=5)
        logger.debug(f"Recorded dashboard metrics: {processing_type}")
    except Exception as exc:
        # Don't fail pipeline if dashboard recording fails
        logger.debug(f"Failed to record dashboard metrics: {exc}")
