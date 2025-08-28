"""Extract factual claims from text using NLP patterns."""

from __future__ import annotations

from crewai.tools import BaseTool

# Import the KG extraction utilities
from kg.extract import extract


class ClaimExtractorTool(BaseTool):
    """Extract factual claims from text using regex patterns and NLP."""

    name: str = "Claim Extractor Tool" 
    description: str = "Extract potential factual claims from text using linguistic patterns."

    def _run(self, text: str) -> dict:
        """Extract claims using the KG extraction module."""
        if not text or not text.strip():
            return {"status": "success", "claims": []}
        
        try:
            # Use existing KG extraction logic
            entities, claims = extract(text.strip())
            
            # Format claims for tool output
            claim_texts = []
            for claim in claims:
                claim_text = claim.text.strip()
                if claim_text and len(claim_text) > 5:  # Filter out very short matches
                    claim_texts.append(claim_text)
            
            return {
                "status": "success", 
                "claims": claim_texts,
                "count": len(claim_texts)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "claims": [],
                "error": str(e)
            }

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)


__all__ = ["ClaimExtractorTool"]

