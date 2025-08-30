"""Lightweight sentiment analysis tool."""

from __future__ import annotations

from ._base import BaseTool

# Sentiment threshold constants (heuristic fallback only)
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


class SentimentTool(BaseTool[dict[str, object]]):
    """Classify text as positive, neutral or negative using a lexical heuristic.

    Rationale: A deterministic, dependency‑free heuristic keeps unit tests fast and
    avoids optional NLTK/VADER imports that previously introduced mypy noise and
    internal cache corruption. We intentionally keep the implementation minimal;
    a future feature flag could reintroduce a model-backed analyzer.
    """

    name: str = "Sentiment Tool"
    description: str = "Return overall sentiment for a piece of text."
    model_config = {"extra": "allow"}

    def _run(self, text: str) -> dict[str, object]:
        positive = {"good", "great", "awesome", "love", "excellent"}
        negative = {"bad", "terrible", "awful", "hate", "poor"}
        tokens = text.lower().split()
        score = sum(tok in positive for tok in tokens) - sum(tok in negative for tok in tokens)
        if score > 0:
            label = "positive"
        elif score < 0:
            label = "negative"
        else:
            label = "neutral"
        return {"status": "success", "sentiment": label, "score": score}

    def run(self, text: str) -> dict[str, object]:  # pragma: no cover - thin wrapper
        return self._run(text)


__all__ = ["SentimentTool"]
