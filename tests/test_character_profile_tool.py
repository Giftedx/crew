from pathlib import Path

from ultimate_discord_intelligence_bot.tools.character_profile_tool import (
    CharacterProfileTool,
)
from ultimate_discord_intelligence_bot.tools.leaderboard_tool import LeaderboardTool
from ultimate_discord_intelligence_bot.tools.trustworthiness_tracker_tool import (
    TrustworthinessTrackerTool,
)


def test_character_profile_tool(tmp_path: Path) -> None:
    leaderboard_path = tmp_path / "board.json"
    trust_path = tmp_path / "trust.json"
    profile_path = tmp_path / "profiles.json"
    leaderboard = LeaderboardTool(storage_path=leaderboard_path)
    trust = TrustworthinessTrackerTool(storage_path=trust_path)
    tool = CharacterProfileTool(
        storage_path=profile_path, leaderboard=leaderboard, trust_tracker=trust
    )

    leaderboard.update_scores("bob", 1, 0, 0)
    trust.run("bob", False)
    tool.record_event("bob", {"video_id": "vid", "ts": 1, "clip": "hi"})

    result = tool.run("bob")
    profile = result["profile"]
    assert profile["leaderboard"]["lies"] == 1
    assert profile["trust"]["lies"] == 1
    assert profile["events"][0]["video_id"] == "vid"
