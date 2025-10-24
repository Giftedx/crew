"""Offline-safe RAG tool: TF-IDF cosine over provided documents.

This tool does not perform any network calls or rely on external indexes.
It accepts a list of documents and a query string, computes simple TF-IDF
vectors with a naive tokenizer and stopword list, and returns the top-K
matching documents by cosine similarity.

Contract:
- run(query: str, documents: list[str], top_k: int = 3) -> StepResult
  data := { "hits": [{"index": int, "score": float, "snippet": str}], "count": int }
"""

# isort: skip_file

from __future__ import annotations

import math
from dataclasses import dataclass

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from .._base import BaseTool
from typing import TYPE_CHECKING
import contextlib

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


def _default_stopwords() -> set[str]:
    return {
        "the",
        "a",
        "an",
        "and",
        "or",
        "is",
        "to",
        "of",
        "in",
        "on",
        "for",
        "with",
        "as",
        "by",
        "it",
        "this",
        "that",
        "be",
        "are",
        "was",
        "were",
        "at",
        "from",
        "but",
        "not",
        "have",
        "has",
        "had",
        "you",
        "we",
    }


def _tokenize(text: str) -> list[str]:
    return [w.strip(".,!?;:\"'()[]{} ").lower() for w in text.split()]


def _terms(words: Iterable[str]) -> list[str]:
    stop = _default_stopwords()
    out: list[str] = []
    for w in words:
        if not w or not w.isalpha() or w in stop:
            continue
        out.append(w)
    return out


def _tf(tokens: Sequence[str]) -> dict[str, float]:
    total = float(len(tokens)) or 1.0
    counts: dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    return {t: c / total for t, c in counts.items()}


def _idf(doc_tokens: list[list[str]]) -> dict[str, float]:
    N = float(len(doc_tokens)) or 1.0
    df: dict[str, int] = {}
    for toks in doc_tokens:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    # Smooth IDF to avoid zero; +1 both numerator and denominator
    return {t: math.log((N + 1.0) / (df_t + 1.0)) + 1.0 for t, df_t in df.items()}


def _tfidf(tf: dict[str, float], idf: dict[str, float]) -> dict[str, float]:
    return {t: tf_val * idf.get(t, 0.0) for t, tf_val in tf.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    # Only intersect keys matter for numerator
    common = set(a.keys()) & set(b.keys())
    num = sum(a[k] * b[k] for k in common)
    den_a = math.sqrt(sum(v * v for v in a.values())) or 1e-12
    den_b = math.sqrt(sum(v * v for v in b.values())) or 1e-12
    return float(num / (den_a * den_b))


@dataclass
class _Hit:
    index: int
    score: float
    snippet: str


def _rank(query: str, documents: list[str], top_k: int) -> list[_Hit]:
    # Prepare doc tokens and IDF
    docs_terms = [_terms(_tokenize(doc)) for doc in documents]
    idf = _idf(docs_terms) if documents else {}

    # Compute doc tf-idf vectors
    doc_vecs = [_tfidf(_tf(toks), idf) if toks else {} for toks in docs_terms]

    # Query vector
    q_terms = _terms(_tokenize(query))
    q_vec = _tfidf(_tf(q_terms), idf) if q_terms else {}

    scores = []
    for i, (doc, vec) in enumerate(zip(documents, doc_vecs, strict=False)):
        s = _cosine(q_vec, vec) if q_vec and vec else 0.0
        snippet = doc[:240].replace("\n", " ")
        scores.append(_Hit(index=i, score=round(float(s), 6), snippet=snippet))
    scores.sort(key=lambda h: h.score, reverse=True)
    return scores[: max(1, top_k)]


class OfflineRAGTool(BaseTool[StepResult]):
    name: str = "Offline RAG Tool"
    description: str = "Rank provided documents against a query using TF-IDF cosine (offline)."

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def run(self, query: str, documents: list[str], top_k: int = 3) -> StepResult:  # pragma: no cover - thin wrapper
        # Validate inputs conservatively
        if not isinstance(documents, list) or any(not isinstance(d, str) for d in documents):
            return StepResult.fail("Invalid params: documents must be a list of strings")
        try:
            top_k = int(top_k)
            if top_k <= 0 or top_k > 25:
                top_k = 3
        except Exception:
            top_k = 3
        try:
            hits = _rank(query or "", documents, top_k)
            data = {"hits": [h.__dict__ for h in hits], "count": len(hits)}
            with contextlib.suppress(Exception):
                self._metrics.counter(
                    "tool_runs_total",
                    labels={"tool": "offline_rag", "outcome": "success"},
                ).inc()
            return StepResult.ok(data=data)
        except Exception as exc:
            with contextlib.suppress(Exception):
                self._metrics.counter(
                    "tool_runs_total",
                    labels={"tool": "offline_rag", "outcome": "error"},
                ).inc()
            return StepResult.fail(error=str(exc), data={"hits": [], "count": 0})
