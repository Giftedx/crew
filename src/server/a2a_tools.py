"""Helpers for A2A adapter: feature flags, API key check, and tool registry.

This module isolates environment-driven toggles and the dynamic tool registry
to keep the main router simple and focused on FastAPI endpoint wiring.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any


try:
    from ultimate_discord_intelligence_bot.step_result import StepResult  # type: ignore
except Exception:  # pragma: no cover - lightweight stub for local/dev

    class StepResult:  # type: ignore
        def __init__(self, success: bool, data: Any | None = None, error: str | None = None):
            self.success = success
            self.data = data
            self.error = error

        @classmethod
        def ok(cls, data: Any | None = None):
            return cls(True, data=data)

        @classmethod
        def fail(cls, error: str, data: Any | None = None):
            return cls(False, data=data, error=error)


ToolFunc = Callable[..., StepResult]


def is_enabled(name: str, default: bool = False) -> bool:
    """Read boolean-like env var with sensible defaults.

    Recognizes 1/true/yes/on (case-insensitive) as truthy.
    """
    return os.getenv(name, "1" if default else "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def api_key_ok(header_val: str | None) -> bool:
    """Validate API key if enabled via env flag.

    ENABLE_A2A_API_KEY=1 and A2A_API_KEY="k1,k2" (comma separated) enable check.
    When disabled, always returns True.
    """
    if not is_enabled("ENABLE_A2A_API_KEY", False):
        return True
    expected = os.getenv("A2A_API_KEY")
    if expected is None:
        return False
    allowed = {p.strip() for p in expected.split(",") if p.strip()}
    return header_val is not None and header_val in allowed


def load_tools() -> dict[str, ToolFunc]:  # pragma: no cover - resolved dynamically and tested via endpoints
    """Build dynamic tool registry based on runtime flags and availability.

    Provides offline-safe fallbacks for a subset of tools to keep JSON-RPC usable
    without heavy optional dependencies.
    """
    tools: dict[str, ToolFunc] = {}

    # Simple demo analyzer
    def _text_analyze(text: str) -> StepResult:
        text = str(text or "")
        words = text.split()
        data = {"length": len(text), "words": len(words), "preview": text[:64]}
        return StepResult.ok(data=data)

    tools["tools.text_analyze"] = _text_analyze

    # Optional skills based on flags; import lazily
    if is_enabled("ENABLE_A2A_SKILL_SUMMARIZE", True):
        try:
            from ultimate_discord_intelligence_bot.tools.lc_summarize_tool import (  # type: ignore
                summarize as lc_summarize,
            )

            tools["tools.lc_summarize"] = lc_summarize  # type: ignore[assignment]
        except Exception:
            # Offline-safe fallback summarizer: pick first N sentences
            def _summarize(text: str, max_sentences: int = 3) -> StepResult:
                text = str(text or "").strip()
                import re

                # naive sentence split
                sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
                chosen = sentences[: max(1, int(max_sentences or 3))]
                summary = " ".join(chosen)
                data = {"summary": summary, "sentences": chosen, "count": len(chosen)}
                return StepResult.ok(data=data)

            tools["tools.lc_summarize"] = _summarize

    if is_enabled("ENABLE_A2A_SKILL_RAG_OFFLINE", True):
        try:
            from ultimate_discord_intelligence_bot.tools.rag_offline_tool import (
                rag_query,
            )  # type: ignore

            tools["tools.rag_query"] = rag_query  # type: ignore[assignment]
        except Exception:
            # Offline TF-IDF-lite fallback using Jaccard similarity
            def _rag_query(query: str, documents: list[str], top_k: int = 3) -> StepResult:
                if not isinstance(documents, list):
                    return StepResult.fail(
                        "Invalid params for tools.rag_query: documents must be a list",
                        data={},
                    )
                q_tokens = {t.lower() for t in str(query or "").split() if t}
                hits: list[dict[str, Any]] = []
                for idx, doc in enumerate(documents):
                    d_tokens = {t.lower() for t in str(doc or "").split() if t}
                    inter = len(q_tokens & d_tokens)
                    union = len(q_tokens | d_tokens) or 1
                    score = inter / union
                    hits.append({"index": idx, "score": score, "snippet": str(doc)[:120]})
                hits.sort(key=lambda x: x["score"], reverse=True)
                hits = hits[: max(1, int(top_k or 3))]
                return StepResult.ok(data={"hits": hits, "count": len(hits)})

            tools["tools.rag_query"] = _rag_query

    if is_enabled("ENABLE_A2A_SKILL_RAG_VECTOR", True):
        try:
            from ultimate_discord_intelligence_bot.tools.rag_vector_tool import (
                rag_query_vs,
            )  # type: ignore

            tools["tools.rag_query_vs"] = rag_query_vs  # type: ignore[assignment]
        except Exception:
            pass

    if is_enabled("ENABLE_A2A_SKILL_RAG_INGEST", False):
        try:
            from ultimate_discord_intelligence_bot.tools.rag_ingest_tool import (
                rag_ingest,
            )  # type: ignore

            tools["tools.rag_ingest"] = rag_ingest  # type: ignore[assignment]
        except Exception:
            pass

    if is_enabled("ENABLE_A2A_SKILL_RAG_INGEST_URL", False):
        try:
            from ultimate_discord_intelligence_bot.tools.rag_ingest_url_tool import (
                rag_ingest_url,
            )  # type: ignore

            tools["tools.rag_ingest_url"] = rag_ingest_url  # type: ignore[assignment]
        except Exception:
            pass

    if is_enabled("ENABLE_A2A_SKILL_RAG_HYBRID", True):
        try:
            from ultimate_discord_intelligence_bot.tools.rag_hybrid_tool import (
                rag_hybrid,
            )  # type: ignore

            tools["tools.rag_hybrid"] = rag_hybrid  # type: ignore[assignment]
        except Exception:
            pass

    if is_enabled("ENABLE_A2A_SKILL_RESEARCH_BRIEF", True):
        try:
            from ultimate_discord_intelligence_bot.tools.research_and_brief_tool import (
                research_and_brief,  # type: ignore
            )

            tools["tools.research_and_brief"] = research_and_brief  # type: ignore[assignment]
        except Exception:
            pass

    # Support both historical and current env flag names
    if is_enabled("ENABLE_A2A_SKILL_RESEARCH_BRIEF_MULTI", False) or is_enabled(
        "ENABLE_A2A_SKILL_RESEARCH_AND_BRIEF_MULTI",
        False,
    ):
        try:
            from ultimate_discord_intelligence_bot.tools.research_and_brief_multi_tool import (
                research_and_brief_multi,
            )  # type: ignore

            tools["tools.research_and_brief_multi"] = research_and_brief_multi  # type: ignore[assignment]
        except Exception:
            # Offline-safe multi-agent fallback producing deterministic brief
            def _multi(
                query: str,
                sources_text: list[str] | None = None,
                max_items: int = 5,
                max_time: float | None = None,
                enable_alerts: bool = False,
            ) -> StepResult:
                q = str(query or "").strip()
                sources = [str(s) for s in (sources_text or [])]
                outline = [f"Overview: {q}"] + [
                    f"Point {i + 1}: {s[:60]}" for i, s in enumerate(sources[: max(0, int(max_items or 5))])
                ]
                key_findings = [s[:80] for s in sources[: max(0, int(max_items or 5))]]
                citations = [{"type": "source", "index": i} for i in range(len(key_findings))]
                risks = ["Limited sources", "Heuristic synthesis"]
                counts = {
                    "sources": len(sources),
                    "tokens_estimate": sum(len(s.split()) for s in sources),
                }
                meta = {
                    "multi_agent": True,
                    "quality_score": None,
                    "execution_time": None,
                }
                data = {
                    "outline": outline or ["Overview"],
                    "key_findings": key_findings or ["No sources provided"],
                    "citations": citations,
                    "risks": risks,
                    "counts": counts,
                    "meta": meta,
                }
                return StepResult.ok(data=data)

            tools["tools.research_and_brief_multi"] = _multi

    return tools


def get_tools() -> dict[str, ToolFunc]:
    """Public accessor used by the router; re-evaluates on each call."""
    return load_tools()


__all__ = ["ToolFunc", "api_key_ok", "get_tools", "is_enabled", "load_tools"]
