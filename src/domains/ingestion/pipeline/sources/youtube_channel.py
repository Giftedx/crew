from __future__ import annotations

from datetime import timedelta
from platform.time import default_utc_now

import domains.ingestion.providers.yt_dlp_download_tool as ytdlp

from .base import DiscoveryItem, SourceConnector, Watch


class YouTubeChannelConnector(SourceConnector):
    """Discover recent videos for a YouTube channel.

    The watch ``handle`` should be a channel URL (e.g., https://www.youtube.com/channel/UC... or /@handle).
    Uses yt-dlp in flat mode via centralized helper to list entries and filters to the
    last 12 months by upload_date when available.
    Cursor semantics: stores the latest processed video id (string) to avoid re-enqueueing.
    """

    def __init__(self, months: int = 12) -> None:
        self.months = months

    def _cutoff(self) -> str:
        dt = default_utc_now() - timedelta(days=30 * self.months)
        return dt.strftime("%Y%m%d")

    def discover(self, watch: Watch, state: dict[str, object]) -> list[DiscoveryItem]:
        try:
            entries = ytdlp.youtube_list_channel_videos(watch.handle)
        except Exception:
            return []
        cutoff = self._cutoff()
        last_seen_id = state.get("cursor")
        items: list[DiscoveryItem] = []
        newest_id: str | None = None
        for e in entries:
            vid = str(e.get("id", ""))
            if not vid:
                continue
            if newest_id is None:
                newest_id = vid
            if last_seen_id and vid == last_seen_id:
                break
            up = e.get("upload_date")
            if isinstance(up, str) and up and (up < cutoff):
                break
            url = str(e.get("url", "")) or f"https://www.youtube.com/watch?v={vid}"
            items.append(DiscoveryItem(external_id=vid, url=url, published_at=up))
        if newest_id:
            state["cursor"] = newest_id
        return items
