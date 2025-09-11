#!/usr/bin/env python
"""Mypy snapshot guard.

Compares current mypy error count to a persisted JSON snapshot. Fails if the
count increases (or optionally on decrease without --update to encourage
explicit snapshot refreshes).

Snapshot schema (stored at path provided via --baseline):
{
  "error_total": int,
  "updated": "YYYY-MM-DD",
  "mypy_version": "x.y.z",
  "command": "python -m mypy src"
}

Exit codes:
 0 - OK (no increase or snapshot updated successfully)
 1 - Error count increased over baseline
 2 - Mypy invocation failure / unexpected parse error

Usage:
  python scripts/mypy_snapshot_guard.py --baseline reports/mypy_snapshot.json
  python scripts/mypy_snapshot_guard.py --baseline reports/mypy_snapshot.json --update
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CMD = [sys.executable, "-m", "mypy", "src"]
SUMMARY_RE = re.compile(r"Found (\d+) errors? in ")
ERROR_LINE_RE = re.compile(r"^(?P<path>[^:]+):\d+:\d+: error: .+")


def run_mypy(cmd: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as exc:  # pragma: no cover
        print(f"ERROR: failed to execute mypy: {exc}", file=sys.stderr)
        return 2, "", str(exc)
    return proc.returncode, proc.stdout + proc.stderr, proc.stderr


def parse_error_total(output: str) -> int:
    # Look for final summary line
    match = SUMMARY_RE.search(output)
    if not match:
        # Fallback: if mypy returned non-zero and no summary, treat as parse error
        raise ValueError("Unable to parse mypy error summary; ensure mypy not run with --no-error-summary")
    return int(match.group(1))


def load_snapshot(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover
        print(f"WARNING: unable to parse snapshot (will recreate): {exc}")
        return None


def write_snapshot(path: Path, total: int, cmd: list[str]) -> None:
    payload = {
        "error_total": total,
        "updated": dt.date.today().isoformat(),
        "mypy_version": os.environ.get("MYPY_VERSION", "unknown"),
        "command": " ".join(cmd),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _compute_breakdown(output: str) -> dict[str, int]:
    """Compute per top-level package error counts from mypy human output."""
    counts: dict[str, int] = {}
    for line in output.splitlines():
        if not line or line.startswith("note:"):
            continue
        m = ERROR_LINE_RE.match(line)
        if not m:
            continue
        rel = m.group("path")
        # Normalize relative path
        try:
            path = Path(rel)
        except Exception:  # pragma: no cover
            continue
        if "src/" in rel:
            # Make relative to src
            try:
                idx = path.parts.index("src")
                parts = path.parts[idx + 1 :]
            except ValueError:
                continue
        elif rel.startswith("src/"):
            parts = path.parts[1:]
        else:
            continue
        if not parts:
            continue
        top = parts[0]
        counts[top] = counts.get(top, 0) + 1
    return counts


def guard(baseline: Path, update: bool, cmd: list[str], *, json_mode: bool = False, breakdown: bool = False) -> int:
    code, out, _err = run_mypy(cmd)
    # We intentionally allow mypy's own non-zero exit code (incremental adoption)
    try:
        current_total = parse_error_total(out)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    snapshot = load_snapshot(baseline)
    status: str
    breakdown_map = _compute_breakdown(out) if breakdown else None
    if snapshot is None:
        status = "created"
        if not json_mode:
            print(f"[mypy-guard] No snapshot found. Creating new baseline at {baseline} (errors={current_total}).")
        write_snapshot(baseline, current_total, cmd)
        if json_mode:
            print(
                json.dumps(
                    {
                        "status": status,
                        "baseline_total": current_total,
                        "current_total": current_total,
                        "delta": 0,
                        "baseline_path": str(baseline),
                        **({"breakdown": breakdown_map} if breakdown_map else {}),
                    }
                )
            )
        return 0

    baseline_total = int(snapshot.get("error_total", -1))
    if baseline_total < 0:
        print("ERROR: invalid snapshot missing error_total", file=sys.stderr)
        return 2

    if update:
        if current_total > baseline_total:
            status = "update-refused-increase"
            if json_mode:
                print(
                    json.dumps(
                        {
                            "status": status,
                            "baseline_total": baseline_total,
                            "current_total": current_total,
                            "delta": current_total - baseline_total,
                            "baseline_path": str(baseline),
                            **({"breakdown": breakdown_map} if breakdown_map else {}),
                        }
                    )
                )
            else:
                print(
                    f"[mypy-guard] Refusing to update snapshot because error count increased: {baseline_total} -> {current_total}",
                    file=sys.stderr,
                )
            return 1
        write_snapshot(baseline, current_total, cmd)
        status = "updated"
        if json_mode:
            print(
                json.dumps(
                    {
                        "status": status,
                        "baseline_total": baseline_total,
                        "current_total": current_total,
                        "delta": current_total - baseline_total,
                        "baseline_path": str(baseline),
                        **({"breakdown": breakdown_map} if breakdown_map else {}),
                    }
                )
            )
        else:
            print(f"[mypy-guard] Snapshot updated: {baseline_total} -> {current_total}")
        return 0

    if current_total > baseline_total:
        status = "increased"
        if json_mode:
            print(
                json.dumps(
                    {
                        "status": status,
                        "baseline_total": baseline_total,
                        "current_total": current_total,
                        "delta": current_total - baseline_total,
                        "baseline_path": str(baseline),
                        **({"breakdown": breakdown_map} if breakdown_map else {}),
                    }
                )
            )
        else:
            print(
                f"[mypy-guard] ERROR: Type errors increased: baseline={baseline_total} current={current_total} (run with --update after fixing).",
                file=sys.stderr,
            )
        return 1

    if current_total < baseline_total:
        status = "decreased"
        msg = f"[mypy-guard] SUCCESS: Type errors decreased: {baseline_total} -> {current_total}. Run with --update to record new baseline."
    else:
        status = "stable"
        msg = f"[mypy-guard] Stable: {current_total} errors (no change)."
    if json_mode:
        print(
            json.dumps(
                {
                    "status": status,
                    "baseline_total": baseline_total,
                    "current_total": current_total,
                    "delta": current_total - baseline_total,
                    "baseline_path": str(baseline),
                    **({"breakdown": breakdown_map} if breakdown_map else {}),
                }
            )
        )
    else:
        print(msg)
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Guard mypy error count against regressions")
    p.add_argument("--baseline", default="reports/mypy_snapshot.json", help="Path to snapshot JSON file")
    p.add_argument("--update", action="store_true", help="Update snapshot to current count (must not increase)")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON status")
    p.add_argument("--breakdown", action="store_true", help="Include per top-level package error counts in JSON output")
    p.add_argument(
        "--cmd",
        nargs=argparse.REMAINDER,
        help="Override mypy command (default: python -m mypy src). Use -- to separate.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])
    cmd = DEFAULT_CMD if not ns.cmd else ns.cmd
    baseline = Path(ns.baseline)
    return guard(baseline, ns.update, cmd, json_mode=ns.json, breakdown=ns.breakdown)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
