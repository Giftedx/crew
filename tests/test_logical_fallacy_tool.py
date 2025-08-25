from ultimate_discord_intelligence_bot.tools.logical_fallacy_tool import LogicalFallacyTool
import pytest


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


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "If we allow A today, inevitably B will happen tomorrow; it's a slippery slope.",
            "slippery slope",
        ),
        (
            "You should believe it because I said so, and I'm an expert!",
            "appeal to authority",
        ),
        ("You're either with us or against us.", "false dilemma"),
    ],
)
def test_detects_additional_fallacies(text, expected):
    tool = LogicalFallacyTool()
    result = tool._run(text)
    assert expected in result["fallacies"]
