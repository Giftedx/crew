"""Tests for ClaimExtractorTool."""

from unittest.mock import patch

import pytest

from domains.intelligence.analysis.claim_extractor_tool import ClaimExtractorTool
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestClaimExtractorTool:
    """Test cases for ClaimExtractorTool."""

    @pytest.fixture
    def tool(self):
        """Create ClaimExtractorTool instance."""
        return ClaimExtractorTool()

    def test_tool_initialization(self, tool):
        """Test tool initializes correctly."""
        assert tool.name == "claim_extractor"
        assert "claim" in tool.description.lower()

    def test_run_with_valid_text(self, tool):
        """Test claim extraction with valid text."""
        with patch.object(tool, "_extract_claims") as mock_extract:
            mock_extract.return_value = StepResult.ok(
                data={
                    "claims": [{"text": "The Earth is round", "confidence": 0.95, "type": "factual"}],
                    "total_claims": 1,
                }
            )
            result = tool._run("The Earth is round and orbits the Sun.")
            assert result.success
            assert "claims" in result.data
            mock_extract.assert_called_once()

    def test_run_with_empty_text(self, tool):
        """Test claim extraction with empty text."""
        result = tool._run("")
        assert not result.success
        assert "empty" in result.error.lower()

    def test_run_with_short_text(self, tool):
        """Test claim extraction with insufficient text."""
        result = tool._run("Hi")
        assert not result.success
        assert "insufficient" in result.error.lower()

    def test_extract_claims_success(self, tool):
        """Test successful claim extraction."""
        text = "The study shows that 90% of participants improved their performance."
        with patch.object(tool, "_identify_claim_patterns") as mock_patterns:
            with patch.object(tool, "_classify_claim_type") as mock_classify:
                with patch.object(tool, "_calculate_confidence") as mock_confidence:
                    mock_patterns.return_value = [
                        "The study shows that 90% of participants improved their performance."
                    ]
                    mock_classify.return_value = "statistical"
                    mock_confidence.return_value = 0.85
                    result = tool._extract_claims(text)
                    assert result.success
                    assert len(result.data["claims"]) == 1
                    assert result.data["claims"][0]["type"] == "statistical"
                    assert result.data["claims"][0]["confidence"] == 0.85

    def test_identify_claim_patterns(self, tool):
        """Test claim pattern identification."""
        text = "The data shows that X is true. However, some studies suggest Y might be false."
        patterns = tool._identify_claim_patterns(text)
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        assert all(isinstance(pattern, str) for pattern in patterns)

    def test_classify_claim_type(self, tool):
        """Test claim type classification."""
        factual_claim = "The Earth orbits the Sun."
        opinion_claim = "I believe this is the best approach."
        statistical_claim = "90% of users prefer this method."
        factual_type = tool._classify_claim_type(factual_claim)
        opinion_type = tool._classify_claim_type(opinion_claim)
        statistical_type = tool._classify_claim_type(statistical_claim)
        assert factual_type in ["factual", "scientific"]
        assert opinion_type in ["opinion", "subjective"]
        assert statistical_type in ["statistical", "quantitative"]

    def test_calculate_confidence(self, tool):
        """Test confidence calculation."""
        strong_claim = "The peer-reviewed study conclusively demonstrates that X causes Y."
        weak_claim = "Some people think this might be true."
        strong_confidence = tool._calculate_confidence(strong_claim)
        weak_confidence = tool._calculate_confidence(weak_claim)
        assert 0 <= strong_confidence <= 1
        assert 0 <= weak_confidence <= 1
        assert strong_confidence > weak_confidence

    def test_handle_extraction_error(self, tool):
        """Test error handling in claim extraction."""
        with patch.object(tool, "_identify_claim_patterns") as mock_patterns:
            mock_patterns.side_effect = Exception("Extraction failed")
            result = tool._extract_claims("test text")
            assert not result.success
            assert "failed" in result.error.lower()

    def test_validate_input_text(self, tool):
        """Test input text validation."""
        assert tool._validate_input_text("This is a valid text for claim extraction.") is True
        assert tool._validate_input_text("") is False
        assert tool._validate_input_text("Hi") is False
        assert tool._validate_input_text(None) is False

    def test_filter_duplicate_claims(self, tool):
        """Test duplicate claim filtering."""
        claims = [
            {"text": "The Earth is round", "confidence": 0.9},
            {"text": "The Earth is round", "confidence": 0.8},
            {"text": "The Sun is hot", "confidence": 0.95},
        ]
        filtered_claims = tool._filter_duplicate_claims(claims)
        assert len(filtered_claims) == 2
        assert filtered_claims[0]["confidence"] == 0.9

    def test_rank_claims_by_confidence(self, tool):
        """Test claim ranking by confidence."""
        claims = [
            {"text": "Claim A", "confidence": 0.7},
            {"text": "Claim B", "confidence": 0.9},
            {"text": "Claim C", "confidence": 0.6},
        ]
        ranked_claims = tool._rank_claims_by_confidence(claims)
        assert ranked_claims[0]["confidence"] == 0.9
        assert ranked_claims[1]["confidence"] == 0.7
        assert ranked_claims[2]["confidence"] == 0.6
