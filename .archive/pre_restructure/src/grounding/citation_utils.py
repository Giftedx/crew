"""Citation formatting utilities.

Central helper to append ordered numeric bracketed citations to an answer
string in a consistent, testable way. This enforces the platform contract
that grounded answers MUST include ordered numeric citations at the tail:

    "Some grounded answer text. [1][2][3]"

Rules / behaviors:
1. If no citations provided -> return original answer unchanged.
2. Citations are appended as a single space + concatenated tokens "[n]" in
   1-index order matching the provided list order.
3. If the answer already ends with an exact matching contiguous citation tail
   for the provided citations, we do not duplicate (idempotent).
4. If the answer ends with a different citation tail (length mismatch or
   numbering not matching count) we append a fresh tail (we do NOT try to
   surgically remove the old one to avoid over-aggressive mutation; upstream
   code should supply the raw model answer before citation formatting).
5. Ensures there is exactly one space separating answer body and first
   citation token (unless answer empty, then returns just the citations).

Edge cases handled:
- Empty answer -> returns "[1]..."? We choose to keep contract that citations
  annotate an answer body; if answer is empty, just return the citation tail
  (space skipped) so downstream can still show provenance. This is rare but
  simplifies invariants.

NOTE: We intentionally keep this utility free of model / tenant context so it
can be imported in tests and lightweight pipelines without circular imports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Sequence

    from .schema import Evidence


__all__ = ["append_numeric_citations"]


def _build_tail(count: int) -> str:
    return "".join(f"[{i}]" for i in range(1, count + 1))


def _existing_tail_matches(answer: str, count: int) -> bool:
    if count <= 0:
        return False
    tail = _build_tail(count)
    # Allow optional leading space before tail
    if answer.endswith(tail):
        prefix = answer[: -len(tail)]
        if not prefix or prefix.endswith(" "):
            return True
    return False


def append_numeric_citations(answer: str, citations: Sequence[Evidence]) -> str:
    """Return answer with ordered numeric bracketed citations appended.

    Parameters
    ----------
    answer: str
        The answer text (unformatted / raw model output).
    citations: Sequence[Evidence]
        Ordered evidence objects to cite. Order is preserved; numbering is
        1-indexed in that order.

    Returns
    -------
    str
        Answer with citation tail appended (idempotent if already present and
        matching length/order).
    """
    count = len(citations)
    if count == 0:
        return answer

    if _existing_tail_matches(answer, count):
        return answer  # Idempotent

    tail = _build_tail(count)

    if not answer:
        return tail

    # Normalize spacing: strip trailing whitespace then add single space.
    answer_stripped = answer.rstrip()
    return f"{answer_stripped} {tail}"


# Minimal self-test (not executed in prod, helpful if imported in REPL)
if __name__ == "__main__":  # pragma: no cover - manual sanity
    from dataclasses import dataclass

    @dataclass
    class _E:  # lightweight stand-in if Evidence import fails in isolation
        quote: str | None = None

    examples = [
        ("Answer", [_E(), _E()], "Answer [1][2]"),
        ("Answer [1][2]", [_E(), _E()], "Answer [1][2]"),
        ("Answer [1]", [_E(), _E()], "Answer [1] [1][2]"),
        ("", [_E()], "[1]"),
    ]
    for a, cites, exp in examples:
        out = append_numeric_citations(a, cites)  # type: ignore[arg-type]
        if out != exp:
            raise SystemExit(f"Sanity mismatch: {a=!r} expected {exp!r} got {out!r}")
    print("citation_utils sanity OK")
