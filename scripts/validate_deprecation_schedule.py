#!/usr/bin/env python
"""Validate deprecation schedule.

Behavior:
* Loads config/deprecations.yaml.
* For each flag entry with stage in {deprecated,pending_removal}:
    - If current UTC date > remove_after, scans repo for references outside allow list.
      If any found -> exit non‑zero and list violations.
    - Else prints upcoming deprecation summary (informational) and does not fail.

Allow list rationale mirrors deprecated flag validator: we permit references in
  - changelog
  - feature flag docs
  - explicit legacy HTTP utilities file
  - the deprecation schedule config itself
  - validator scripts / governance tests

Future: unify with validate_deprecated_flags.py; for now we keep lightweight to
avoid coupling and speed.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEDULE = ROOT / "config" / "deprecations.yaml"

ALLOWED_SUBSTRINGS = {
    "CHANGELOG.md",
    "docs/feature_flags.md",
    "grounding/",  # allow mention if describing provenance (conservative)
    "core/http_utils.py",  # legacy reference note
    "config/deprecations.yaml",
    "scripts/validate_deprecation_schedule.py",
    "scripts/validate_deprecated_flags.py",
    "tests/test_deprecation_schedule.py",
    "tests/test_deprecated_flag_usage.py",
    "FUTURE_WORK.md",
    "README.md",
}

SKIP_DIRS = {".git", ".venv", "__pycache__", "yt-dlp"}


@dataclass
class DeprecationEntry:
    name: str
    stage: str
    remove_after: date
    replacement: str | None = None
    notes: str | None = None


def _load_schedule() -> list[DeprecationEntry]:
    if not SCHEDULE.exists():  # fail fast
        print("schedule file missing", file=sys.stderr)
        return []
    raw = yaml.safe_load(SCHEDULE.read_text()) or {}
    entries: list[DeprecationEntry] = []
    for item in raw.get("flags", []) or []:
        try:
            remove_after = datetime.strptime(str(item["remove_after"]), "%Y-%m-%d").date()
        except Exception as e:  # noqa: BLE001
            print(f"invalid remove_after for {item}: {e}", file=sys.stderr)
            continue
        entries.append(
            DeprecationEntry(
                name=str(item["name"]),
                stage=str(item.get("stage", "deprecated")),
                remove_after=remove_after,
                replacement=item.get("replacement"),
                notes=item.get("notes"),
            )
        )
    return entries


def _iter_code_files() -> Iterable[Path]:
    for path in ROOT.rglob("*"):
        if path.is_dir():
            if path.name in SKIP_DIRS:
                continue
            # skip nested virtual envs or build artifacts heuristically
            if any(seg in SKIP_DIRS for seg in path.parts):
                continue
            continue
        if path.suffix in {".py", ".md", ".yaml", ".yml", ".txt"} or "config" in path.parts:
            yield path


def _is_allowed(path: Path) -> bool:
    p = str(path.relative_to(ROOT))
    return any(sub in p for sub in ALLOWED_SUBSTRINGS)


def _scan_for(flag: str) -> list[Path]:
    pattern = re.compile(rf"\b{re.escape(flag)}\b")
    hits: list[Path] = []
    for file in _iter_code_files():
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:  # noqa: BLE001
            logging.debug("Failed reading %s: %s", file, exc)
            continue
        if pattern.search(text):
            hits.append(file)
    return hits


def main() -> int:
    entries = _load_schedule()
    override = os.getenv("DEPRECATION_AS_OF")
    today = datetime.now(UTC).date()
    if override:
        try:
            today = datetime.strptime(override, "%Y-%m-%d").date()
        except ValueError:
            logging.warning("Invalid DEPRECATION_AS_OF=%s (expected YYYY-MM-DD) - ignoring", override)

    if not entries:
        print("No deprecations scheduled.")
        return 0

    violations: list[str] = []
    upcoming: list[str] = []

    for entry in entries:
        hits = _scan_for(entry.name)
        # Filter allowed
        disallowed = [h for h in hits if not _is_allowed(h)]
        if today > entry.remove_after:
            if disallowed:
                violations.append(
                    f"{entry.name} past removal ({entry.remove_after}) still present in: "
                    + ", ".join(str(p.relative_to(ROOT)) for p in disallowed)
                )
        else:
            remaining_days = (entry.remove_after - today).days
            upcoming.append(
                f"{entry.name} removal in {remaining_days}d on {entry.remove_after} "
                f"replacement={entry.replacement or '-'}"
            )

    if upcoming:
        print("Upcoming deprecations:")
        for line in sorted(upcoming):
            print("  -", line)

    if violations:
        print("\nViolations:")
        for v in violations:
            print("  -", v)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
