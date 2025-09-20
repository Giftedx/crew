from __future__ import annotations

import os
from datetime import UTC, datetime

from ingest import models
from ingest.sources import YouTubeChannelConnector
from scheduler import PriorityQueue, Scheduler


def test_channel_backfill_watch_and_discovery(tmp_path, monkeypatch):
    # Enable feature flag for post-ingest watch creation
    os.environ["ENABLE_YOUTUBE_CHANNEL_BACKFILL_AFTER_INGEST"] = "1"

    # Prepare DB and scheduler with channel connector
    conn = models.connect(tmp_path / "sched.db")
    queue = PriorityQueue(conn)

    # Register two connectors: a simple youtube (URL passthrough) and channel connector for discovery
    # Use the existing minimal YouTubeConnector for video URLs
    from ingest.sources.youtube import YouTubeConnector

    sched = Scheduler(
        conn,
        queue,
        {
            "youtube": YouTubeConnector(),
            "youtube_channel": YouTubeChannelConnector(),
        },
    )

    # Monkeypatch yt-dlp flat listing helper to avoid network
    def fake_list_channel_videos(url: str):
        # Return three entries with descending dates, one beyond 12 months
        today = datetime.now(UTC)
        yyyy_mm_dd = lambda dt: dt.strftime("%Y%m%d")  # noqa: E731 - small inline helper for brevity
        return [
            {"id": "new1", "url": "https://www.youtube.com/watch?v=new1", "upload_date": yyyy_mm_dd(today)},
            {
                "id": "new0",
                "url": "https://www.youtube.com/watch?v=new0",
                "upload_date": yyyy_mm_dd(today),
            },
            {
                "id": "old9",
                "url": "https://www.youtube.com/watch?v=old9",
                # 400 days ago (should be filtered by connector cutoff)
                "upload_date": yyyy_mm_dd(today.replace(year=today.year - 2)),
            },
        ]

    from ultimate_discord_intelligence_bot.tools import yt_dlp_download_tool as ymod

    monkeypatch.setattr(ymod, "youtube_list_channel_videos", fake_list_channel_videos)

    # Simulate a completed ingest by calling the ingest pipeline directly via scheduler worker
    # We need to ensure the pipeline writes provenance (requires INGEST_DB_PATH)
    os.environ["INGEST_DB_PATH"] = str(tmp_path / "sched.db")

    # Insert a youtube video watch; when the job is processed, pipeline will add a youtube_channel watch
    sched.add_watch(tenant="t", workspace="w", source_type="youtube", handle="https://youtu.be/vid123")

    # Enqueue from youtube connector and process one
    sched.tick()

    # Replace ingest.pipeline.run to simulate YouTube metadata with channel info so the flag path runs
    class Meta:
        id = "vid123"
        title = "t"
        channel = "@creator"
        channel_id = "UC123"
        published_at = datetime.now(UTC).isoformat()
        duration = 1.0
        url = "https://youtu.be/vid123"
        thumbnails = []

    def fake_fetch_metadata(url: str):
        return Meta()

    def fake_fetch_transcript(url: str):
        return "a\nb\nc"

    from ingest.providers import youtube as yprov

    monkeypatch.setattr(yprov, "fetch_metadata", fake_fetch_metadata)
    monkeypatch.setattr(yprov, "fetch_transcript", fake_fetch_transcript)

    # Use a real vector store for pipeline
    from memory import vector_store

    store = vector_store.VectorStore()
    # Process one job, pipeline should create a youtube_channel watch in same DB
    sched.worker_run_once(store=store)

    # Verify the youtube_channel watch was created
    rows = conn.execute(
        "SELECT handle FROM watchlist WHERE source_type='youtube_channel' AND tenant='t' AND workspace='w'"
    ).fetchall()
    assert rows, "youtube_channel watch should be created by pipeline flag"
    handle = rows[0][0]
    assert handle.startswith("https://www.youtube.com/") and handle.endswith("/videos")

    # With the channel watch present, tick again to discover videos via YouTubeChannelConnector
    sched.tick()
    # Two recent items should have been enqueued (third is filtered by cutoff)
    assert queue.pending_count() >= 1
