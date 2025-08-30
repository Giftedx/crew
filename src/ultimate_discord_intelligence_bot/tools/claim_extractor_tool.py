"""Extract factual claims from text using NLP patterns."""

from __future__ import annotations

from kg.extract import extract

from ._base import BaseTool

MIN_CLAIM_LEN = 5  # Minimum characters for a claim to be considered


class ClaimExtractorTool(BaseTool[dict[str, object]]):
    """Extract factual claims from text using regex patterns and NLP.

    Return schema (dict):
      status: "success" | "error"
      claims: list[str]
      count: int (present on success)
      error: str (present on error)
    """

    name: str = "Claim Extractor Tool"
    description: str = "Extract potential factual claims from text using linguistic patterns."

    def _run(self, text: str) -> dict[str, object]:
        """Extract claims using the KG extraction module."""
        if not text or not text.strip():
            return {"status": "success", "claims": []}

        try:
            # Use existing KG extraction logic
            entities, claims = extract(text.strip())

            # Format claims for tool output
            claim_texts: list[str] = []
            for claim in claims:
                claim_text = claim.text.strip()
                if claim_text and len(claim_text) > MIN_CLAIM_LEN:  # Filter out very short matches
                    claim_texts.append(claim_text)

            return {"status": "success", "claims": claim_texts, "count": len(claim_texts)}

        except Exception as e:  # pragma: no cover - defensive
            return {"status": "error", "claims": [], "error": str(e)}

    def run(self, text: str) -> dict[str, object]:  # pragma: no cover - thin wrapper
        return self._run(text)


__all__ = ["ClaimExtractorTool"]
