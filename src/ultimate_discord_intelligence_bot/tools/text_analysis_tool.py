"""Text analysis helper built on top of NLTK.

Design notes (typing):
        * NLTK is an optional dependency; we avoid importing it at type-check time
            to prevent mypy crashes / missing-import noise in strict mode.
        * Runtime imports are performed lazily inside ``__init__``; for mypy we
            supply minimal Protocol-like attribute expectations via ``TYPE_CHECKING``
            guarded imports.
"""

import logging
import os
from collections import Counter
from typing import TYPE_CHECKING, TypedDict

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


class TextAnalysisTool(BaseTool):
    name: str = "Text Analysis Tool"
    description: str = "Analyze text to extract sentiment, keywords, and topics."

    def __init__(self) -> None:
        super().__init__()
        self._load_runtime()
        if nltk is None or stopwords is None or SentimentIntensityAnalyzer is object:
            raise RuntimeError("NLTK dependency unavailable")
        self._metrics = get_metrics()
        self._nltk_available = True
        self._ensure_nltk_data()
        try:
            self.sia = SentimentIntensityAnalyzer()
        except Exception as exc:  # pragma: no cover - unexpected init failure
            raise RuntimeError(f"Failed to initialize NLTK sentiment analyzer: {exc}")

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
            # Import moved to top-level could be considered; kept local to avoid heavy import in cold paths
            from ultimate_discord_intelligence_bot.models.structured_responses import (
                AnalysisStatus,
                SentimentScore,
                TextAnalysisResult,
            )

            sentiment_data = self.get_sentiment(text)
            keywords = self.get_keywords(text)
            word_count = len(word_tokenize(text)) if word_tokenize and text else 0
            compound = sentiment_data.get("compound", 0.0)
            pos_threshold = 0.05
            neg_threshold = -0.05
            if compound >= pos_threshold:
                sentiment_label = "positive"
                sentiment_score = compound
            elif compound <= neg_threshold:
                sentiment_label = "negative"
                sentiment_score = abs(compound)
            else:
                sentiment_label = "neutral"
                sentiment_score = abs(compound)
            structured_sentiment = SentimentScore(label=sentiment_label, score=min(1.0, sentiment_score))
            readability = self._calculate_readability_score(text)
            result = TextAnalysisResult(
                status=AnalysisStatus.SUCCESS,
                sentiment=structured_sentiment,
                key_phrases=keywords[:10],
                word_count=word_count,
                language_detected="en",
                readability_score=readability,
            )
            data = result.model_dump()
            try:
                self._metrics.counter("tool_runs_total", labels={"tool": "text_analysis", "outcome": "success"}).inc()
            except Exception as exc:  # pragma: no cover - metrics failure shouldn't break tool
                logging.debug("metrics increment failed: %s", exc)
            return StepResult.ok(data=data)
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
        if self.sia is None:
            return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}
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
            stop_words = set(stopwords.words("english")) if stopwords else set()
        except Exception:
            stop_words = {"the", "a", "and", "or", "is", "to", "of", "in"}
        try:
            words = word_tokenize(text.lower()) if word_tokenize else text.lower().split()
        except Exception:
            words = text.lower().split()
        words = [word for word in words if word.isalpha() and word not in stop_words]
        word_counts = Counter(words)
        return [word for word, _ in word_counts.most_common(num_keywords)]

    def run(self, text: str) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(text)
