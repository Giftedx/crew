"""Background job definitions for Arq task queue."""

from __future__ import annotations

import asyncio
import logging
from typing import Any


try:
    from arq import cron

    ARQ_AVAILABLE = True
except ImportError:
    ARQ_AVAILABLE = False
    cron = None  # type: ignore[assignment,misc]


logger = logging.getLogger(__name__)


def _extract_job_context(ctx: dict[str, Any] | None) -> dict[str, Any]:
    """Return a sanitized snapshot of interesting job metadata."""

    if not isinstance(ctx, dict):
        return {}

    interesting_keys = ("job_id", "job_try", "queue", "enqueue_time", "scheduled")
    snapshot = {k: ctx.get(k) for k in interesting_keys if ctx.get(k) is not None}

    job = ctx.get("job")
    if job is not None:
        snapshot.setdefault("job", getattr(job, "id", str(job)))

    return snapshot


async def process_video_async(ctx: dict[str, Any], video_url: str, tenant: str, workspace: str) -> dict[str, Any]:
    """Background job to process video content asynchronously.

    Args:
        ctx: Arq context
        video_url: URL of video to process
        tenant: Tenant identifier
        workspace: Workspace identifier

    Returns:
        dict with processing results
    """
    try:
        job_context = _extract_job_context(ctx)
        logger.info(
            "Processing video",
            extra={"video_url": video_url, "tenant": tenant, "workspace": workspace, "job_context": job_context},
        )

        # Import here to avoid circular dependencies
        from ultimate_discord_intelligence_bot.tools import MultiPlatformDownloadTool

        tool = MultiPlatformDownloadTool()
        result = tool._run(url=video_url, tenant=tenant, workspace=workspace)

        if result.success:
            return {
                "status": "success",
                "data": result.data,
                "url": video_url,
                "tenant": tenant,
                "workspace": workspace,
                "job_context": job_context,
            }
        else:
            return {
                "status": "failed",
                "error": result.error,
                "url": video_url,
                "job_context": job_context,
            }

    except Exception as e:
        job_context = _extract_job_context(ctx)
        logger.error(
            "Video processing failed",
            extra={"video_url": video_url, "tenant": tenant, "workspace": workspace, "job_context": job_context},
        )
        return {
            "status": "error",
            "error": str(e),
            "url": video_url,
            "job_context": job_context,
        }


async def batch_analysis_async(
    ctx: dict[str, Any], content_items: list[str], tenant: str, workspace: str
) -> dict[str, Any]:
    """Background job to analyze multiple content items in batch.

    Args:
        ctx: Arq context
        content_items: List of content URLs or text to analyze
        tenant: Tenant identifier
        workspace: Workspace identifier

    Returns:
        dict with batch analysis results
    """
    try:
        job_context = _extract_job_context(ctx)
        logger.info(
            "Batch analysis",
            extra={
                "item_count": len(content_items),
                "tenant": tenant,
                "workspace": workspace,
                "job_context": job_context,
            },
        )

        results = []
        for item in content_items:
            # Simulate analysis - replace with actual analysis tool
            await asyncio.sleep(0.1)  # Simulate processing time
            results.append(
                {
                    "item": item,
                    "status": "analyzed",
                }
            )

        return {
            "status": "success",
            "processed_count": len(results),
            "results": results,
            "tenant": tenant,
            "workspace": workspace,
            "job_context": job_context,
        }

    except Exception as e:
        job_context = _extract_job_context(ctx)
        logger.error(
            "Batch analysis failed",
            extra={"tenant": tenant, "workspace": workspace, "job_context": job_context},
        )
        return {
            "status": "error",
            "error": str(e),
            "job_context": job_context,
        }


async def scheduled_monitoring_async(ctx: dict[str, Any]) -> dict[str, Any]:
    """Scheduled job to monitor system health and content sources.

    Args:
        ctx: Arq context

    Returns:
        dict with monitoring results
    """
    try:
        job_context = _extract_job_context(ctx)
        logger.info("Running scheduled monitoring check", extra={"job_context": job_context})

        # Simulate monitoring checks
        checks = {
            "timestamp": "2024-01-01T00:00:00Z",
            "checks": {
                "database": "healthy",
                "redis": "healthy",
                "qdrant": "healthy",
            },
        }

        return {
            "status": "success",
            "checks": checks,
            "job_context": job_context,
        }

    except Exception as e:
        job_context = _extract_job_context(ctx)
        logger.error("Scheduled monitoring failed", extra={"job_context": job_context})
        return {
            "status": "error",
            "error": str(e),
            "job_context": job_context,
        }


# Arq job function registry
ARQ_FUNCTIONS = [
    process_video_async,
    batch_analysis_async,
    scheduled_monitoring_async,
]

# Scheduled cron jobs
ARQ_CRON_JOBS = (
    [
        # Run monitoring every 5 minutes
        cron(scheduled_monitoring_async, hour=set(range(24)), minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
    ]
    if ARQ_AVAILABLE
    else []
)
