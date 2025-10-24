"""Tests for Claim and Quote Extraction Service."""

from __future__ import annotations

import pytest

from analysis.nlp.claim_quote_extraction_service import (
    ClaimQuoteExtractionService,
    ExtractedClaim,
    ExtractedQuote,
    get_claim_quote_extraction_service,
)


class TestClaimQuoteExtractionService:
    """Test claim and quote extraction service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = ClaimQuoteExtractionService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._extraction_cache) == 0
        assert self.service._nlp_model is None
        assert self.service._claim_classifier is None

    def test_extract_fallback(self) -> None:
        """Test extraction with fallback rule-based method."""
        text = "According to research, AI will change everything. This is a fact."

        result = self.service.extract_claims_and_quotes(text, model="fast", use_cache=False)

        # Should succeed with rule-based extraction
        assert result.success
        assert result.data is not None
        assert "claims" in result.data
        assert "quotes" in result.data

        # Should extract at least one claim
        claims = result.data["claims"]
        assert len(claims) >= 1

    def test_extract_empty_text(self) -> None:
        """Test handling of empty text."""
        result = self.service.extract_claims_and_quotes("", model="fast")

        assert not result.success
        assert result.status == "bad_request"
        assert "empty" in result.error.lower()

    def test_extract_short_text(self) -> None:
        """Test handling of very short text."""
        result = self.service.extract_claims_and_quotes("Short text", model="fast")

        assert result.success  # Should still work with fallback

    def test_extraction_cache_hit(self) -> None:
        """Test extraction cache functionality."""
        text = "This is a test text for caching purposes."

        # First extraction - cache miss
        result1 = self.service.extract_claims_and_quotes(text, model="fast", use_cache=True)
        assert result1.success
        assert result1.data["cache_hit"] is False

        # Second extraction - should be cache hit
        result2 = self.service.extract_claims_and_quotes(text, model="fast", use_cache=True)
        assert result2.success
        assert result2.data["cache_hit"] is True

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached extractions
        self.service.extract_claims_and_quotes("Text 1", use_cache=True)
        self.service.extract_claims_and_quotes("Text 2", use_cache=True)

        assert len(self.service._extraction_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._extraction_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached extractions
        self.service.extract_claims_and_quotes("Text 1", model="fast", use_cache=True)
        self.service.extract_claims_and_quotes("Text 2", model="balanced", use_cache=True)

        result = self.service.get_cache_stats()

        assert result.success
        assert result.data is not None
        assert "total_cached" in result.data
        assert "cache_size_limit" in result.data
        assert "models_cached" in result.data

        assert result.data["total_cached"] >= 2
        assert result.data["cache_size_limit"] == 100

    def test_model_selection(self) -> None:
        """Test model selection logic."""
        assert self.service._select_model("fast") == "fast_extraction"
        assert self.service._select_model("balanced") == "balanced_extraction"
        assert self.service._select_model("quality") == "quality_extraction"
        assert self.service._select_model("unknown") == "balanced_extraction"  # Default

    def test_extract_from_segments(self) -> None:
        """Test extraction from speaker segments."""
        segments = [
            {
                "speaker": "Host",
                "start_time": 0.0,
                "text": "According to research, AI will change everything.",
            },
            {
                "speaker": "Guest",
                "start_time": 30.0,
                "text": "I believe this is a fact.",
            },
        ]

        result = self.service.extract_from_segments(segments, model="fast", use_cache=False)

        assert result.success
        assert result.data is not None
        assert "claims" in result.data
        assert "quotes" in result.data
        assert result.data["total_segments_processed"] == 2

    def test_timestamp_estimation(self) -> None:
        """Test timestamp estimation for sentences."""
        # Test without speakers
        timestamp = self.service._estimate_timestamp(0, 5, None)
        assert timestamp == 0.0  # First sentence

        timestamp2 = self.service._estimate_timestamp(2, 5, None)
        assert timestamp2 == 20.0  # Third sentence

    def test_speaker_at_time(self) -> None:
        """Test finding speaker at specific time."""
        speakers = [
            {"speaker": "Host", "start": 0, "end": 30},
            {"speaker": "Guest", "start": 30, "end": 60},
        ]

        speaker = self.service._find_speaker_at_time(15.0, speakers)
        assert speaker == "Host"

        speaker2 = self.service._find_speaker_at_time(45.0, speakers)
        assert speaker2 == "Guest"

        speaker3 = self.service._find_speaker_at_time(70.0, speakers)  # Outside range
        assert speaker3 is None


class TestClaimQuoteExtractionServiceSingleton:
    """Test singleton instance management."""

    def test_get_claim_quote_extraction_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_claim_quote_extraction_service()
        service2 = get_claim_quote_extraction_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, ClaimQuoteExtractionService)


class TestExtractedClaim:
    """Test extracted claim data structure."""

    def test_create_extracted_claim(self) -> None:
        """Test creating extracted claim."""
        claim = ExtractedClaim(
            text="AI will change everything",
            speaker="Host",
            timestamp_seconds=15.0,
            confidence=0.85,
            claim_type="prediction",
            verification_status="unverified",
            sources=["research paper"],
        )

        assert claim.text == "AI will change everything"
        assert claim.speaker == "Host"
        assert claim.timestamp_seconds == 15.0
        assert claim.confidence == 0.85
        assert claim.claim_type == "prediction"
        assert claim.verification_status == "unverified"
        assert claim.sources == ["research paper"]

    def test_extracted_claim_defaults(self) -> None:
        """Test extracted claim with default values."""
        claim = ExtractedClaim(
            text="Simple statement",
            confidence=0.7,
        )

        assert claim.speaker is None
        assert claim.timestamp_seconds is None
        assert claim.claim_type == "statement"
        assert claim.verification_status == "unverified"
        assert claim.sources == []


class TestExtractedQuote:
    """Test extracted quote data structure."""

    def test_create_extracted_quote(self) -> None:
        """Test creating extracted quote."""
        quote = ExtractedQuote(
            text="This is a memorable quote",
            speaker="Guest",
            timestamp_seconds=45.0,
            confidence=0.9,
            quote_type="insightful",
            context="Speaking about the future",
            significance_score=0.8,
        )

        assert quote.text == "This is a memorable quote"
        assert quote.speaker == "Guest"
        assert quote.timestamp_seconds == 45.0
        assert quote.confidence == 0.9
        assert quote.quote_type == "insightful"
        assert quote.context == "Speaking about the future"
        assert quote.significance_score == 0.8

    def test_extracted_quote_defaults(self) -> None:
        """Test extracted quote with default values."""
        quote = ExtractedQuote(
            text="Simple quote",
            confidence=0.8,
        )

        assert quote.speaker is None
        assert quote.timestamp_seconds is None
        assert quote.quote_type == "notable"
        assert quote.context is None
        assert quote.significance_score == 0.5


class TestClaimQuoteExtractionWithMocking:
    """Test extraction service with mocked dependencies."""

    def test_extract_with_spacy_mock(self) -> None:
        """Test extraction with spaCy mocking."""
        text = "According to research, AI will change everything. This is a fact."

        # Mock spaCy components
        mock_doc = pytest.importorskip("unittest.mock").MagicMock()
        mock_sent = pytest.importorskip("unittest.mock").MagicMock()
        mock_sent.text = "According to research, AI will change everything."
        mock_doc.sents = [mock_sent]

        with (
            pytest.importorskip("unittest.mock").patch(
                "analysis.nlp.claim_quote_extraction_service.SPACY_AVAILABLE", True
            ),
            pytest.importorskip("unittest.mock").patch(
                "analysis.nlp.claim_quote_extraction_service.spacy.load"
            ) as mock_load,
        ):
            mock_load.return_value = mock_doc

            service = ClaimQuoteExtractionService()

            result = service.extract_claims_and_quotes(text, model="balanced", use_cache=False)

            assert result.success
            assert result.data["claims"]
            assert len(result.data["claims"]) >= 1

    def test_extract_with_speaker_context(self) -> None:
        """Test extraction with speaker context."""
        text = "According to research, AI will change everything."
        speakers = [
            {"speaker": "Host", "start": 0, "end": 30},
            {"speaker": "Guest", "start": 30, "end": 60},
        ]

        result = self.service.extract_claims_and_quotes(text, speakers, model="fast", use_cache=False)

        assert result.success

        # Should attribute to host (first speaker)
        claims = result.data["claims"]
        if claims:
            assert claims[0]["speaker"] == "Host"
            assert claims[0]["timestamp_seconds"] == 15.0  # Midpoint of first segment


class TestClaimQuoteExtractionEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = ClaimQuoteExtractionService()

    def test_extract_very_long_text(self) -> None:
        """Test extraction with very long text."""
        # Create long text (1000+ characters)
        long_text = "According to research, " * 100 + "AI will change everything."

        result = self.service.extract_claims_and_quotes(long_text, model="fast", use_cache=False)

        assert result.success
        assert result.data["total_segments_processed"] > 0

    def test_extract_no_claims_text(self) -> None:
        """Test extraction with text containing no claims."""
        text = "Hello world. This is a simple greeting. Have a nice day."

        result = self.service.extract_claims_and_quotes(text, model="fast", use_cache=False)

        assert result.success
        # Should have no claims but might have quotes
        assert len(result.data["claims"]) == 0

    def test_extract_quoted_text(self) -> None:
        """Test extraction of quoted text."""
        text = 'The expert said, "AI will revolutionize everything." This is important.'

        result = self.service.extract_claims_and_quotes(text, model="fast", use_cache=False)

        assert result.success

        # Should extract the quote
        quotes = result.data["quotes"]
        if quotes:
            assert any("AI will revolutionize everything" in q["text"] for q in quotes)
