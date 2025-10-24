"""Tests for cross-profile analytics in the profile store."""

from datetime import datetime

from ultimate_discord_intelligence_bot.profiles.store import ProfileStore


def test_record_and_fetch_collaborators(tmp_path):
    store = ProfileStore(tmp_path / "p.db")
    ts = datetime(2024, 1, 1)
    store.record_link("A", "B", ts)
    store.record_link("A", "B", ts)
    collabs = store.get_collaborators("A")
    assert collabs == [("B", 2)]
