"""Simple scheduler to poll creator platforms for updates."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from ..profiles.store import ProfileStore


class ContentPoller:
    """Periodically update profiles with a ``last_checked`` timestamp."""

    def __init__(self, store: ProfileStore, interval: int = 300) -> None:
        self.store = store
        self.interval = interval

    async def poll_once(self) -> datetime:
        """Poll all profiles once and update ``last_checked``."""
        now = datetime.now(UTC)
        for profile in self.store.all_profiles():
            profile.last_checked["poller"] = now
            self.store.upsert_profile(profile)
        return now

    async def run(self) -> None:  # pragma: no cover - simple loop
        while True:
            await self.poll_once()
            await asyncio.sleep(self.interval)


__all__ = ["ContentPoller"]
