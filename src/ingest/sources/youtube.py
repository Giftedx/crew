from __future__ import annotations

from typing import List

from .base import Watch, DiscoveryItem, SourceConnector


class YouTubeConnector(SourceConnector):
    """Minimal YouTube discovery connector.

    For the purposes of tests this connector treats ``watch.handle`` as both the
    external ID and the URL to ingest.  A simple cursor stored in ``state``
    ensures items are only emitted once.
    """

    def discover(self, watch: Watch, state: dict) -> List[DiscoveryItem]:
        cursor = state.get("cursor")
        if cursor == watch.handle:
            return []
        state["cursor"] = watch.handle
        return [DiscoveryItem(external_id=watch.handle, url=watch.handle)]

