"""Tests for claim_extractor_tool."""

from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.tools.claim_extractor_tool import (
    ClaimExtractorTool,
)


@pytest.fixture
def claim_extractor_tool():
    """Create a ClaimExtractorTool instance for testing."""
    return ClaimExtractorTool()


def test_claim_extractor_tool_empty_text(claim_extractor_tool):
    """Test claim extractor with empty text."""
    result = claim_extractor_tool._run("")

    assert result["status"] == "success"
    assert result["claims"] == []


def test_claim_extractor_tool_whitespace_only(claim_extractor_tool):
    """Test claim extractor with whitespace-only text."""
    result = claim_extractor_tool._run("   \n\t  ")

    assert result["status"] == "success"
    assert result["claims"] == []


def test_claim_extractor_tool_none_input(claim_extractor_tool):
    """Test claim extractor with None input."""
    result = claim_extractor_tool._run(None)

    assert result["status"] == "success"
    assert result["claims"] == []


@patch("ultimate_discord_intelligence_bot.tools.claim_extractor_tool.extract")
def test_claim_extractor_tool_successful_extraction(mock_extract, claim_extractor_tool):
    """Test successful claim extraction."""
    # Mock the KG extract function
    mock_entities = [Mock(text="Entity1"), Mock(text="Entity2")]
    mock_claims = [
        Mock(text="The Earth is round"),
        Mock(text="Water boils at 100°C"),
        Mock(text="AI"),  # Short claim that should be filtered
    ]
    mock_extract.return_value = (mock_entities, mock_claims)

    text = "The Earth is round and water boils at 100 degrees Celsius."
    result = claim_extractor_tool._run(text)

    assert result["status"] == "success"
    assert "claims" in result
    assert len(result["claims"]) == 2  # Should filter out the short "AI" claim
    assert "The Earth is round" in result["claims"]
    assert "Water boils at 100°C" in result["claims"]
    assert "AI" not in result["claims"]  # Filtered due to length

    # Verify extract was called with stripped text
    mock_extract.assert_called_once_with(text)


@patch("ultimate_discord_intelligence_bot.tools.claim_extractor_tool.extract")
def test_claim_extractor_tool_filters_short_claims(mock_extract, claim_extractor_tool):
    """Test that short claims are filtered out."""
    mock_claims = [
        Mock(text="This is a proper length claim that should be included"),
        Mock(text="Hi"),  # Too short
        Mock(text="   No  "),  # Too short after strip
        Mock(text=""),  # Empty
        Mock(text="Another valid claim for testing purposes"),
    ]
    mock_extract.return_value = ([], mock_claims)

    result = claim_extractor_tool._run("Some test text")

    assert result["status"] == "success"
    assert len(result["claims"]) == 2  # Only the two long claims
    assert "This is a proper length claim that should be included" in result["claims"]
    assert "Another valid claim for testing purposes" in result["claims"]


@patch("ultimate_discord_intelligence_bot.tools.claim_extractor_tool.extract")
def test_claim_extractor_tool_handles_extract_exception(mock_extract, claim_extractor_tool):
    """Test handling of exceptions from the extract function."""
    mock_extract.side_effect = Exception("KG extraction failed")

    result = claim_extractor_tool._run("Some text that causes extraction to fail")

    assert result["status"] == "error"
    assert "error" in result
    assert "KG extraction failed" in result["error"]


@patch("ultimate_discord_intelligence_bot.tools.claim_extractor_tool.extract")
def test_claim_extractor_tool_handles_extract_returning_none(mock_extract, claim_extractor_tool):
    """Test handling when extract returns None or invalid data."""
    mock_extract.return_value = None

    result = claim_extractor_tool._run("Some text")

    assert result["status"] == "error"
    assert "error" in result


