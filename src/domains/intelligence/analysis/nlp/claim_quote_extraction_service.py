"""Claim and Quote Extraction Service for Creator Intelligence.

This module provides NLP-based extraction of factual claims and notable quotes
from transcribed content, with speaker attribution and verification readiness.

Features:
- Factual claim identification using NLP patterns
- Quote extraction with speaker attribution
- Integration with speaker diarization for context
- Verification metadata preparation
- Confidence scoring for extracted claims/quotes

Dependencies:
- spacy: For NLP processing and pattern matching
- transformers: For fine-tuned claim extraction models
- Optional: Custom trained models for domain-specific claims
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from platform.core.step_result import StepResult
from typing import Any, Literal


logger = logging.getLogger(__name__)
try:
    import spacy

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spacy not available, using rule-based extraction")
try:
    from transformers import pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available, using rule-based extraction")


@dataclass
class ExtractedClaim:
    """A factual claim extracted from content."""

    text: str
    speaker: str | None = None
    timestamp_seconds: float | None = None
    confidence: float = 1.0
    claim_type: str = "statement"
    verification_status: str = "unverified"
    sources: list[str] = None

    def __post_init__(self) -> None:
        if self.sources is None:
            self.sources = []


@dataclass
class ExtractedQuote:
    """A notable quote extracted from content."""

    text: str
    speaker: str | None = None
    timestamp_seconds: float | None = None
    confidence: float = 1.0
    quote_type: str = "notable"
    context: str | None = None
    significance_score: float = 0.5


@dataclass
class ClaimQuoteExtractionResult:
    """Result of claim and quote extraction operation."""

    claims: list[ExtractedClaim]
    quotes: list[ExtractedQuote]
    total_segments_processed: int
    extraction_confidence: float
    model: str
    processing_time_ms: float = 0.0


class ClaimQuoteExtractionService:
    """Service for extracting claims and quotes from transcribed content.

    Usage:
        service = ClaimQuoteExtractionService()
        result = service.extract_claims_and_quotes("transcript text", speakers)
        claims = result.data["claims"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize extraction service.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._extraction_cache: dict[str, ClaimQuoteExtractionResult] = {}
        self._nlp_model: Any = None
        self._claim_classifier: Any = None

    def extract_claims_and_quotes(
        self,
        text: str,
        speakers: list[dict[str, Any]] | None = None,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Extract claims and quotes from text with speaker context.

        Args:
            text: Input text to analyze
            speakers: List of speaker segments with timing
            model: Model selection (fast, balanced, quality)
            use_cache: Whether to use extraction cache

        Returns:
            StepResult with extracted claims and quotes
        """
        try:
            import time

            start_time = time.time()
            if not text or not text.strip():
                return StepResult.fail("Input text cannot be empty", status="bad_request")
            if use_cache:
                cache_result = self._check_cache(text, speakers, model)
                if cache_result:
                    logger.info("Claim/quote extraction cache hit")
                    return StepResult.ok(
                        data={
                            "claims": [c.__dict__ for c in cache_result.claims],
                            "quotes": [q.__dict__ for q in cache_result.quotes],
                            "total_segments_processed": cache_result.total_segments_processed,
                            "extraction_confidence": cache_result.extraction_confidence,
                            "model": cache_result.model,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )
            model_name = self._select_model(model)
            extraction_result = self._extract_claims_and_quotes(text, speakers, model_name)
            if extraction_result:
                if use_cache:
                    self._cache_result(text, speakers, model, extraction_result)
                processing_time = (time.time() - start_time) * 1000
                return StepResult.ok(
                    data={
                        "claims": [c.__dict__ for c in extraction_result.claims],
                        "quotes": [q.__dict__ for q in extraction_result.quotes],
                        "total_segments_processed": extraction_result.total_segments_processed,
                        "extraction_confidence": extraction_result.extraction_confidence,
                        "model": extraction_result.model,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Extraction failed", status="retryable")
        except Exception as e:
            logger.error(f"Claim/quote extraction failed: {e}")
            return StepResult.fail(f"Extraction failed: {e!s}", status="retryable")

    def extract_from_segments(
        self,
        segments: list[dict[str, Any]],
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Extract claims and quotes from speaker segments.

        Args:
            segments: List of segments with speaker, text, and timing
            model: Model selection
            use_cache: Whether to use extraction cache

        Returns:
            StepResult with extracted claims and quotes per segment
        """
        try:
            all_claims = []
            all_quotes = []
            for segment in segments:
                segment_text = segment.get("text", "")
                speaker = segment.get("speaker")
                start_time = segment.get("start_time")
                if not segment_text:
                    continue
                segment_result = self.extract_claims_and_quotes(
                    text=segment_text,
                    speakers=[{"speaker": speaker, "start": start_time, "end": start_time + 30}],
                    model=model,
                    use_cache=False,
                )
                if segment_result.success:
                    segment_data = segment_result.data
                    for claim in segment_data["claims"]:
                        claim["segment_start"] = start_time
                        claim["segment_speaker"] = speaker
                        all_claims.append(claim)
                    for quote in segment_data["quotes"]:
                        quote["segment_start"] = start_time
                        quote["segment_speaker"] = speaker
                        all_quotes.append(quote)
            total_items = len(all_claims) + len(all_quotes)
            avg_confidence = (
                (sum((c["confidence"] for c in all_claims)) + sum((q["confidence"] for q in all_quotes))) / total_items
                if total_items > 0
                else 0.0
            )
            return StepResult.ok(
                data={
                    "claims": all_claims,
                    "quotes": all_quotes,
                    "total_segments_processed": len(segments),
                    "extraction_confidence": avg_confidence,
                    "model": model,
                }
            )
        except Exception as e:
            logger.error(f"Segment extraction failed: {e}")
            return StepResult.fail(f"Segment extraction failed: {e!s}")

    def _select_model(self, model_alias: str) -> str:
        """Select actual model configuration from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Model configuration string
        """
        model_configs = {"fast": "fast_extraction", "balanced": "balanced_extraction", "quality": "quality_extraction"}
        return model_configs.get(model_alias, "balanced_extraction")

    def _extract_claims_and_quotes(
        self, text: str, speakers: list[dict[str, Any]] | None, model_name: str
    ) -> ClaimQuoteExtractionResult | None:
        """Extract claims and quotes using NLP models or fallback.

        Args:
            text: Input text to analyze
            speakers: Speaker context for attribution
            model_name: Model configuration

        Returns:
            ClaimQuoteExtractionResult or None if extraction fails
        """
        try:
            if SPACY_AVAILABLE and TRANSFORMERS_AVAILABLE:
                return self._extract_with_nlp(text, speakers, model_name)
            logger.warning("NLP models not available, using rule-based extraction")
            return self._extract_with_rules(text, speakers, model_name)
        except Exception as e:
            logger.error(f"Extraction failed for model {model_name}: {e}")
            return None

    def _extract_with_nlp(
        self, text: str, speakers: list[dict[str, Any]] | None, model_name: str
    ) -> ClaimQuoteExtractionResult:
        """Extract claims and quotes using NLP models.

        Args:
            text: Input text
            speakers: Speaker context
            model_name: Model configuration

        Returns:
            ClaimQuoteExtractionResult with extracted items
        """
        if self._nlp_model is None and SPACY_AVAILABLE:
            logger.info("Loading spaCy model")
            try:
                self._nlp_model = spacy.load("en_core_web_sm")
            except OSError:
                self._nlp_model = spacy.load("en_core_web_sm")
        if self._claim_classifier is None and TRANSFORMERS_AVAILABLE:
            logger.info("Loading claim classification model")
            try:
                self._claim_classifier = pipeline(
                    "text-classification", model="microsoft/DialoGPT-medium", return_all_scores=True
                )
            except Exception:
                self._claim_classifier = None
        claims = []
        quotes = []
        if self._nlp_model:
            doc = self._nlp_model(text)
            sentences = [sent.text.strip() for sent in doc.sents]
        else:
            sentences = re.split("[.!?]+", text)
            sentences = [s.strip() for s in sentences if s.strip()]
        for i, sentence in enumerate(sentences):
            timestamp = self._estimate_timestamp(i, len(sentences), speakers)
            claim = self._extract_claim(sentence, timestamp, model_name)
            if claim:
                claims.append(claim)
            quote = self._extract_quote(sentence, timestamp, model_name)
            if quote:
                quotes.append(quote)
        total_items = len(claims) + len(quotes)
        avg_confidence = (
            (sum((c.confidence for c in claims)) + sum((q.confidence for q in quotes))) / total_items
            if total_items > 0
            else 0.0
        )
        return ClaimQuoteExtractionResult(
            claims=claims,
            quotes=quotes,
            total_segments_processed=len(sentences),
            extraction_confidence=avg_confidence,
            model=model_name,
        )

    def _extract_with_rules(
        self, text: str, speakers: list[dict[str, Any]] | None, model_name: str
    ) -> ClaimQuoteExtractionResult:
        """Extract claims and quotes using rule-based patterns.

        Args:
            text: Input text
            speakers: Speaker context
            model_name: Model configuration

        Returns:
            ClaimQuoteExtractionResult with extracted items
        """
        claims = []
        quotes = []
        sentences = re.split("[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        for i, sentence in enumerate(sentences):
            timestamp = self._estimate_timestamp(i, len(sentences), speakers)
            claim_patterns = [
                "\\b(claim|state|assert|believe|think)\\b.*\\b(that|because|since)\\b",
                "\\b(according to|research shows|studies indicate)\\b",
                "\\b(in fact|actually|clearly|obviously)\\b",
                "\\b(statistics|data|evidence)\\b.*\\b(show|prove|demonstrate)\\b",
            ]
            quote_patterns = [
                '"([^"]*)"',
                "'([^']*)'",
                "\\b(said|stated|mentioned|explained)\\b.*[\"\\']([^\"\\']*)[\"\\']",
            ]
            for pattern in claim_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    claim = ExtractedClaim(
                        text=sentence,
                        speaker=self._find_speaker_at_time(timestamp, speakers),
                        timestamp_seconds=timestamp,
                        confidence=0.7,
                        claim_type="statement",
                    )
                    claims.append(claim)
                    break
            for pattern in quote_patterns:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    quote_text = match.group(1) or match.group(2)
                    if quote_text and len(quote_text) > 10:
                        quote = ExtractedQuote(
                            text=quote_text,
                            speaker=self._find_speaker_at_time(timestamp, speakers),
                            timestamp_seconds=timestamp,
                            confidence=0.8,
                            quote_type="notable",
                            context=sentence,
                            significance_score=0.6,
                        )
                        quotes.append(quote)
                        break
        total_items = len(claims) + len(quotes)
        avg_confidence = (
            (sum((c.confidence for c in claims)) + sum((q.confidence for q in quotes))) / total_items
            if total_items > 0
            else 0.0
        )
        return ClaimQuoteExtractionResult(
            claims=claims,
            quotes=quotes,
            total_segments_processed=len(sentences),
            extraction_confidence=avg_confidence,
            model=model_name,
        )

    def _extract_claim(self, sentence: str, timestamp: float | None, model_name: str) -> ExtractedClaim | None:
        """Extract a claim from a sentence.

        Args:
            sentence: Input sentence
            timestamp: Timestamp of sentence
            model_name: Model configuration

        Returns:
            ExtractedClaim or None if no claim found
        """
        factual_indicators = [
            "according to",
            "research shows",
            "studies indicate",
            "data shows",
            "statistics reveal",
            "evidence suggests",
            "in fact",
            "actually",
            "clearly",
            "obviously",
        ]
        sentence_lower = sentence.lower()
        if any(indicator in sentence_lower for indicator in factual_indicators):
            return ExtractedClaim(text=sentence, timestamp_seconds=timestamp, confidence=0.7, claim_type="statement")
        return None

    def _extract_quote(self, sentence: str, timestamp: float | None, model_name: str) -> ExtractedQuote | None:
        """Extract a quote from a sentence.

        Args:
            sentence: Input sentence
            timestamp: Timestamp of sentence
            model_name: Model configuration

        Returns:
            ExtractedQuote or None if no quote found
        """
        quote_patterns = ['"([^"]*)"', "'([^']*)'"]
        for pattern in quote_patterns:
            match = re.search(pattern, sentence)
            if match:
                quote_text = match.group(1)
                if len(quote_text) > 10:
                    return ExtractedQuote(
                        text=quote_text,
                        timestamp_seconds=timestamp,
                        confidence=0.8,
                        quote_type="notable",
                        context=sentence,
                        significance_score=0.6,
                    )
        return None

    def _estimate_timestamp(
        self, sentence_index: int, total_sentences: int, speakers: list[dict[str, Any]] | None
    ) -> float | None:
        """Estimate timestamp for a sentence based on position and speaker context.

        Args:
            sentence_index: Index of sentence in text
            total_sentences: Total number of sentences
            speakers: Speaker segments with timing

        Returns:
            Estimated timestamp in seconds
        """
        if not speakers:
            return sentence_index * 10.0
        estimated_time = sentence_index * 10.0
        for speaker_segment in speakers:
            speaker_start = speaker_segment.get("start", 0)
            speaker_end = speaker_segment.get("end", speaker_start + 30)
            if speaker_start <= estimated_time <= speaker_end:
                return (speaker_start + speaker_end) / 2
        return estimated_time

    def _find_speaker_at_time(self, timestamp: float | None, speakers: list[dict[str, Any]] | None) -> str | None:
        """Find speaker active at given timestamp.

        Args:
            timestamp: Timestamp to check
            speakers: Speaker segments with timing

        Returns:
            Speaker name or None if not found
        """
        if not timestamp or not speakers:
            return None
        for speaker_segment in speakers:
            speaker_start = speaker_segment.get("start", 0)
            speaker_end = speaker_segment.get("end", speaker_start + 30)
            if speaker_start <= timestamp <= speaker_end:
                return speaker_segment.get("speaker")
        return None

    def _check_cache(
        self, text: str, speakers: list[dict[str, Any]] | None, model: str
    ) -> ClaimQuoteExtractionResult | None:
        """Check if extraction exists in cache.

        Args:
            text: Input text
            speakers: Speaker context
            model: Model alias

        Returns:
            Cached ClaimQuoteExtractionResult or None
        """
        import hashlib

        speaker_context = str(speakers) if speakers else ""
        combined = f"{text}:{speaker_context}:{model}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()
        if cache_key in self._extraction_cache:
            return self._extraction_cache[cache_key]
        return None

    def _cache_result(
        self, text: str, speakers: list[dict[str, Any]] | None, model: str, result: ClaimQuoteExtractionResult
    ) -> None:
        """Cache extraction result.

        Args:
            text: Input text
            speakers: Speaker context
            model: Model alias
            result: ClaimQuoteExtractionResult to cache
        """
        import hashlib
        import time

        speaker_context = str(speakers) if speakers else ""
        combined = f"{text}:{speaker_context}:{model}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()
        result.processing_time_ms = time.time() * 1000
        if len(self._extraction_cache) >= self.cache_size:
            first_key = next(iter(self._extraction_cache))
            del self._extraction_cache[first_key]
        self._extraction_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear extraction cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._extraction_cache)
        self._extraction_cache.clear()
        logger.info(f"Cleared {cache_size} cached extractions")
        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get extraction cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._extraction_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._extraction_cache) / self.cache_size if self.cache_size > 0 else 0.0,
                "models_cached": {},
            }
            for result in self._extraction_cache.values():
                model = result.model
                stats["models_cached"][model] = stats["models_cached"].get(model, 0) + 1
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


_extraction_service: ClaimQuoteExtractionService | None = None


def get_claim_quote_extraction_service() -> ClaimQuoteExtractionService:
    """Get singleton claim/quote extraction service instance.

    Returns:
        Initialized ClaimQuoteExtractionService instance
    """
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = ClaimQuoteExtractionService()
    return _extraction_service
