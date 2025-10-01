from requests import RequestException

from ultimate_discord_intelligence_bot.tools.fact_check_tool import FactCheckTool


def test_fact_check_aggregates(monkeypatch):
    tool = FactCheckTool()
    monkeypatch.setattr(tool, "_search_duckduckgo", lambda q: [{"title": "A", "url": "u", "snippet": "a"}])
    monkeypatch.setattr(tool, "_search_serply", lambda q: [{"title": "B", "url": "u", "snippet": "b"}])
    monkeypatch.setattr(tool, "_search_exa", lambda q: [])
    monkeypatch.setattr(tool, "_search_perplexity", lambda q: [])
    monkeypatch.setattr(tool, "_search_wolfram", lambda q: [])
    result = tool.run("sample claim")
    assert result["status"] == "success"
    titles = [e["title"] for e in result["evidence"]]
    assert "A" in titles and "B" in titles


def test_fact_check_skips_failed_backend(monkeypatch):
    tool = FactCheckTool()

    def boom(_query):
        raise RequestException("network down")

    monkeypatch.setattr(tool, "_search_duckduckgo", boom)
    monkeypatch.setattr(tool, "_search_serply", lambda q: [])
    monkeypatch.setattr(tool, "_search_exa", lambda q: [])
    monkeypatch.setattr(tool, "_search_perplexity", lambda q: [])
    monkeypatch.setattr(tool, "_search_wolfram", lambda q: [])
    result = tool.run("sample claim")
    assert result["status"] == "success"
    assert result["evidence"] == []