@patch("ultimate_discord_intelligence_bot.tools.claim_extractor_tool.extract")
def test_claim_extractor_tool_real_world_example(mock_extract, claim_extractor_tool):
    """Test with a realistic example text."""
    mock_claims = [
        Mock(text="Python is a programming language"),
        Mock(text="Python was created by Guido van Rossum"),
        Mock(text="Python is used for data science"),
        Mock(text="pandas is a Python library"),
    ]
    mock_extract.return_value = ([], mock_claims)

    text = """
    Python is a popular programming language that was created by Guido van Rossum.
    It's widely used for data science, and pandas is one of its most popular libraries.
    """

    result = claim_extractor_tool._run(text)

    assert result["status"] == "success"
    assert len(result["claims"]) == 4
    assert all(
        claim in result["claims"]
        for claim in [
            "Python is a programming language",
            "Python was created by Guido van Rossum",
            "Python is used for data science",
            "pandas is a Python library",
        ]
    )


@patch("ultimate_discord_intelligence_bot.tools.claim_extractor_tool.extract")
def test_claim_extractor_tool_deduplicates_claims(mock_extract, claim_extractor_tool):
    """Test that duplicate claims are handled appropriately."""
    mock_claims = [
        Mock(text="The sky is blue"),
        Mock(text="The sky is blue"),  # Duplicate
        Mock(text="Water is wet"),
        Mock(text="The sky is blue"),  # Another duplicate
    ]
    mock_extract.return_value = ([], mock_claims)

    result = claim_extractor_tool._run("The sky is blue and water is wet.")

    assert result["status"] == "success"
    # UPDATED: Our enhanced version deduplicates claims (improvement over original behavior)
    # Should only have 2 unique claims, not 4 with duplicates
    assert len(result["claims"]) == 2  # Duplicates removed
    assert "The sky is blue" in result["claims"]
    assert "Water is wet" in result["claims"]


def test_claim_extractor_tool_properties():
    """Test that the tool has the correct properties."""
    tool = ClaimExtractorTool()

    assert tool.name == "Claim Extractor Tool"
    # The description property in CrewAI tools includes formatting
    assert "Extract potential factual claims from text using linguistic patterns." in tool.description

    # Test that it's a proper CrewAI tool
    assert hasattr(tool, "_run")
    assert callable(tool._run)


@patch("ultimate_discord_intelligence_bot.tools.claim_extractor_tool.extract")
def test_claim_extractor_tool_strips_whitespace_from_claims(mock_extract, claim_extractor_tool):
    """Test that whitespace is properly stripped from extracted claims."""
    mock_claims = [
        Mock(text="  Claim with leading spaces"),
        Mock(text="Claim with trailing spaces  "),
        Mock(text="  Claim with both  "),
        Mock(text="\tClaim with tabs\n"),
    ]
    mock_extract.return_value = ([], mock_claims)

    result = claim_extractor_tool._run("Test text")

    assert result["status"] == "success"
    expected_claims = [
        "Claim with leading spaces",
        "Claim with trailing spaces",
        "Claim with both",
        "Claim with tabs",
    ]

    for expected in expected_claims:
        assert expected in result["claims"]

    # Ensure no claims have leading/trailing whitespace
    for claim in result["claims"]:
        assert claim == claim.strip()


@patch("ultimate_discord_intelligence_bot.tools.claim_extractor_tool.extract")
def test_claim_extractor_tool_handles_unicode_text(mock_extract, claim_extractor_tool):
    """Test handling of Unicode text."""
    mock_claims = [
        Mock(text="The café serves good coffee"),
        Mock(text="Temperature is 25°C"),
        Mock(text="The résumé was impressive"),
    ]
    mock_extract.return_value = ([], mock_claims)

    unicode_text = "The café serves good coffee at 25°C. The résumé was impressive."
    result = claim_extractor_tool._run(unicode_text)

    assert result["status"] == "success"
    assert len(result["claims"]) == 3
    assert "The café serves good coffee" in result["claims"]
    assert "Temperature is 25°C" in result["claims"]
    assert "The résumé was impressive" in result["claims"]
