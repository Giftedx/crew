#!/usr/bin/env python3
"""Documentation validation script to check links and file references.

Optional: pass --fail-imports to treat import issues as failures.
"""

import argparse
import re
import sys
from pathlib import Path


def check_file_references(doc_content: str, doc_path: Path, repo_root: Path, docs_dir: Path) -> list[str]:
    """Check if file paths referenced in documentation exist.

    Heuristics:
    - Backticked file references (e.g., `config/retry.yaml`, `core/http_utils.py`) are assumed repo-root relative.
      If not found, attempt smart fallbacks:
        * If the path starts with a known top-level package (core/, obs/, ingest/, server/, ultimate_discord_intelligence_bot/),
          also check under src/ (e.g., src/core/http_utils.py).
        * If it's a bare filename (no '/'), search under src/ recursively for a match.
    - Markdown links to .md files are resolved relative to the docs directory for typical intra-doc links.
    """
    issues: list[str] = []

    known_src_prefixes = (
        "core/",
        "obs/",
        "ingest/",
        "server/",
        "ultimate_discord_intelligence_bot/",
        "memory/",
        "security/",
        "scheduler/",
    )

    # Backticked file refs and explicit File:/Directory: refs (repo-root semantics)
    root_ref_patterns = [
        r"`([^`]*\.(?:py|yaml|json|md))`",
        r"File:\*\* `([^`]+)`",
        r"Directory:\*\* `([^`]+)`",
    ]
    for pattern in root_ref_patterns:
        matches = re.findall(pattern, doc_content)
        for match in matches:
            raw = match.strip()
            # First try repo-root
            candidate = repo_root / raw
            ok = candidate.exists()
            # If not found, try src-prefixed for known packages
            if not ok and any(raw.startswith(p) for p in known_src_prefixes):
                candidate = repo_root / "src" / raw
                ok = candidate.exists()
            # If still not, and no directory components present, search under src recursively
            if not ok and "/" not in raw:
                found = list((repo_root / "src").rglob(raw))
                ok = len(found) > 0
            if not ok:
                issues.append(f"Missing file/directory: {raw}")

    # Markdown links resolved relative to docs dir (typical intra-doc links)
    md_link_pattern = r"\[.*\]\(([^)]*\.md)\)"
    for raw in re.findall(md_link_pattern, doc_content):
        link = raw.strip()
        # Absolute links (starting with http) are ignored by this checker
        if link.startswith("http://") or link.startswith("https://"):
            continue
        # Resolve relative to docs dir
        candidate = (docs_dir / link).resolve()
        if not candidate.exists():
            issues.append(f"Missing file/directory: {link}")

    return issues


def check_import_statements(doc_content):
    """Check if import statements in code blocks are valid."""
    issues: list[str] = []

    # Extract Python code blocks
    code_blocks = re.findall(r"```python\n(.*?)\n```", doc_content, re.DOTALL)

    for code_block in code_blocks:
        import_lines = [
            line.strip() for line in code_block.split("\n") if line.strip().startswith(("import ", "from "))
        ]
        # PERF401: build transformed list and extend once instead of appending inside a loop
        issues.extend(
            f"Import may need PYTHONPATH: {import_line}"
            for import_line in import_lines
            if "ultimate_discord_intelligence_bot" in import_line
        )

    return issues


def validate_documentation(fail_imports: bool = False, ignore_import_files: set[str] | None = None):
    """Main validation function.

    If ``fail_imports`` is True, import issues are included in the failure count.
    """
    docs_dir = Path("/home/crew/docs")
    repo_root = Path("/home/crew")
    total_issues = []
    ignore_import_files = ignore_import_files or set()

    for doc_file in docs_dir.glob("*.md"):
        print(f"Checking {doc_file.name}...")

        with open(doc_file, encoding="utf-8") as f:
            content = f.read()

        # Check file references with improved resolution
        file_issues = check_file_references(content, doc_file, repo_root, docs_dir)
        if file_issues:
            print(f"  File reference issues in {doc_file.name}:")
            for issue in file_issues:
                print(f"    ❌ {issue}")
                total_issues.append((doc_file.name, issue))

        # Check imports
        import_issues = check_import_statements(content)
        if import_issues:
            print(f"  Import issues in {doc_file.name}:")
            for issue in import_issues:
                print(f"    ⚠️  {issue}")
            if fail_imports and doc_file.name not in ignore_import_files:
                total_issues.extend((doc_file.name, i) for i in import_issues)

        if not file_issues and not import_issues:
            print("  ✅ No issues found")

    print(f"\nSummary: Found {len(total_issues)} file reference issues across all docs")
    return len(total_issues) == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-imports", action="store_true", help="Fail if import issues are detected")
    parser.add_argument(
        "--ignore-import-files",
        type=str,
        default="",
        help="Comma-separated list of doc file basenames to ignore import warnings for (only used with --fail-imports)",
    )
    args = parser.parse_args()
    ignore_set = (
        set(filter(None, (s.strip() for s in args.ignore_import_files.split(","))))
        if args.ignore_import_files
        else set()
    )
    success = validate_documentation(fail_imports=args.fail_imports, ignore_import_files=ignore_set)
    sys.exit(0 if success else 1)
