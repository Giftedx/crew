from __future__ import annotations

"""High-level privacy filter combining policy checks and redaction."""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from ..policy import policy_engine
from . import pii_detector, redactor


@dataclass
class PrivacyReport:
    found: List[pii_detector.Span]
    redacted: bool
    policy_decision: policy_engine.PolicyDecision


def filter_text(text: str, context: Dict[str, Any] | None = None) -> Tuple[str, PrivacyReport]:
    """Return ``text`` sanitized of PII according to loaded policy."""
    policy = policy_engine.load_policy()
    decision = policy_engine.check_payload(text, policy)
    spans = pii_detector.detect(text) if decision.decision != "block" else []
    cleaned = redactor.apply(text, spans, policy.redaction_rules) if spans else text
    report = PrivacyReport(found=spans, redacted=bool(spans), policy_decision=decision)
    return cleaned, report

