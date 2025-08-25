from unittest.mock import MagicMock

from ultimate_discord_intelligence_bot.tools.discord_qa_tool import DiscordQATool


def test_discord_qa_tool_returns_snippets():
    search = MagicMock()
    search.run.return_value = [{"text": "result"}]
    tool = DiscordQATool(search_tool=search)
    out = tool.run("question")
    assert out["status"] == "success"
    assert out["snippets"] == ["result"]
    search.run.assert_called_once()
