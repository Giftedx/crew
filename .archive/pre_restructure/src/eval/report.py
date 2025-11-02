"""Helpers to summarise evaluation results."""

from __future__ import annotations

import json
from pathlib import Path


def save(report: dict[str, dict[str, float]], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)


def summary_markdown(report: dict[str, dict[str, float]]) -> str:
    lines = ["| task | quality | cost_usd | latency_ms |", "|---|---|---|---|"]
    for task, m in report.items():
        lines.append(f"| {task} | {m['quality']:.2f} | {m['cost_usd']:.2f} | {m['latency_ms']:.1f} |")
    return "\n".join(lines)


__all__ = ["save", "summary_markdown"]
