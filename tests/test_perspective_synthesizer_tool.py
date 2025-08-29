from ultimate_discord_intelligence_bot.services import MemoryService
from ultimate_discord_intelligence_bot.tools.perspective_synthesizer_tool import (
    PerspectiveSynthesizerTool,
)


def test_combines_inputs(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    tool = PerspectiveSynthesizerTool()
    result = tool._run("A", "B")
    assert result["status"] == "success"
    expected = ("Summarise the following information:\nA\nB").upper()
    assert result["summary"] == expected


def test_retrieves_memory(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    memory = MemoryService()
    memory.add("extra context")
    tool = PerspectiveSynthesizerTool(memory=memory)
    result = tool._run("extra")
    assert "EXTRA CONTEXT" in result["summary"]
