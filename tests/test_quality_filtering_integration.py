import pytest

from ultimate_discord_intelligence_bot.tools import ContentQualityAssessmentTool


@pytest.fixture(autouse=True)
def enable_quality_filtering(monkeypatch):
    monkeypatch.setenv("ENABLE_QUALITY_FILTERING", "1")
    yield


def test_content_quality_tool_low_quality_bypass():
    tool = ContentQualityAssessmentTool()
    res = tool.run({"transcript": "Um, yeah. Bad. Short."})
    assert res.success
    data = res.data.get("result", {})
    assert data.get("should_process") is False
    assert data.get("overall_score") < 0.7
    assert "insufficient_content" in (data.get("bypass_reason") or "")


def test_content_quality_tool_high_quality_process():
    # Override thresholds directly (env vars read at class import time)
    ContentQualityAssessmentTool.MIN_WORD_COUNT = 150
    ContentQualityAssessmentTool.MIN_SENTENCE_COUNT = 8
    ContentQualityAssessmentTool.MIN_COHERENCE_SCORE = 0.4
    ContentQualityAssessmentTool.MIN_OVERALL_SCORE = 0.7
    tool = ContentQualityAssessmentTool()
    # Build multi-sentence transcript to satisfy word + sentence + quality thresholds
    base_sentence = "Quantum computing research demonstrates sustained coherence and meaningful entanglement enabling practical algorithmic breakthroughs in optimization and simulation."
    sentences = [base_sentence for _ in range(12)]  # 12 sentences (>10 threshold)
    transcript = " ".join(sentences)
    res = tool.run({"transcript": transcript})
    assert res.success
    data = res.data.get("result", {})
    # After lowering thresholds majority should pass and processing allowed
    assert data.get("should_process") is True, f"Bypass reason: {data.get('bypass_reason')}"
    assert data.get("overall_score") >= 0.7
