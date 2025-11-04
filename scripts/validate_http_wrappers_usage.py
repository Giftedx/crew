#!/usr/bin/env python3
"""Guardrail: forbid direct 'requests' calls outside approved modules.

Allowed:
- platform.http.http_utils (wrappers live here)
- src/ultimate_discord_intelligence_bot/core/http_utils.py (compatibility shim)
- tests/** (tests may patch or assert direct requests semantics)
- src/ultimate_discord_intelligence_bot/tools/discord_download_tool.py (string literal only)

All other Python files under src/ must use http_utils (resilient_get/post or retrying_*).
"""

from __future__ import annotations

import io
import logging
import pathlib
import re
import sys
import tokenize


ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

ALLOWED_FILES = {
    "src/ultimate_discord_intelligence_bot/core/http_utils.py",  # Compatibility shim
    "src/core/connection_pool.py",  # Uses Session for pooling but routes through http_utils
    # This tool contains a string literal reference used for debugging output only.
    "src/ultimate_discord_intelligence_bot/tools/discord_download_tool.py",
}

# Flag any direct requests.<method>(...) usage. This is intentionally broad
# to catch variable/param usages too; allowed files are excluded above.
# Match an opening parenthesis with optional whitespace (no string literal required)
# so calls like `requests.get(url)` are detected.
# ALSO catch session.get/post and client.get/post patterns to prevent Session/httpx.Client bypass
# Match either direct `requests.get(...)` style calls or calls on variables named
# `session`/`client` (common escape hatches). The tokenized/cleaned source may
# remove whitespace, so we allow optional spaces around dots.
PATTERN = re.compile(
    r"\b(?:"
    r"requests\s*\.\s*(?:get|post|put|delete|patch|head)"
    r"|(?:session|client)\s*\.\s*(?:get|post|put|delete|patch|head)"
    r")\s*\(",
    re.IGNORECASE,
)


def strip_strings_and_comments(text: str) -> str:
    """Remove string literals and comments using tokenize to avoid false positives.

    This preserves actual code structure while eliminating docstrings, inline strings,
    and comments where examples like "requests.get(" might appear.
    """
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        parts: list[str] = []
        for tok_type, tok_str, *_ in tokens:
            if tok_type in (tokenize.STRING, tokenize.COMMENT):
                continue
            # Append token text directly to preserve punctuation adjacency
            parts.append(tok_str)
        return "".join(parts)
    except Exception:
        # Fallback to original text if tokenization fails
        return text


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
        except Exception as exc:
            logging.warning("validate_http_wrappers_usage: failed to read %s: %s", rel, exc)
            continue
        # Remove strings and comments before scanning
        cleaned = strip_strings_and_comments(text)
        if PATTERN.search(cleaned):
            violations.append(rel)
    if violations:
        print("Direct 'requests' usage detected; use core.http_utils helpers instead:")
        for v in sorted(violations):
            print(f" - {v}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
