from ultimate_discord_intelligence_bot.tools.logical_fallacy_tool import LogicalFallacyTool


def test_detects_straw_man():
    tool = LogicalFallacyTool()
    result = tool._run("This is a straw man argument")
    assert result["status"] == "success"
    assert "straw man" in result["fallacies"]


def test_handles_no_fallacies():
    tool = LogicalFallacyTool()
    result = tool._run("All is well with this statement")
    assert result["status"] == "success"
    assert result["fallacies"] == []
