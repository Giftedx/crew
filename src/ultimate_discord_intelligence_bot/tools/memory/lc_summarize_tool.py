"""Lightweight summarization tool (LangChain-style) with offline fallback.

Design:
- Attempts to use langchain text splitters if available for nicer chunking.
- Offline extractive summarization: score sentences by word frequency and
  pick top-K distinct sentences preserving original order.
- Returns StepResult with a compact summary and selected sentences.

No external network calls; safe in offline CI.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ._base import BaseTool
from typing import TYPE_CHECKING
import contextlib
if TYPE_CHECKING:
    from collections.abc import Iterable

def _try_split_sentences(text: str) -> list[str]:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(separators=['. ', '! ', '? ', '\n'], chunk_size=400, chunk_overlap=0)
        chunks = splitter.split_text(text)
        out: list[str] = []
        for ch in chunks:
            for s in ch.replace('\n', ' ').split('. '):
                s = s.strip()
                if s:
                    out.append(s if s.endswith(('.', '!', '?')) else s + '.')
        return out or [text]
    except Exception:
        tmp = text.replace('?', '.').replace('!', '.').replace('\n', ' ')
        return [s.strip() + '.' for s in tmp.split('.') if s.strip()]

def _default_stopwords() -> set[str]:
    return {'the', 'a', 'an', 'and', 'or', 'is', 'to', 'of', 'in', 'on', 'for', 'with', 'as', 'by', 'it', 'this', 'that', 'be', 'are', 'was', 'were', 'at', 'from', 'but', 'not', 'have', 'has', 'had', 'you', 'we'}

def _tokenize_words(text: str) -> list[str]:
    return [w.strip('.,!?;:"\'()[]{} ').lower() for w in text.split()]

def _word_frequencies(text: str, stop: Iterable[str]) -> dict[str, int]:
    freq: dict[str, int] = {}
    for w in _tokenize_words(text):
        if not w or w in stop or (not w.isalpha()):
            continue
        freq[w] = freq.get(w, 0) + 1
    return freq

def _score_sentence(sentence: str, freq: dict[str, int]) -> float:
    words = [w for w in _tokenize_words(sentence) if w.isalpha()]
    if not words:
        return 0.0
    score = sum((freq.get(w, 0) for w in words)) / math.sqrt(len(words))
    return float(score)

@dataclass
class _SummaryResult:
    summary: str
    sentences: list[str]

def _summarize(text: str, max_sentences: int) -> _SummaryResult:
    sentences = _try_split_sentences(text)
    if len(sentences) <= max_sentences:
        summary = ' '.join(sentences)
        return _SummaryResult(summary=summary, sentences=sentences)
    stop = _default_stopwords()
    freq = _word_frequencies(text, stop)
    scored = [(idx, s, _score_sentence(s, freq)) for idx, s in enumerate(sentences)]
    top = sorted(sorted(scored, key=lambda x: x[2], reverse=True)[:max_sentences], key=lambda x: x[0])
    chosen = [s for _, s, _ in top]
    summary = ' '.join(chosen)
    return _SummaryResult(summary=summary, sentences=chosen)

class LCSummarizeTool(BaseTool[StepResult]):
    name: str = 'LangChain Summarize Tool'
    description: str = 'Summarize long text into a concise set of key sentences (offline, extractive).'

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def run(self, *args, **kwargs) -> StepResult:
        text = str(args[0]) if args and len(args) > 0 else str(kwargs.get('text', kwargs.get('content', '')))
        try:
            max_sentences = int(max(1, min(10, int(kwargs.get('max_sentences', 3)))))
        except Exception:
            max_sentences = 3
        try:
            if not text.strip():
                with contextlib.suppress(Exception):
                    self._metrics.counter('tool_runs_total', labels={'tool': 'lc_summarize', 'outcome': 'skipped'}).inc()
            if not text.strip():
                return StepResult.skip(reason='empty text', data={'summary': '', 'sentences': [], 'count': 0})
            res = _summarize(text or '', max_sentences)
            data = {'summary': res.summary, 'sentences': res.sentences, 'count': len(res.sentences)}
            with contextlib.suppress(Exception):
                self._metrics.counter('tool_runs_total', labels={'tool': 'lc_summarize', 'outcome': 'success'}).inc()
            return StepResult.ok(data=data)
        except Exception as exc:
            with contextlib.suppress(Exception):
                self._metrics.counter('tool_runs_total', labels={'tool': 'lc_summarize', 'outcome': 'error'}).inc()
            return StepResult.fail(error=str(exc), data={'summary': '', 'sentences': []})