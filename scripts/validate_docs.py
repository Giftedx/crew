#!/usr/bin/env python3
"""Documentation validation script to check links and file references."""

import re
import sys
from pathlib import Path


def check_file_references(doc_content, base_path="/home/crew"):
    """Check if file paths referenced in documentation exist."""
    issues = []

    # Find file path references
    file_patterns = [
        r"`([^`]*\.(?:py|yaml|json|md))`",  # Files in backticks
        r"File:\*\* `([^`]+)`",  # File: references
        r"Directory:\*\* `([^`]+)`",  # Directory: references
        r"\[.*\]\(([^)]*\.md)\)",  # Markdown links
    ]

    for pattern in file_patterns:
        matches = re.findall(pattern, doc_content)
        for match in matches:
            file_path = Path(base_path) / match
            if not file_path.exists():
                issues.append(f"Missing file/directory: {match}")

    return issues


def check_import_statements(doc_content):
    """Check if import statements in code blocks are valid."""
    issues: list[str] = []

    # Extract Python code blocks
    code_blocks = re.findall(r"```python\n(.*?)\n```", doc_content, re.DOTALL)

    for code_block in code_blocks:
        import_lines = [
            line.strip()
            for line in code_block.split("\n")
            if line.strip().startswith(("import ", "from "))
        ]
        # PERF401: build transformed list and extend once instead of appending inside a loop
        issues.extend(
            f"Import may need PYTHONPATH: {import_line}"
            for import_line in import_lines
            if "ultimate_discord_intelligence_bot" in import_line
        )

    return issues


def validate_documentation():
    """Main validation function."""
    docs_dir = Path("/home/crew/docs")
    total_issues = []

    for doc_file in docs_dir.glob("*.md"):
        print(f"Checking {doc_file.name}...")

        with open(doc_file, encoding="utf-8") as f:
            content = f.read()

        # Check file references
        file_issues = check_file_references(content)
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

        if not file_issues and not import_issues:
            print("  ✅ No issues found")

    print(f"\nSummary: Found {len(total_issues)} file reference issues across all docs")
    return len(total_issues) == 0


if __name__ == "__main__":
    success = validate_documentation()
    sys.exit(0 if success else 1)
