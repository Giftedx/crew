import pytest

from ultimate_discord_intelligence_bot.tools import GovernancePolicyTool


@pytest.mark.parametrize(
    "text, expected_action",
    [
        ("This contains discussion of weapon and potential attack.", "block"),
        ("This is a neutral transcript with no sensitive terms.", "pass"),
        ("Some adult explicit content is mentioned.", "review"),
    ],
)
def test_governance_policy_tool_actions(text, expected_action):
    tool = GovernancePolicyTool()
    result = tool.run({"transcript": text})
    assert result.success is True
    data = result.data
    # unwrap if nested
    if "result" in data and isinstance(data["result"], dict):
        data = data["result"]
    assert data.get("action") == expected_action
    assert isinstance(data.get("confidence"), float)


def test_governance_policy_tool_empty_input_validation():
    tool = GovernancePolicyTool()
    res = tool.run({"transcript": "   "})
    assert res.success is False
    assert res["status"] == "error"
    assert "empty" in (res.error or "").lower()
