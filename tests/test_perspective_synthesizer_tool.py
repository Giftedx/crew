from ultimate_discord_intelligence_bot.tools.perspective_synthesizer_tool import PerspectiveSynthesizerTool


def test_combines_inputs():
    tool = PerspectiveSynthesizerTool()
    result = tool._run("A", "B")
    assert result["status"] == "success"
    assert result["summary"] == "A\nB"
