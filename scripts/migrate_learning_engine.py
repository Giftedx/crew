#!/usr/bin/env python
"""Migration script for LearningEngine import path changes.

This script helps migrate from the deprecated services.learning_engine.LearningEngine
to the new core.learning_engine.LearningEngine import path.

Usage:
    python scripts/migrate_learning_engine.py [--dry-run] [--apply]

Options:
    --dry-run: Show what would be changed without making changes
    --apply: Apply the migration changes
    --help: Show this help message

The script will:
1. Scan for imports of services.learning_engine.LearningEngine
2. Identify different usage patterns (imports, instantiations, references)
3. Provide automated replacement options
4. Generate a migration report
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Maximum examples to show per file in report
MAX_EXAMPLES_PER_FILE = 3

# Files that should NOT be migrated (grandfathered)
ALLOWED_FILES = {
    "scripts/migrate_learning_engine.py",  # Don't modify this script itself
    "src/ultimate_discord_intelligence_bot/services/learning_engine.py",  # The shim itself
    "config/deprecations.yaml",
    "docs/feature_flags.md",
    "docs/configuration.md",
    "docs/dev_assistants/CLAUDE.md",
    "docs/architecture/CLAUDE_CONTEXT.md",
    "docs/operations/CHANGELOG.md",
    "docs/operations/CLAUDE_GUIDE.md",
}

# Replacement patterns for different usage types
REPLACEMENTS = {
    "import_statement": {
        "from ultimate_discord_intelligence_bot.services.learning_engine import LearningEngine": "from core.learning_engine import LearningEngine",
        "from services.learning_engine import LearningEngine": "from core.learning_engine import LearningEngine",
    },
    "import_module": {
        "import ultimate_discord_intelligence_bot.services.learning_engine": "import core.learning_engine",
        "import services.learning_engine": "import core.learning_engine",
    },
    "full_reference": {
        "ultimate_discord_intelligence_bot.services.learning_engine.LearningEngine": "core.learning_engine.LearningEngine",
        "services.learning_engine.LearningEngine": "core.learning_engine.LearningEngine",
    },
}


class MigrationResult:
    """Result of a migration operation."""

    def __init__(self, file_path: Path, line_number: int, old_content: str, new_content: str | None = None):
        self.file_path = file_path
        self.line_number = line_number
        self.old_content = old_content
        self.new_content = new_content

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number}: {self.old_content}"


def should_skip_file(file_path: Path) -> bool:
    """Check if a file should be skipped during migration."""
    relative_path = file_path.relative_to(ROOT)
    return str(relative_path) in ALLOWED_FILES


def find_usage_patterns(file_path: Path) -> list[MigrationResult]:
    """Find all usage patterns of services.learning_engine.LearningEngine in a file."""
    results = []

    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            line_str = line.strip()

            # Check each replacement pattern
            for pattern_type, replacements in REPLACEMENTS.items():
                for old_pattern, new_pattern in replacements.items():
                    if old_pattern in line_str:
                        results.append(
                            MigrationResult(file_path, i, line_str, line_str.replace(old_pattern, new_pattern))
                        )
                        break  # Only one replacement per line

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return results


def scan_codebase() -> dict[Path, list[MigrationResult]]:
    """Scan the entire codebase for services.learning_engine.LearningEngine usage."""
    results = {}

    # Scan Python files
    for py_file in ROOT.rglob("*.py"):
        if should_skip_file(py_file):
            continue

        usages = find_usage_patterns(py_file)
        if usages:
            results[py_file] = usages

    return results


def apply_migrations(results: dict[Path, list[MigrationResult]], dry_run: bool = True) -> None:
    """Apply the migration changes to files."""
    total_changes = 0

    for file_path, usages in results.items():
        if not usages:
            continue

        print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing {file_path.relative_to(ROOT)}:")

        # Read the file
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"  Error reading file: {e}")
            continue

        # Apply changes
        changes_made = 0
        for usage in usages:
            if usage.new_content is None:
                print(f"  Line {usage.line_number}: {usage.old_content} (manual review needed)")
                continue

            old_line = lines[usage.line_number - 1]
            new_line = old_line.replace(usage.old_content, usage.new_content)

            if old_line != new_line:
                if dry_run:
                    print(f"  Line {usage.line_number}: {usage.old_content} -> {usage.new_content}")
                else:
                    lines[usage.line_number - 1] = new_line
                    print(f"  Line {usage.line_number}: Updated")
                changes_made += 1

        # Write back if not dry run
        if not dry_run and changes_made > 0:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                print(f"  Applied {changes_made} changes")
            except Exception as e:
                print(f"  Error writing file: {e}")

        total_changes += changes_made

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Total changes: {total_changes}")


def generate_report(results: dict[Path, list[MigrationResult]]) -> None:
    """Generate a migration report."""
    total_files = len(results)
    total_usages = sum(len(usages) for usages in results.values())

    print("\n" + "=" * 70)
    print("MIGRATION REPORT: services.learning_engine → core.learning_engine")
    print("=" * 70)
    print(f"Total files with usage: {total_files}")
    print(f"Total usage instances: {total_usages}")
    print()

    if results:
        print("Files requiring migration:")
        for file_path, usages in sorted(results.items()):
            print(f"  {file_path.relative_to(ROOT)} ({len(usages)} instances)")
            for usage in usages[:MAX_EXAMPLES_PER_FILE]:  # Show first few examples
                print(f"    Line {usage.line_number}: {usage.old_content}")
            if len(usages) > MAX_EXAMPLES_PER_FILE:
                print(f"    ... and {len(usages) - MAX_EXAMPLES_PER_FILE} more")
        print()

        print("Migration details:")
        print("- Import statements will be updated from 'services.learning_engine' to 'core.learning_engine'")
        print(
            "- Full references will be updated from 'services.learning_engine.LearningEngine' to 'core.learning_engine.LearningEngine'"
        )
        print("- Class instantiation (LearningEngine(...)) remains unchanged")
        print()

        print("Next steps:")
        print("1. Review the changes above")
        print("2. Run with --apply to apply the migrations")
        print("3. Test the changes thoroughly")
        print("4. Update any external documentation or examples")
        print("5. Verify that the shim in services.learning_engine still works during grace period")
    else:
        print("✅ No migration needed - all usage is in allowed files!")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate services.learning_engine.LearningEngine to core.learning_engine.LearningEngine"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show what would be changed without making changes (default)",
    )
    parser.add_argument("--apply", action="store_true", help="Apply the migration changes")
    parser.add_argument(
        "--report-only", action="store_true", help="Only generate report, don't show individual changes"
    )

    args = parser.parse_args()

    if args.apply:
        args.dry_run = False

    print("Scanning codebase for services.learning_engine.LearningEngine usage...")
    results = scan_codebase()

    if not args.report_only:
        apply_migrations(results, dry_run=args.dry_run)

    generate_report(results)

    if results and args.dry_run:
        print("\nTo apply these changes, run with --apply flag")
        return 1
    elif results and not args.dry_run:
        print("\nMigration completed! Please test thoroughly.")
        return 0
    else:
        return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
