from ultimate_discord_intelligence_bot.tools.truth_scoring_tool import (
    TruthScoringTool,
)


def test_truth_scoring_tool_scores_verdicts():
    tool = TruthScoringTool()
    result = tool.run([True, False, True])
    assert result["status"] == "success"
    assert result["score"] == 2 / 3


def test_truth_scoring_tool_handles_empty():
    tool = TruthScoringTool()
    result = tool.run([])
    assert result["score"] == 0.0
