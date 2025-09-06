#!/usr/bin/env python
"""Maintain and enforce a mypy error-count baseline.

Usage:
  python scripts/type_baseline.py check   # exit 0 if current <= baseline, else 1
  python scripts/type_baseline.py update  # rewrite baseline if current <= baseline (or --force)

Baseline file: mypy_baseline.json

This focuses on count comparison (not exact error text) so incremental improvements are encouraged
without creating noisy churn when line numbers shift.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

BASELINE_PATH = Path("mypy_baseline.json")
MYPY_CMD = [sys.executable, "-m", "mypy", "src"]
ERROR_RE = re.compile(r"Found (\d+) errors? in ")
USAGE_MIN_ARGS = 2  # minimum argv length (script + command)


@dataclass
class Result:
    count: int
    raw: str


def run_mypy() -> Result:
    # Security note (S603): command arguments are a static list (no user input)
    # and we do not invoke a shell. We intentionally keep check=False so we can
    # parse mypy's stdout/stderr even on non‑zero exit (regression reporting).
    proc = subprocess.run(  # noqa: S603
        MYPY_CMD, check=False, capture_output=True, text=True
    )
    out = proc.stdout + "\n" + proc.stderr
    match = ERROR_RE.search(out)
    count = int(match.group(1)) if match else 0
    return Result(count=count, raw=out)


def load_baseline() -> int:
    if not BASELINE_PATH.exists():
        return 0
    data = json.loads(BASELINE_PATH.read_text())
    return int(data.get("error_count", 0))


def save_baseline(count: int) -> None:
    BASELINE_PATH.write_text(json.dumps({"error_count": count}, indent=2) + "\n")


def cmd_check() -> int:
    res = run_mypy()
    baseline = load_baseline()
    if baseline and res.count > baseline:
        print(f"mypy error count regression: {res.count} > baseline {baseline}", file=sys.stderr)
        return 1
    print(f"mypy errors: {res.count} (baseline {baseline or 'unset'})")
    if baseline == 0:
        print("(Baseline not set yet; run update to establish current count)")
    return 0


def cmd_update(force: bool = False) -> int:
    res = run_mypy()
    baseline = load_baseline()
    if baseline and res.count > baseline and not force:
        print(f"Refusing to increase baseline ({res.count} > {baseline}). Use --force to override.", file=sys.stderr)
        return 1
    save_baseline(res.count)
    print(f"Baseline updated to {res.count} errors.")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < USAGE_MIN_ARGS or argv[1] not in {"check", "update"}:
        print("Usage: type_baseline.py {check|update} [--force]", file=sys.stderr)
        return 2
    cmd = argv[1]
    force = "--force" in argv[2:]
    if cmd == "check":
        return cmd_check()
    return cmd_update(force=force)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv))
