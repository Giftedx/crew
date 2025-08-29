"""Tests for extended DebateCommandTool commands."""

from datetime import datetime

from ultimate_discord_intelligence_bot.debate_analysis_pipeline import DebateAnalysisPipeline
from ultimate_discord_intelligence_bot.profiles.store import ProfileStore
from ultimate_discord_intelligence_bot.tools.character_profile_tool import (
    CharacterProfileTool,
)
from ultimate_discord_intelligence_bot.tools.debate_command_tool import DebateCommandTool


def test_latest_and_collabs(tmp_path):
    profile_tool = CharacterProfileTool(storage_path=tmp_path / "chars.json")
    pipeline = DebateAnalysisPipeline(profile_tool=profile_tool)
    store = ProfileStore(tmp_path / "p.db")
    tool = DebateCommandTool(pipeline=pipeline, profile_store=store)

    profile_tool.record_event("Ethan", {"video_id": "v1", "ts": 1})
    store.record_link("Ethan", "Hasan", datetime(2024, 1, 1))

    latest = tool._run("latest", person="Ethan")
    assert latest["events"][0]["video_id"] == "v1"

    collabs = tool._run("collabs", person="Ethan")
    assert collabs["collabs"] == [("Hasan", 1)]


def test_creator_and_verify_profiles(tmp_path):
    profile_tool = CharacterProfileTool(storage_path=tmp_path / "chars.json")
    pipeline = DebateAnalysisPipeline(profile_tool=profile_tool)
    store = ProfileStore(tmp_path / "p.db")
    tool = DebateCommandTool(pipeline=pipeline, profile_store=store)

    verify = tool._run("verify_profiles")
    assert "H3H3 Productions" in verify["verified"]
    creator = tool._run("creator", person="H3H3 Productions")
    assert creator["profile"]["person"] == "H3H3 Productions"
