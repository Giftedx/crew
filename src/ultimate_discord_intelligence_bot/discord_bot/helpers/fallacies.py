from __future__ import annotations


def _fallacy_database() -> dict[tuple[str, ...], tuple[str, str]]:
    """Return the minimal fallacy pattern database used by tests.

    Keys are tuples of trigger substrings (lowercased). Values are
    (Label, Explanation). Keep deterministic and lightweight.
    """
    return {
        (
            "everyone knows",
            "most people think",
            "common sense says",
        ): (
            "Appeal to Popularity",
            "Asserts truth based on popularity rather than evidence.",
        ),
        (
            "will end if we allow",
            "if we allow this",
            "slippery slope",
        ): (
            "Slippery Slope",
            "Claims a small step inevitably leads to extreme outcomes.",
        ),
        (
            "you're stupid",
            "idiot",
            "moron",
        ): (
            "Ad Hominem",
            "Attacks the person rather than addressing the argument.",
        ),
        (
            "because i said so",
            "as i said",
            "trust me, i'm an expert",
        ): (
            "Appeal to Authority",
            "Uses authority or assertion in place of evidence.",
        ),
    }


def _detect_fallacies(text: str) -> list[tuple[str, str]]:
    """Detect rhetorical fallacies via simple substring checks.

    Returns a list of (label, explanation) pairs for each detected fallacy.
    """
    if not isinstance(text, str) or not text:
        return []
    t = text.lower()
    results: list[tuple[str, str]] = []
    for triggers, (label, explanation) in _fallacy_database().items():
        if any(trig in t for trig in triggers):
            results.append((label, explanation))
    return results


__all__ = ["_fallacy_database", "_detect_fallacies"]
