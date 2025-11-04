"""Arq worker infrastructure for background job processing."""

from __future__ import annotations

import asyncio
import logging
import signal
from typing import Any


try:
    from arq import ArqRedis, Worker
    from arq.connections import RedisSettings

    ARQ_AVAILABLE = True
except ImportError:
    ARQ_AVAILABLE = False
    Worker = None  # type: ignore[assignment,misc]
    ArqRedis = None  # type: ignore[assignment,misc]
    RedisSettings = None  # type: ignore[assignment,misc]

from tasks.arq_config import get_arq_settings


logger = logging.getLogger(__name__)


class ArqWorker:
    """Arq worker for async task processing."""

    def __init__(self):
        """Initialize Arq worker."""
        if not ARQ_AVAILABLE:
            raise ImportError("Arq not available. Install with: pip install arq")

        self.settings = get_arq_settings()
        self.worker: Worker | None = None
        self.shutdown_event = asyncio.Event()
        self._background_tasks: set[asyncio.Task[Any]] = set()

    async def start(self):
        """Start the Arq worker."""
        if not ARQ_AVAILABLE:
            logger.error("Arq not available, cannot start worker")
            return

        try:
            redis_settings = RedisSettings(**self.settings["redis_settings"])

            # Create worker with job functions from jobs module
            self.worker = Worker(
                functions=[],  # Will be populated from jobs.py
                redis_settings=redis_settings,
                max_jobs=self.settings["max_jobs"],
                job_timeout=self.settings["timeout"],
            )

            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGTERM, self._handle_shutdown)
            signal.signal(signal.SIGINT, self._handle_shutdown)

            logger.info("Starting Arq worker...")
            await self.worker.async_run()

        except Exception as e:
            logger.error(f"Failed to start Arq worker: {e}")
            raise

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown_event.set()
        if self.worker:
            # Trigger worker shutdown
            task = asyncio.create_task(self.worker.close())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    async def stop(self):
        """Stop the Arq worker gracefully."""
        if self.worker:
            logger.info("Stopping Arq worker...")
            await self.worker.close()
            logger.info("Arq worker stopped")

    def get_worker_stats(self) -> dict[str, Any]:
        """Get worker statistics."""
        if not self.worker:
            return {"status": "not_started"}

        return {
            "status": "running",
            "max_jobs": self.settings["max_jobs"],
            "timeout": self.settings["timeout"],
        }


if __name__ == "__main__":
    # Simple CLI entrypoint for `python -m tasks.worker`
    try:
        worker = ArqWorker()
        asyncio.run(worker.start())
    except Exception as exc:
        logger.error(f"Arq worker failed to start: {exc}")
        raise
