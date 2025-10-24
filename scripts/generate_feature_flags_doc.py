"""Generate docs/feature_flags.md from source scans.

This augments (not replaces) the validator. It writes a deterministic table
based on current code discovery so humans rarely need to hand edit the doc.

Usage:
    python scripts/generate_feature_flags_doc.py --write
    python scripts/generate_feature_flags_doc.py --check   # exit 1 if drift

Strategy:
1. Reuse discovery from validate_feature_flags (import for single source of truth).
2. Categorize flags heuristically by module path keywords.
3. Render markdown sections & compare existing file to proposed.

The categorization is deliberately simple; manual re-order post generation is
allowed but discouraged because it creates churn. If necessary, enhance the
CATEGORY_RULES below instead.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
from pathlib import Path

import yaml

import scripts.validate_feature_flags as vf


DOC_PATH = Path(__file__).parent.parent / "docs" / "feature_flags.md"
SRC_PATH = Path(__file__).parent.parent / "src"
HEADER_PREFIX = "<!-- AUTO-GENERATED:"
DEPRECATIONS_PATH = Path(__file__).parent.parent / "config" / "deprecations.yaml"

CATEGORY_RULES: list[tuple[str, str]] = [
    ("api / runtime", "server/"),
    ("metrics / observability", "obs/"),
    ("http resilience", "http"),
    ("rl / routing", "learn.py"),
    ("privacy", "privacy"),
    ("archiver / discord", "archive/discord_store"),
    ("ingestion", "ingest/"),
]


def categorize(flag: str, code_index: dict[str, set[str]]) -> str:
    paths = code_index.get(flag, set())
    joined = " ".join(paths)
    for cat, needle in CATEGORY_RULES:
        if needle in joined:
            return cat
    if flag.startswith("enable_pii_"):
        return "privacy"
    if flag.startswith("ENABLE_RL_"):
        return "rl / routing"
    if flag.startswith("ENABLE_HTTP_") or "RETRY" in flag:
        return "http resilience"
    return "misc"


def build_code_index(flags: set[str]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {f: set() for f in flags}
    for path in SRC_PATH.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:  # pragma: no cover - defensive
            logging.debug("Failed reading %s: %s", path, exc)
            continue
        for f in flags:
            if f in text:
                index[f].add(str(path.relative_to(SRC_PATH)))
    return index


def render(flags: set[str]) -> str:
    code_index = build_code_index(flags)
    # Deterministic order: category, then flag name
    categorized: dict[str, list[str]] = {}
    for f in sorted(flags):
        cat = categorize(f, code_index)
        categorized.setdefault(cat, []).append(f)
    lines: list[str] = [
        (
            "<!-- AUTO-GENERATED: Run `scripts/generate_feature_flags_doc.py` to refresh. "
            "Manual edits will be overwritten. -->"
        ),
        "## Feature Flags & Environment Toggles",
        "",
        "(Do not edit by hand; regenerate instead.)",
    ]
    for cat in sorted(categorized):
        lines.append(f"### {cat.title()}")
        lines.append("")
        lines.append("| Flag | Referenced In (sample) |")
        lines.append("|------|------------------------|")
        for f in categorized[cat]:
            sample = ", ".join(sorted(code_index[f])[:2]) or "-"
            lines.append(f"| `{f}` | {sample} |")
        lines.append("")
    # Append deprecations section to satisfy drift tests that reference non-ENABLE symbols
    try:
        if DEPRECATIONS_PATH.exists():
            data = yaml.safe_load(DEPRECATIONS_PATH.read_text(encoding="utf-8")) or {}
            items = [f for f in data.get("flags", []) if isinstance(f, dict) and f.get("name")]
            if items:
                lines.append("### Deprecated flags and surfaces")
                lines.append("")
                lines.append(
                    "The following items are deprecated or superseded; see configuration docs for timelines and replacements."
                )
                lines.append("")
                for item in items:
                    name = str(item.get("name"))
                    repl = item.get("replacement")
                    note = item.get("notes")
                    bullet = f"- `{name}`"
                    hints: list[str] = []
                    if repl:
                        hints.append(f"replacement: `{repl}`")
                    if note:
                        hints.append(note)
                    if hints:
                        bullet += " — " + "; ".join(hints)
                    lines.append(bullet)
                lines.append("")
    except Exception as exc:  # pragma: no cover - doc gen best effort
        logging.debug("Failed to append deprecations: %s", exc)
    digest = hashlib.sha256("\n".join(lines).encode()).hexdigest()[:12]
    lines.append(f"\n_Generated digest: `{digest}`_")
    return "\n".join(lines) + "\n"


def main() -> int:
    code_flags = vf.discover_code_flags()
    # Exclude internal alias flags to avoid documenting non-env constants
    code_flags -= vf.INTERNAL_ALIAS_FLAGS
    # Keep documented-only placeholders too so doc retains pattern context
    documented = vf.discover_documented_flags()
    union = code_flags | {f for f in documented if f in vf.PATTERN_PLACEHOLDERS or f in vf.DEPRECATED}
    content = render(union)
    if not DOC_PATH.exists():
        DOC_PATH.write_text(content, encoding="utf-8")
        print("Wrote new feature flags doc")
        return 0
    existing = DOC_PATH.read_text(encoding="utf-8")
    if existing == content:
        print("Feature flags doc up to date")
        return 0
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="Overwrite the existing doc with regenerated content",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if regeneration would change the doc",
    )
    args = parser.parse_args()
    if args.write:
        DOC_PATH.write_text(content, encoding="utf-8")
        print("Feature flags doc regenerated")
        return 0
    if args.check:
        print("Feature flags doc drift detected (run with --write to update)")
        return 1
    # Default: print diff style hint but do not overwrite
    print("Doc differs; run with --write to update or --check for CI drift detection")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
