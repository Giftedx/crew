"""Simple scheduler to poll creator platforms for updates."""
from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING
from core.time import default_utc_now
if TYPE_CHECKING:
    from platform.core.step_result import StepResult
    from ..profiles.store import ProfileStore

class ContentPoller:
    """Periodically update profiles with a ``last_checked`` timestamp."""

    def __init__(self, store: ProfileStore, interval: int=300) -> StepResult:
        self.store = store
        self.interval = interval

    async def poll_once(self) -> StepResult:
        """Poll all profiles once and update ``last_checked``."""
        now = default_utc_now()
        for profile in self.store.all_profiles():
            profile.last_checked['poller'] = now
            self.store.upsert_profile(profile)
        return now

    async def run(self) -> StepResult:
        while True:
            await self.poll_once()
            await asyncio.sleep(self.interval)
__all__ = ['ContentPoller']