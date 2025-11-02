from dataclasses import dataclass

from grounding.citation_utils import append_numeric_citations


@dataclass
class Evidence:  # Lightweight stand-in matching required interface (quote optional)
    quote: str | None = None


def test_append_citations_basic():
    cites = [Evidence(), Evidence(), Evidence()]
    out = append_numeric_citations("Answer body", cites)
    assert out == "Answer body [1][2][3]"


def test_append_citations_idempotent():
    cites = [Evidence(), Evidence()]
    first = append_numeric_citations("Answer", cites)
    second = append_numeric_citations(first, cites)
    assert first == second == "Answer [1][2]"


def test_append_citations_empty_answer():
    cites = [Evidence()]
    out = append_numeric_citations("", cites)
    assert out == "[1]"


def test_append_citations_mismatch_existing_tail():
    # Existing tail shorter should trigger re-append (non-destructive)
    cites = [Evidence(), Evidence()]
    out = append_numeric_citations("Answer [1]", cites)
    # We do not attempt tail removal; we append a fresh tail separated by space
    assert out.endswith("[1] [1][2]")
    assert out.startswith("Answer")
