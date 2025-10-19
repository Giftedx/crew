"""Enhanced text analysis tool with advanced sentiment analysis and topic modeling.

This tool extends the basic NLTK-based text analysis with:
- Advanced emotion detection (joy, anger, fear, sadness, etc.)
- Topic modeling and categorization
- Context-aware sentiment analysis
- Multi-dimensional sentiment scoring
- Trend detection capabilities

Future extensions planned:
- Multi-modal analysis (images, videos, audio)
- Visual sentiment detection
- Video frame-by-frame emotion tracking
- Audio speaker identification and tone analysis
- Cross-media correlation and synthesis
"""

import logging
import os
from collections import Counter
from typing import TYPE_CHECKING, Any, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

# Allow intentional runtime imports inside methods for optional dependencies
# without triggering E402 (import at top of file) lint warnings.
# ruff: noqa: E402

if TYPE_CHECKING:  # pragma: no cover - hints only
    import nltk
    from nltk.corpus import stopwords
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.tokenize import word_tokenize
else:  # lightweight runtime placeholders until loaded
    nltk = None  # type: ignore
    stopwords = None  # type: ignore
    SentimentIntensityAnalyzer = object  # type: ignore

    def word_tokenize(s: str) -> list[str]:  # type: ignore
        return []


class _SentimentResult(TypedDict, total=False):
    neg: float
    neu: float
    pos: float
    compound: float


class _EmotionResult(TypedDict, total=False):
    joy: float
    anger: float
    fear: float
    sadness: float
    surprise: float
    disgust: float
    anticipation: float
    trust: float
    dominant_emotion: str
    emotion_intensity: float


class _TopicResult(TypedDict, total=False):
    primary_topics: list[str]
    topic_categories: list[str]
    topic_confidence: dict[str, float]
    content_themes: list[str]


