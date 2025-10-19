"""Unit tests for fact-checking extractors module."""

from src.ultimate_discord_intelligence_bot.orchestrator import fact_checking_extractors


class TestFactCheckingExtractors:
    """Test suite for fact-checking extraction functions."""

    def test_extract_fact_checks_from_crew_verified(self):
        """Test fact check extraction with verified content."""
        crew_result = "This claim has been verified and confirmed as accurate"
        fact_checks = fact_checking_extractors.extract_fact_checks_from_crew(crew_result)
        assert "verified_claims" in fact_checks
        assert "disputed_claims" in fact_checks
        assert fact_checks["confidence"] > 0.5

    def test_extract_fact_checks_from_crew_disputed(self):
        """Test fact check extraction with disputed content."""
        crew_result = "This claim is disputed and appears to be false"
        fact_checks = fact_checking_extractors.extract_fact_checks_from_crew(crew_result)
        assert fact_checks["confidence"] < 0.5

    def test_extract_fact_checks_from_crew_empty(self):
        """Test fact check extraction with empty result."""
        fact_checks = fact_checking_extractors.extract_fact_checks_from_crew(None)
        assert fact_checks["verified_claims"] == []
        assert fact_checks["disputed_claims"] == []
        assert fact_checks["confidence"] == 0.0

    def test_extract_logical_analysis_from_crew_fallacies(self):
        """Test logical analysis extraction with fallacies detected."""
        crew_result = "This argument contains personal attacks and straw man arguments"
        analysis = fact_checking_extractors.extract_logical_analysis_from_crew(crew_result)
        assert "fallacies_detected" in analysis
        assert "logical_strength" in analysis
        assert len(analysis["fallacies_detected"]) > 0

    def test_extract_logical_analysis_from_crew_no_fallacies(self):
        """Test logical analysis extraction with no fallacies."""
        crew_result = "This is a well-structured logical argument"
        analysis = fact_checking_extractors.extract_logical_analysis_from_crew(crew_result)
        assert analysis["logical_strength"] > 0.5

    def test_extract_logical_analysis_from_crew_empty(self):
        """Test logical analysis extraction with empty result."""
        analysis = fact_checking_extractors.extract_logical_analysis_from_crew(None)
        assert analysis["fallacies_detected"] == []
        assert analysis["logical_strength"] == 0.0

    def test_extract_credibility_from_crew_high(self):
        """Test credibility extraction with high credibility indicators."""
        crew_result = "This source is reputable and authoritative with expert analysis"
        credibility = fact_checking_extractors.extract_credibility_from_crew(crew_result)
        # The function finds multiple credibility indicators, so score should be reasonable
        assert credibility["overall_credibility"] > 0.0
        assert len(credibility["factors"]) > 0

    def test_extract_credibility_from_crew_low(self):
        """Test credibility extraction with low credibility indicators."""
        crew_result = "This source lacks evidence and transparency"
        credibility = fact_checking_extractors.extract_credibility_from_crew(crew_result)
        assert credibility["overall_credibility"] <= 0.5

    def test_extract_credibility_from_crew_empty(self):
        """Test credibility extraction with empty result."""
        credibility = fact_checking_extractors.extract_credibility_from_crew(None)
        assert credibility["overall_credibility"] == 0.5
        assert credibility["factors"] == []
        assert credibility["confidence"] == 0.0

    def test_extract_source_validation_from_crew_with_sources(self):
        """Test source validation extraction with sources present."""
        crew_result = "According to https://example.com and (Smith, 2023), this is verified"
        validation = fact_checking_extractors.extract_source_validation_from_crew(crew_result)
        assert validation["sources_validated"] > 0
        assert validation["reliability"] > 0.0

    def test_extract_source_validation_from_crew_peer_reviewed(self):
        """Test source validation extraction with peer-reviewed sources."""
        crew_result = "This is peer-reviewed research with verified sources"
        validation = fact_checking_extractors.extract_source_validation_from_crew(crew_result)
        assert validation["validation_method"] == "peer_review"
        assert validation["reliability"] > 0.5

    def test_extract_source_validation_from_crew_no_sources(self):
        """Test source validation extraction with no sources."""
        crew_result = "This is just an opinion without any sources"
        validation = fact_checking_extractors.extract_source_validation_from_crew(crew_result)
        assert validation["sources_validated"] == 0
        assert validation["validation_method"] == "none"

    def test_calculate_verification_confidence_high(self):
        """Test verification confidence calculation with high confidence indicators."""
        crew_result = "This is confirmed and verified with certainty"
        confidence = fact_checking_extractors.calculate_verification_confidence_from_crew(crew_result)
        assert confidence > 0.7

    def test_calculate_verification_confidence_medium(self):
        """Test verification confidence calculation with medium confidence indicators."""
        crew_result = "This is likely and probably accurate"
        confidence = fact_checking_extractors.calculate_verification_confidence_from_crew(crew_result)
        assert 0.4 <= confidence <= 0.7

    def test_calculate_verification_confidence_low(self):
        """Test verification confidence calculation with low confidence indicators."""
        crew_result = "This is uncertain and unclear with doubtful accuracy"
        confidence = fact_checking_extractors.calculate_verification_confidence_from_crew(crew_result)
        assert confidence < 0.4

    def test_calculate_verification_confidence_empty(self):
        """Test verification confidence calculation with empty result."""
        confidence = fact_checking_extractors.calculate_verification_confidence_from_crew(None)
        assert confidence == 0.0
