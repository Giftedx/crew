"""Feature flag documentation synchronization validator.

Scans the codebase for feature flag usage and ensures `docs/feature_flags.md` is
in sync. Intended to be lightweight (regex + a bit of AST resilience) and free
of third‑party deps so it can run in CI quickly.

Detection heuristics (kept deliberately simple, deterministic, and cheap):

1. Direct env lookups: os.getenv("ENABLE_...") or os.environ.get("ENABLE_...")
2. Settings model aliases: Field(... alias="ENABLE_...") in `core/settings.py`
3. Flag service calls: flags.enabled("<name>") — we include names even if
   lower‑case (e.g. privacy flags) so they appear in the canonical set. Only
   names that either start with ENABLE_ or start with `enable_` (privacy) are
   kept.
4. Explicit constants like `ENABLE_DISCORD_ARCHIVER` where the env var name is
   clearly embedded (pattern ENABLE_[A-Z0-9_]+) within assignments.
5. Pattern for RL domain flags: we record the literal `ENABLE_RL_GLOBAL` plus a
   symbolic pattern marker `ENABLE_RL_<DOMAIN>` when we encounter an f-string
   building `f"ENABLE_RL_{domain.upper()}"`.

The script produces three sets:
- code_flags: flags discovered in source
- documented_flags: flags listed in docs/feature_flags.md (regex extracted)
- deprecated_flags: internal allow-list of flags that may appear in docs but
    can be absent in code (or slated for removal) without failing validation.

Additional allow-lists to avoid noisy failures:
- proposed_flags: future design placeholders documented ahead of implementation
- example_flags: illustrative examples (e.g. a specific RL domain flag)
- internal_alias_flags: internal constant names that differ from the actual
    environment variable (e.g. ENABLE_ARCHIVER wraps ENABLE_DISCORD_ARCHIVER)

Exit codes:
- 0: in sync (after ignoring deprecated & pattern placeholders)
- 1: drift detected (will print human-readable diff)

Programmatic usage:
    from scripts.validate_feature_flags import validate
    validate(raise_on_error=True)

This module avoids any network or disk‑write side effects beyond reading files.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterable


RE_ENABLE = re.compile(r"ENABLE_[A-Z0-9_]+")
RE_PRIVACY = re.compile(r"enable_pii_(?:detection|redaction)")
RE_FIELD_ALIAS = re.compile(r"alias=\"(ENABLE_[A-Z0-9_]+)\"")
RE_FLAGS_ENABLED = re.compile(r"flags\.enabled\(\s*['\"]([^'\"]+)['\"]")
RE_FSTRING_RL = re.compile(r"f\"ENABLE_RL_{domain\.upper\(\)}\"")

DOC_PATH = Path(__file__).parent.parent / "docs" / "feature_flags.md"
SRC_PATH = Path(__file__).parent.parent / "src"

# Flags that are intentionally deprecated but still documented until removal.
DEPRECATED: set[str] = {"ENABLE_HTTP_RETRY"}
# Symbolic pattern placeholders that are expected in docs but not discovered as literal flags.
PATTERN_PLACEHOLDERS: set[str] = {"ENABLE_RL_<DOMAIN>"}
# Proposed (future) flags intentionally documented early.
PROPOSED_FLAGS: set[str] = {"ENABLE_DISTRIBUTED_RATE_LIMITING"}
# Example-only flags shown for illustration (dynamic RL domains, etc.).
EXAMPLE_FLAGS: set[str] = {"ENABLE_RL_ROUTING"}
# Internal alias constants (not actual env var names) to ignore in drift calc.
INTERNAL_ALIAS_FLAGS: set[str] = {"ENABLE_ARCHIVER"}


def _iter_source_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        # Skip virtual env or build outputs just in case
        if any(part.startswith(".") for part in p.parts):
            continue
        yield p


def discover_code_flags() -> set[str]:
    flags: set[str] = set()
    rl_pattern_seen = False
    for file in _iter_source_files(SRC_PATH):
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:  # pragma: no cover - defensive logging
            logging.debug("Failed reading %s: %s", file, exc)
            continue
        # Direct ENABLE_ pattern occurrences
        for m in RE_ENABLE.finditer(text):
            flags.add(m.group(0))
        # Field alias patterns
        for m in RE_FIELD_ALIAS.finditer(text):
            flags.add(m.group(1))
        # flags.enabled calls
        for m in RE_FLAGS_ENABLED.finditer(text):
            name = m.group(1)
            if name.startswith(("ENABLE_", "enable_pii_")):
                flags.add(name)
        # RL f-string pattern marker
        if RE_FSTRING_RL.search(text):
            rl_pattern_seen = True
    if rl_pattern_seen:
        flags.add("ENABLE_RL_GLOBAL")  # ensure global present
        # We add pattern placeholder only in docs comparison stage; code uses dynamic set.
    return flags


def discover_documented_flags(doc_path: Path = DOC_PATH) -> set[str]:
    text = doc_path.read_text(encoding="utf-8")
    documented: set[str] = set(RE_ENABLE.findall(text))
    # privacy lowercase flags
    for m in RE_PRIVACY.finditer(text):
        documented.add(m.group(0))
    # Add pattern placeholder if present explicitly
    if "ENABLE_RL_<DOMAIN>" in text:
        documented.add("ENABLE_RL_<DOMAIN>")
    return documented


def diff_flags(code_flags: set[str], documented_flags: set[str]) -> tuple[set[str], set[str]]:
    """Return (undocumented, stale) sets after accounting for deprecated & patterns.

    - undocumented: in code but not documented (excluding deprecated & pattern placeholders)
    - stale: in docs but not in code and not deprecated and not pattern placeholder
    """
    normalized_code = set(code_flags)
    normalized_docs = set(documented_flags)

    # Remove deprecated from consideration if they no longer appear in code
    effective_docs = {f for f in normalized_docs if f not in DEPRECATED}
    # Pattern placeholders are documentation-only aids
    effective_docs = {f for f in effective_docs if f not in PATTERN_PLACEHOLDERS}

    # Remove internal alias flags from consideration (they need not be documented)
    normalized_code -= INTERNAL_ALIAS_FLAGS

    undocumented = normalized_code - normalized_docs
    stale = effective_docs - (normalized_code | PROPOSED_FLAGS | EXAMPLE_FLAGS)

    # Remove stale items that are explicitly proposed / examples
    stale -= PROPOSED_FLAGS
    stale -= EXAMPLE_FLAGS
    return undocumented, stale


def validate(raise_on_error: bool = False) -> bool:
    code_flags = discover_code_flags()
    documented_flags = discover_documented_flags()
    undocumented, stale = diff_flags(code_flags, documented_flags)

    ok = not undocumented and not stale
    if not ok:
        lines = ["Feature flag documentation drift detected:"]
        if undocumented:
            lines.append("  Undocumented flags (present in code, missing in docs):")
            lines.extend([f"    - {f}" for f in sorted(undocumented)])
        if stale:
            lines.append("  Stale documented flags (listed in docs, absent in code):")
            lines.extend([f"    - {f}" for f in sorted(stale)])
        message = "\n".join(lines)
        if raise_on_error:
            raise SystemExit(message)
        print(message, file=sys.stderr)
    return ok


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    # trivial CLI: no args
    ok = validate(raise_on_error=False)
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
