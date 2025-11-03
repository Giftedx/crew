"""High-level privacy filter that combines policy checks and redaction.

Docstring precedes future import per Ruff E402.
"""

from __future__ import annotations

from dataclasses import dataclass
from platform import flags
from typing import Any


try:
    from platform.rl.learning_engine import LearningEngine
except Exception:

    class LearningEngine:
        def recommend(self, *_args, **_kwargs) -> str:
            return "lenient"

        def record(self, *_args, **_kwargs) -> None:
            return None


from policy import policy_engine

from . import pii_detector, redactor


@dataclass
class PrivacyReport:
    found: list[pii_detector.Span]
    redacted_by_type: dict[str, int]
    decisions: list[policy_engine.Decision]


def filter_text(
    text: str, context: dict[str, Any] | None = None, learning: LearningEngine | None = None, domain: str = "safety"
) -> tuple[str, PrivacyReport]:
    if not text or text.strip() == "":
        return (text, PrivacyReport([], {}, []))
    ctx = context or {}
    policy = policy_engine.load_policy(ctx.get("tenant"))
    decisions = []
    source_keys = ("source_platform", "type")
    if any(k in ctx for k in source_keys):
        src_dec = policy_engine.check_source(ctx, policy)
        decisions.append(src_dec)
        if src_dec.decision == "block":
            return (text, PrivacyReport([], {}, decisions))
    payload_dec = policy_engine.check_payload(text, ctx, policy)
    decisions.append(payload_dec)
    if payload_dec.decision == "block":
        return (text, PrivacyReport([], {}, decisions))
    engine = learning or LearningEngine()
    try:
        arm = engine.recommend(domain, ctx, ["strict", "lenient"])
        registered = True
    except KeyError:
        arm = "lenient"
        registered = False
    detect_enabled = ctx.get("enable_detection", flags.enabled("enable_pii_detection", True))
    redact_enabled = ctx.get("enable_redaction", flags.enabled("enable_pii_redaction", True))
    if arm == "strict":
        detect_enabled = True
        redact_enabled = True
    spans = pii_detector.detect(text) if detect_enabled else []
    redacted = redactor.apply(text, spans, policy.masks) if spans and redact_enabled else text
    counts: dict[str, int] = {}
    for s in spans:
        counts[s.type] = counts.get(s.type, 0) + 1
    if registered:
        engine.record(domain, ctx, arm, 1.0 if spans else 0.5)
    return (redacted, PrivacyReport(spans, counts, decisions))


__all__ = ["PrivacyReport", "filter_text"]
