#!/usr/bin/env python
"""Deprecation reference scanner.

Scans the repository for occurrences of deprecated or removed symbols declared in
`config/deprecations.yaml`.

Exit codes:
 0 - OK (no past-deadline references; structure sane)
 1 - Past-deadline symbol still referenced OR removed symbol present.
 2 - Malformed deprecations file.

Simplifications:
 - Only scans text files with .py / .md / .yaml / .yml extensions inside src/ and tests/.
 - Ignores the config/deprecations.yaml file itself and this script.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json as _json
import logging
import sys
from collections.abc import Iterable
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEP_FILE = ROOT / "config" / "deprecations.yaml"

TEXT_EXT = {".py", ".md", ".yaml", ".yml"}
SCAN_DIRS = [ROOT / "src", ROOT / "tests"]
TODAY = dt.date.today()


def iter_files() -> Iterable[Path]:
    for base in SCAN_DIRS:
        if base.exists():
            yield from (
                p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXT
            )


def load_deprecations() -> list[dict]:
    try:
        data = yaml.safe_load(DEP_FILE.read_text()) or {}
    except Exception as exc:  # pragma: no cover - IO error
        print(f"ERROR: unable to read {DEP_FILE}: {exc}", file=sys.stderr)
        sys.exit(2)
    flags = data.get("flags")
    if not isinstance(flags, list):
        print("ERROR: 'flags' list missing in deprecations file", file=sys.stderr)
        sys.exit(2)
    return flags


def _collect_texts() -> dict[str, str]:
    collected: dict[str, str] = {}
    for f in iter_files():
        try:
            txt = f.read_text(errors="ignore")
        except Exception as exc:  # pragma: no cover
            logging.debug("Skipping unreadable file %s: %s", f, exc)
            continue
        collected[str(f.relative_to(ROOT))] = txt
    return collected


def _evaluate_entry(entry: dict, texts: dict[str, str]) -> tuple[dict | None, int]:
    name = entry.get("name")
    stage = entry.get("stage")
    remove_after = entry.get("remove_after")
    replacement = entry.get("replacement")
    if not isinstance(name, str):
        print(f"ERROR: invalid deprecation entry missing name: {entry}", file=sys.stderr)
        return None, 2
    # Accept either an ISO date string or a date object (yaml may auto-coerce)
    if isinstance(remove_after, dt.date):
        deadline = remove_after
        remove_after_str = deadline.isoformat()
    else:
        if not isinstance(remove_after, str):
            print(f"ERROR: invalid deprecation entry: {entry}", file=sys.stderr)
            return None, 2
        try:
            deadline = dt.date.fromisoformat(remove_after)
        except ValueError:
            print(f"ERROR: invalid date for {name}: {remove_after}", file=sys.stderr)
            return None, 2
        remove_after_str = remove_after
    needle = name.rsplit(".", 1)[-1]
    occurrences = [
        path
        for path, text in texts.items()
        if name in text or (needle != name and needle in text)
    ]
    past_deadline = deadline < TODAY
    removed_refs = stage == "removed" and bool(occurrences)
    overdue_refs = past_deadline and stage != "removed" and bool(occurrences)
    violation = bool(removed_refs or overdue_refs)
    row = {
        "name": name,
        "stage": stage,
        "remove_after": remove_after_str,
        "past_deadline": past_deadline,
        "occurrence_count": len(occurrences),
        "violation": violation,
        "replacement": replacement,
        "days_until_removal": (deadline - TODAY).days,
    }
    return row, (1 if violation else 0)


def _render_table(results: list[dict]) -> None:
    columns = [
        "name",
        "stage",
        "remove_after",
        "occurrence_count",
        "past_deadline",
        "violation",
    ]
    widths = {k: 0 for k in columns}
    for row in results:
        for k, w in widths.items():  # noqa: B007 (intentional read of w for clarity)
            widths[k] = max(w, len(str(row[k])))
    header = " | ".join(k.ljust(widths[k]) for k in columns)
    print(header)
    print("-+-".join("-" * widths[k] for k in columns))
    for row in results:
        print(" | ".join(str(row[k]).ljust(widths[k]) for k in columns))


def scan(upcoming_days: int = 120, *, print_table: bool = True):  # noqa: D401 - simple facade
    """Run scan and return (exit_code, results, upcoming).

    Parameters
    ----------
    upcoming_days: int
        Horizon (days) used to populate the upcoming list.
    print_table: bool
        If True, render table to stdout (human mode). Disabled for JSON consumption.
    """
    flags = load_deprecations()
    texts = _collect_texts()
    results: list[dict] = []
    upcoming: list[dict] = []
    exit_code = 0
    for entry in flags:
        row, code = _evaluate_entry(entry, texts)
        if row is None:
            exit_code = max(exit_code, code)
            continue
        results.append(row)
        if 0 <= row["days_until_removal"] <= upcoming_days:
            upcoming.append(row)
        exit_code = max(exit_code, code)
    if print_table:
        _render_table(results)
        if exit_code == 0:
            print("All deprecation checks passed.")
        else:
            print("Deprecation violations detected.", file=sys.stderr)
    return exit_code, results, upcoming


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan for deprecated symbol usage")
    parser.add_argument("--json", action="store_true", help="Emit machine readable JSON")
    parser.add_argument(
        "--upcoming-days",
        type=int,
        default=120,
        help="Window (days) to include in upcoming removals list",
    )
    parser.add_argument(
        "--fail-on-upcoming",
        type=int,
        metavar="DAYS",
        help=(
            "Exit non-zero if any deprecation has a removal date within DAYS (inclusive). "
            "Returns exit code 1 (unless a harder failure already occurred)."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])
    code, results, upcoming = scan(upcoming_days=ns.upcoming_days, print_table=not ns.json)

    # Proactive upcoming failure evaluation
    fail_upcoming_triggered = False
    if ns.fail_on_upcoming is not None:
        horizon = ns.fail_on_upcoming
        for r in results:
            if 0 <= r["days_until_removal"] <= horizon:
                fail_upcoming_triggered = True
                break

    # Emit JSON if requested
    if ns.json:
        payload = {
            "date": TODAY.isoformat(),
            "results": results,
            "upcoming_window_days": ns.upcoming_days,
            "upcoming": upcoming,
            "fail_on_upcoming": ns.fail_on_upcoming,
            "upcoming_triggered": fail_upcoming_triggered,
            "base_exit_code": code,
        }
        print(_json.dumps(payload, indent=2, sort_keys=True))
        # In JSON mode we don't show human table (already suppressed above)
    elif ns.fail_on_upcoming is not None:
        if fail_upcoming_triggered:
            print(
                f"Fail-on-upcoming: at least one deprecation removes within {ns.fail_on_upcoming} days (will fail)."
            )
        else:
            print(
                f"Fail-on-upcoming: no deprecations within {ns.fail_on_upcoming} days (no failure)."
            )

    # Exit code precedence: structural/violation (existing code) > upcoming trigger
    if code != 0:
        return code
    if fail_upcoming_triggered:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
