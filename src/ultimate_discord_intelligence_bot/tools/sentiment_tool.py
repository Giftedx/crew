"""Lightweight sentiment analysis tool."""

from __future__ import annotations

from crewai.tools import BaseTool

# Sentiment threshold constants (VADER recommended)
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05

try:  # pragma: no cover - optional dependency
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
except Exception:  # pragma: no cover
    nltk = None
    SentimentIntensityAnalyzer = None


class SentimentTool(BaseTool):
    """Classify text as positive, neutral or negative using VADER."""

    name: str = "Sentiment Tool"
    description: str = "Return overall sentiment for a piece of text."
    model_config = {"extra": "allow"}

    def __init__(self) -> None:
        super().__init__()
        if nltk and SentimentIntensityAnalyzer:
            try:  # pragma: no cover - download once
                nltk.data.find("sentiment/vader_lexicon")
            except LookupError:  # pragma: no cover
                nltk.download("vader_lexicon")
            self.analyzer = SentimentIntensityAnalyzer()
        else:  # pragma: no cover
            self.analyzer = None

    def _run(self, text: str) -> dict:
        if self.analyzer:
            scores = self.analyzer.polarity_scores(text)
            compound = scores.get("compound", 0.0)
            if compound >= POSITIVE_THRESHOLD:
                label = "positive"
            elif compound <= NEGATIVE_THRESHOLD:
                label = "negative"
            else:
                label = "neutral"
            return {"status": "success", "sentiment": label, "scores": scores}
        # Fallback simple lexical approach
        positive = {"good", "great", "awesome", "love", "excellent"}
        negative = {"bad", "terrible", "awful", "hate", "poor"}
        tokens = text.lower().split()
        score = sum(t in positive for t in tokens) - sum(t in negative for t in tokens)
        if score > 0:
            label = "positive"
        elif score < 0:
            label = "negative"
        else:
            label = "neutral"
        return {"status": "success", "sentiment": label, "score": score}

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)


__all__ = ["SentimentTool"]
