"""Lightweight response quality assessment utilities.

This module provides a basic, dependency-free heuristic for assessing LLM
response quality. It is intentionally conservative and fast so it can run on
the critical path without noticeable overhead. Use this to attach a
``quality_assessment`` block to routing results for downstream consumers
(dashboards, post-processors, or evaluators).
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any

from ..prompt_engine import PromptEngine


def _count_tokens(text: str) -> int:
    try:
        # Default to a provider-agnostic estimate
        return PromptEngine().count_tokens(text)
    except Exception:
        return max(1, len(text.split()))


_STOPWORDS = {
    # Tiny stopword set to avoid heavy deps
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "as",
    "by",
    "is",
    "are",
    "was",
    "were",
    "be",
    "this",
    "that",
    "it",
    "at",
    "from",
    "about",
}


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^A-Za-z0-9']+", (text or "").lower()) if w]


def _ngrams(tokens, n: int) -> list[tuple[str, ...]]:
    toks = list(tokens)
    return [tuple(toks[i : i + n]) for i in range(max(0, len(toks) - n + 1))]


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / max(1, union)


def _count_urls(text: str) -> int:
    return len(re.findall(r"https?://\S+", text or ""))


def _count_code_blocks(text: str) -> int:
    return (text or "").count("```")


def _repetition_ratio(text: str) -> float:
    toks = _words(text)
    if len(toks) < 6:
        return 0.0
    bigrams = _ngrams(toks, 2)
    if not bigrams:
        return 0.0
    # fraction of bigrams that appear at least 3 times
    counts: dict[tuple[str, ...], int] = {}
    for bg in bigrams:
        counts[bg] = counts.get(bg, 0) + 1
    repeated = sum(1 for c in counts.values() if c >= 3)
    return repeated / max(1, len(counts))


def _expected_list_count_from_prompt(prompt: str | None) -> int | None:
    if not prompt:
        return None
    p = prompt.lower()
    # Patterns like: list 3, give me 4, top 5, provide 6, 7 steps
    m = re.search(r"(?:list|give\s+me|provide|top|return|show)\s+(\d{1,2})", p)
    if not m:
        m = re.search(r"\b(\d{1,2})\s+(?:items|points|bullets|reasons|steps|tips)\b", p)
    try:
        if m:
            n = int(m.group(1))
            if 1 <= n <= 20:
                return n
    except Exception:
        pass
    return None


def _count_list_items(text: str) -> int:
    count = 0
    for ln in (text or "").splitlines():
        s = ln.lstrip()
        if s.startswith(("- ", "* ")) or re.match(r"^\d+\.\s+", s):
            count += 1
    return count


def _python_blocks_parse_ok(text: str) -> tuple[int, int]:
    """Return (ok_count, total_py_blocks) for fenced python code blocks."""
    total = 0
    ok = 0
    for m in re.finditer(r"```python\n(.*?)```", text or "", flags=re.DOTALL | re.IGNORECASE):
        total += 1
        code = m.group(1)
        try:
            ast.parse(code)
            ok += 1
        except Exception:
            pass
    return ok, total


def _ttr(text: str) -> float:
    toks = [w for w in _words(text) if w not in _STOPWORDS]
    if not toks:
        return 0.0
    return len(set(toks)) / float(len(toks))


def quality_assessment(
    text: str,
    prompt: str | None = None,
    *,
    min_tokens: int = 80,
    expect_json: bool = False,
) -> dict[str, Any]:
    """Advanced, dependency-light assessment for an LLM response.

    - If ``prompt`` is provided, computes a simple relevance proxy via Jaccard
      overlap of non-stopword tokens.
    - If ``expect_json`` is True, validates JSON and adjusts score.
    - Adds repetition and code/explanation balance signals.
    """

    text = (text or "").strip()
    tokens = _count_tokens(text)

    # Signals
    apology_markers = (
        "i'm sorry",
        "i am sorry",
        "cannot assist",
        "can't assist",
        "as an ai",
        "as a language model",
        "i cannot",
        "i can't",
        "i do not have access",
    )
    has_apology = any(m in text.lower() for m in apology_markers)

    structure_markers = (
        "\n- ",
        "\n* ",
        "\n1.",
        "\n2.",
        "\n3.",
        "## ",
        "### ",
        "```",
    )
    has_structure = any(m in text for m in structure_markers)

    url_count = _count_urls(text)
    code_blocks = _count_code_blocks(text)
    rep_ratio = _repetition_ratio(text)
    ttr = _ttr(text)
    exp_list_n = _expected_list_count_from_prompt(prompt)
    list_items = _count_list_items(text)
    py_ok, py_total = _python_blocks_parse_ok(text)

    # Suspicious long runs of non-whitespace separators (likely paths/garbage)
    suspicious_pattern = re.compile(r"\b[a-zA-Z0-9_/\\.-]{20,}\b")
    has_suspicious = bool(suspicious_pattern.search(text)) and url_count == 0

    # JSON validation when expected
    json_valid = False
    if expect_json:
        candidate = text
        # Try to detect fenced json blocks
        m = re.search(r"```json\n(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
        if m:
            candidate = m.group(1)
        try:
            json.loads(candidate)
            json_valid = True
        except Exception:
            json_valid = False

    # Very short one-liners are often low-signal
    length_factor = min(1.0, tokens / max(1.0, float(min_tokens)))

    # Relevance proxy (if prompt provided)
    relevance = 0.0
    if prompt:
        p_words = [w for w in _words(prompt) if w not in _STOPWORDS]
        t_words = [w for w in _words(text) if w not in _STOPWORDS]
        relevance = _jaccard(set(p_words[:50]), set(t_words[:200]))

    # Code vs explanation balance: encourage some narrative with code
    explanation_lines = [ln for ln in (text.splitlines()) if not ln.strip().startswith("```")]
    code_lines = [ln for ln in (text.splitlines()) if ln.strip().startswith("```") or ln.strip().endswith("```")]
    explain_ratio = len(explanation_lines) / max(1, len(explanation_lines) + len(code_lines))
    has_code = code_blocks > 0

    # Compose score from components
    score = 0.0
    score += 0.45 * length_factor
    score += 0.15 * relevance
    score += 0.1 * (1.0 if has_structure else 0.6)
    score += 0.1 * (1.0 if not has_apology else 0.6)
    if expect_json:
        score += 0.05 * (1.0 if json_valid else 0.0)
        if not json_valid:
            score -= 0.1
    # TTR encouragement (discourage extreme repetition while not over-weighting)
    if ttr < 0.2:
        score -= 0.05
    elif ttr >= 0.35:
        score += 0.03
    # Penalties
    if has_suspicious:
        score -= 0.05
    if rep_ratio >= 0.2:
        score -= 0.1
    # Code/explanation balance
    if has_code and explain_ratio < 0.3:
        score -= 0.05
    elif has_code and explain_ratio >= 0.4:
        score += 0.05
    # Python parseability (very light influence)
    if py_total > 0:
        ratio_ok = py_ok / float(py_total)
        if ratio_ok >= 0.75:
            score += 0.03
        elif ratio_ok < 0.25:
            score -= 0.03
    # List-count expectation from prompt
    if exp_list_n is not None:
        if list_items >= exp_list_n:
            score += 0.04
        elif list_items >= max(1, exp_list_n - 1):
            score += 0.02
        else:
            score -= 0.04

    score = max(0.0, min(1.0, score))

    return {
        "score": round(float(score), 3),
        "tokens": int(tokens),
        "min_tokens": int(min_tokens),
        "signals": {
            "has_apology": bool(has_apology),
            "has_structure": bool(has_structure),
            "has_suspicious": bool(has_suspicious),
            "has_code": bool(has_code),
            "url_count": int(url_count),
            "repetition_ratio": round(float(rep_ratio), 3),
            "json_valid": bool(json_valid),
            "relevance": round(float(relevance), 3),
            "code_block_count": int(code_blocks),
            "python_blocks_ok": int(py_ok),
            "python_blocks_total": int(py_total),
            "ttr": round(float(ttr), 3),
            "list_items": int(list_items),
            "expected_list_items": int(exp_list_n) if isinstance(exp_list_n, int) else None,
        },
        "components": {
            "length_factor": round(float(length_factor), 3),
            "relevance": round(float(relevance), 3),
            "explain_ratio": round(float(explain_ratio), 3),
        },
    }


def quality_ensemble_assessment(
    responses: list[str],
    prompt: str | None = None,
    *,
    min_tokens: int = 80,
    expect_json: bool = False,
) -> dict[str, Any]:
    """Aggregate quality and diversity across multiple candidate responses.

    This is dependency-light and focuses on lexical/structural diversity.
    Returns per-response assessments, average pairwise diversity, and a simple
    cluster count estimate via greedy grouping on high Jaccard similarity.
    """
    safe_responses = [str(r or "").strip() for r in (responses or [])]
    per = [quality_assessment(r, prompt=prompt, min_tokens=min_tokens, expect_json=expect_json) for r in safe_responses]

    # Pairwise lexical diversity via Jaccard of content words
    def _content_set(s: str) -> set[str]:
        return set([w for w in _words(s) if w not in _STOPWORDS][:200])

    sets = [_content_set(r) for r in safe_responses]
    n = len(sets)
    if n <= 1:
        avg_div = 0.0
    else:
        acc = 0.0
        pairs = 0
        for i in range(n):
            for j in range(i + 1, n):
                sim = _jaccard(sets[i], sets[j])
                acc += 1.0 - sim  # diversity
                pairs += 1
        avg_div = (acc / pairs) if pairs else 0.0

    # Greedy clustering by high similarity threshold
    used = [False] * n
    clusters = 0
    for i in range(n):
        if used[i]:
            continue
        clusters += 1
        used[i] = True
        for j in range(i + 1, n):
            if (not used[j]) and (_jaccard(sets[i], sets[j]) >= 0.75):
                used[j] = True

    scores = [p.get("score", 0.0) for p in per]
    best_idx = int(max(range(len(scores)), key=lambda k: scores[k])) if scores else -1
    best = per[best_idx] if best_idx >= 0 else None

    return {
        "assessments": per,
        "avg_pairwise_diversity": round(float(avg_div), 3),
        "cluster_count": int(clusters),
        "best_index": best_idx,
        "best_score": round(float(scores[best_idx]), 3) if best_idx >= 0 else None,
        "best": best,
    }


def basic_quality_assessment(text: str, *, min_tokens: int = 80) -> dict[str, Any]:
    """Return a compact quality assessment for ``text``.

    Backwards-compatible wrapper that exposes a minimal signal set and a score.
    """
    adv = quality_assessment(text, None, min_tokens=min_tokens, expect_json=False)
    # Only expose the original three signals for compatibility
    minimal_signals = {k: adv["signals"].get(k, False) for k in ("has_apology", "has_structure", "has_suspicious")}
    return {
        "score": adv["score"],
        "tokens": adv["tokens"],
        "min_tokens": adv["min_tokens"],
        "signals": minimal_signals,
    }
