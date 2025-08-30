"""Privacy flag matrix tests.

Validates combinations of detection/redaction feature flags and the RL
"strict" arm override path forcing both behaviors on regardless of context.
"""

from __future__ import annotations

from core.privacy import privacy_filter

SAMPLE = "Contact me at alice@example.com or 555-123-4567 for details."


def _span_types(spans):
    return {s.type for s in spans}


def test_detection_and_redaction_enabled():
    redacted, report = privacy_filter.filter_text(
        SAMPLE,
        {"enable_detection": True, "enable_redaction": True},
    )
    assert report.found, "Expected PII spans when detection enabled"
    assert redacted != SAMPLE, "Redaction should modify text when enabled and spans found"
    assert "email" in _span_types(report.found) or "phone" in _span_types(report.found)


def test_detection_enabled_redaction_disabled():
    clean, report = privacy_filter.filter_text(
        SAMPLE,
        {"enable_detection": True, "enable_redaction": False},
    )
    assert report.found, "Expected spans with detection on"
    assert clean == SAMPLE, "Text should remain unchanged when redaction disabled"


def test_detection_disabled():
    clean, report = privacy_filter.filter_text(
        SAMPLE,
        {"enable_detection": False, "enable_redaction": True},
    )
    assert not report.found, "No spans expected when detection disabled"
    assert clean == SAMPLE


class _StrictLearning:
    def recommend(self, domain, ctx, arms):  # noqa: D401 - simple stub
        return "strict"

    def record(self, domain, ctx, arm, reward):  # noqa: D401 - stub
        pass


def test_strict_arm_forces_detection_and_redaction():
    # Even if context disables flags, 'strict' arm should override
    redacted, report = privacy_filter.filter_text(
        SAMPLE,
        {"enable_detection": False, "enable_redaction": False},
        learning=_StrictLearning(),
    )
    # With strict, detection forced True; ensure result differs and spans present
    assert report.found, "Strict arm should force detection"
    assert redacted != SAMPLE, "Strict arm should force redaction"
