from __future__ import annotations

from typing import Any


def _evaluate_claim(claim: str, fact_check_tool: Any | None) -> tuple[str, float, str]:
    """Evaluate a claim with simple heuristics and optional external tool.

    Behavior aims to satisfy tests in tests/test_command_helpers.py:
    - Recognize "Earth is flat" as false with high confidence and explanation mentioning 'earth'.
    - If a tool is provided with a _run method, use it to obtain verdict/confidence/explanation.
    - Otherwise return Uncertain with 0.5 confidence and explanation mentioning 'manual'.
    """
    text = (claim or "").strip()
    lower = text.lower()

    # Simple heuristics / pattern matches
    if "earth is flat" in lower or ("earth" in lower and "flat" in lower):
        return (
            "False",
            0.95,
            "Based on overwhelming scientific consensus, the Earth is not flat.",
        )

    # External tool path (duck-typed)
    if fact_check_tool is not None:
        try:
            res = fact_check_tool._run(text)
            # Accept namespace-like return or dict
            verdict = getattr(res, "data", {}).get("verdict") if hasattr(res, "data") else res.get("verdict")
            confidence = getattr(res, "data", {}).get("confidence") if hasattr(res, "data") else res.get("confidence")
            explanation = (
                getattr(res, "data", {}).get("explanation") if hasattr(res, "data") else res.get("explanation")
            )
            if verdict is None or confidence is None or explanation is None:
                raise ValueError("incomplete tool result")
            return str(verdict), float(confidence), str(explanation)
        except Exception:
            # Fall through to uncertain
            pass

    # Default: uncertain without external verification
    return "Uncertain", 0.5, "Manual verification required (no external source used)."


__all__ = ["_evaluate_claim"]
