"""Task queue service for managing background jobs."""

from __future__ import annotations

import logging
from typing import Any

try:
    from arq import ArqRedis, create_pool
    from arq.connections import RedisSettings
    ARQ_AVAILABLE = True
except ImportError:
    ARQ_AVAILABLE = False
    ArqRedis = None  # type: ignore[assignment,misc]
    create_pool = None  # type: ignore[assignment,misc]
    RedisSettings = None  # type: ignore[assignment,misc]

from ultimate_discord_intelligence_bot.step_result import StepResult

from src.tasks.arq_config import get_arq_settings

logger = logging.getLogger(__name__)


class TaskQueueService:
    """Service for managing async task queue operations."""

    def __init__(self):
        """Initialize task queue service."""
        if not ARQ_AVAILABLE:
            logger.warning("Arq not available, task queue operations will be no-ops")
            self.redis_pool: ArqRedis | None = None
            return
        
        self.settings = get_arq_settings()
        self.redis_pool: ArqRedis | None = None

    async def initialize(self):
        """Initialize Redis connection pool."""
        if not ARQ_AVAILABLE:
            return
        
        try:
            redis_settings = RedisSettings(**self.settings["redis_settings"])
            self.redis_pool = await create_pool(redis_settings)
            logger.info("Task queue service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize task queue: {e}")
            self.redis_pool = None

    async def enqueue(self, job_function: str, **kwargs: Any) -> str | None:
        """Enqueue a job for background processing.
        
        Args:
            job_function: Name of the job function to execute
            **kwargs: Arguments to pass to the job function
            
        Returns:
            Job ID if successful, None otherwise
        """
        if not self.redis_pool:
            logger.error("Task queue not initialized")
            return None
        
        try:
            job = await self.redis_pool.enqueue_job(job_function, **kwargs)
            logger.info(f"Enqueued job: {job.job_id}")
            return job.job_id if job else None
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            return None

    async def get_status(self, job_id: str) -> dict[str, Any] | None:
        """Get status of a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            dict with job status or None if not found
        """
        if not self.redis_pool:
            return None
        
        try:
            job = await self.redis_pool.get_job_result(job_id)
            if job:
                return {
                    "job_id": job_id,
                    "status": job.status,
                    "result": job.result,
                    "error": str(job.error) if job.error else None,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if not self.redis_pool:
            return False
        
        try:
            await self.redis_pool.abort_job(job_id)
            logger.info(f"Cancelled job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job: {e}")
            return False

    async def retry(self, job_id: str) -> str | None:
        """Retry a failed job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            New job ID if successful, None otherwise
        """
        if not self.redis_pool:
            return None
        
        try:
            # Get original job info and retry
            job = await self.redis_pool.get_job_result(job_id)
            if job and job.info:
                # Re-enqueue with same parameters
                new_job = await self.redis_pool.enqueue_job(
                    job.info.function_name,
                    *job.info.args,
                    **job.info.kwargs
                )
                logger.info(f"Retrying job {job_id} as {new_job.job_id}")
                return new_job.job_id if new_job else None
            return None
        except Exception as e:
            logger.error(f"Failed to retry job: {e}")
            return None

    async def close(self):
        """Close Redis connection pool."""
        if self.redis_pool:
            await self.redis_pool.close()
            logger.info("Task queue service closed")
