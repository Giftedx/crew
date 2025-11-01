#!/usr/bin/env python3
"""Script to migrate crew callers to new unified API.

This script automatically updates import statements across the codebase
to use the new crew_core package instead of legacy crew*.py files.
"""

from __future__ import annotations

import re
from pathlib import Path

# Old import patterns to migrate
OLD_PATTERNS = [
    (
        r"from ultimate_discord_intelligence_bot\.crew import (.+)",
        r"from ultimate_discord_intelligence_bot.crew_core import \1",
    ),
    (
        r"from ultimate_discord_intelligence_bot\.crew_new import (.+)",
        r"from ultimate_discord_intelligence_bot.crew_core import \1",
    ),
    (
        r"from ultimate_discord_intelligence_bot\.crew_modular import (.+)",
        r"from ultimate_discord_intelligence_bot.crew_core import \1",
    ),
    (
        r"from ultimate_discord_intelligence_bot\.crew_refactored import (.+)",
        r"from ultimate_discord_intelligence_bot.crew_core import \1",
    ),
    (
        r"from ultimate_discord_intelligence_bot\.crew_consolidation import (.+)",
        r"from ultimate_discord_intelligence_bot.crew_core import \1",
    ),
    (
        r"from ultimate_discord_intelligence_bot\.crew_error_handler import (.+)",
        r"from ultimate_discord_intelligence_bot.crew_core.error_handling import \1",
    ),
    (
        r"from ultimate_discord_intelligence_bot\.crew_insight_helpers import (.+)",
        r"from ultimate_discord_intelligence_bot.crew_core.insights import \1",
    ),
    (
        r"import ultimate_discord_intelligence_bot\.crew",
        r"import ultimate_discord_intelligence_bot.crew_core",
    ),
]


def migrate_file(file_path: Path) -> tuple[bool, int]:
    """Migrate a single file.

    Args:
        file_path: Path to the file to migrate

    Returns:
        Tuple of (modified, replacement_count)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content
        total_replacements = 0

        for old_pattern, new_pattern in OLD_PATTERNS:
            content, count = re.subn(old_pattern, new_pattern, content)
            total_replacements += count

        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            return (True, total_replacements)

        return (False, 0)

    except Exception as e:
        print(f"❌ Error migrating {file_path}: {e}")
        return (False, 0)


def main() -> None:
    """Migrate all Python files in the repository."""
    src_dir = Path("src")

    if not src_dir.exists():
        print("❌ src/ directory not found")
        return

    # Find all Python files, excluding crew_core itself
    python_files = [
        f
        for f in src_dir.rglob("*.py")
        if "crew_core" not in str(f) and not str(f).endswith("__pycache__")
    ]

    print(f"🔍 Found {len(python_files)} Python files to check")
    print()

    modified_files = 0
    total_replacements = 0

    for py_file in python_files:
        modified, replacements = migrate_file(py_file)
        if modified:
            modified_files += 1
            total_replacements += replacements
            print(f"✅ Migrated: {py_file} ({replacements} replacements)")

    print()
    print("=" * 60)
    print(f"✅ Migration complete!")
    print(f"   Files modified: {modified_files}")
    print(f"   Total replacements: {total_replacements}")
    print("=" * 60)

    # Create deprecation warnings in old files
    print()
    print("📝 Adding deprecation warnings to legacy files...")

    legacy_files = [
        "src/ultimate_discord_intelligence_bot/crew.py",
        "src/ultimate_discord_intelligence_bot/crew_new.py",
        "src/ultimate_discord_intelligence_bot/crew_modular.py",
        "src/ultimate_discord_intelligence_bot/crew_refactored.py",
        "src/ultimate_discord_intelligence_bot/crew_consolidation.py",
        "src/ultimate_discord_intelligence_bot/crew_error_handler.py",
        "src/ultimate_discord_intelligence_bot/crew_insight_helpers.py",
    ]

    deprecation_notice = '''"""
DEPRECATED: This file is deprecated and will be removed in a future version.
Please use ultimate_discord_intelligence_bot.crew_core instead.

Migration guide:
- Import from crew_core instead of this module
- Use UnifiedCrewExecutor for crew execution
- Use CrewErrorHandler for error handling
- Use CrewInsightGenerator for insight generation

Example:
    from ultimate_discord_intelligence_bot.crew_core import (
        UnifiedCrewExecutor,
        CrewConfig,
        CrewTask,
    )
"""

import warnings

warnings.warn(
    "This module is deprecated. Use ultimate_discord_intelligence_bot.crew_core instead.",
    DeprecationWarning,
    stacklevel=2,
)

'''

    for legacy_file in legacy_files:
        legacy_path = Path(legacy_file)
        if legacy_path.exists():
            try:
                content = legacy_path.read_text(encoding="utf-8")
                if "DEPRECATED" not in content:
                    # Add deprecation notice at the top (after any shebang/encoding)
                    lines = content.split("\n")
                    insert_index = 0

                    # Skip shebang and encoding declarations
                    for i, line in enumerate(lines):
                        if line.startswith("#") and (
                            "coding" in line or "!" in line
                        ):
                            insert_index = i + 1
                        else:
                            break

                    lines.insert(insert_index, deprecation_notice)
                    legacy_path.write_text("\n".join(lines), encoding="utf-8")
                    print(f"   ✅ Added warning to {legacy_file}")
            except Exception as e:
                print(f"   ❌ Failed to add warning to {legacy_file}: {e}")

    print()
    print("🎉 All done! Please run tests to validate the migration.")


if __name__ == "__main__":
    main()
