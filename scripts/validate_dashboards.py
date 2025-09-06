#!/usr/bin/env python3
"""Validate Grafana dashboard JSON files under docs/grafana.

Checks basic JSON validity and required fields. Prints a summary and exits non-zero on failure.
"""
from __future__ import annotations

import json
from pathlib import Path


def validate_dashboard(path: Path) -> list[str]:
    errs: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path.name}: invalid JSON ({exc})"]
    # Minimal required keys
    for key in ("panels", "title"):
        if key not in data:
            errs.append(f"{path.name}: missing key '{key}'")
    # Panels should be a list
    if not isinstance(data.get("panels", []), list):
        errs.append(f"{path.name}: 'panels' is not a list")
    return errs


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ddir = root / "docs" / "grafana"
    if not ddir.exists():
        print("No dashboards directory found; skipping")
        return 0
    problems: list[str] = []
    for f in ddir.glob("*.json"):
        problems.extend(validate_dashboard(f))
    if problems:
        print("Dashboard validation failed:")
        for p in problems:
            print(" -", p)
        return 1
    print(f"Validated {len(list(ddir.glob('*.json')))} dashboard(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

