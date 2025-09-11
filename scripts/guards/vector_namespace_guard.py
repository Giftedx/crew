"""Lightweight guard to detect improper vector namespace usage.

Checks for common anti-patterns:
- Hard-coded single-part namespaces (e.g. "default" or "main") instead of tenant:workspace.
- f-strings missing delimiter ':' when composing namespace.
- Direct concatenation without ':' present.

This is heuristic: it scans source files under `src/` for suspicious patterns and
prints findings; exit code 0 (non-blocking) so it can be added to CI informationally first.

Usage:
  python scripts/guards/vector_namespace_guard.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / ".." / "src"

SUSPICIOUS_LITERAL = re.compile(r"namespace\s*=\s*['\"](default|main)['\"]")
FSTRING_NO_COLON = re.compile(r"f\"\{tenant\}\{workspace\}\"|f'\{tenant\}\{workspace\}'")
CONCAT_PATTERN = re.compile(r"tenant\s*\+\s*workspace")


def scan_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    findings: list[str] = []
    if SUSPICIOUS_LITERAL.search(text):
        findings.append("hard-coded single-part namespace literal")
    if FSTRING_NO_COLON.search(text):
        findings.append("f-string missing ':' delimiter between tenant and workspace")
    if CONCAT_PATTERN.search(text):
        findings.append("string concatenation of tenant + workspace without ':'")
    return [f"{path}: {msg}" for msg in findings]


def main() -> int:
    if not SRC_ROOT.exists():
        print(f"[vector-namespace-guard] src root not found: {SRC_ROOT}")
        return 0
    issues: list[str] = []
    for py_file in SRC_ROOT.rglob("*.py"):
        issues.extend(scan_file(py_file))
    if issues:
        print("[vector-namespace-guard] Potential namespace issues detected (expect 'tenant:workspace'):")
        for line in issues:
            print(" -", line)
    else:
        print("[vector-namespace-guard] No obvious namespace anti-patterns found.")
    # Non-blocking for now
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
