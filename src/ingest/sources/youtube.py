from __future__ import annotations

from .base import DiscoveryItem, SourceConnector, Watch


class YouTubeConnector(SourceConnector):
    """Minimal YouTube discovery connector.

    For the purposes of tests this connector treats ``watch.handle`` as both the
    external ID and the URL to ingest.  A simple cursor stored in ``state``
    ensures items are only emitted once.
    """

    def discover(self, watch: Watch, state: dict[str, object]) -> list[DiscoveryItem]:
        cursor = state.get("cursor")
        if cursor == watch.handle:
            return []
        state["cursor"] = watch.handle
        return [DiscoveryItem(external_id=watch.handle, url=watch.handle)]
