"""Utility helpers for plugin golden datasets.

The helpers intentionally stay minimal: they read JSON Lines files into
standard Python structures so plugin tests can replay golden scenarios.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load(pattern: str) -> list[dict[str, Any]]:
    """Load JSONL records matching ``pattern``.

    Parameters
    ----------
    pattern:
        Glob pattern pointing to JSONL files.
    """

    p = Path(pattern)
    if p.is_absolute():
        base = p.parent
        glob_pat = p.name
    else:
        base = Path()
        glob_pat = pattern

    records: list[dict[str, Any]] = []
    for path in sorted(base.glob(glob_pat)):
        with path.open("r", encoding="utf-8") as fh:
            for raw_line in fh:
                stripped = raw_line.strip()
                if stripped:
                    records.append(json.loads(stripped))
    return records


__all__ = ["load"]
