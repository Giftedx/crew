"""Auto-follow uploader and enqueue recent videos.

Public helper used by Discord or crew pipeline callers after processing a
video. It inspects the download result for uploader/channel information and
enqueues a backfill job for the last 12 months of content from that uploader.

All actions are guarded by environment flags so this remains opt-in.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

from ingest.backfill import BackfillPlan, enqueue_backfill
from scheduler.priority_queue import PriorityQueue


def _is_youtube(platform: str | None) -> bool:
    return (platform or "").lower() == "youtube"


def trigger_auto_follow(
    download_result: dict[str, Any],
    queue: PriorityQueue,
    *,
    tenant: str,
    workspace: str,
) -> dict[str, Any]:
    """If enabled, enqueue uploader backfill for the last 12 months.

    Parameters
    ----------
    download_result: dict
        The step result from a download tool; should include platform, uploader,
        and url/video_id where possible.
    queue: PriorityQueue
        The existing scheduler queue to enqueue ingest jobs.
    tenant, workspace: str
        Context values used in the ingest namespace and scheduler.

    Returns
    -------
    dict
        {"enabled": bool, "enqueued": int, "note": str}
    """

    if os.getenv("ENABLE_AUTO_FOLLOW_UPLOADER", "0") != "1":
        return {"enabled": False, "enqueued": 0, "note": "auto-follow disabled"}

    platform = str(download_result.get("platform", ""))
    uploader = str(download_result.get("uploader", "")).strip()
    if not uploader or not _is_youtube(platform):
        return {"enabled": True, "enqueued": 0, "note": "unsupported platform or missing uploader"}

    # Compute 12-month boundary
    since = datetime.now(UTC) - timedelta(days=365)
    since_iso = since.isoformat()

    # Prefer stable channel URL/ID over display name to avoid 404s
    channel_id = str(download_result.get("channel_id")) if download_result.get("channel_id") else None
    channel_url = str(download_result.get("channel_url")) if download_result.get("channel_url") else None
    uploader_url = str(download_result.get("uploader_url")) if download_result.get("uploader_url") else None

    if channel_url and "/channel/" in channel_url:
        handle_or_url = channel_url
    elif channel_id:
        handle_or_url = f"https://www.youtube.com/channel/{channel_id}"
    elif uploader_url and "/@" in uploader_url:
        handle_or_url = uploader_url
    else:
        # Fallback to a sanitized @handle (strip spaces)
        handle = uploader.replace(" ", "")
        handle = handle if handle.startswith("@") else f"@{handle}"
        handle_or_url = f"https://www.youtube.com/{handle}"

    plan = BackfillPlan(
        source_type="youtube",
        uploader_handle=handle_or_url,
        tenant=tenant,
        workspace=workspace,
        since_iso=since_iso,
        limit=int(os.getenv("AUTO_FOLLOW_MAX_VIDEOS", "200")),
    )
    count = enqueue_backfill(plan, queue)
    return {"enabled": True, "enqueued": count, "note": "ok"}


__all__ = ["trigger_auto_follow"]
