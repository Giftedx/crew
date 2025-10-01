"""Extract factual claims from text using NLP patterns."""

from __future__ import annotations

from kg.extract import extract
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

MIN_CLAIM_LEN = 5  # Minimum characters for a claim to be considered


class ClaimExtractorTool(BaseTool[StepResult]):
    """Extract factual claims from text using regex patterns and NLP.

    Return schema (dict):
      status: "success" | "error"
      claims: list[str]
      count: int (present on success)
      error: str (present on error)
    """

    name: str = "Claim Extractor Tool"
    description: str = "Extract potential factual claims from text using linguistic patterns."

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def _run(self, text: str) -> StepResult:
        """Extract claims using the KG extraction module returning StepResult."""
        if not text or not text.strip():
            self._metrics.counter("tool_runs_total", labels={"tool": "claim_extractor", "outcome": "success"}).inc()
            return StepResult.ok(claims=[], count=0)

        try:
            _, claims = extract(text.strip())
            claim_texts: list[str] = []
            for claim in claims:
                claim_text = claim.text.strip()
                if claim_text and len(claim_text) > MIN_CLAIM_LEN:
                    claim_texts.append(claim_text)
            self._metrics.counter("tool_runs_total", labels={"tool": "claim_extractor", "outcome": "success"}).inc()
            return StepResult.ok(claims=claim_texts, count=len(claim_texts))
        except Exception as e:  # pragma: no cover - defensive
            self._metrics.counter("tool_runs_total", labels={"tool": "claim_extractor", "outcome": "error"}).inc()
            return StepResult.fail(error=str(e), claims=[])

    def run(self, text: str) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(text)


__all__ = ["ClaimExtractorTool"]
