from ultimate_discord_intelligence_bot.tools.deception_scoring_tool import (
    DeceptionScoringTool,
)


def test_deception_scoring_basic():
    tool = DeceptionScoringTool()
    # Two adverse fact-checks and one fallacy should yield moderate/high risk
    factchecks = [
        {"verdict": "False", "confidence": 0.9},
        {"verdict": "Likely False", "confidence": 0.8},
        {"verdict": "True", "confidence": 0.95},
    ]
    fallacies = {"fallacies": [{"type": "ad hominem"}]}
    res = tool.run({"factchecks": factchecks, "fallacies": fallacies})
    # StepResult exposes mapping view for status/keys
    assert res["status"] == "success"
    score = res.get("score")
    assert isinstance(score, float) and 0.0 <= score <= 1.0
    # Expect score to be at least moderate
    assert score >= 0.4
