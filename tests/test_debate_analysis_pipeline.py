from ultimate_discord_intelligence_bot.debate_analysis_pipeline import DebateAnalysisPipeline
from ultimate_discord_intelligence_bot.tools.leaderboard_tool import LeaderboardTool
from ultimate_discord_intelligence_bot.tools.debate_command_tool import DebateCommandTool
from ultimate_discord_intelligence_bot.tools.timeline_tool import TimelineTool
from ultimate_discord_intelligence_bot.tools.trustworthiness_tracker_tool import (
    TrustworthinessTrackerTool,
)
from ultimate_discord_intelligence_bot.tools.character_profile_tool import (
    CharacterProfileTool,
)


class DummyMemory:
    def __init__(self):
        self.calls = []

    def run(self, text, metadata, collection=None):
        self.calls.append((text, metadata, collection))
        return {"status": "success"}


def test_debate_pipeline_smoke(tmp_path):
    lb = LeaderboardTool(storage_path=tmp_path / "lb.json")
    tl = TimelineTool(storage_path=tmp_path / "timeline.json")
    trust = TrustworthinessTrackerTool(storage_path=tmp_path / "trust.json")
    profile = CharacterProfileTool(
        storage_path=tmp_path / "profiles.json", leaderboard=lb, trust_tracker=trust
    )
    memory = DummyMemory()
    pipeline = DebateAnalysisPipeline(
        leaderboard=lb,
        timeline=tl,
        memory_storage=memory,
        trust_tracker=trust,
        profile_tool=profile,
        ethan_defender=lambda _: "Ethan closing",
        hasan_defender=lambda _: "Hasan closing",
    )
    tool = DebateCommandTool(pipeline=pipeline)
    transcript = "hello there\nthis is a test"
    result = tool.run(
        "analyze",
        url="video1",
        ts=5,
        clip_text="hello",
        person="hasan",
        transcript=transcript,
    )
    assert result["status"] == "success"
    top = lb.get_top()
    assert top and top[0]["person"] == "hasan"
    events = tl.get_timeline("video1")
    assert events and events[0]["clip"] == "hello"
    assert memory.calls and memory.calls[0][1]["video_id"] == "video1"
    assert memory.calls[0][2] == "analysis"
    prof = profile.get_profile("hasan")
    assert prof["leaderboard"]["lies"] in (0, 1)
    assert result["ethan_defender"] == "Ethan closing"
    assert result["hasan_defender"] == "Hasan closing"
    cmd_profile = tool.run("profile", person="hasan")
    assert cmd_profile["status"] == "success"