class TextAnalysisTool(BaseTool[StepResult]):
    name: str = "Enhanced Text Analysis Tool"
    description: str = "Advanced text analysis with emotion detection, topic modeling, and enhanced sentiment analysis."

    def __init__(self) -> None:
        super().__init__()
        self._load_runtime()
        self._metrics = get_metrics()
        # Graceful capability detection: operate in degraded mode when NLTK isn't available.
        self._nltk_available = bool(
            nltk is not None and stopwords is not None and SentimentIntensityAnalyzer is not object
        )
        self.sia = None  # set below if available
        if self._nltk_available:
            self._ensure_nltk_data()
            try:
                self.sia = SentimentIntensityAnalyzer()  # type: ignore[call-arg]
            except Exception:
                # Fall back to degraded mode if sentiment init fails at runtime
                logging.warning("NLTK SentimentIntensityAnalyzer init failed; falling back to heuristic mode")
                self._nltk_available = False
        if not self._nltk_available:
            # Default to strict failure unless explicitly permitted to degrade.
            allow_degraded = os.getenv("ALLOW_NLTK_DEGRADED_MODE", "0").lower() in {"1", "true", "yes", "on"}
            if allow_degraded:
                logging.info(
                    "NLTK not available; TextAnalysisTool using heuristic fallback mode due to "
                    "ALLOW_NLTK_DEGRADED_MODE=1. Install nltk for richer analysis."
                )
            else:
                logging.warning(
                    "NLTK not available and ALLOW_NLTK_DEGRADED_MODE not enabled; refusing to run in degraded mode."
                )
                # Align behavior with tests: raise clearly so callers can choose to enable fallback.
                raise RuntimeError(
                    "NLTK not available; set ALLOW_NLTK_DEGRADED_MODE=1 to use heuristic fallback or install nltk."
                )

    def _load_runtime(self) -> None:
        global nltk, stopwords, SentimentIntensityAnalyzer, word_tokenize  # noqa: PLW0603
        if nltk is not None:  # already loaded
            return
        try:  # pragma: no cover - import side effects
            import nltk as _nltk
            from nltk.corpus import stopwords as _stopwords
            from nltk.sentiment.vader import SentimentIntensityAnalyzer as _SentimentIntensityAnalyzer
            from nltk.tokenize import word_tokenize as _word_tokenize

            nltk = _nltk
            stopwords = _stopwords
            SentimentIntensityAnalyzer = _SentimentIntensityAnalyzer
            word_tokenize = _word_tokenize
            print("✅ NLTK runtime components loaded successfully")
        except Exception as e:
            print(f"⚠️  NLTK import failed: {e}")
            nltk = None  # leave placeholders; __init__ will raise

    def _ensure_nltk_data(self) -> None:  # pragma: no cover - setup helper
        if os.getenv("NLTK_OFFLINE"):
            logging.info("NLTK_OFFLINE set - skipping NLTK data downloads")
            return
        resources = [
            ("sentiment/vader_lexicon", "vader_lexicon"),
            ("tokenizers/punkt", "punkt"),
            ("tokenizers/punkt_tab", "punkt_tab"),
            ("corpora/stopwords", "stopwords"),
        ]
        for path, name in resources:
            if nltk is None or not hasattr(nltk, "data"):
                continue
            try:
                nltk.data.find(path)
            except LookupError:
                try:
                    getattr(nltk, "download")(name, quiet=True)
                except Exception as exc:  # pragma: no cover
                    logging.warning("Failed to download %s: %s", name, exc)

    def _run(self, text: str) -> StepResult:
        # (nltk availability enforced in __init__; no degraded path)
        try:  # full analysis path (or degraded neutral path)
            # Import kept local to avoid heavy import on cold paths
            from ultimate_discord_intelligence_bot.models.structured_responses import (
                AnalysisStatus,
                SentimentScore,
                TextAnalysisResult,
            )

            sentiment_raw = self.get_sentiment(text)
            keywords = self.get_keywords(text)
            word_count = len(word_tokenize(text)) if word_tokenize and text else 0

            # Enhanced analysis
            enhanced_analysis = self.get_enhanced_sentiment_analysis(text)

            # Map compound polarity to coarse label for downstream tags/memory
            compound = sentiment_raw.get("compound", 0.0)
            pos_threshold = 0.05
            neg_threshold = -0.05
            if compound >= pos_threshold:
                sentiment_label = "positive"
                sentiment_score = float(compound)
            elif compound <= neg_threshold:
                sentiment_label = "negative"
                sentiment_score = float(abs(compound))
            else:
                sentiment_label = "neutral"
                sentiment_score = float(abs(compound))

            structured_sentiment = SentimentScore(label=sentiment_label, score=min(1.0, sentiment_score))
            readability = self._calculate_readability_score(text)

            # Preserve rich structured payload for advanced consumers
            structured = TextAnalysisResult(
                status=AnalysisStatus.SUCCESS,
                sentiment=structured_sentiment,
                key_phrases=keywords[:10],
                word_count=word_count,
                language_detected="en",
                readability_score=readability,
            ).model_dump()

            # IMPORTANT: Return top-level fields expected by pipeline/tests
            # - 'sentiment': coarse string label for tagging
            # - 'sentiment_score': numeric score for metrics
            # - 'keywords': alias of key_phrases for compatibility
            # Also include original rich payloads under *_details to avoid data loss
            # Enhanced analysis data
            out = {
                "sentiment": sentiment_label,
                "sentiment_score": sentiment_score,
                "keywords": keywords[:10],
                "key_phrases": keywords[:10],
                "word_count": word_count,
                "language_detected": "en",
                "readability_score": readability,
                "sentiment_details": sentiment_raw,
                "structured": structured,
                # Enhanced analysis features
                "emotions": enhanced_analysis["emotions"],
                "topics": enhanced_analysis["topics"],
                "enhanced_insights": enhanced_analysis["enhanced_insights"],
                "dominant_emotion": enhanced_analysis["emotions"]["dominant_emotion"],
                "emotion_intensity": enhanced_analysis["emotions"]["emotion_intensity"],
                "primary_topics": enhanced_analysis["topics"]["primary_topics"],
                "content_themes": enhanced_analysis["topics"]["content_themes"],
            }

            try:
                self._metrics.counter("tool_runs_total", labels={"tool": "text_analysis", "outcome": "success"}).inc()
            except Exception as exc:  # pragma: no cover - metrics failure shouldn't break tool
                logging.debug("metrics increment failed: %s", exc)
            return StepResult.ok(**out)
        except Exception as e:  # broad to ensure tool robustness
            try:
                self._metrics.counter("tool_runs_total", labels={"tool": "text_analysis", "outcome": "error"}).inc()
            except Exception as exc:  # pragma: no cover
                logging.debug("metrics increment failed (error path): %s", exc)
            return StepResult.fail(error=str(e), data={"sentiment": {"label": "neutral", "score": 0.0}})

    def _calculate_readability_score(self, text: str) -> float | None:
        try:
            if not text.strip():
                return None
            sentence_count = max(1, text.count(".") + text.count("!") + text.count("?"))
            words = word_tokenize(text) if word_tokenize else text.split()
            word_count = len(words)
            if word_count == 0:
                return None
            syllable_count = 0
            for word in words:
                vowels = "aeiouyAEIOUY"
                word_syllables = 0
                prev_was_vowel = False
                for char in word:
                    if char in vowels:
                        if not prev_was_vowel:
                            word_syllables += 1
                        prev_was_vowel = True
                    else:
                        prev_was_vowel = False
                syllable_count += max(1, word_syllables)
            avg_sentence_length = word_count / sentence_count
            avg_syllables_per_word = syllable_count / word_count
            score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
            return max(0.0, min(100.0, score))
        except Exception:
            return None

    def get_sentiment(self, text: str) -> _SentimentResult:
        # Degraded heuristic mode when NLTK is unavailable
        if not self._nltk_available or self.sia is None:
            # Simple lexicon-based polarity: tiny but robust fallback
            pos_words = {
                "good",
                "great",
                "excellent",
                "amazing",
                "positive",
                "love",
                "like",
                "enjoy",
                "success",
                "benefit",
            }
            neg_words = {
                "bad",
                "terrible",
                "awful",
                "horrible",
                "negative",
                "hate",
                "dislike",
                "fail",
                "problem",
                "issue",
            }
            # Lowercase tokenization (fallback to simple split if tokenizer missing)
            try:
                toks = word_tokenize(text.lower()) if word_tokenize else text.lower().split()
            except Exception:
                toks = text.lower().split()
            pos_hits = sum(1 for t in toks if t.isalpha() and t in pos_words)
            neg_hits = sum(1 for t in toks if t.isalpha() and t in neg_words)
            total = max(1, pos_hits + neg_hits)
            # Map to approximate compound: (pos - neg) / total
            compound = (pos_hits - neg_hits) / total
            return {
                "neg": max(0.0, float(neg_hits / total)),
                "neu": float(max(0.0, 1.0 - (pos_hits + neg_hits) / max(1, len(toks)))) if toks else 1.0,
                "pos": max(0.0, float(pos_hits / total)),
                "compound": float(compound),
            }
        # Full NLTK path
        raw = self.sia.polarity_scores(text)
        result: _SentimentResult = {}
        if "neg" in raw:
            result["neg"] = float(raw["neg"])
        if "neu" in raw:
            result["neu"] = float(raw["neu"])
        if "pos" in raw:
            result["pos"] = float(raw["pos"])
        if "compound" in raw:
            result["compound"] = float(raw["compound"])
        return result

    def get_keywords(self, text: str, num_keywords: int = 10) -> list[str]:
        try:
            stop_words = set(stopwords.words("english")) if (self._nltk_available and stopwords) else set()
        except Exception:
            stop_words = {"the", "a", "and", "or", "is", "to", "of", "in", "on", "for", "with"}
        try:
            words = word_tokenize(text.lower()) if word_tokenize else text.lower().split()
        except Exception:
            words = text.lower().split()
        words = [word for word in words if word.isalpha() and word not in stop_words]
        word_counts = Counter(words)
        return [word for word, _ in word_counts.most_common(num_keywords)]

    def get_emotions(self, text: str) -> _EmotionResult:
        """Advanced emotion detection using enhanced lexical analysis."""
        # Enhanced emotion lexicons
        emotion_lexicons = {
            "joy": {
                "happy",
                "excited",
                "pleased",
                "delighted",
                "thrilled",
                "ecstatic",
                "cheerful",
                "jubilant",
                "elated",
                "overjoyed",
                "blissful",
                "radiant",
                "laughing",
                "smiling",
                "grinning",
                "beaming",
                "glowing",
                "exuberant",
            },
            "anger": {
                "angry",
                "furious",
                "irate",
                "enraged",
                "livid",
                "incensed",
                "outraged",
                "infuriated",
                "irritated",
                "annoyed",
                "frustrated",
                "aggravated",
                "exasperated",
                "provoked",
                "hostile",
                "aggressive",
            },
            "fear": {
                "scared",
                "afraid",
                "frightened",
                "terrified",
                "panicked",
                "alarmed",
                "anxious",
                "worried",
                "nervous",
                "uneasy",
                "apprehensive",
                "dread",
                "terror",
                "horror",
                "panic",
                "alarm",
                "fearful",
                "timid",
            },
            "sadness": {
                "sad",
                "depressed",
                "unhappy",
                "miserable",
                "despairing",
                "sorrowful",
                "grieving",
                "melancholy",
                "heartbroken",
                "devastated",
                "disappointed",
                "downhearted",
                "dejected",
                "despondent",
                "hopeless",
                "forlorn",
            },
            "surprise": {
                "surprised",
                "shocked",
                "astonished",
                "amazed",
                "stunned",
                "astounded",
                "dumbfounded",
                "flabbergasted",
                "speechless",
                "incredulous",
                "amazed",
                "unexpected",
                "sudden",
                "startling",
                "shocking",
                "amazing",
            },
            "disgust": {
                "disgusted",
                "repulsed",
                "revolted",
                "nauseated",
                "sickened",
                "appalled",
                "horrified",
                "outraged",
                "repugnant",
                "vile",
                "loathsome",
                "abhorrent",
                "detestable",
                "repulsive",
                "nauseating",
                "sickening",
            },
            "anticipation": {
                "anticipating",
                "expecting",
                "awaiting",
                "looking forward",
                "hopeful",
                "eager",
                "excited",
                "impatient",
                "anxious",
                "expectant",
                "pending",
                "upcoming",
                "forthcoming",
                "imminent",
                "prospective",
                "awaited",
            },
            "trust": {
                "trust",
                "believe",
                "confident",
                "reliable",
                "dependable",
                "faithful",
                "loyal",
                "honest",
                "sincere",
                "genuine",
                "authentic",
                "credible",
                "trustworthy",
                "reputable",
                "honorable",
                "integrity",
            },
        }

        try:
            words = word_tokenize(text.lower()) if word_tokenize else text.lower().split()
        except Exception:
            words = text.lower().split()

        # Count emotion words
        emotion_scores = {}
        total_emotion_words = 0

        for emotion, lexicon in emotion_lexicons.items():
            score = sum(1 for word in words if word in lexicon)
            emotion_scores[emotion] = score
            total_emotion_words += score

        # Normalize scores
        if total_emotion_words > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] = emotion_scores[emotion] / total_emotion_words

        # Determine dominant emotion
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0] if emotion_scores else "neutral"
        max_score = max(emotion_scores.values()) if emotion_scores else 0

        # Calculate emotion intensity (0-1 scale)
        emotion_intensity = min(1.0, max_score * 2)  # Scale factor to make intensity more sensitive

        return {
            "joy": emotion_scores.get("joy", 0.0),
            "anger": emotion_scores.get("anger", 0.0),
            "fear": emotion_scores.get("fear", 0.0),
            "sadness": emotion_scores.get("sadness", 0.0),
            "surprise": emotion_scores.get("surprise", 0.0),
            "disgust": emotion_scores.get("disgust", 0.0),
            "anticipation": emotion_scores.get("anticipation", 0.0),
            "trust": emotion_scores.get("trust", 0.0),
            "dominant_emotion": dominant_emotion,
            "emotion_intensity": emotion_intensity,
        }

    def get_topics(self, text: str) -> _TopicResult:
        """Extract topics and themes from text using enhanced analysis."""
        # Topic categories and their associated keywords
        topic_categories = {
            "politics": {
                "government",
                "policy",
                "election",
                "president",
                "congress",
                "senate",
                "democrat",
                "republican",
                "legislation",
                "law",
                "regulation",
                "vote",
                "campaign",
                "candidate",
                "political",
                "partisan",
                "ideology",
            },
            "technology": {
                "technology",
                "tech",
                "software",
                "hardware",
                "computer",
                "internet",
                "digital",
                "innovation",
                "artificial intelligence",
                "AI",
                "machine learning",
                "automation",
                "cybersecurity",
                "programming",
                "development",
                "app",
            },
            "business": {
                "business",
                "company",
                "corporate",
                "industry",
                "market",
                "economy",
                "finance",
                "investment",
                "stock",
                "revenue",
                "profit",
                "growth",
                "strategy",
                "management",
                "entrepreneurship",
                "startup",
            },
            "science": {
                "science",
                "research",
                "study",
                "experiment",
                "discovery",
                "theory",
                "scientific",
                "biology",
                "chemistry",
                "physics",
                "mathematics",
                "data",
                "analysis",
                "evidence",
                "hypothesis",
                "conclusion",
            },
            "health": {
                "health",
                "medical",
                "medicine",
                "doctor",
                "patient",
                "treatment",
                "disease",
                "illness",
                "wellness",
                "fitness",
                "nutrition",
                "mental health",
                "therapy",
                "diagnosis",
                "prevention",
                "care",
                "hospital",
            },
            "environment": {
                "environment",
                "climate",
                "sustainability",
                "green",
                "eco",
                "nature",
                "pollution",
                "conservation",
                "renewable",
                "energy",
                "carbon",
                "emissions",
                "ecosystem",
                "biodiversity",
                "wildlife",
                "planet",
            },
            "education": {
                "education",
                "school",
                "university",
                "college",
                "student",
                "teacher",
                "learning",
                "curriculum",
                "academic",
                "degree",
                "knowledge",
                "skill",
                "training",
                "development",
                "instruction",
                "pedagogy",
            },
            "entertainment": {
                "entertainment",
                "movie",
                "film",
                "music",
                "song",
                "artist",
                "celebrity",
                "game",
                "gaming",
                "sport",
                "athlete",
                "performance",
                "show",
                "concert",
                "festival",
                "media",
                "streaming",
            },
        }

        try:
            words = word_tokenize(text.lower()) if word_tokenize else text.lower().split()
        except Exception:
            words = text.lower().split()

        # Count topic keywords
        topic_scores = {}
        topic_word_counts = {}

        for topic, keywords in topic_categories.items():
            count = sum(1 for word in words if word in keywords)
            if count > 0:
                topic_scores[topic] = count / len(words)  # Normalize by text length
                topic_word_counts[topic] = count

        # Sort topics by relevance score
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)

        # Extract primary topics (top 3)
        primary_topics = [topic for topic, _ in sorted_topics[:3]]

        # Extract topic categories with confidence scores
        topic_confidence = {topic: score for topic, score in sorted_topics}

        # Generate content themes (broader categories)
        content_themes = []
        if any(score > 0.01 for score in topic_scores.values()):  # At least some topical content
            # Determine dominant theme based on highest scoring topic category
            if sorted_topics:
                dominant_topic = sorted_topics[0][0]
                content_themes.append(dominant_topic)

                # Add secondary themes if they have significant scores
                for topic, score in sorted_topics[1:3]:
                    if score > 0.005:  # Lower threshold for secondary themes
                        content_themes.append(topic)

        return {
            "primary_topics": primary_topics,
            "topic_categories": list(topic_categories.keys()),
            "topic_confidence": topic_confidence,
            "content_themes": content_themes,
        }

    def get_enhanced_sentiment_analysis(self, text: str) -> dict[str, Any]:
        """Enhanced sentiment analysis with emotion detection and topic modeling."""
        # Get basic sentiment
        basic_sentiment = self.get_sentiment(text)

        # Get emotion analysis
        emotions = self.get_emotions(text)

        # Get topic analysis
        topics = self.get_topics(text)

        # Combine analyses for enhanced insights
        enhanced_analysis = {
            "basic_sentiment": basic_sentiment,
            "emotions": emotions,
            "topics": topics,
            "enhanced_insights": self._generate_enhanced_insights(basic_sentiment, emotions, topics),
        }

        return enhanced_analysis

    def _generate_enhanced_insights(
        self, sentiment: _SentimentResult, emotions: _EmotionResult, topics: _TopicResult
    ) -> dict[str, Any]:
        """Generate enhanced insights by combining sentiment, emotion, and topic data."""
        insights = {}

        # Sentiment intensity interpretation
        compound_score = sentiment.get("compound", 0)
        if compound_score > 0.6:
            insights["sentiment_interpretation"] = "Strongly positive sentiment with high emotional engagement"
        elif compound_score > 0.2:
            insights["sentiment_interpretation"] = "Moderately positive sentiment"
        elif compound_score > -0.2:
            insights["sentiment_interpretation"] = "Neutral sentiment with balanced emotional tone"
        elif compound_score > -0.6:
            insights["sentiment_interpretation"] = "Moderately negative sentiment"
        else:
            insights["sentiment_interpretation"] = "Strongly negative sentiment with intense emotional response"

        # Emotional context
        dominant_emotion = emotions.get("dominant_emotion", "neutral")
        emotion_intensity = emotions.get("emotion_intensity", 0)

        if emotion_intensity > 0.3:
            insights["emotional_context"] = f"High emotional intensity with dominant {dominant_emotion} tone"
        elif emotion_intensity > 0.1:
            insights["emotional_context"] = f"Moderate emotional engagement, primarily {dominant_emotion}"
        else:
            insights["emotional_context"] = "Low emotional intensity, relatively neutral tone"

        # Topic relevance
        primary_topics = topics.get("primary_topics", [])
        if primary_topics:
            insights["topic_relevance"] = f"Content primarily discusses: {', '.join(primary_topics[:2])}"
        else:
            insights["topic_relevance"] = "Content appears to be general or conversational"

        # Overall content classification
        if topics.get("content_themes"):
            theme = topics["content_themes"][0]
            if emotions.get("joy", 0) > 0.1 and sentiment.get("pos", 0) > 0.3:
                insights["content_classification"] = f"Positive {theme} content with engaging emotional tone"
            elif emotions.get("anger", 0) > 0.1 and sentiment.get("neg", 0) > 0.3:
                insights["content_classification"] = f"Critical {theme} content with strong negative emotions"
            else:
                insights["content_classification"] = f"Neutral {theme} discussion"

        return insights

    def run(self, text: str) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(text)
