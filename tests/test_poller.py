"""Tests for the content poller service."""

import asyncio

from ultimate_discord_intelligence_bot.profiles.schema import CreatorProfile
from ultimate_discord_intelligence_bot.profiles.store import ProfileStore
from ultimate_discord_intelligence_bot.services.poller import ContentPoller


def test_poller_updates_last_checked(tmp_path):
    store = ProfileStore(tmp_path / "p.db")
    store.upsert_profile(CreatorProfile(name="Tester"))
    poller = ContentPoller(store, interval=0)
    asyncio.run(poller.poll_once())
    prof = store.get_profile("Tester")
    assert "poller" in prof.last_checked
