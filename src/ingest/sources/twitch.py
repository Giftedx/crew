from __future__ import annotations

from typing import List

from .base import Watch, DiscoveryItem, SourceConnector


class TwitchConnector(SourceConnector):
    """Minimal Twitch discovery connector used in tests.

    Behaviour mirrors :class:`YouTubeConnector` by emitting the watch handle once
    as the discovered item.
    """

    def discover(self, watch: Watch, state: dict) -> List[DiscoveryItem]:
        cursor = state.get("cursor")
        if cursor == watch.handle:
            return []
        state["cursor"] = watch.handle
        return [DiscoveryItem(external_id=watch.handle, url=watch.handle)]

