#!/usr/bin/env python3
"""Fast grep-based import counter for quick verification.

Quick verification tool using grep to count imports by pattern.
Faster than AST analysis but less precise.

Usage:
    python scripts/count_imports.py > import-count-baseline.txt
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def count_imports(pattern: str, directory: Path = Path("src/")) -> int:
    """Count imports matching a pattern using grep.

    Args:
        pattern: Grep pattern to search for
        directory: Directory to search in

    Returns:
        Count of matching lines
    """
    try:
        result = subprocess.run(
            ["grep", "-r", pattern, str(directory)],
            capture_output=True,
            text=True,
            check=False,
        )
        # Filter out __pycache__ matches
        lines = [line for line in result.stdout.split("\n") if line and "__pycache__" not in line]
        return len(lines)
    except Exception:
        return 0


def main() -> int:
    """Main entry point."""
    directory = Path("src/")
    patterns = [
        ("from core.", "core.* imports"),
        ("from ai.", "ai.* imports"),
        ("from obs.", "obs.* imports"),
        ("from ingest.", "ingest.* imports"),
        ("from analysis.", "analysis.* imports"),
        ("from memory.", "memory.* imports (excluding domains.memory)"),
        ("from platform.", "platform.* imports"),
        ("from domains.", "domains.* imports"),
    ]

    print("Import Count Baseline")
    print("=" * 60)
    print(f"Directory: {directory}\n")

    for pattern, description in patterns:
        count = count_imports(pattern, directory)
        print(f"{description}: {count}")

    print("\n" + "=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
