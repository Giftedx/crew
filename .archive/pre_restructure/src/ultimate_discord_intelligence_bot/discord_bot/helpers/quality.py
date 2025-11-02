from __future__ import annotations


def assess_response_quality(text: str) -> float:
    """Heuristic quality score in [0,1] for response text.

    Simple signal mix:
    - Very short or contains the word 'error' -> low score.
    - Presence of signal words (evidence, sources, verified, analysis, reasoning, data, research)
      increases score.
    - Mild length normalization up to a cap.
    Deterministic and side-effect-free to keep tests stable.
    """
    if not text:
        return 0.0
    t = text.strip()
    lower = t.lower()
    if "error" in lower:
        return 0.1
    base = 0.0
    signals = {
        "evidence": 0.15,
        "sources": 0.15,
        "verified": 0.15,
        "analysis": 0.15,
        "reasoning": 0.15,
        "data": 0.1,
        "research": 0.1,
    }
    for k, w in signals.items():
        if k in lower:
            base += w
    # Length component (up to ~800 chars contributes meaningfully)
    length_bonus = min(len(t) / 800.0, 1.0) * 0.4
    score = base + length_bonus
    # Clamp
    return max(0.0, min(1.0, score))


__all__ = ["assess_response_quality"]
