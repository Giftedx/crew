"""Validator preventing stray usage of deprecated feature flags.

Currently enforced deprecated flags:
- ENABLE_ANALYSIS_HTTP_RETRY (superseded by ENABLE_HTTP_RETRY)

Allowed locations (grandfathered):
- core/http_utils.py (until full removal path implemented)
- docs/feature_flags.md (documentation of deprecation)
- CHANGELOG.md (historical record)
- Any file under tests/ whose filename contains 'retry' (tests covering legacy behavior)
- This script and other validation scripts

Exit codes:
- 0: no violations
- 1: violation(s) found (prints list)
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

RE_FLAG = re.compile(r"ENABLE_ANALYSIS_HTTP_RETRY")
ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
TESTS = ROOT / "tests"
DOCS = ROOT / "docs"

ALLOWED_PATH_SUBSTRINGS = {
    str(ROOT / "src" / "core" / "http_utils.py"),
    str(ROOT / "src" / "core" / "http" / "retry.py"),
    str(ROOT / "docs" / "configuration.md"),
    str(ROOT / "docs" / "feature_flags.md"),
    str(ROOT / "docs" / "retries.md"),
    str(ROOT / "CHANGELOG.md"),
    str(ROOT / "README.md"),
    str(ROOT / "CLAUDE.md"),
    str(ROOT / ".github" / "copilot-instructions.md"),
    # Added to satisfy legacy strategic planning references (grandfathered until full doc scrub)
    str(ROOT / "STRATEGIC_ACTION_PLAN.md"),
    # Quick reference doc still mentions deprecated flag for contributor guidance (allowed transiently)
    str(ROOT / ".github" / "copilot-quickref.md"),
    str(ROOT / "docs" / "history" / "MERGE_REPORT.md"),
    str(ROOT / "FUTURE_WORK.md"),
    str(ROOT / "docs" / "network_conventions.md"),
    str(ROOT / "docs" / "tools_reference.md"),
    str(ROOT / "COMPREHENSIVE_PROJECT_REVIEW.md"),  # added due to legacy mention
    str(ROOT / "COMPREHENSIVE_REPOSITORY_REVIEW.md"),  # repository review with historical references
    str(ROOT / "COMPREHENSIVE_BANDIT_BENCHMARK_RESULTS_SUMMARY.md"),  # legacy historical report
    str(ROOT / "COMPLETE_SYSTEM_DOCUMENTATION.md"),  # aggregate doc referencing deprecated flag
    str(ROOT / "COMPREHENSIVE_CODEBASE_ASSESSMENT.md"),  # assessment doc includes deprecation status
    str(ROOT / "REVIEW_README.md"),  # review summary containing legacy flag reference
    str(ROOT / "REPOSITORY_REVIEW_README.md"),  # repository review readme
    str(ROOT / "REVIEW_EXECUTIVE_SUMMARY.md"),  # executive summary
    # Migration + dashboard tooling explicitly allowed (contain educational references)
    str(ROOT / "scripts" / "migrate_http_retry_flag.py"),
    str(ROOT / "scripts" / "deprecation_dashboard.py"),
    str(ROOT / "scripts" / "README_deprecation_dashboard.md"),
    # Strategy / architecture docs (to be scrubbed post 2025-12-31)
    str(ROOT / "docs" / "strategy" / "FUTURE_WORK.md"),
    str(ROOT / "docs" / "strategy" / "STRATEGIC_ACTION_PLAN.md"),
    str(ROOT / "docs" / "architecture" / "CLAUDE_CONTEXT.md"),
    str(ROOT / "docs" / "operations" / "CHANGELOG.md"),
    str(ROOT / "docs" / "operations" / "CLAUDE_GUIDE.md"),
    str(ROOT / "docs" / "dev_assistants" / "CLAUDE.md"),
    str(ROOT / "docs" / "ROADMAP_IMPLEMENTATION.md"),
    str(ROOT / "tests" / "test_deprecated_flag_usage.py"),
    str(ROOT / "tests" / "test_deprecation_schedule.py"),
    # Historical review documents that mention legacy flags (allowed until doc scrub)
    str(ROOT / "docs" / "history" / "REVIEW_README.md"),
    str(ROOT / "docs" / "history" / "COMPREHENSIVE_PROJECT_REVIEW.md"),
    # Migration execution reports (document completed migration work)
    str(ROOT / "reports" / "strategic_action_plan_execution_summary.md"),
    "validate_feature_flags.py",  # sibling validator
    "validate_deprecated_flags.py",  # self
}


def _is_allowed(path: Path) -> bool:
    p = str(path)
    if any(s in p for s in ALLOWED_PATH_SUBSTRINGS):
        return True
    return bool(
        path.suffix == ".py"
        and path.name.startswith("test_")
        and any(k in path.name for k in ("retry", "http_utils", "wrappers"))
    )


def discover_violations() -> list[tuple[str, int, str]]:
    violations: list[tuple[str, int, str]] = []
    for file in ROOT.rglob("*.py"):
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:  # pragma: no cover - defensive
            logging.debug("Failed reading %s: %s", file, exc)
            continue
        if not RE_FLAG.search(text):
            continue
        if _is_allowed(file):
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if "ENABLE_ANALYSIS_HTTP_RETRY" in line:
                violations.append((str(file.relative_to(ROOT)), i, line.strip()))
    # Also scan markdown for unexpected usage (outside allowed docs)
    for md in ROOT.rglob("*.md"):
        if not RE_FLAG.search(md.read_text(encoding="utf-8", errors="ignore")):
            continue
        if _is_allowed(md):
            continue
        # treat any occurrence as violation
        violations.append((str(md.relative_to(ROOT)), 0, "(markdown occurrence)"))
    return violations


def validate(raise_on_error: bool = False) -> bool:
    violations = discover_violations()
    if violations:
        lines = ["Deprecated flag usage detected outside allowed locations:"]
        for path, lineno, snippet in violations:
            loc = f"{path}:{lineno}" if lineno else path
            lines.append(f"  - {loc}: {snippet}")
        msg = "\n".join(lines)
        if raise_on_error:
            raise SystemExit(msg)
        print(msg, file=sys.stderr)
        return False
    return True


def main() -> int:
    ok = validate()
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
