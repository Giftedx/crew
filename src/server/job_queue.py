"""Async job queue for long-running pipeline tasks.

Provides in-memory job storage with background execution support,
enabling the pipeline API to return immediately while processing
continues in the background.
"""
from __future__ import annotations
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
logger = logging.getLogger(__name__)

class JobStatus(str, Enum):
    """Job execution states."""
    QUEUED = 'queued'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

@dataclass
class Job:
    """Job metadata and execution state."""
    job_id: str
    status: JobStatus
    url: str
    quality: str
    tenant_id: str
    workspace_id: str
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    progress: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert job to API-friendly dict."""
        return {'job_id': self.job_id, 'status': self.status.value, 'url': self.url, 'quality': self.quality, 'tenant_id': self.tenant_id, 'workspace_id': self.workspace_id, 'created_at': self.created_at.isoformat() if self.created_at else None, 'started_at': self.started_at.isoformat() if self.started_at else None, 'completed_at': self.completed_at.isoformat() if self.completed_at else None, 'result': self.result, 'error': self.error, 'progress': self.progress}

class JobQueue:
    """In-memory job queue with async execution support."""

    def __init__(self, max_concurrent: int=5, job_ttl_seconds: int=3600):
        """Initialize job queue.

        Args:
            max_concurrent: Maximum concurrent running jobs
            job_ttl_seconds: TTL for completed/failed jobs (default 1 hour)
        """
        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()
        self._max_concurrent = max_concurrent
        self._job_ttl_seconds = job_ttl_seconds
        self._running_count = 0

    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        timestamp = int(time.time())
        unique = uuid.uuid4().hex[:8]
        return f'job_{timestamp}_{unique}'

    async def create_job(self, url: str, quality: str, tenant_id: str, workspace_id: str) -> str:
        """Create a new job in the queue.

        Args:
            url: Media URL to process
            quality: Video quality setting
            tenant_id: Tenant identifier
            workspace_id: Workspace identifier

        Returns:
            job_id: Unique job identifier
        """
        async with self._lock:
            job_id = self._generate_job_id()
            job = Job(job_id=job_id, status=JobStatus.QUEUED, url=url, quality=quality, tenant_id=tenant_id, workspace_id=workspace_id)
            self._jobs[job_id] = job
            logger.info('Created pipeline job', extra={'job_id': job_id, 'tenant_id': tenant_id, 'workspace_id': workspace_id, 'url': url})
            try:
                from platform.observability.metrics import get_metrics
                get_metrics().counter('pipeline_jobs_created_total', labels={'tenant': tenant_id, 'workspace': workspace_id})
            except Exception as exc:
                logger.debug('Metrics emission failed: %s', exc)
            return job_id

    async def get_job(self, job_id: str) -> Job | None:
        """Retrieve job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job object or None if not found
        """
        async with self._lock:
            return self._jobs.get(job_id)

    async def update_status(self, job_id: str, status: JobStatus, *, started_at: datetime | None=None, completed_at: datetime | None=None, result: dict[str, Any] | None=None, error: str | None=None, progress: float | None=None) -> None:
        """Update job status and metadata.

        Args:
            job_id: Job identifier
            status: New status
            started_at: Execution start time (optional)
            completed_at: Execution completion time (optional)
            result: Job result data (optional)
            error: Error message (optional)
            progress: Progress percentage 0-100 (optional)
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning('Job not found for status update: %s', job_id)
                return
            old_status = job.status
            job.status = status
            if started_at:
                job.started_at = started_at
            if completed_at:
                job.completed_at = completed_at
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            if progress is not None:
                job.progress = progress
            if old_status != JobStatus.RUNNING and status == JobStatus.RUNNING:
                self._running_count += 1
            elif old_status == JobStatus.RUNNING and status != JobStatus.RUNNING:
                self._running_count -= 1
            logger.info('Job status updated', extra={'job_id': job_id, 'old_status': old_status.value, 'new_status': status.value, 'progress': job.progress})
            if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                try:
                    from platform.observability.metrics import get_metrics
                    get_metrics().counter('pipeline_jobs_completed_total', labels={'tenant': job.tenant_id, 'workspace': job.workspace_id, 'status': status.value})
                    if job.started_at and job.completed_at:
                        duration = (job.completed_at - job.started_at).total_seconds()
                        get_metrics().histogram('pipeline_job_duration_seconds', duration, labels={'tenant': job.tenant_id, 'workspace': job.workspace_id})
                except Exception as exc:
                    logger.debug('Metrics emission failed: %s', exc)

    async def delete_job(self, job_id: str) -> bool:
        """Delete job from queue.

        Args:
            job_id: Job identifier

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            job = self._jobs.pop(job_id, None)
            if job:
                if job.status == JobStatus.RUNNING:
                    self._running_count -= 1
                logger.info('Job deleted', extra={'job_id': job_id})
                return True
            return False

    async def list_jobs(self, *, tenant_id: str | None=None, workspace_id: str | None=None, status: JobStatus | None=None) -> list[Job]:
        """List jobs with optional filtering.

        Args:
            tenant_id: Filter by tenant (optional)
            workspace_id: Filter by workspace (optional)
            status: Filter by status (optional)

        Returns:
            List of matching jobs
        """
        async with self._lock:
            jobs = list(self._jobs.values())
            if tenant_id:
                jobs = [j for j in jobs if j.tenant_id == tenant_id]
            if workspace_id:
                jobs = [j for j in jobs if j.workspace_id == workspace_id]
            if status:
                jobs = [j for j in jobs if j.status == status]
            return jobs

    async def cleanup_expired_jobs(self) -> int:
        """Remove expired completed/failed jobs.

        Returns:
            Number of jobs removed
        """
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self._job_ttl_seconds)
            expired_ids = []
            for job_id, job in self._jobs.items():
                if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED) and job.completed_at and (job.completed_at < cutoff):
                    expired_ids.append(job_id)
            for job_id in expired_ids:
                del self._jobs[job_id]
            if expired_ids:
                logger.info('Cleaned up %d expired jobs', len(expired_ids))
            return len(expired_ids)

    @property
    def running_count(self) -> int:
        """Get number of currently running jobs."""
        return self._running_count

    @property
    def can_start_job(self) -> bool:
        """Check if a new job can be started (under max_concurrent limit)."""
        return self._running_count < self._max_concurrent
__all__ = ['Job', 'JobQueue', 'JobStatus']