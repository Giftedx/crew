#!/usr/bin/env python3
"""Guard script preventing new modules in deprecated directories.

This script enforces architectural consolidation decisions by blocking
new files in directories marked as deprecated per ADRs 0001-0005.

Exit codes:
  0 - No violations found
  1 - New modules detected in deprecated directories
"""

from __future__ import annotations

import subprocess
import sys


# Directories marked as deprecated (relative to repo root)
DEPRECATED_DIRS = [
    "src/core/routing",
    "src/ai/routing",
    "src/performance",
    "src/ultimate_discord_intelligence_bot/services/cache_optimizer.py",
    "src/ultimate_discord_intelligence_bot/services/rl_cache_optimizer.py",
]

# Files explicitly allowed in deprecated directories (legacy compatibility)
ALLOWED_FILES = {
    "src/core/routing/.deprecated",
    "src/ai/routing/.deprecated",
    "src/performance/.deprecated",
}


def get_staged_new_files() -> list[str]:
    """Get list of new files staged for commit."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-status", "--diff-filter=A"],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split("\n")
        return [line.split("\t", 1)[1] for line in lines if line.startswith("A\t")]
    except subprocess.CalledProcessError:
        return []


def check_deprecated_violations(new_files: list[str]) -> list[tuple[str, str]]:
    """Check if any new files are in deprecated directories.

    Returns list of (file_path, deprecated_dir) tuples for violations.
    """
    violations = []

    for file_path in new_files:
        if file_path in ALLOWED_FILES:
            continue

        for deprecated_dir in DEPRECATED_DIRS:
            if file_path.startswith(deprecated_dir):
                violations.append((file_path, deprecated_dir))
                break

    return violations


def main() -> int:
    """Run deprecation guard check."""
    new_files = get_staged_new_files()

    if not new_files:
        print("✓ No new files staged")
        return 0

    violations = check_deprecated_violations(new_files)

    if not violations:
        print(f"✓ Checked {len(new_files)} new files - no deprecated directory violations")
        return 0

    print(f"❌ Found {len(violations)} violations:")
    print()
    for file_path, deprecated_dir in violations:
        print(f"  {file_path}")
        print(f"    → in deprecated directory: {deprecated_dir}")

        # Find relevant ADR
        adr_refs = {
            "src/core/routing": "ADR-0003 (docs/architecture/adr-0003-routing-consolidation.md)",
            "src/ai/routing": "ADR-0003 (docs/architecture/adr-0003-routing-consolidation.md)",
            "src/performance": "ADR-0001, ADR-0005 (cache + analytics consolidation)",
        }

        for dir_prefix, adr in adr_refs.items():
            if deprecated_dir.startswith(dir_prefix):
                print(f"    → See {adr}")
                break

    print()
    print("These directories are deprecated and should not receive new modules.")
    print("Please use the canonical replacements documented in the ADRs.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
