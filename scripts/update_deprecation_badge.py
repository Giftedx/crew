#!/usr/bin/env python
"""Update README with a deprecation status badge/table.

Inserts a compact table summarising active deprecations between the marker
comments:
  <!-- DEPRECATIONS:START -->
  <!-- DEPRECATIONS:END -->

The script reuses the scanning logic from `scripts/check_deprecations.py`.

Usage:
  python scripts/update_deprecation_badge.py [--upcoming-days 120] [--no-sort]

It will fail (non‑zero) if markers are missing to avoid accidental README corruption.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from textwrap import dedent

# Local import (works because both scripts live in scripts/ directory)
import check_deprecations  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
START = "<!-- DEPRECATIONS:START -->"
END = "<!-- DEPRECATIONS:END -->"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inject deprecation badge/table into README")
    p.add_argument("--upcoming-days", type=int, default=120)
    p.add_argument("--no-sort", action="store_true", help="Preserve original ordering of flags")
    return p.parse_args(argv)


def _build_table(rows: list[dict], upcoming_days: int, preserve: bool) -> str:
    active = [r for r in rows if not r["past_deadline"]]
    if not preserve:
        active.sort(key=lambda r: (r["days_until_removal"], r["name"]))
    header = "| Name | Stage | Remove After | Days Left | Occurrences | Violation | Replacement |"
    sep = "|------|-------|--------------|-----------|-------------|-----------|-------------|"
    lines = [header, sep]
    for r in active:
        days_left = r["days_until_removal"]
        status_icon = "❌" if r["violation"] else "✅"
        repl = r.get("replacement") or ""
        lines.append(
            "| `{name}` | {stage} | {remove_after} | {days} | {occ} | {icon} | {repl} |".format(
                name=r["name"],
                stage=r["stage"],
                remove_after=r["remove_after"],
                days=days_left,
                occ=r["occurrence_count"],
                icon=status_icon,
                repl=repl,
            )
        )
    summary = dedent(
        f"""
        **Deprecations:** {len(active)} active (<= {upcoming_days} days window highlighted)  \\
        Generated via `scripts/update_deprecation_badge.py`.
        """.strip()
    )
    return summary + "\n\n" + "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])
    code, results, _upcoming = check_deprecations.scan(upcoming_days=ns.upcoming_days)
    if not README.exists():
        print("README.md not found", file=sys.stderr)
        return 2
    original = README.read_text()
    if START not in original or END not in original:
        print("Markers not found in README. Aborting.", file=sys.stderr)
        return 3
    table = _build_table(results, ns.upcoming_days, ns.no_sort)
    # Replace content between markers (non-greedy)
    pattern = re.compile(rf"{re.escape(START)}.*?{re.escape(END)}", re.DOTALL)
    replacement = START + "\n" + table + END
    updated = pattern.sub(replacement, original, count=1)
    if updated != original:
        README.write_text(updated)
        print("README deprecation badge updated.")
    else:
        print("README already up to date.")
    # Propagate scan exit code (so CI still fails if violations exist)
    return code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
