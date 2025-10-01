from __future__ import annotations

# Re-export helper functions for convenience if callers import the package.
from .evaluation import _evaluate_claim
from .fallacies import _detect_fallacies, _fallacy_database
from .platform import _infer_platform
from .quality import assess_response_quality

__all__ = [
    "_infer_platform",
    "_evaluate_claim",
    "_fallacy_database",
    "_detect_fallacies",
    "assess_response_quality",
]
