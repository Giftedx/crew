"""Integration between Arq task queue and content pipeline."""

from __future__ import annotations

import logging
from typing import Any

from src.tasks.queue_service import TaskQueueService


logger = logging.getLogger(__name__)


class PipelineIntegration:
    """Integration layer between content pipeline and task queue."""

    def __init__(self):
        """Initialize pipeline integration."""
        self.queue_service = TaskQueueService()

    async def enqueue_video_processing(self, video_url: str, tenant: str, workspace: str) -> str | None:
        """Enqueue video processing job.

        Args:
            video_url: URL of video to process
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            Job ID if successful, None otherwise
        """
        try:
            job_id = await self.queue_service.enqueue(
                "process_video_async", video_url=video_url, tenant=tenant, workspace=workspace
            )
            logger.info(f"Enqueued video processing: {video_url} -> {job_id}")
            return job_id
        except Exception as e:
            logger.error(f"Failed to enqueue video processing: {e}")
            return None

    async def get_processing_status(self, job_id: str) -> dict[str, Any] | None:
        """Get status of video processing job.

        Args:
            job_id: Job identifier

        Returns:
            dict with job status or None
        """
        return await self.queue_service.get_status(job_id)
