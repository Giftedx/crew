import types

import requests

from ultimate_discord_intelligence_bot.tools.fact_check_tool import FactCheckTool


def test_fact_check(monkeypatch):
    def fake_get(url, params=None, timeout=10):
        class Resp:
            def json(self):
                return {
                    "RelatedTopics": [
                        {"Text": "Example", "FirstURL": "http://example.com"}
                    ]
                }

        return Resp()

    monkeypatch.setattr(requests, "get", fake_get)
    tool = FactCheckTool()
    result = tool.run("sample claim")
    assert result["status"] == "success"
    assert result["evidence"]
