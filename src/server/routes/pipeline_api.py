from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from fastapi.responses import JSONResponse

from fastapi import Body, FastAPI, HTTPException, status


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


def register_pipeline_routes(app: FastAPI, settings: Any) -> None:
    """Register the ContentPipeline HTTP trigger when enabled.

    The endpoint is guarded by the ``ENABLE_PIPELINE_RUN_API`` flag and uses the
    existing ``PipelineTool`` implementation so budgeting, tracing, and metrics
    instrumentation remain centralised.
    """

    try:
        enabled = bool(settings.enable_pipeline_run_api)
    except Exception as exc:  # pragma: no cover - defensive settings access
        logger.debug("pipeline API flag lookup failed: %s", exc)
        return

    if not enabled:
        return

    try:
        from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant
        from ultimate_discord_intelligence_bot.tools.pipeline_tool import PipelineTool
    except Exception as exc:  # pragma: no cover - optional dependency path
        logger.debug("pipeline API wiring skipped: %s", exc)
        return

    @app.post("/pipeline/run", summary="Run the content pipeline")
    async def _pipeline_run(
        payload: dict[str, Any] = Body(..., embed=False),
    ) -> JSONResponse:
        url = payload.get("url")
        quality = payload.get("quality")
        tenant_id = payload.get("tenant_id") or payload.get("tenant") or "default"
        workspace_id = payload.get("workspace_id") or payload.get("workspace") or "main"

        if not isinstance(url, str) or not url.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="`url` is required",
            )

        if quality is not None and not isinstance(quality, str):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="`quality` must be a string",
            )

        resolved_quality = quality.strip() if isinstance(quality, str) else None

        tool = PipelineTool()
        ctx = TenantContext(tenant_id=tenant_id, workspace_id=workspace_id)

        try:
            logger.info(
                "pipeline API request",
                extra={"tenant_id": tenant_id, "workspace_id": workspace_id},
            )
            with with_tenant(ctx):
                result: StepResult = await tool._run_async(url.strip(), resolved_quality or "1080p")
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - pipeline error path
            logger.exception("pipeline run failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Pipeline execution failed",
            )

        response_payload = result.to_dict()
        data = response_payload.setdefault("data", {})
        if isinstance(data, dict):
            data.setdefault("tenant_id", tenant_id)
            data.setdefault("workspace_id", workspace_id)

        http_status = status.HTTP_200_OK if result.success else status.HTTP_502_BAD_GATEWAY
        return JSONResponse(status_code=http_status, content=response_payload)

    # Check if async job queue is enabled
    try:
        job_queue_enabled = bool(settings.enable_pipeline_job_queue)
    except Exception as exc:
        logger.debug("pipeline job queue flag lookup failed: %s", exc)
        job_queue_enabled = False

    if not job_queue_enabled:
        return

    # Initialize singleton job queue
    try:
        from server.job_queue import JobQueue, JobStatus
    except Exception as exc:  # pragma: no cover
        logger.debug("job queue import failed: %s", exc)
        return

    # Create queue instance
    queue = JobQueue(
        max_concurrent=int(getattr(settings, "pipeline_max_concurrent_jobs", 5)),
        job_ttl_seconds=int(getattr(settings, "pipeline_job_ttl_seconds", 3600)),
    )

    async def _execute_job_background(job_id: str) -> None:
        """Execute pipeline job in background."""
        from datetime import datetime

        job = await queue.get_job(job_id)
        if not job:
            logger.warning("Job not found for execution: %s", job_id)
            return

        try:
            # Update status to running
            await queue.update_status(job_id, JobStatus.RUNNING, started_at=datetime.utcnow())

            # Execute pipeline
            tool = PipelineTool()
            ctx = TenantContext(tenant_id=job.tenant_id, workspace_id=job.workspace_id)
            with with_tenant(ctx):
                result: StepResult = await tool._run_async(job.url, job.quality)

            # Update with result
            await queue.update_status(
                job_id,
                JobStatus.COMPLETED,
                result=result.to_dict(),
                completed_at=datetime.utcnow(),
                progress=100.0,
            )

        except Exception as exc:
            # Update with error
            logger.exception("Job execution failed: %s", exc, extra={"job_id": job_id})
            await queue.update_status(
                job_id,
                JobStatus.FAILED,
                error=str(exc),
                completed_at=datetime.utcnow(),
            )

    @app.post(
        "/pipeline/jobs",
        summary="Create async pipeline job",
        status_code=status.HTTP_201_CREATED,
    )
    async def _create_pipeline_job(
        payload: dict[str, Any] = Body(..., embed=False),
    ) -> JSONResponse:
        """Create a new pipeline job for async execution."""
        url = payload.get("url")
        quality = payload.get("quality")
        tenant_id = payload.get("tenant_id") or payload.get("tenant") or "default"
        workspace_id = payload.get("workspace_id") or payload.get("workspace") or "main"

        if not isinstance(url, str) or not url.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="`url` is required",
            )

        if quality is not None and not isinstance(quality, str):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="`quality` must be a string",
            )

        resolved_quality = quality.strip() if isinstance(quality, str) else "1080p"

        # Create job
        job_id = await queue.create_job(
            url=url.strip(),
            quality=resolved_quality,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        )

        # Start background execution
        asyncio.create_task(_execute_job_background(job_id))

        # Return job info
        job = await queue.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create job",
            )

        return JSONResponse(status_code=status.HTTP_201_CREATED, content=job.to_dict())

    @app.get("/pipeline/jobs/{job_id}", summary="Get pipeline job status")
    async def _get_pipeline_job(job_id: str) -> JSONResponse:
        """Retrieve job status and result."""
        job = await queue.get_job(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job not found: {job_id}")

        return JSONResponse(status_code=status.HTTP_200_OK, content=job.to_dict())

    @app.delete("/pipeline/jobs/{job_id}", summary="Cancel/delete pipeline job")
    async def _delete_pipeline_job(job_id: str) -> JSONResponse:
        """Cancel a running job or delete a completed job."""
        job = await queue.get_job(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job not found: {job_id}")

        # If job is running, mark as cancelled
        if job.status == JobStatus.RUNNING:
            from datetime import datetime

            await queue.update_status(job_id, JobStatus.CANCELLED, completed_at=datetime.utcnow())

        # Delete job
        deleted = await queue.delete_job(job_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete job",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "job_id": job_id,
                "status": "cancelled" if job.status == JobStatus.RUNNING else "deleted",
            },
        )

    @app.get("/pipeline/jobs", summary="List pipeline jobs")
    async def _list_pipeline_jobs(
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> JSONResponse:
        """List all jobs with optional filtering."""
        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = JobStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid status: {status}. Must be one of: queued, running, completed, failed, cancelled",
                )

        # List jobs
        jobs = await queue.list_jobs(tenant_id=tenant_id, workspace_id=workspace_id, status=status_filter)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"jobs": [job.to_dict() for job in jobs], "count": len(jobs)},
        )

    # Start cleanup task
    async def _cleanup_task() -> None:
        """Periodic cleanup of expired jobs."""
        while True:
            await asyncio.sleep(300)  # 5 minutes
            try:
                count = await queue.cleanup_expired_jobs()
                if count > 0:
                    logger.info("Cleaned up %d expired jobs", count)
            except Exception as exc:
                logger.exception("Cleanup task error: %s", exc)

    asyncio.create_task(_cleanup_task())


__all__ = ["register_pipeline_routes"]
