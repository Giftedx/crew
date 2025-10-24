"""Uploader backfill helpers.

This module provides minimal, flag-guarded utilities to enumerate recent
videos for an uploader and enqueue ingest jobs. It intentionally avoids
hard wiring into the scheduler to keep changes low-risk; callers pass in
the existing PriorityQueue from ``scheduler``.

Network-heavy paths are feature-flagged so tests can run offline safely.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from core.time import default_utc_now
from ingest import pipeline as ingest_pipeline


if TYPE_CHECKING:
    from collections.abc import Iterable

    from scheduler.priority_queue import PriorityQueue


logger = logging.getLogger(__name__)


# --------------------------- data contracts
@dataclass
class BackfillPlan:
    source_type: str  # e.g., "youtube"
    uploader_handle: str  # e.g., "@somechannel" or channel URL
    tenant: str
    workspace: str
    since_iso: str  # ISO8601 timestamp boundary
    limit: int = 200


# --------------------------- provider-specific enumeration
# All yt-dlp interactions must go through approved wrappers in
# ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool per guardrails.
try:
    # Lightweight metadata listing helper (no downloads)
    from ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool import (
        youtube_list_channel_videos,
    )
except Exception:  # pragma: no cover - import-time environment mismatch
    youtube_list_channel_videos = None  # type: ignore[assignment]


def _normalize_youtube_handle(handle_or_url: str) -> str:
    """Return a canonical channel videos URL for a given handle or URL.

    Accepts forms like "@handle", "https://www.youtube.com/@handle",
    "https://www.youtube.com/channel/UC.." and returns a ``/videos`` URL
    suitable for scraping with yt-dlp.
    """

    h = handle_or_url.strip()
    if "youtube.com/" in h:
        base = h.split("?")[0].rstrip("/")
    elif h.startswith("@"):
        base = f"https://www.youtube.com/{h}"
    else:
        # Fallback: treat as raw handle
        base = f"https://www.youtube.com/@{h}"
    if not base.endswith("/videos"):
        base = base + "/videos"
    return base


def enumerate_youtube_recent_videos(handle_or_url: str, since_iso: str, *, limit: int = 200) -> list[dict[str, str]]:
    """Enumerate recent YouTube videos for ``handle_or_url`` since ``since_iso``.

    Returns list of dicts with ``external_id`` and ``url`` keys. This uses
    yt-dlp in "extract_flat" mode to avoid downloads. If yt-dlp is not
    available or networking is disabled, returns an empty list.
    """

    import os

    if os.getenv("ENABLE_UPLOADER_BACKFILL", "0") != "1":
        logger.info("Backfill disabled via ENABLE_UPLOADER_BACKFILL")
        return []

    # Require approved helper to be importable
    if youtube_list_channel_videos is None:
        logger.warning("yt-dlp helper not available; cannot enumerate channel videos")
        return []

    channel_videos_url = _normalize_youtube_handle(handle_or_url)

    # Build cutoff date
    since_dt_env_fallback = default_utc_now() - timedelta(days=365)
    try:
        since_dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00")).astimezone(UTC)
    except Exception:
        since_dt = since_dt_env_fallback
    since_ymd = since_dt.strftime("%Y%m%d")

    try:
        entries: Iterable[dict[str, Any]] = youtube_list_channel_videos(channel_videos_url)  # type: ignore[misc]
    except Exception as exc:  # pragma: no cover - network/dep dependent
        logger.warning("Channel listing failed for %s: %s", channel_videos_url, exc)
        return []

    out: list[dict[str, str]] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        vid = str(e.get("id") or "").strip()
        url = str(e.get("url") or "").strip()
        if not vid:
            continue
        up_raw = str(e.get("upload_date") or "")
        if up_raw and len(up_raw) == 8 and up_raw.isdigit():
            # Compare as YYYYMMDD strings for efficiency
            if up_raw < since_ymd:
                continue
        # Construct URL when missing
        if not url:
            url = f"https://www.youtube.com/watch?v={vid}"
        out.append({"external_id": vid, "url": url})
        if len(out) >= limit:
            break

    return out


# --------------------------- enqueue helpers
def enqueue_backfill(plan: BackfillPlan, queue: PriorityQueue) -> int:
    """Enumerate and enqueue ingest jobs per ``plan``.

    Returns number of jobs enqueued. Currently supports ``source_type='youtube'``.
    """

    if plan.source_type.lower() != "youtube":
        logger.info("Backfill source %s not supported", plan.source_type)
        return 0

    items = enumerate_youtube_recent_videos(plan.uploader_handle, plan.since_iso, limit=plan.limit)
    if not items:
        return 0

    jobs: list[ingest_pipeline.IngestJob] = []
    for it in items:
        jobs.append(
            ingest_pipeline.IngestJob(
                source="youtube",
                external_id=it["external_id"],
                url=it["url"],
                tenant=plan.tenant,
                workspace=plan.workspace,
                tags=[],
                visibility="public",
            )
        )

    queue.enqueue_bulk(jobs)
    return len(jobs)


__all__ = [
    "BackfillPlan",
    "enqueue_backfill",
    "enumerate_youtube_recent_videos",
]
