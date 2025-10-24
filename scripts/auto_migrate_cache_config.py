#!/usr/bin/env python3
"""Automated migration helper for cache configuration consolidation.

This script scans the codebase for legacy cache TTL patterns and prints
actionable suggestions to migrate them to the unified cache configuration
in core/cache/unified_config.py.

Usage:
  python3 scripts/auto_migrate_cache_config.py [--apply]

By default, it runs in report mode and does not modify files.
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Iterator
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# Patterns to find legacy TTL usage
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("cache_ttl_llm attribute", re.compile(r"cache_ttl_llm\s*=\s*\d+")),
    ("hardcoded ttl kwarg", re.compile(r"ttl\s*=\s*(\d{2,}|[0-9_]+)")),
    ("TOOL CACHE_TTL env", re.compile(r"TOOL_CACHE_TTL|CACHE_TTL")),
    ("TRANSCRIPTION TTL env", re.compile(r"TRANSCRIPTION_CACHE_TTL_DAYS")),
    ("ANALYSIS TTL env", re.compile(r"ANALYSIS_CACHE_TTL_HOURS")),
]

SUGGESTIONS = {
    "llm": "get_unified_cache_config().get_ttl_for_domain('llm')",
    "routing": "get_unified_cache_config().get_ttl_for_domain('routing')",
    "tool": "get_unified_cache_config().get_ttl_for_domain('tool')",
    "analysis": "get_unified_cache_config().get_ttl_for_domain('analysis')",
    "transcription": "get_unified_cache_config().get_ttl_for_domain('transcription')",
}


def iter_py_files(root: Path) -> Iterator[Path]:
    for p in root.rglob("*.py"):
        # Skip virtual envs, caches, and __pycache__
        if any(part in {".venv", "venv", "__pycache__"} for part in p.parts):
            continue
        yield p


def scan_file(path: Path) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return hits
    for label, rx in PATTERNS:
        for m in rx.finditer(text):
            # Compute line number
            line_no = text.count("\n", 0, m.start()) + 1
            # Extract line snippet
            line_start = text.rfind("\n", 0, m.start()) + 1
            line_end = text.find("\n", m.end())
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end].strip()
            hits.append((label, line_no, line))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Reserved for future automatic edits")
    args = parser.parse_args()

    print("=" * 80)
    print("CACHE CONFIG MIGRATION - SCAN REPORT")
    print("=" * 80)
    print(f"Root: {SRC}")
    print()

    total_hits = 0
    for path in iter_py_files(SRC):
        hits = scan_file(path)
        if not hits:
            continue
        rel = path.relative_to(ROOT)
        print(f"\nFile: {rel}")
        for label, line_no, line in hits:
            total_hits += 1
            print(f"  L{line_no:>4}  [{label}]  {line}")

    print()
    print("=" * 80)
    print(f"Total matches found: {total_hits}")
    print("=" * 80)
    print()

    if total_hits == 0:
        print("✅ No legacy cache TTL patterns found.")
        return 0

    print("Suggested migrations:")
    print("- Replace hardcoded `ttl=...` with domain-based TTL getters, e.g.:")
    for domain, sugg in SUGGESTIONS.items():
        print(f"  • {domain}: {sugg}")
    print("- Replace TOOL env lookups (TOOL_CACHE_TTL/CACHE_TTL) with unified config in tools")
    print("- Replace TRANSCRIPTION/ANALYSIS env vars with unified domain TTLs")
    print()
    print("Note: --apply is reserved; current version only reports matches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
