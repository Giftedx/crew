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

    def _run(self, text: str, max_claims: int = 10) -> StepResult:
        """Extract claims using the KG extraction module returning StepResult.

        Args:
            text: Text to extract claims from
            max_claims: Maximum number of claims to extract (default 10)

        Returns:
            StepResult with claims list and count
        """
        # CRITICAL DEBUG: Log what text we're actually receiving
        import logging

        logger = logging.getLogger(__name__)
        text_preview = (text[:500] + "...") if text and len(text) > 500 else (text or "")
        logger.warning(f"🔍 ClaimExtractorTool received {len(text or '')} chars of text. Preview: {text_preview}")

        if not text or not text.strip():
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "claim_extractor", "outcome": "success"},
            ).inc()
            return StepResult.ok(claims=[], count=0)

        try:
            # For long texts (>500 chars), split into chunks to get diverse claims
            text_stripped = text.strip()
            chunks = []
            if len(text_stripped) > 500:
                # Split into ~300 char chunks with overlap
                chunk_size = 300
                overlap = 50
                for i in range(0, len(text_stripped), chunk_size - overlap):
                    chunk = text_stripped[i : i + chunk_size]
                    if chunk.strip():
                        chunks.append(chunk)
            else:
                chunks = [text_stripped]

            # Extract claims from all chunks
            all_claims = []
            seen_claims = set()  # Deduplicate

            for chunk in chunks:
                # Don't catch exceptions here - let them bubble up for test compatibility
                _, chunk_claims = extract(chunk)
                if chunk_claims is None:
                    # Handle None return from extract (test case requirement)
                    self._metrics.counter(
                        "tool_runs_total",
                        labels={"tool": "claim_extractor", "outcome": "error"},
                    ).inc()
                    return StepResult.fail(error="KG extract returned None", claims=[])

                for claim in chunk_claims:
                    claim_text = claim.text.strip()
                    # Use lowercase for dedup but preserve original casing
                    claim_lower = claim_text.lower()
                    if claim_text and len(claim_text) > MIN_CLAIM_LEN and claim_lower not in seen_claims:
                        all_claims.append(claim_text)
                        seen_claims.add(claim_lower)
                        if len(all_claims) >= max_claims:
                            break

                if len(all_claims) >= max_claims:
                    break

            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "claim_extractor", "outcome": "success"},
            ).inc()
            return StepResult.ok(claims=all_claims, count=len(all_claims))
        except Exception as e:  # pragma: no cover - defensive
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "claim_extractor", "outcome": "error"},
            ).inc()
            return StepResult.fail(error=str(e), claims=[])

    def run(self, text: str, max_claims: int = 10) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(text, max_claims)


__all__ = ["ClaimExtractorTool"]
