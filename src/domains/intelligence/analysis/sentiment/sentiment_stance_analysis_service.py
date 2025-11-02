"""Sentiment and Stance Analysis Service for Creator Intelligence.

This module provides sentiment analysis, stance detection, and rhetorical device
identification using pre-trained transformers from Hugging Face.

Features:
- Sentiment analysis (positive, negative, neutral)
- Stance detection (agree, disagree, neutral)
- Emotion recognition (joy, anger, fear, sadness, etc.)
- Rhetorical device detection (questions, exclamations, etc.)
- Integration with multimodal understanding pipeline

Dependencies:
- transformers: For pre-trained sentiment and stance models
- torch: For model inference
- Optional: Custom fine-tuned models for domain-specific analysis
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)

# Try to import transformers (optional dependency)
try:
    from transformers import pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None  # type: ignore
    logger.warning("transformers not available, using rule-based sentiment analysis")


@dataclass
class SentimentAnalysis:
    """Sentiment analysis result for a text segment."""

    sentiment: str  # positive, negative, neutral
    confidence: float  # 0.0 to 1.0
    intensity: float  # 0.0 to 1.0 (how strongly the sentiment is expressed)


@dataclass
class EmotionAnalysis:
    """Emotion analysis result for a text segment."""

    primary_emotion: str  # joy, anger, fear, sadness, surprise, disgust, neutral
    confidence: float  # 0.0 to 1.0
    emotion_scores: dict[str, float]  # emotion -> score mapping


@dataclass
class StanceAnalysis:
    """Stance analysis result for a text segment."""

    stance: str  # agree, disagree, neutral, questioning
    confidence: float  # 0.0 to 1.0
    stance_type: str  # explicit, implicit, rhetorical


@dataclass
class RhetoricalAnalysis:
    """Rhetorical device analysis for a text segment."""

    has_question: bool
    has_exclamation: bool
    has_emphasis: bool
    rhetorical_questions: list[str]
    emphasis_words: list[str]


@dataclass
class SentimentStanceAnalysisResult:
    """Result of sentiment and stance analysis operation."""

    sentiment: SentimentAnalysis
    emotion: EmotionAnalysis
    stance: StanceAnalysis
    rhetorical: RhetoricalAnalysis
    text_segment: str
    speaker: str | None = None
    timestamp: float | None = None
    analysis_confidence: float = 1.0


class SentimentStanceAnalysisService:
    """Service for sentiment, stance, and rhetorical analysis.

    Usage:
        service = SentimentStanceAnalysisService()
        result = service.analyze_text("This is amazing content!")
        sentiment = result.data["sentiment"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize sentiment analysis service.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._analysis_cache: dict[str, SentimentStanceAnalysisResult] = {}

        # Load models lazily
        self._sentiment_pipeline: Any = None
        self._emotion_pipeline: Any = None
        self._stance_pipeline: Any = None

    def analyze_text(
        self,
        text: str,
        speaker: str | None = None,
        timestamp: float | None = None,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Analyze text for sentiment, emotion, stance, and rhetorical devices.

        Args:
            text: Input text to analyze
            speaker: Speaker name (optional)
            timestamp: Timestamp of text segment (optional)
            model: Model selection
            use_cache: Whether to use analysis cache

        Returns:
            StepResult with sentiment and stance analysis
        """
        try:
            import time

            start_time = time.time()

            # Validate input
            if not text or not text.strip():
                return StepResult.fail("Input text cannot be empty", status="bad_request")

            # Check cache first
            if use_cache:
                cache_result = self._check_cache(text, speaker, model)
                if cache_result:
                    logger.info("Sentiment analysis cache hit")
                    return StepResult.ok(
                        data={
                            "sentiment": cache_result.sentiment.__dict__,
                            "emotion": cache_result.emotion.__dict__,
                            "stance": cache_result.stance.__dict__,
                            "rhetorical": cache_result.rhetorical.__dict__,
                            "text_segment": cache_result.text_segment,
                            "speaker": cache_result.speaker,
                            "timestamp": cache_result.timestamp,
                            "analysis_confidence": cache_result.analysis_confidence,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )

            # Perform analysis
            model_name = self._select_model(model)
            analysis_result = self._analyze_text(text, speaker, timestamp, model_name)

            if analysis_result:
                # Cache result
                if use_cache:
                    self._cache_result(text, speaker, model, analysis_result)

                processing_time = (time.time() - start_time) * 1000

                return StepResult.ok(
                    data={
                        "sentiment": analysis_result.sentiment.__dict__,
                        "emotion": analysis_result.emotion.__dict__,
                        "stance": analysis_result.stance.__dict__,
                        "rhetorical": analysis_result.rhetorical.__dict__,
                        "text_segment": analysis_result.text_segment,
                        "speaker": analysis_result.speaker,
                        "timestamp": analysis_result.timestamp,
                        "analysis_confidence": analysis_result.analysis_confidence,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Analysis failed", status="retryable")

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return StepResult.fail(f"Analysis failed: {e!s}", status="retryable")

    def analyze_segments(
        self,
        segments: list[dict[str, Any]],
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Analyze multiple text segments for sentiment and stance.

        Args:
            segments: List of segments with text, speaker, and timing
            model: Model selection
            use_cache: Whether to use analysis cache

        Returns:
            StepResult with analysis results for all segments
        """
        try:
            results = []

            for segment in segments:
                segment_text = segment.get("text", "")
                speaker = segment.get("speaker")
                timestamp = segment.get("timestamp")

                if not segment_text:
                    continue

                # Analyze this segment
                segment_result = self.analyze_text(
                    text=segment_text,
                    speaker=speaker,
                    timestamp=timestamp,
                    model=model,
                    use_cache=False,  # Don't cache individual segments
                )

                if segment_result.success:
                    segment_data = segment_result.data

                    # Add segment context
                    segment_data["segment_index"] = len(results)
                    segment_data["original_text"] = segment_text

                    results.append(segment_data)

            # Calculate overall confidence
            if results:
                confidences = [r["analysis_confidence"] for r in results]
                avg_confidence = sum(confidences) / len(confidences)
            else:
                avg_confidence = 0.0

            return StepResult.ok(
                data={
                    "results": results,
                    "total_segments": len(segments),
                    "analyzed_segments": len(results),
                    "average_confidence": avg_confidence,
                    "model": model,
                }
            )

        except Exception as e:
            logger.error(f"Segment analysis failed: {e}")
            return StepResult.fail(f"Segment analysis failed: {e!s}")

    def _select_model(self, model_alias: str) -> str:
        """Select actual model configuration from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Model configuration string
        """
        model_configs = {
            "fast": "fast_analysis",
            "balanced": "balanced_analysis",
            "quality": "quality_analysis",
        }

        return model_configs.get(model_alias, "balanced_analysis")

    def _analyze_text(
        self, text: str, speaker: str | None, timestamp: float | None, model_name: str
    ) -> SentimentStanceAnalysisResult | None:
        """Analyze text using sentiment models or fallback.

        Args:
            text: Input text
            speaker: Speaker name
            timestamp: Timestamp
            model_name: Model configuration

        Returns:
            SentimentStanceAnalysisResult or None if analysis fails
        """
        try:
            # Try advanced transformer-based analysis
            if TRANSFORMERS_AVAILABLE:
                return self._analyze_with_transformers(text, speaker, timestamp, model_name)

            # Fallback to rule-based analysis
            logger.warning("Transformers not available, using rule-based analysis")
            return self._analyze_with_rules(text, speaker, timestamp, model_name)

        except Exception as e:
            logger.error(f"Text analysis failed for model {model_name}: {e}")
            return None

    def _analyze_with_transformers(
        self, text: str, speaker: str | None, timestamp: float | None, model_name: str
    ) -> SentimentStanceAnalysisResult:
        """Analyze text using transformer models.

        Args:
            text: Input text
            speaker: Speaker name
            timestamp: Timestamp
            model_name: Model configuration

        Returns:
            SentimentStanceAnalysisResult with analysis
        """
        # Load models lazily
        if self._sentiment_pipeline is None:
            logger.info("Loading sentiment analysis pipeline")
            try:
                self._sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    return_all_scores=True,
                )
            except Exception:
                self._sentiment_pipeline = None

        if self._emotion_pipeline is None:
            logger.info("Loading emotion analysis pipeline")
            try:
                self._emotion_pipeline = pipeline(
                    "text-classification",
                    model="j-hartmann/emotion-english-distilroberta-base",
                    return_all_scores=True,
                )
            except Exception:
                self._emotion_pipeline = None

        # Perform sentiment analysis
        sentiment = self._analyze_sentiment(text)

        # Perform emotion analysis
        emotion = self._analyze_emotion(text)

        # Perform stance analysis
        stance = self._analyze_stance(text)

        # Perform rhetorical analysis
        rhetorical = self._analyze_rhetorical(text)

        # Calculate overall confidence
        confidences = [
            sentiment.confidence,
            emotion.confidence,
            stance.confidence,
        ]
        avg_confidence = sum(confidences) / len(confidences)

        return SentimentStanceAnalysisResult(
            sentiment=sentiment,
            emotion=emotion,
            stance=stance,
            rhetorical=rhetorical,
            text_segment=text,
            speaker=speaker,
            timestamp=timestamp,
            analysis_confidence=avg_confidence,
        )

    def _analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """Analyze sentiment of text.

        Args:
            text: Input text

        Returns:
            SentimentAnalysis result
        """
        if self._sentiment_pipeline:
            try:
                results = self._sentiment_pipeline(text)

                # Convert to our format
                if results and isinstance(results[0], list):
                    scores = results[0]

                    # Find dominant sentiment
                    dominant = max(scores, key=lambda x: x["score"])
                    sentiment_label = dominant["label"].lower()

                    # Map to our categories
                    sentiment_map = {
                        "positive": "positive",
                        "negative": "negative",
                        "neutral": "neutral",
                    }

                    sentiment = sentiment_map.get(sentiment_label, "neutral")

                    # Calculate intensity (difference from neutral)
                    neutral_score = next(
                        (item["score"] for item in scores if item["label"].lower() == "neutral"),
                        0,
                    )
                    intensity = abs(dominant["score"] - neutral_score)

                    return SentimentAnalysis(
                        sentiment=sentiment,
                        confidence=dominant["score"],
                        intensity=intensity,
                    )

            except Exception as e:
                logger.warning(f"Transformer sentiment analysis failed: {e}")

        # Fallback to rule-based analysis
        return self._analyze_sentiment_rules(text)

    def _analyze_emotion(self, text: str) -> EmotionAnalysis:
        """Analyze emotions in text.

        Args:
            text: Input text

        Returns:
            EmotionAnalysis result
        """
        if self._emotion_pipeline:
            try:
                results = self._emotion_pipeline(text)

                if results and isinstance(results[0], list):
                    scores = results[0]

                    # Find primary emotion
                    primary = max(scores, key=lambda x: x["score"])
                    primary_emotion = primary["label"].lower()

                    # Create emotion score mapping
                    emotion_scores = {item["label"].lower(): item["score"] for item in scores}

                    return EmotionAnalysis(
                        primary_emotion=primary_emotion,
                        confidence=primary["score"],
                        emotion_scores=emotion_scores,
                    )

            except Exception as e:
                logger.warning(f"Transformer emotion analysis failed: {e}")

        # Fallback to rule-based analysis
        return self._analyze_emotion_rules(text)

    def _analyze_stance(self, text: str) -> StanceAnalysis:
        """Analyze stance in text.

        Args:
            text: Input text

        Returns:
            StanceAnalysis result
        """
        # Simple rule-based stance detection
        text_lower = text.lower()

        # Agreement indicators
        agreement_words = [
            "agree",
            "yes",
            "right",
            "correct",
            "exactly",
            "absolutely",
            "definitely",
        ]
        if any(word in text_lower for word in agreement_words):
            return StanceAnalysis(
                stance="agree",
                confidence=0.7,
                stance_type="explicit",
            )

        # Disagreement indicators
        disagreement_words = [
            "disagree",
            "no",
            "wrong",
            "incorrect",
            "not true",
            "false",
            "dispute",
        ]
        if any(word in text_lower for word in disagreement_words):
            return StanceAnalysis(
                stance="disagree",
                confidence=0.7,
                stance_type="explicit",
            )

        # Questioning indicators
        if text.endswith("?") or "what about" in text_lower or "how about" in text_lower:
            return StanceAnalysis(
                stance="questioning",
                confidence=0.8,
                stance_type="rhetorical",
            )

        # Default to neutral
        return StanceAnalysis(
            stance="neutral",
            confidence=0.5,
            stance_type="implicit",
        )

    def _analyze_rhetorical(self, text: str) -> RhetoricalAnalysis:
        """Analyze rhetorical devices in text.

        Args:
            text: Input text

        Returns:
            RhetoricalAnalysis result
        """
        # Simple rhetorical device detection
        has_question = text.endswith("?")
        has_exclamation = text.endswith("!")

        # Find emphasis words
        emphasis_words = []
        for word in text.split():
            if word.isupper() and len(word) > 2:
                emphasis_words.append(word)

        # Find rhetorical questions
        rhetorical_questions = []
        if has_question and not text.lower().startswith(("what", "who", "when", "where", "why", "how")):
            rhetorical_questions.append(text)

        return RhetoricalAnalysis(
            has_question=has_question,
            has_exclamation=has_exclamation,
            has_emphasis=len(emphasis_words) > 0,
            rhetorical_questions=rhetorical_questions,
            emphasis_words=emphasis_words,
        )

    def _analyze_sentiment_rules(self, text: str) -> SentimentAnalysis:
        """Rule-based sentiment analysis fallback.

        Args:
            text: Input text

        Returns:
            SentimentAnalysis result
        """
        text_lower = text.lower()

        # Positive indicators
        positive_words = [
            "amazing",
            "great",
            "excellent",
            "wonderful",
            "awesome",
            "fantastic",
            "love",
            "like",
            "good",
            "best",
            "perfect",
        ]
        positive_count = sum(1 for word in positive_words if word in text_lower)

        # Negative indicators
        negative_words = [
            "terrible",
            "awful",
            "horrible",
            "hate",
            "worst",
            "bad",
            "stupid",
            "wrong",
            "disappointing",
        ]
        negative_count = sum(1 for word in negative_words if word in text_lower)

        # Determine sentiment
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.6 + (positive_count * 0.1), 0.9)
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(0.6 + (negative_count * 0.1), 0.9)
        else:
            sentiment = "neutral"
            confidence = 0.5

        # Calculate intensity
        total_indicators = positive_count + negative_count
        intensity = min(total_indicators * 0.2, 1.0)

        return SentimentAnalysis(
            sentiment=sentiment,
            confidence=confidence,
            intensity=intensity,
        )

    def _analyze_emotion_rules(self, text: str) -> EmotionAnalysis:
        """Rule-based emotion analysis fallback.

        Args:
            text: Input text

        Returns:
            EmotionAnalysis result
        """
        text_lower = text.lower()

        # Emotion indicators
        emotion_indicators = {
            "joy": [
                "amazing",
                "great",
                "love",
                "awesome",
                "fantastic",
                "wonderful",
                "happy",
            ],
            "anger": ["hate", "angry", "mad", "furious", "annoying", "terrible"],
            "fear": ["scared", "afraid", "worried", "anxious", "nervous", "terrified"],
            "sadness": [
                "sad",
                "depressed",
                "disappointed",
                "unhappy",
                "miserable",
                "heartbroken",
            ],
            "surprise": ["wow", "amazing", "incredible", "unbelievable", "shocking"],
            "disgust": ["gross", "disgusting", "revolting", "nauseating", "awful"],
        }

        # Count emotion indicators
        emotion_scores = {}
        for emotion, words in emotion_indicators.items():
            count = sum(1 for word in words if word in text_lower)
            emotion_scores[emotion] = count * 0.1  # Simple scoring

        # Find primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores.keys(), key=lambda k: emotion_scores[k])
            primary_confidence = emotion_scores[primary_emotion]
        else:
            primary_emotion = "neutral"
            primary_confidence = 0.5

        return EmotionAnalysis(
            primary_emotion=primary_emotion,
            confidence=primary_confidence,
            emotion_scores=emotion_scores,
        )

    def _check_cache(self, text: str, speaker: str | None, model: str) -> SentimentStanceAnalysisResult | None:
        """Check if analysis exists in cache.

        Args:
            text: Input text
            speaker: Speaker name
            model: Model alias

        Returns:
            Cached SentimentStanceAnalysisResult or None
        """
        import hashlib

        # Create cache key from text and context
        context = f"{speaker or 'unknown'}:{model}"
        combined = f"{text}:{context}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()

        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]

        return None

    def _cache_result(
        self,
        text: str,
        speaker: str | None,
        model: str,
        result: SentimentStanceAnalysisResult,
    ) -> None:
        """Cache analysis result.

        Args:
            text: Input text
            speaker: Speaker name
            model: Model alias
            result: SentimentStanceAnalysisResult to cache
        """
        import hashlib
        import time

        # Create cache key
        context = f"{speaker or 'unknown'}:{model}"
        combined = f"{text}:{context}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()

        # Add processing timestamp
        result.analysis_confidence = time.time() * 1000  # Simplified timestamp

        # Evict old entries if cache is full
        if len(self._analysis_cache) >= self.cache_size:
            # Simple FIFO eviction - remove first key
            first_key = next(iter(self._analysis_cache))
            del self._analysis_cache[first_key]

        self._analysis_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear analysis cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._analysis_cache)
        self._analysis_cache.clear()

        logger.info(f"Cleared {cache_size} cached analyses")

        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get analysis cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._analysis_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._analysis_cache) / self.cache_size if self.cache_size > 0 else 0.0,
                "models_cached": {},
            }

            # Count entries per model
            for result in self._analysis_cache.values():
                # Use a simplified model identifier
                model = "transformer" if hasattr(result, "sentiment") else "rule_based"
                stats["models_cached"][model] = stats["models_cached"].get(model, 0) + 1

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


# Singleton instance
_analysis_service: SentimentStanceAnalysisService | None = None


def get_sentiment_stance_analysis_service() -> SentimentStanceAnalysisService:
    """Get singleton sentiment analysis service instance.

    Returns:
        Initialized SentimentStanceAnalysisService instance
    """
    global _analysis_service

    if _analysis_service is None:
        _analysis_service = SentimentStanceAnalysisService()

    return _analysis_service
