from __future__ import annotations

"""Simple verifier that checks :class:`AnswerContract` objects."""

from dataclasses import dataclass
from typing import List

from .contracts import load_config
from .schema import AnswerContract


@dataclass
class VerifierReport:
    verdict: str
    missing_citations: List[int]
    contradictions: List[str]
    suggested_fixes: List[str]
    confidence: float


def verify(contract: AnswerContract, *, use_case: str, tenant: str | None = None) -> VerifierReport:
    """Verify ``contract`` against config rules."""

    cfg = load_config(tenant)
    rules = cfg.commands.get(use_case, cfg.defaults)
    min_cit = int(rules.get("min_citations", 1))
    if len(contract.citations) < min_cit:
        missing = list(range(len(contract.citations) + 1, min_cit + 1))
        return VerifierReport(
            verdict="fail",
            missing_citations=missing,
            contradictions=[],
            suggested_fixes=["add more citations"],
            confidence=0.0,
        )
    return VerifierReport(
        verdict="pass",
        missing_citations=[],
        contradictions=[],
        suggested_fixes=[],
        confidence=1.0,
    )


__all__ = ["verify", "VerifierReport"]
