from ultimate_discord_intelligence_bot.tools.steelman_argument_tool import (
    SteelmanArgumentTool,
)


def test_steelman_argument_tool_combines_evidence():
    tool = SteelmanArgumentTool()
    claim = "Universal healthcare improves outcomes"
    evidence = [
        {"source": "study", "snippet": "countries with universal coverage live longer"},
        {"source": "report", "snippet": "families face fewer medical bankruptcies"},
    ]
    result = tool.run(claim=claim, evidence=evidence)
    assert result["status"] == "success"
    assert "universal coverage" in result["argument"].lower()
    assert claim in result["argument"]


def test_steelman_argument_tool_handles_no_evidence():
    tool = SteelmanArgumentTool()
    claim = "Water is wet"
    result = tool.run(claim=claim, evidence=[])
    assert result["status"] == "uncertain"
    assert result["argument"] == claim
    assert "no supporting evidence" in result["notes"]
