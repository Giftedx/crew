import json
from ultimate_discord_intelligence_bot.tools.trustworthiness_tracker_tool import (
    TrustworthinessTrackerTool,
)


def test_tracker_updates_counts(tmp_path):
    path = tmp_path / "trust.json"
    tool = TrustworthinessTrackerTool(storage_path=path)
    first = tool.run(person="Alice", verdict=True)
    assert first["score"] == 1.0
    second = tool.run(person="Alice", verdict=False)
    assert second["score"] == 0.5
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["Alice"]["truths"] == 1
    assert data["Alice"]["lies"] == 1
