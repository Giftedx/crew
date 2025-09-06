#!/usr/bin/env python3
"""Guardrail: forbid direct 'requests' calls outside approved modules.

Allowed:
- src/core/http_utils.py (wrappers live here)
- tests/** (tests may patch or assert direct requests semantics)
- src/ultimate_discord_intelligence_bot/tools/discord_download_tool.py (string literal only)

All other Python files under src/ must use http_utils (resilient_get/post or retrying_*).
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

ALLOWED_FILES = {
    "src/core/http_utils.py",
    # This tool contains a string literal reference used for debugging output only.
    "src/ultimate_discord_intelligence_bot/tools/discord_download_tool.py",
}

# Flag any direct requests.<method>(...) usage. This is intentionally broad
# to catch variable/param usages too; allowed files are excluded above.
# Match an opening parenthesis with optional whitespace (no string literal required)
# so calls like `requests.get(url)` are detected.
PATTERN = re.compile(r"\brequests\.(get|post|put|delete|patch|head)\s*\(")



def main() -> int:
    violations: list[str] = []
    skip_dirs = {"venv", ".venv", "site-packages", ".git", "build", "dist"}
    for path in SRC.rglob("*.py"):
        rel = str(path.relative_to(ROOT))
        parts = set(rel.split("/"))
        if parts & skip_dirs:
            continue
        if rel in ALLOWED_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if PATTERN.search(text):
            violations.append(rel)
    if violations:
        print("Direct 'requests' usage detected; use core.http_utils helpers instead:")
        for v in sorted(violations):
            print(f" - {v}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
