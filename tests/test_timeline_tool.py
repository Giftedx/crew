from ultimate_discord_intelligence_bot.tools.timeline_tool import TimelineTool


def test_timeline_tool_add_get(tmp_path):
    tool = TimelineTool(storage_path=tmp_path / "timeline.json")
    tool.add_event("vid", {"ts": 2, "desc": "later"})
    tool.add_event("vid", {"ts": 1, "desc": "earlier"})
    events = tool.get_timeline("vid")
    assert events[0]["ts"] == 1 and events[1]["ts"] == 2
