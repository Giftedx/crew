"""Lightweight sentiment analysis tool (StepResult version)."""

from __future__ import annotations

import logging

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

# Sentiment threshold constants (heuristic fallback only)
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


class SentimentTool(BaseTool):
    """Classify text as positive, neutral or negative using a lexical heuristic.

    Rationale: A deterministic, dependency‑free heuristic keeps unit tests fast and
    avoids optional NLTK/VADER imports that previously introduced mypy noise and
    internal cache corruption. We intentionally keep the implementation minimal;
    a future feature flag could reintroduce a model-backed analyzer.
    """

    name: str = "Sentiment Tool"
    description: str = "Return overall sentiment for a piece of text."
    model_config = {"extra": "allow"}

    def __init__(self):
        super().__init__()
        self._metrics = get_metrics()

    def _run(self, text: str) -> StepResult:
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
        try:
            self._metrics.counter("tool_runs_total", labels={"tool": "sentiment", "outcome": "success"}).inc()
        except Exception as exc:  # pragma: no cover - defensive metrics
            logging.debug("sentiment metrics emit failed: %s", exc)
        return StepResult.ok(data={"sentiment": label, "score": score})

    def run(self, text: str) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(text)


__all__ = ["SentimentTool"]
