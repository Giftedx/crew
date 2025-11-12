"""Tests for FactCheckTool."""

from unittest.mock import patch

import pytest

from domains.intelligence.verification.fact_check_tool import FactCheckTool
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestFactCheckTool:
    """Test cases for FactCheckTool."""

    @pytest.fixture
    def tool(self):
        """Create FactCheckTool instance."""
        return FactCheckTool()

    def test_tool_initialization(self, tool):
        """Test tool initializes correctly."""
        assert tool.name == "fact_check"
        assert "fact" in tool.description.lower()

    def test_run_with_valid_claim(self, tool):
        """Test fact checking with valid claim."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verify.return_value = StepResult.ok(
                data={
                    "claim": "The Earth is round",
                    "verification_status": "verified",
                    "confidence_score": 0.95,
                    "sources": ["NASA", "Scientific consensus"],
                }
            )
            result = tool._run("The Earth is round")
            assert result.success
            assert "verification_status" in result.data
            mock_verify.assert_called_once()

    def test_run_with_empty_claim(self, tool):
        """Test fact checking with empty claim."""
        result = tool._run("")
        assert not result.success
        assert "empty" in result.error.lower()

    def test_run_with_short_claim(self, tool):
        """Test fact checking with insufficient claim."""
        result = tool._run("Hi")
        assert not result.success
        assert "insufficient" in result.error.lower()

    def test_verify_claim_success(self, tool):
        """Test successful claim verification."""
        claim = "The Earth orbits the Sun."
        with patch.object(tool, "_search_evidence") as mock_search:
            with patch.object(tool, "_analyze_evidence") as mock_analyze:
                with patch.object(tool, "_determine_verification_status") as mock_status:
                    mock_search.return_value = ["NASA data", "Astronomical observations"]
                    mock_analyze.return_value = {"reliability": 0.95, "consensus": 0.98}
                    mock_status.return_value = "verified"
                    result = tool._verify_claim(claim)
                    assert result.success
                    assert result.data["verification_status"] == "verified"
                    assert "confidence_score" in result.data

    def test_search_evidence(self, tool):
        """Test evidence search functionality."""
        claim = "Climate change is real"
        with patch.object(tool, "_query_knowledge_base") as mock_query:
            mock_query.return_value = ["IPCC reports", "Scientific studies"]
            evidence = tool._search_evidence(claim)
            assert isinstance(evidence, list)
            assert len(evidence) > 0
            mock_query.assert_called_once_with(claim)

    def test_analyze_evidence(self, tool):
        """Test evidence analysis."""
        evidence = ["Peer-reviewed study", "Expert testimony", "Data analysis"]
        analysis = tool._analyze_evidence(evidence)
        assert "reliability" in analysis
        assert "consensus" in analysis
        assert 0 <= analysis["reliability"] <= 1
        assert 0 <= analysis["consensus"] <= 1

    def test_determine_verification_status(self, tool):
        """Test verification status determination."""
        high_reliability = {"reliability": 0.95, "consensus": 0.98}
        status1 = tool._determine_verification_status(high_reliability)
        assert status1 in ["verified", "highly_verified"]
        low_reliability = {"reliability": 0.3, "consensus": 0.4}
        status2 = tool._determine_verification_status(low_reliability)
        assert status2 in ["unverified", "disputed", "insufficient_evidence"]

    def test_handle_verification_error(self, tool):
        """Test error handling in claim verification."""
        with patch.object(tool, "_search_evidence") as mock_search:
            mock_search.side_effect = Exception("Search failed")
            result = tool._verify_claim("test claim")
            assert not result.success
            assert "failed" in result.error.lower()

    def test_validate_input_claim(self, tool):
        """Test input claim validation."""
        assert tool._validate_input_claim("This is a valid claim for fact checking.") is True
        assert tool._validate_input_claim("") is False
        assert tool._validate_input_claim("Hi") is False
        assert tool._validate_input_claim(None) is False

    def test_calculate_confidence_score(self, tool):
        """Test confidence score calculation."""
        evidence_analysis = {"reliability": 0.9, "consensus": 0.85}
        confidence = tool._calculate_confidence_score(evidence_analysis)
        assert 0 <= confidence <= 1
        assert confidence > 0.8

    def test_format_verification_result(self, tool):
        """Test verification result formatting."""
        claim = "Test claim"
        status = "verified"
        confidence = 0.95
        sources = ["Source 1", "Source 2"]
        result = tool._format_verification_result(claim, status, confidence, sources)
        assert result["claim"] == claim
        assert result["verification_status"] == status
        assert result["confidence_score"] == confidence
        assert result["sources"] == sources
