"""Unit tests for the comprehensive bias analyzer."""

from __future__ import annotations

import pytest

from ultimate_discord_intelligence_bot.analysis.bias_metrics import BiasAnalyzer, BiasMetrics


def test_analyze_bias_identifies_left_leaning_content() -> None:
    """Content saturated with left-leaning indicators should score negative leaning."""
    analyzer = BiasAnalyzer()
    content = (
        "Progressive liberal socialist advocates promote universal healthcare, social "
        "justice, and environmental sustainability across communities."
    )

    result = analyzer.analyze_bias(content)

    assert result.success is True
    metrics = result.data["bias_metrics"]
    assert isinstance(metrics, BiasMetrics)
    assert metrics.political_leaning < 0.0


def test_analyze_bias_uses_temporal_context() -> None:
    """Temporal consistency should reflect differences against historical bias."""
    analyzer = BiasAnalyzer()
    content = (
        "Progressive advocates highlight social justice programs while conservative "
        "leaders emphasize freedom and merit within policy debates."
    )

    result = analyzer.analyze_bias(content, context={"historical_bias": 0.8})

    assert result.success is True
    metrics = result.data["bias_metrics"]
    expected = 1.0 - abs(metrics.political_leaning - 0.8)
    assert metrics.temporal_consistency == pytest.approx(expected)


def test_generate_bias_report_triggers_human_review_when_scores_high() -> None:
    """The report should flag human review when the overall score is elevated."""
    analyzer = BiasAnalyzer()
    content = (
        "Some believe progressive, liberal, and social justice policies help communities, "
        "while others argue conservative values protect freedom, merit, and traditional "
        "principles. Proponents say studies proves the approach works, demonstrates "
        "successes, and confirms important outcomes, while opponents say research refutes "
        "several claims, challenges the findings, contradicts the evidence, and disputes "
        "the testimony. Critics argue the analysis opposes key data, undermines the "
        "conclusions, and questions reports. According to experts, data suggests both "
        "sides provide evidence, research, studies, and analysis. Historically, urban and "
        "rural groups present different views with various perspectives."
    )

    report_result = analyzer.generate_bias_report(content, context={"historical_bias": 0.0})

    assert report_result.success is True
    bias_report = report_result.data["bias_report"]

    assert "content_analysis" in bias_report
    assert "overall_assessment" in bias_report
    assert isinstance(bias_report["overall_assessment"]["recommendations"], list)
    assert bias_report["overall_assessment"]["human_review_required"] is True
    assert bias_report["overall_assessment"]["bias_level"] in {
        "Low bias",
        "Moderate bias",
        "High bias",
        "Extreme bias",
    }


def test_compare_bias_metrics_produces_similarity_score() -> None:
    """Comparing two metric sets should yield bounded similarity output."""
    analyzer = BiasAnalyzer()
    metrics_one = BiasMetrics(
        political_leaning=-0.5,
        partisan_intensity=0.8,
        viewpoint_diversity=0.2,
        evidence_balance=0.3,
        framing_neutrality=0.4,
        source_diversity=0.1,
        temporal_consistency=0.2,
    )
    metrics_two = BiasMetrics(
        political_leaning=0.1,
        partisan_intensity=0.2,
        viewpoint_diversity=0.7,
        evidence_balance=0.6,
        framing_neutrality=0.8,
        source_diversity=0.5,
        temporal_consistency=0.9,
    )

    comparison_result = analyzer.compare_bias_metrics(metrics_one, metrics_two)

    assert comparison_result.success is True
    comparison = comparison_result.data["comparison"]
    assert set(comparison.keys()) == {
        "political_leaning_diff",
        "partisan_intensity_diff",
        "viewpoint_diversity_diff",
        "evidence_balance_diff",
        "framing_neutrality_diff",
        "source_diversity_diff",
        "temporal_consistency_diff",
        "overall_bias_diff",
    }
    assert 0.0 <= comparison_result.data["overall_similarity"] <= 1.0


def test_analyze_bias_failure_is_captured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Errors during analysis should surface through a failed StepResult."""
    analyzer = BiasAnalyzer()

    def kaboom(_: str) -> float:
        raise RuntimeError("analysis boom")

    monkeypatch.setattr(analyzer, "_analyze_political_leaning", kaboom)

    result = analyzer.analyze_bias("sample content")

    assert result.success is False
    assert isinstance(result.error, str)
    assert "Bias analysis failed" in result.error


def test_generate_bias_report_structure_for_balanced_content() -> None:
    """Reports for balanced content should still include recommendations text."""
    analyzer = BiasAnalyzer()
    content = (
        "Progressive thinkers argue universal healthcare can help communities, while "
        "conservative leaders say freedom and merit remain vital. According to research, "
        "data suggests both sides present evidence and experts note diverse viewpoints."
    )

    report_result = analyzer.generate_bias_report(content)

    assert report_result.success is True
    bias_report = report_result.data["bias_report"]
    assert isinstance(bias_report["overall_assessment"]["recommendations"], list)
    assert len(bias_report["overall_assessment"]["recommendations"]) >= 1
