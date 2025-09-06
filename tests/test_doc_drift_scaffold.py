"""Feature flag documentation drift test.

Validates that every deprecation-tracked flag in `config/deprecations.yaml` is
present in `docs/feature_flags.md` (unless explicitly removed from active scope).
Additional future enhancements can diff ENABLE_* patterns in source code.
"""

import re
from pathlib import Path

import yaml

DOC_PATH = Path("docs/feature_flags.md")
DEPRECATIONS_PATH = Path("config/deprecations.yaml")


def _load_deprecation_flags():
    if not DEPRECATIONS_PATH.exists():  # pragma: no cover - defensive
        return []
    data = yaml.safe_load(DEPRECATIONS_PATH.read_text(encoding="utf-8")) or {}
    return [f["name"] for f in data.get("flags", []) if "name" in f]


def _extract_documented_flags(md_text: str):
    # capture backticked code spans
    code_spans = set(re.findall(r"`([A-Za-z0-9_\.]+)`", md_text))
    # capture first column raw tokens (between pipes) including dots
    table_first_col = set()
    for line in md_text.splitlines():
        if line.strip().startswith("| ") and "|" in line[2:]:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if parts:
                token = parts[0]
                # strip optional backticks
                token = token.strip("`")
                if re.match(r"[A-Za-z0-9_\.]+", token):
                    table_first_col.add(token)
    return code_spans | table_first_col


def test_deprecation_flags_documented():
    flags = _load_deprecation_flags()
    assert flags, "Expected at least one deprecation-tracked flag"
    assert DOC_PATH.exists(), "Feature flags documentation file missing"
    md = DOC_PATH.read_text(encoding="utf-8")
    documented = _extract_documented_flags(md)
    missing = [f for f in flags if f not in documented]
    assert not missing, f"Undocumented deprecated flags: {missing}"


def test_doc_contains_retry_precedence_note():
    # Ensure unified retry precedence is documented (heuristic keyword search)
    if not DOC_PATH.exists():  # pragma: no cover
        raise AssertionError("Missing feature flags doc")
    text = DOC_PATH.read_text(encoding="utf-8")
    assert "ENABLE_HTTP_RETRY" in text
    assert "superseded" in text.lower() or "deprecated" in text.lower()
