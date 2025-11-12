from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from fastapi import Body, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult
_BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()


def _track_task(task: asyncio.Task[Any]) -> None:
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)


logger = logging.getLogger(__name__)


def register_pipeline_routes(app: FastAPI, settings: Any) -> None:
    """Register the ContentPipeline HTTP trigger when enabled.

    The endpoint is guarded by the ``ENABLE_PIPELINE_RUN_API`` flag and uses the
    existing ``PipelineTool`` implementation so budgeting, tracing, and metrics
    instrumentation remain centralised.
    """
    try:
        enabled = bool(settings.enable_pipeline_run_api)
    except Exception as exc:
        logger.debug("pipeline API flag lookup failed: %s", exc)
        return
    if not enabled:
        return
    try:
        from ultimate_discord_intelligence_bot.mission_api import run_mission
        from ultimate_discord_intelligence_bot.tenancy import TenantContext
    except Exception as exc:
        logger.debug("pipeline API wiring skipped: %s", exc)
        return

    @app.post("/pipeline/run", summary="Run the content pipeline")
    async def _pipeline_run(payload: dict[str, Any] = Body(..., embed=False)) -> JSONResponse:
        url = payload.get("url")
        quality = payload.get("quality")
        tenant_id = payload.get("tenant_id") or payload.get("tenant") or "default"
        workspace_id = payload.get("workspace_id") or payload.get("workspace") or "main"
        if not isinstance(url, str) or not url.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="`url` is required")
        if quality is not None and (not isinstance(quality, str)):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="`quality` must be a string")
        resolved_quality = quality.strip() if isinstance(quality, str) else None
        ctx = TenantContext(tenant_id=tenant_id, workspace_id=workspace_id)
        try:
            logger.info("pipeline API request", extra={"tenant_id": tenant_id, "workspace_id": workspace_id})
            result: StepResult = await run_mission(
                {"url": url.strip(), "quality": resolved_quality or "1080p"}, tenant_ctx=ctx
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("pipeline run failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Pipeline execution failed"
            ) from exc
        response_payload = result.to_dict()
        data = response_payload.setdefault("data", {})
        if isinstance(data, dict):
            data.setdefault("tenant_id", tenant_id)
            data.setdefault("workspace_id", workspace_id)
        http_status = status.HTTP_200_OK if result.success else status.HTTP_502_BAD_GATEWAY
        return JSONResponse(status_code=http_status, content=response_payload)

    try:
        job_queue_enabled = bool(settings.enable_pipeline_job_queue)
    except Exception as exc:
        logger.debug("pipeline job queue flag lookup failed: %s", exc)
        job_queue_enabled = False
    if not job_queue_enabled:
        return
    try:
        from server.job_queue import JobQueue, JobStatus
    except Exception as exc:
        logger.debug("job queue import failed: %s", exc)
        return
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
            await queue.update_status(job_id, JobStatus.RUNNING, started_at=datetime.utcnow())
            ctx = TenantContext(tenant_id=job.tenant_id, workspace_id=job.workspace_id)
            result: StepResult = await run_mission({"url": job.url, "quality": job.quality}, tenant_ctx=ctx)
            await queue.update_status(
                job_id, JobStatus.COMPLETED, result=result.to_dict(), completed_at=datetime.utcnow(), progress=100.0
            )
        except Exception as exc:
            logger.exception("Job execution failed: %s", exc, extra={"job_id": job_id})
            await queue.update_status(job_id, JobStatus.FAILED, error=str(exc), completed_at=datetime.utcnow())

    @app.post("/pipeline/jobs", summary="Create async pipeline job", status_code=status.HTTP_201_CREATED)
    async def _create_pipeline_job(payload: dict[str, Any] = Body(..., embed=False)) -> JSONResponse:
        """Create a new pipeline job for async execution."""
        url = payload.get("url")
        quality = payload.get("quality")
        tenant_id = payload.get("tenant_id") or payload.get("tenant") or "default"
        workspace_id = payload.get("workspace_id") or payload.get("workspace") or "main"
        if not isinstance(url, str) or not url.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="`url` is required")
        if quality is not None and (not isinstance(quality, str)):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="`quality` must be a string")
        resolved_quality = quality.strip() if isinstance(quality, str) else "1080p"
        job_id = await queue.create_job(
            url=url.strip(), quality=resolved_quality, tenant_id=tenant_id, workspace_id=workspace_id
        )
        task = asyncio.create_task(_execute_job_background(job_id))
        _track_task(task)
        job = await queue.get_job(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create job")
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
        if job.status == JobStatus.RUNNING:
            from datetime import datetime

            await queue.update_status(job_id, JobStatus.CANCELLED, completed_at=datetime.utcnow())
        deleted = await queue.delete_job(job_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete job")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"job_id": job_id, "status": "cancelled" if job.status == JobStatus.RUNNING else "deleted"},
        )

    @app.get("/pipeline/jobs", summary="List pipeline jobs")
    async def _list_pipeline_jobs(
        tenant_id: str | None = None, workspace_id: str | None = None, status: str | None = None
    ) -> JSONResponse:
        """List all jobs with optional filtering."""
        status_filter = None
        if status:
            try:
                status_filter = JobStatus(status)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid status: {status}. Must be one of: queued, running, completed, failed, cancelled",
                ) from exc
        jobs = await queue.list_jobs(tenant_id=tenant_id, workspace_id=workspace_id, status=status_filter)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"jobs": [job.to_dict() for job in jobs], "count": len(jobs)}
        )

    async def _cleanup_task() -> None:
        """Periodic cleanup of expired jobs."""
        while True:
            await asyncio.sleep(300)
            try:
                count = await queue.cleanup_expired_jobs()
                if count > 0:
                    logger.info("Cleaned up %d expired jobs", count)
            except Exception as exc:
                logger.exception("Cleanup task error: %s", exc)

    task = asyncio.create_task(_cleanup_task())
    _track_task(task)


__all__ = ["register_pipeline_routes"]
