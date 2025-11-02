"""Unit tests for bias and manipulation extractors module."""

from src.ultimate_discord_intelligence_bot.orchestrator import (
    bias_manipulation_extractors,
)


class TestBiasManipulationExtractors:
    """Test suite for bias and manipulation extraction functions."""

    def test_extract_bias_indicators_from_crew_political(self):
        """Test bias indicator extraction with political bias."""
        crew_result = "This shows clear liberal bias with democratic perspectives"
        biases = bias_manipulation_extractors.extract_bias_indicators_from_crew(crew_result)
        assert len(biases) > 0
        political_biases = [b for b in biases if b["type"] == "political_bias"]
        assert len(political_biases) == 1
        assert political_biases[0]["confidence"] > 0

    def test_extract_bias_indicators_from_crew_confirmation(self):
        """Test bias indicator extraction with confirmation bias."""
        crew_result = "This confirms and supports our existing beliefs"
        biases = bias_manipulation_extractors.extract_bias_indicators_from_crew(crew_result)
        confirmation_biases = [b for b in biases if b["type"] == "confirmation_bias"]
        assert len(confirmation_biases) == 1

    def test_extract_bias_indicators_from_crew_no_bias(self):
        """Test bias indicator extraction with no bias indicators."""
        crew_result = "This is neutral content without bias indicators"
        biases = bias_manipulation_extractors.extract_bias_indicators_from_crew(crew_result)
        assert biases == []

    def test_extract_bias_indicators_from_crew_empty(self):
        """Test bias indicator extraction with empty result."""
        biases = bias_manipulation_extractors.extract_bias_indicators_from_crew(None)
        assert biases == []

    def test_extract_deception_analysis_from_crew_high(self):
        """Test deception analysis extraction with high deception indicators."""
        crew_result = "This content avoids direct answers and contains contradictions"
        analysis = bias_manipulation_extractors.extract_deception_analysis_from_crew(crew_result)
        assert analysis["deception_score"] > 0.0
        assert len(analysis["indicators"]) > 0
        assert analysis["risk_level"] in ["low", "medium", "high"]

    def test_extract_deception_analysis_from_crew_low(self):
        """Test deception analysis extraction with low deception indicators."""
        crew_result = "This is honest and transparent content"
        analysis = bias_manipulation_extractors.extract_deception_analysis_from_crew(crew_result)
        assert analysis["deception_score"] < 0.5

    def test_extract_deception_analysis_from_crew_empty(self):
        """Test deception analysis extraction with empty result."""
        analysis = bias_manipulation_extractors.extract_deception_analysis_from_crew(None)
        assert analysis["deception_score"] == 0.0
        assert analysis["indicators"] == []
        assert analysis["confidence"] == 0.0

    def test_extract_manipulation_indicators_from_crew_emotional(self):
        """Test manipulation indicator extraction with emotional manipulation."""
        crew_result = "This uses guilt and fear to manipulate emotions"
        indicators = bias_manipulation_extractors.extract_manipulation_indicators_from_crew(crew_result)
        assert len(indicators) > 0
        emotional_indicators = [i for i in indicators if i["technique"] == "emotional_manipulation"]
        assert len(emotional_indicators) == 1

    def test_extract_manipulation_indicators_from_crew_gaslighting(self):
        """Test manipulation indicator extraction with gaslighting."""
        crew_result = "This gaslights by denying reality and questioning your memory"
        indicators = bias_manipulation_extractors.extract_manipulation_indicators_from_crew(crew_result)
        gaslighting_indicators = [i for i in indicators if i["technique"] == "gaslighting"]
        assert len(gaslighting_indicators) == 1

    def test_extract_manipulation_indicators_from_crew_no_manipulation(self):
        """Test manipulation indicator extraction with no manipulation."""
        crew_result = "This is straightforward content without manipulation"
        indicators = bias_manipulation_extractors.extract_manipulation_indicators_from_crew(crew_result)
        assert indicators == []

    def test_extract_narrative_integrity_from_crew_high(self):
        """Test narrative integrity extraction with high integrity."""
        crew_result = "This is consistent, coherent, and transparent"
        integrity = bias_manipulation_extractors.extract_narrative_integrity_from_crew(crew_result)
        assert integrity["integrity_score"] > 0.5
        assert integrity["coherence"] >= 0.0
        assert integrity["consistency"] >= 0.0

    def test_extract_narrative_integrity_from_crew_low(self):
        """Test narrative integrity extraction with low integrity."""
        crew_result = "This is inconsistent and contradictory with misleading information"
        integrity = bias_manipulation_extractors.extract_narrative_integrity_from_crew(crew_result)
        assert integrity["integrity_score"] < 0.5
        assert integrity["red_flags"] > integrity["green_flags"]

    def test_extract_narrative_integrity_from_crew_empty(self):
        """Test narrative integrity extraction with empty result."""
        integrity = bias_manipulation_extractors.extract_narrative_integrity_from_crew(None)
        assert integrity["integrity_score"] == 0.5
        assert integrity["coherence"] == 0.0
        assert integrity["consistency"] == 0.0

    def test_extract_psychological_threats_from_crew_high(self):
        """Test psychological threat extraction with high threats."""
        crew_result = "This manipulates and intimidates while exploiting vulnerabilities"
        threats = bias_manipulation_extractors.extract_psychological_threats_from_crew(crew_result)
        assert threats["threat_level"] in ["low", "medium", "high"]
        assert len(threats["threats_detected"]) > 0
        assert threats["risk_score"] > 0.0

    def test_extract_psychological_threats_from_crew_low(self):
        """Test psychological threat extraction with low threats."""
        crew_result = "This is supportive and non-threatening content"
        threats = bias_manipulation_extractors.extract_psychological_threats_from_crew(crew_result)
        assert threats["threat_level"] == "low"
        assert threats["risk_score"] < 0.4

    def test_extract_psychological_threats_from_crew_empty(self):
        """Test psychological threat extraction with empty result."""
        threats = bias_manipulation_extractors.extract_psychological_threats_from_crew(None)
        assert threats["threat_level"] == "low"
        assert threats["threats_detected"] == []
        assert threats["risk_score"] == 0.0

    def test_calculate_comprehensive_threat_score_high(self):
        """Test comprehensive threat score calculation with high threats."""
        crew_result = "This is deceptive and manipulative with high bias and psychological threats"
        score = bias_manipulation_extractors.calculate_comprehensive_threat_score_from_crew(crew_result)
        assert 0.0 <= score <= 1.0

    def test_calculate_comprehensive_threat_score_low(self):
        """Test comprehensive threat score calculation with low threats."""
        crew_result = "This is honest and transparent content"
        score = bias_manipulation_extractors.calculate_comprehensive_threat_score_from_crew(crew_result)
        assert score < 0.5

    def test_calculate_comprehensive_threat_score_empty(self):
        """Test comprehensive threat score calculation with empty result."""
        score = bias_manipulation_extractors.calculate_comprehensive_threat_score_from_crew(None)
        assert score == 0.0
