from __future__ import annotations

"""Simple verifier that checks :class:`AnswerContract` objects."""

from dataclasses import dataclass

from . import consistency
from .contracts import load_config
from .schema import AnswerContract


@dataclass
class VerifierReport:
    verdict: str
    missing_citations: list[int]
    contradictions: list[str]
    suggested_fixes: list[str]
    confidence: float


def verify(contract: AnswerContract, *, use_case: str, tenant: str | None = None) -> VerifierReport:
    """Verify ``contract`` against config rules."""

    cfg = load_config(tenant)
    rules = cfg.commands.get(use_case, cfg.defaults)
    min_cit = int(rules.get("min_citations", 1))

    # Check for contradictions using the consistency module
    contradictions = consistency.check(contract)

    # Initialize suggested fixes list
    suggested_fixes = []

    # Check minimum citations
    missing_citations = []
    if len(contract.citations) < min_cit:
        missing_citations = list(range(len(contract.citations) + 1, min_cit + 1))
        suggested_fixes.append("add more citations")

    # Add fix suggestions for contradictions
    if contradictions:
        suggested_fixes.append("resolve contradictions in evidence or answer text")

    # Calculate verdict
    if missing_citations or contradictions:
        verdict = "fail"
        confidence = 0.0
    else:
        verdict = "pass"
        confidence = 1.0

    return VerifierReport(
        verdict=verdict,
        missing_citations=missing_citations,
        contradictions=contradictions,
        suggested_fixes=suggested_fixes,
        confidence=confidence,
    )


__all__ = ["verify", "VerifierReport"]
