"""Research and brief tool (offline-safe core).

Synthesizes an outline and key findings from provided text sources. URL fetching is
reserved for a future extension and will be guarded by a feature flag; this tool's
default path operates only on provided texts to keep CI deterministic.

Inputs:
- query: str
- sources_text: list[str] | None
- max_items: int = 5 (cap number of findings/outline bullets)

Outputs:
- StepResult.ok with data: {
    outline: list[str],
    key_findings: list[str],
    citations: list[{ type: "text", index: int }],
    risks: list[str],
    counts: { sources: int, tokens_estimate: int },
  }

Notes:
- Designed so we can later swap internals to CrewAI/AutoGen orchestration with strict limits.
"""

from __future__ import annotations

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


def _split_sentences(text: str) -> list[str]:
    # Minimal sentence splitter (period/exclamation/question) with trimming
    parts = []
    buf = []
    for ch in text:
        buf.append(ch)
        if ch in ".!?":
            s = "".join(buf).strip()
            if s:
                parts.append(s)
            buf = []
    if buf:
        s = "".join(buf).strip()
        if s:
            parts.append(s)
    return [p.replace("\n", " ").strip() for p in parts if p.strip()]


def _score_sentences(sentences: list[str], query: str) -> list[tuple[float, str]]:
    # Lightweight scoring: term overlap with query
    q_terms = set(t for t in query.lower().split() if t.isalpha())
    scored: list[tuple[float, str]] = []
    for s in sentences:
        terms = [t for t in s.lower().split() if t.isalpha()]
        overlap = len(q_terms.intersection(terms)) if q_terms else 0
        score = overlap / (1 + len(terms))
        scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


class ResearchAndBriefTool(BaseTool[StepResult]):
    name: str = "Research and Brief Tool"
    description: str = "Synthesize an outline and key findings from provided text sources (offline-safe)."

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def run(self, *, query: str, sources_text: list[str] | None = None, max_items: int = 5) -> StepResult:
        if sources_text is not None and (
            not isinstance(sources_text, list) or any(not isinstance(t, str) for t in sources_text)
        ):
            return StepResult.fail("Invalid params: sources_text must be a list of strings or null")
        try:
            max_items = int(max_items)
            if max_items <= 0 or max_items > 10:
                max_items = 5
        except Exception:
            max_items = 5

        texts = [t for t in (sources_text or []) if isinstance(t, str) and t.strip()]
        if not texts:
            # Empty sources: produce an uncertain result rather than hard-fail
            data = {
                "outline": [],
                "key_findings": [],
                "citations": [],
                "risks": ["Insufficient sources provided; findings may be incomplete."],
                "counts": {"sources": 0, "tokens_estimate": 0},
            }
            return StepResult.uncertain(data=data)

        # Extract candidate sentences across sources
        sentences: list[tuple[int, str]] = []
        token_count = 0
        for idx, t in enumerate(texts):
            token_count += len(t.split())
            for s in _split_sentences(t):
                sentences.append((idx, s))

        # Score and select top sentences for findings
        scored = _score_sentences([s for _, s in sentences], query)
        top = scored[:max_items]
        key_findings = [s for _, s in top]

        # Outline heuristics: convert to concise bullets (truncate)
        outline = []
        for s in key_findings:
            # Shorten overly long sentences for outline
            o = s
            if len(o) > 200:
                o = o[:197] + "..."
            outline.append(o)

        # Citations: map top sentences back to source indexes
        text_to_index: dict[str, int] = {}
        for idx, s in sentences:
            if s not in text_to_index:
                text_to_index[s] = idx
        citations = []
        for s in key_findings:
            src_idx = text_to_index.get(s, 0)
            citations.append({"type": "text", "index": int(src_idx)})

        # Risks: simplistic flags
        risks = []
        if len(texts) < 2:
            risks.append("Single source used; low diversity of evidence.")
        if token_count < 50:
            risks.append("Very small corpus; conclusions may be brittle.")

        data = {
            "outline": outline,
            "key_findings": key_findings,
            "citations": citations,
            "risks": risks,
            "counts": {"sources": len(texts), "tokens_estimate": token_count},
        }
        try:
            self._metrics.counter("tool_runs_total", labels={"tool": "research_and_brief", "outcome": "success"}).inc()
        except Exception:
            pass
        return StepResult.ok(data=data)


__all__ = ["ResearchAndBriefTool"]
