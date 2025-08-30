"""Text analysis helper built on top of NLTK.

Design notes (typing):
        * NLTK is an optional dependency; we avoid importing it at type-check time
            to prevent mypy crashes / missing-import noise in strict mode.
        * Runtime imports are performed lazily inside ``__init__``; for mypy we
            supply minimal Protocol-like attribute expectations via ``TYPE_CHECKING``
            guarded imports.
"""

import importlib
import logging
from collections import Counter
from typing import TYPE_CHECKING, TypedDict

from ._base import BaseTool

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


class TextAnalysisTool(BaseTool[dict[str, object]]):
    name: str = "Text Analysis Tool"
    description: str = "Analyze text to extract sentiment, keywords, and topics."

    def __init__(self) -> None:
        super().__init__()
        self._load_runtime()
        if nltk is None or stopwords is None or SentimentIntensityAnalyzer is object:
            raise RuntimeError("nltk is not installed; install 'nltk' extra to use this tool")
        self._ensure_nltk_data()
        self.sia = SentimentIntensityAnalyzer()

    def _load_runtime(self) -> None:
        global nltk, stopwords, SentimentIntensityAnalyzer, word_tokenize  # noqa: PLW0603
        if nltk is not None:  # already loaded
            return
        try:  # pragma: no cover - import side effects
            nltk = importlib.import_module("nltk")
            stopwords = importlib.import_module("nltk.corpus").stopwords
            sentiment_mod = importlib.import_module("nltk.sentiment")
            SentimentIntensityAnalyzer = getattr(sentiment_mod, "SentimentIntensityAnalyzer")
            word_tokenize = importlib.import_module("nltk.tokenize").word_tokenize
        except Exception:
            nltk = None  # leave placeholders; __init__ will raise

    def _ensure_nltk_data(self) -> None:  # pragma: no cover - setup helper
        resources = [
            ("sentiment/vader_lexicon", "vader_lexicon"),
            ("tokenizers/punkt", "punkt"),
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

    def _run(self, text: str) -> dict[str, object]:
        """Analyze a piece of text."""
        try:
            sentiment = self.get_sentiment(text)
            keywords = self.get_keywords(text)

            return {"status": "success", "sentiment": sentiment, "keywords": keywords}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_sentiment(self, text: str) -> _SentimentResult:
        """Get the sentiment of a piece of text."""
        raw = self.sia.polarity_scores(text)
        # Assign using literal keys to satisfy TypedDict literal-required constraint
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
        """Get the most common keywords from a piece of text."""
        stop_words = set(stopwords.words("english"))
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalpha() and word not in stop_words]

        word_counts = Counter(words)
        keywords = [word for word, count in word_counts.most_common(num_keywords)]

        return keywords

    # Provide explicit run method for pipeline usage
    def run(self, text: str) -> dict[str, object]:  # pragma: no cover - thin wrapper
        return self._run(text)
