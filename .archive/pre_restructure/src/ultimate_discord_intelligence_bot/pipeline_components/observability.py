"""Utilities for aggregating pipeline observability metadata."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Iterable


def merge_log_pattern_summaries(
    step_summaries: dict[str, dict[str, Any]],
    *,
    top_n: int = 10,
) -> dict[str, Any]:
    """Merge per-step log pattern summaries into a pipeline-level view.

    The input ``step_summaries`` maps step names to the ``log_patterns`` payload
    emitted by :class:`LogPatternMiddleware`. The merged structure provides
    aggregate counters (total records, severity totals, top recurring patterns)
    while retaining the per-step summaries for drill-down consumers.
    """

    if not step_summaries:
        return {
            "step_count": 0,
            "total_records": 0,
            "level_totals": {},
            "top_patterns": [],
            "recent_errors": [],
        }

    level_totals: Counter[str] = Counter()
    pattern_counter: Counter[str] = Counter()
    pattern_levels: defaultdict[str, set[str]] = defaultdict(set)
    pattern_examples: dict[str, str] = {}
    recent_errors: list[dict[str, Any]] = []
    total_records = 0
    first_ts: float | None = None
    last_ts: float | None = None
    observed_steps = 0

    for step, summary in step_summaries.items():
        if not isinstance(summary, dict):
            continue
        observed_steps += 1

        total_records += int(summary.get("total_records", 0) or 0)

        for level, count in _iter_dict(summary.get("levels")):
            level_totals[level] += int(count or 0)

        for entry in summary.get("top_patterns", []) or []:
            if not isinstance(entry, dict):
                continue
            pattern = entry.get("pattern")
            if not pattern:
                continue
            count = int(entry.get("count", 0) or 0)
            pattern_counter[pattern] += count
            pattern_levels[pattern].update(entry.get("levels", []) or [])
            if pattern not in pattern_examples and entry.get("example"):
                pattern_examples[pattern] = str(entry["example"])

        for error in summary.get("recent_errors", []) or []:
            if isinstance(error, dict):
                enriched = dict(error)
                enriched.setdefault("step", step)
                recent_errors.append(enriched)

        first = summary.get("first_timestamp")
        if isinstance(first, (int, float)):
            first_ts = first if first_ts is None else min(first_ts, float(first))
        last = summary.get("last_timestamp")
        if isinstance(last, (int, float)):
            last_ts = last if last_ts is None else max(last_ts, float(last))

    top_patterns: list[dict[str, Any]] = []
    for pattern, count in pattern_counter.most_common(top_n):
        top_patterns.append(
            {
                "pattern": pattern,
                "count": count,
                "levels": sorted(pattern_levels[pattern]),
                "example": pattern_examples.get(pattern),
            }
        )

    recent_errors = recent_errors[-top_n:]

    summary_payload: dict[str, Any] = {
        "step_count": observed_steps,
        "total_records": total_records,
        "level_totals": dict(level_totals),
        "top_patterns": top_patterns,
        "recent_errors": recent_errors,
    }
    if first_ts is not None:
        summary_payload["first_timestamp"] = first_ts
    if last_ts is not None:
        summary_payload["last_timestamp"] = last_ts

    return summary_payload


def _iter_dict(data: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(data, dict):
        return data.items()
    return []


__all__ = ["merge_log_pattern_summaries"]
