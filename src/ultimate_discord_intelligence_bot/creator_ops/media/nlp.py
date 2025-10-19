"""
NLP pipeline for content analysis and processing.

This module provides comprehensive NLP capabilities including topic segmentation,
keyphrase extraction, claim detection, sentiment analysis, and content safety scoring.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import torch
from transformers import (
    pipeline,
)

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.media.alignment import AlignedSegment, AlignedTranscript
from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


@dataclass
class TopicSegment:
    """Topic segment with boundaries and metadata."""

    start_time: float
    end_time: float
    topic: str
    confidence: float
    keywords: list[str]
    segment_indices: list[int]


@dataclass
class Keyphrase:
    """Extracted keyphrase with metadata."""

    text: str
    score: float
    start_time: float | None = None
    end_time: float | None = None
    speaker: str | None = None


@dataclass
class Entity:
    """Named entity with metadata."""

    text: str
    label: str
    confidence: float
    start_time: float | None = None
    end_time: float | None = None
    speaker: str | None = None


@dataclass
class Claim:
    """Fact-checkable claim with metadata."""

    text: str
    confidence: float
    start_time: float
    end_time: float
    speaker: str | None = None
    claim_type: str | None = None
    verifiability: str | None = None


@dataclass
class SentimentAnalysis:
    """Sentiment analysis result."""

    label: str
    score: float
    start_time: float
    end_time: float
    speaker: str | None = None


@dataclass
class ContentSafety:
    """Content safety analysis result."""

    toxicity_score: float
    brand_suitability_score: float  # 1-5 scale
    controversy_flags: list[str]
    risk_level: str  # low, medium, high
    start_time: float
    end_time: float
    speaker: str | None = None


@dataclass
class NLPResult:
    """Complete NLP analysis result."""

    topic_segments: list[TopicSegment]
    keyphrases: list[Keyphrase]
    entities: list[Entity]
    claims: list[Claim]
    sentiment_analysis: list[SentimentAnalysis]
    content_safety: list[ContentSafety]
    processing_time: float
    model_versions: dict[str, str]
    created_at: datetime


class NLPPipeline:
    """
    Comprehensive NLP pipeline for content analysis.

    Features:
    - Topic segmentation with boundary detection
    - Keyphrase and entity extraction
    - Claim detection and verifiability assessment
    - Sentiment analysis per segment
    - Toxicity and brand suitability scoring
    - Controversy and risk flag detection
    """

    def __init__(
        self,
        config: CreatorOpsConfig | None = None,
        device: str | None = None,
    ) -> None:
        """Initialize NLP pipeline."""
        self.config = config or CreatorOpsConfig()
        self.device = device or self._get_optimal_device()

        # Initialize models
        self.sentiment_pipeline = None
        self.toxicity_pipeline = None
        self.ner_pipeline = None
        self.topic_model = None

        self._initialize_models()

    def _get_optimal_device(self) -> str:
        """Get optimal device for NLP processing."""
        if self.config.use_gpu and torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _initialize_models(self) -> None:
        """Initialize NLP models."""
        try:
            # Sentiment analysis
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.device == "cuda" else -1,
            )

            # Toxicity detection
            self.toxicity_pipeline = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                device=0 if self.device == "cuda" else -1,
            )

            # Named entity recognition
            self.ner_pipeline = pipeline(
                "ner",
                model="dbmdz/bert-large-cased-finetuned-conll03-english",
                device=0 if self.device == "cuda" else -1,
            )

            logger.info(f"NLP models loaded on {self.device}")

        except Exception as e:
            logger.error(f"Failed to initialize NLP models: {str(e)}")
            raise

    def analyze_transcript(
        self,
        aligned_transcript: AlignedTranscript,
        analysis_options: dict[str, bool] | None = None,
    ) -> StepResult:
        """
        Perform comprehensive NLP analysis on aligned transcript.

        Args:
            aligned_transcript: Aligned transcript to analyze
            analysis_options: Analysis options to enable/disable

        Returns:
            StepResult with NLPResult
        """
        start_time = datetime.utcnow()

        try:
            # Default analysis options
            options = analysis_options or {
                "topic_segmentation": True,
                "keyphrase_extraction": True,
                "entity_extraction": True,
                "claim_detection": True,
                "sentiment_analysis": True,
                "content_safety": True,
            }

            # Perform analysis
            topic_segments = []
            if options.get("topic_segmentation", False):
                topic_segments = self._segment_topics(aligned_transcript.segments)

            keyphrases = []
            if options.get("keyphrase_extraction", False):
                keyphrases = self._extract_keyphrases(aligned_transcript.segments)

            entities = []
            if options.get("entity_extraction", False):
                entities = self._extract_entities(aligned_transcript.segments)

            claims = []
            if options.get("claim_detection", False):
                claims = self._detect_claims(aligned_transcript.segments)

            sentiment_analysis = []
            if options.get("sentiment_analysis", False):
                sentiment_analysis = self._analyze_sentiment(aligned_transcript.segments)

            content_safety = []
            if options.get("content_safety", False):
                content_safety = self._analyze_content_safety(aligned_transcript.segments)

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Create result
            result = NLPResult(
                topic_segments=topic_segments,
                keyphrases=keyphrases,
                entities=entities,
                claims=claims,
                sentiment_analysis=sentiment_analysis,
                content_safety=content_safety,
                processing_time=processing_time,
                model_versions={
                    "sentiment": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                    "toxicity": "unitary/toxic-bert",
                    "ner": "dbmdz/bert-large-cased-finetuned-conll03-english",
                },
                created_at=start_time,
            )

            return StepResult.ok(data=result)

        except Exception as e:
            logger.error(f"NLP analysis failed: {str(e)}")
            return StepResult.fail(f"NLP analysis failed: {str(e)}")

    def _segment_topics(self, segments: list[AlignedSegment]) -> list[TopicSegment]:
        """Segment transcript into topics."""
        topic_segments = []

        # Simple topic segmentation based on speaker changes and time gaps
        current_topic_start = 0
        current_topic = "Introduction"
        topic_keywords = []

        for i, segment in enumerate(segments):
            # Check for topic boundary conditions
            is_topic_boundary = False

            # Speaker change
            if i > 0 and segment.speaker != segments[i - 1].speaker:
                is_topic_boundary = True

            # Time gap > 5 seconds
            if i > 0 and segment.start_time - segments[i - 1].end_time > 5.0:
                is_topic_boundary = True

            # Long segment (> 2 minutes)
            if segment.end_time - segment.start_time > 120.0:
                is_topic_boundary = True

            if is_topic_boundary and i > current_topic_start:
                # Create topic segment
                topic_segment = TopicSegment(
                    start_time=segments[current_topic_start].start_time,
                    end_time=segments[i - 1].end_time,
                    topic=current_topic,
                    confidence=0.8,  # Placeholder
                    keywords=topic_keywords,
                    segment_indices=list(range(current_topic_start, i)),
                )
                topic_segments.append(topic_segment)

                # Start new topic
                current_topic_start = i
                current_topic = f"Topic {len(topic_segments) + 1}"
                topic_keywords = []

            # Extract keywords from segment
            words = segment.text.lower().split()
            topic_keywords.extend([w for w in words if len(w) > 3])

        # Add final topic segment
        if current_topic_start < len(segments):
            topic_segment = TopicSegment(
                start_time=segments[current_topic_start].start_time,
                end_time=segments[-1].end_time,
                topic=current_topic,
                confidence=0.8,
                keywords=topic_keywords,
                segment_indices=list(range(current_topic_start, len(segments))),
            )
            topic_segments.append(topic_segment)

        return topic_segments

    def _extract_keyphrases(self, segments: list[AlignedSegment]) -> list[Keyphrase]:
        """Extract keyphrases from segments."""
        keyphrases = []

        # Simple TF-IDF based keyphrase extraction
        word_freq = {}
        total_words = 0

        # Count word frequencies
        for segment in segments:
            words = segment.text.lower().split()
            for word in words:
                if len(word) > 3:  # Filter short words
                    word_freq[word] = word_freq.get(word, 0) + 1
                    total_words += 1

        # Calculate TF-IDF scores (simplified)
        for word, freq in word_freq.items():
            if freq > 2:  # Only include words that appear multiple times
                score = freq / total_words

                # Find segments containing this word
                for segment in segments:
                    if word in segment.text.lower():
                        keyphrase = Keyphrase(
                            text=word,
                            score=score,
                            start_time=segment.start_time,
                            end_time=segment.end_time,
                            speaker=segment.speaker,
                        )
                        keyphrases.append(keyphrase)
                        break  # Only add once

        # Sort by score and return top keyphrases
        keyphrases.sort(key=lambda x: x.score, reverse=True)
        return keyphrases[:50]  # Top 50 keyphrases

    def _extract_entities(self, segments: list[AlignedSegment]) -> list[Entity]:
        """Extract named entities from segments."""
        entities = []

        for segment in segments:
            if len(segment.text.strip()) < 10:  # Skip very short segments
                continue

            try:
                # Run NER
                ner_results = self.ner_pipeline(segment.text)

                for entity in ner_results:
                    if entity["score"] > 0.5:  # Confidence threshold
                        entity_obj = Entity(
                            text=entity["word"],
                            label=entity["entity"],
                            confidence=entity["score"],
                            start_time=segment.start_time,
                            end_time=segment.end_time,
                            speaker=segment.speaker,
                        )
                        entities.append(entity_obj)

            except Exception as e:
                logger.warning(f"NER failed for segment: {str(e)}")
                continue

        return entities

    def _detect_claims(self, segments: list[AlignedSegment]) -> list[Claim]:
        """Detect fact-checkable claims in segments."""
        claims = []

        # Simple claim detection based on keywords and patterns
        claim_indicators = [
            "according to",
            "studies show",
            "research indicates",
            "it's a fact that",
            "the truth is",
            "scientists say",
            "experts believe",
            "data shows",
            "statistics prove",
        ]

        for segment in segments:
            text_lower = segment.text.lower()

            for indicator in claim_indicators:
                if indicator in text_lower:
                    # Simple verifiability assessment
                    verifiability = "medium"
                    if any(word in text_lower for word in ["study", "research", "data", "statistics"]):
                        verifiability = "high"
                    elif any(word in text_lower for word in ["believe", "think", "opinion"]):
                        verifiability = "low"

                    claim = Claim(
                        text=segment.text,
                        confidence=0.7,  # Placeholder
                        start_time=segment.start_time,
                        end_time=segment.end_time,
                        speaker=segment.speaker,
                        claim_type="factual",
                        verifiability=verifiability,
                    )
                    claims.append(claim)
                    break  # Only one claim per segment

        return claims

    def _analyze_sentiment(self, segments: list[AlignedSegment]) -> list[SentimentAnalysis]:
        """Analyze sentiment for each segment."""
        sentiment_results = []

        for segment in segments:
            if len(segment.text.strip()) < 5:  # Skip very short segments
                continue

            try:
                # Run sentiment analysis
                sentiment_result = self.sentiment_pipeline(segment.text)

                # Map to standard labels
                label_mapping = {
                    "LABEL_0": "negative",
                    "LABEL_1": "neutral",
                    "LABEL_2": "positive",
                }

                sentiment = SentimentAnalysis(
                    label=label_mapping.get(sentiment_result[0]["label"], "neutral"),
                    score=sentiment_result[0]["score"],
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    speaker=segment.speaker,
                )
                sentiment_results.append(sentiment)

            except Exception as e:
                logger.warning(f"Sentiment analysis failed for segment: {str(e)}")
                continue

        return sentiment_results

    def _analyze_content_safety(self, segments: list[AlignedSegment]) -> list[ContentSafety]:
        """Analyze content safety and brand suitability."""
        safety_results = []

        for segment in segments:
            if len(segment.text.strip()) < 5:  # Skip very short segments
                continue

            try:
                # Run toxicity detection
                toxicity_result = self.toxicity_pipeline(segment.text)

                # Calculate toxicity score
                toxicity_score = 0.0
                for result in toxicity_result:
                    if "toxic" in result["label"].lower():
                        toxicity_score = max(toxicity_score, result["score"])

                # Calculate brand suitability score (1-5, higher is better)
                brand_suitability_score = 5.0 - (toxicity_score * 4.0)
                brand_suitability_score = max(1.0, min(5.0, brand_suitability_score))

                # Detect controversy flags
                controversy_flags = []
                text_lower = segment.text.lower()

                controversial_topics = [
                    "politics",
                    "religion",
                    "race",
                    "gender",
                    "sexuality",
                    "conspiracy",
                    "fake news",
                    "misinformation",
                ]

                for topic in controversial_topics:
                    if topic in text_lower:
                        controversy_flags.append(topic)

                # Determine risk level
                risk_level = "low"
                if toxicity_score > 0.7 or len(controversy_flags) > 2:
                    risk_level = "high"
                elif toxicity_score > 0.3 or len(controversy_flags) > 0:
                    risk_level = "medium"

                safety = ContentSafety(
                    toxicity_score=toxicity_score,
                    brand_suitability_score=brand_suitability_score,
                    controversy_flags=controversy_flags,
                    risk_level=risk_level,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    speaker=segment.speaker,
                )
                safety_results.append(safety)

            except Exception as e:
                logger.warning(f"Content safety analysis failed for segment: {str(e)}")
                continue

        return safety_results

    def get_model_info(self) -> dict[str, Any]:
        """Get model information."""
        return {
            "device": self.device,
            "has_gpu": torch.cuda.is_available(),
            "models_loaded": {
                "sentiment": self.sentiment_pipeline is not None,
                "toxicity": self.toxicity_pipeline is not None,
                "ner": self.ner_pipeline is not None,
            },
        }

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.sentiment_pipeline:
            del self.sentiment_pipeline
            self.sentiment_pipeline = None

        if self.toxicity_pipeline:
            del self.toxicity_pipeline
            self.toxicity_pipeline = None

        if self.ner_pipeline:
            del self.ner_pipeline
            self.ner_pipeline = None

        # Clear CUDA cache if using GPU
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
