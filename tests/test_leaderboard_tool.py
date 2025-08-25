from pathlib import Path

from ultimate_discord_intelligence_bot.tools.leaderboard_tool import LeaderboardTool


def test_update_and_get_top(tmp_path):
    storage = tmp_path / "board.json"
    tool = LeaderboardTool(storage)
    tool.update_scores("Alice", 1, 2, 3)
    tool.update_scores("Bob", 0, 1, 0)
    top = tool.get_top()
    assert top[0]["person"] == "Alice"
    assert top[0]["lies"] == 1 and top[0]["misinfo"] == 3
