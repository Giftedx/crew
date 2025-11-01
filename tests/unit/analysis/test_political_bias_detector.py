"""Unit tests for the political bias detector toolkit."""

from __future__ import annotations

import pytest

from ultimate_discord_intelligence_bot.analysis.political_bias_detector import (
    BiasIndicators,
    DiversityScore,
    FramingAnalysis,
    PoliticalBiasDetector,
    SelectivityScore,
)


@pytest.fixture
def detector() -> PoliticalBiasDetector:
    """Return a fresh instance of the detector for each test."""
    return PoliticalBiasDetector()


def test_detect_bias_indicators_neutral_content(detector: PoliticalBiasDetector) -> None:
    """Neutral content should yield near-zero bias indicators."""
    content = (
        "The committee reviewed the budget figures and provided a factual summary "
        "of routine operational updates for all departments without commentary."
    )

    result = detector.detect_bias_indicators(content)

    assert result.success is True
    assert result.data["analysis_complete"] is True

    indicators = result.data["bias_indicators"]
    assert isinstance(indicators, BiasIndicators)
    assert indicators.partisan_language == pytest.approx(0.0)
    assert indicators.overall_bias_score() == pytest.approx(result.data["overall_bias_score"])
    assert result.data["overall_bias_score"] == pytest.approx(0.0)


def test_detect_bias_indicators_identifies_partisan_language(
    detector: PoliticalBiasDetector,
) -> None:
    """Highly partisan language should be captured with high indicator scores."""
    content = (
        "Progressive liberal socialist policies are dangerous and radical, inspiring "
        "outrage among opponents who refuse to compromise."
    )

    result = detector.detect_bias_indicators(content)

    assert result.success is True

    indicators = result.data["bias_indicators"]
    assert isinstance(indicators, BiasIndicators)
    assert indicators.partisan_language == pytest.approx(1.0)
    assert indicators.emotional_manipulation == pytest.approx(1.0)
    assert result.data["overall_bias_score"] > 0.2


def test_measure_viewpoint_diversity_reports_perspectives(
    detector: PoliticalBiasDetector,
) -> None:
    """The diversity analysis should reflect multiple perspectives and sources."""
    content = (
        "Some believe progressive policies help communities, while others argue "
        "conservative principles remain vital. According to studies, experts say "
        "recently collected data suggests both urban and rural residents are represented."
    )

    result = detector.measure_viewpoint_diversity(content)

    assert result.success is True

    diversity_score = result.data["diversity_score"]
    assert isinstance(diversity_score, DiversityScore)
    assert diversity_score.perspective_count >= 2
    assert result.data["overall_diversity"] == pytest.approx(diversity_score.overall_diversity())
    assert result.data["overall_diversity"] > 0.0


def test_analyze_framing_techniques_detects_loaded_language(
    detector: PoliticalBiasDetector,
) -> None:
    """Loaded terms should increase framing bias metrics."""
    content = "The radical proposal is a dangerous threat that brave citizens must stop."

    result = detector.analyze_framing_techniques(content)

    assert result.success is True

    framing_analysis = result.data["framing_analysis"]
    assert isinstance(framing_analysis, FramingAnalysis)
    assert framing_analysis.loaded_language > 0.0
    assert framing_analysis.overall_framing_bias() == pytest.approx(result.data["overall_framing_bias"])


def test_detect_selective_evidence_supporting_bias(detector: PoliticalBiasDetector) -> None:
    """Content with only supporting evidence should surface selectivity concerns."""
    content = (
        "Studies show the initiative works, research confirms the results, and data proves "
        "the findings while evidence suggests continued success."
    )

    result = detector.detect_selective_evidence(content)

    assert result.success is True

    selectivity_score = result.data["selectivity_score"]
    assert isinstance(selectivity_score, SelectivityScore)
    assert selectivity_score.supporting_evidence_ratio == pytest.approx(1.0)
    assert selectivity_score.opposing_evidence_ratio == pytest.approx(0.0)
    assert selectivity_score.overall_selectivity() == pytest.approx(result.data["overall_selectivity"])
    assert result.data["overall_selectivity"] > 0.0


def test_detect_bias_indicators_returns_failure_on_exception(
    detector: PoliticalBiasDetector, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the detector raises internally, the StepResult should capture the failure."""

    def boom(_: str) -> float:
        raise RuntimeError("kaboom")

    monkeypatch.setattr(detector, "_analyze_partisan_language", boom)

    result = detector.detect_bias_indicators("example content")

    assert result.success is False
    assert isinstance(result.error, str)
    assert "Bias detection failed" in result.error
