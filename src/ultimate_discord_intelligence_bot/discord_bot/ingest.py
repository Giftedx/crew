from __future__ import annotations
import asyncio
import os
from pathlib import Path
from typing import Any
from domains.ingestion.pipeline import models as _ingest_models
from domains.ingestion.pipeline.sources.youtube_channel import YouTubeChannelConnector as _YouTubeChannelConnector
from domains.memory.vector_store import VectorStore as _VectorStore
from scheduler.scheduler import Scheduler as _Scheduler
from ultimate_discord_intelligence_bot.services.ingest_queue import get_ingest_queue

async def start_ingest_workers(loop: asyncio.AbstractEventLoop | None=None) -> None:
    """Start ingest worker(s) and discovery loop using configured settings.

    This is a direct lift from the original script with minimal changes.
    """
    try:
        db_path = os.getenv('INGEST_DB_PATH') or str(Path(__file__).resolve().parents[3] / 'data' / 'ingest.db')
        print(f'🧵 Starting ingest workers (db={db_path})…')
        conn = _ingest_models.connect(db_path)
        queue = get_ingest_queue()
        try:
            from domains.ingestion.pipeline.sources.youtube import YouTubeConnector as _YouTubeConnector
        except Exception:
            _YouTubeConnector = None
        connectors: dict[str, Any] = {'youtube_channel': _YouTubeChannelConnector()}
        if _YouTubeConnector is not None:
            connectors['youtube'] = _YouTubeConnector()
        scheduler = _Scheduler(conn, queue, connectors)
        store = _VectorStore()
        try:
            concurrency = max(1, int(os.getenv('INGEST_WORKER_CONCURRENCY', '1')))
        except Exception:
            concurrency = 1
        try:
            idle_sleep = max(0.5, float(os.getenv('INGEST_WORKER_IDLE_SLEEP', '2.0')))
        except Exception:
            idle_sleep = 2.0
        try:
            tick_seconds = max(5.0, float(os.getenv('INGEST_WORKER_TICK_SECONDS', '60.0')))
        except Exception:
            tick_seconds = 60.0

        async def _worker_loop(name: str):
            print(f'🔁 Ingest worker {name} started')
            while True:
                try:
                    job = await asyncio.to_thread(scheduler.worker_run_once, store)
                    if job is not None:
                        print(f'✅ Worker {name}: processed {job.source} job for {job.url}')
                    if job is None:
                        await asyncio.sleep(idle_sleep)
                except Exception as e:
                    print(f'⚠️  Worker {name} error: {e}')
                    await asyncio.sleep(idle_sleep)

        async def _discovery_loop():
            print('🔎 Ingest discovery loop started')
            while True:
                try:
                    await asyncio.to_thread(scheduler.tick)
                    print('✅ Discovery tick complete')
                except Exception as e:
                    print(f'⚠️  Discovery tick error: {e}')
                await asyncio.sleep(tick_seconds)
        loop = loop or asyncio.get_running_loop()
        for i in range(concurrency):
            loop.create_task(_worker_loop(f'#{i + 1}'))
        loop.create_task(_discovery_loop())
        print(f'✅ Ingest workers running (concurrency={concurrency}, tick={tick_seconds}s)')
    except Exception as e:
        print(f'⚠️  Failed to start ingest workers: {e}')
__all__ = ['start_ingest_workers']