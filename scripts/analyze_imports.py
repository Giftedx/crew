#!/usr/bin/env python3
"""AST-based import analysis tool.

Analyzes all Python files to generate import dependency graphs and counts.

Usage:
    python scripts/analyze_imports.py --baseline src/ > import-counts-baseline.json
    python scripts/analyze_imports.py src/ > import-counts.json
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def extract_imports(file_path: Path) -> list[str]:
    """Extract all imports from a Python file using AST.

    Args:
        file_path: Path to Python file

    Returns:
        List of import module names
    """
    imports: list[str] = []
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Failed to parse {file_path}: {e}")
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports


def categorize_import(module_name: str) -> str:
    """Categorize import by source pattern.

    Args:
        module_name: Module name from import

    Returns:
        Category string (legacy, platform, domains, app, stdlib, third-party)
    """
    if not module_name:
        return "unknown"

    parts = module_name.split(".")

    # Standard library
    stdlib_modules = {
        "os",
        "sys",
        "logging",
        "typing",
        "pathlib",
        "collections",
        "dataclasses",
        "enum",
        "asyncio",
        "json",
        "time",
        "datetime",
        "math",
        "random",
        "hashlib",
        "urllib",
        "http",
        "email",
        "re",
        "string",
        "functools",
        "itertools",
        "abc",
        "contextlib",
        "warnings",
    }
    if parts[0] in stdlib_modules:
        return "stdlib"

    # Legacy imports
    if parts[0] in ("core", "ai", "obs", "ingest", "analysis", "memory"):
        return "legacy"
    if module_name.startswith("src.core") or module_name.startswith("src.ai") or module_name.startswith("src.obs"):
        return "legacy"
    if module_name.startswith("ultimate_discord_intelligence_bot.core"):
        return "legacy"
    if module_name.startswith("ultimate_discord_intelligence_bot.ai"):
        return "legacy"

    # Platform imports
    if parts[0] == "platform" or module_name.startswith("platform."):
        return "platform"

    # Domains imports
    if parts[0] == "domains" or module_name.startswith("domains."):
        return "domains"

    # App imports
    if parts[0] == "app" or module_name.startswith("app."):
        return "app"

    # Third-party
    return "third-party"


def analyze_directory(directory: Path) -> dict[str, Any]:
    """Analyze all imports in a directory.

    Args:
        directory: Root directory to analyze

    Returns:
        Analysis results dictionary
    """
    all_imports: list[str] = []
    imports_by_category: defaultdict[str, int] = defaultdict(int)
    imports_by_module: Counter[str] = Counter()
    legacy_patterns: list[str] = []

    py_files = list(directory.rglob("*.py"))
    total_files = len(py_files)

    print(f"Analyzing {total_files} Python files...")

    for i, py_file in enumerate(py_files, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{total_files} files...")

        imports = extract_imports(py_file)
        all_imports.extend(imports)

        for module_name in imports:
            category = categorize_import(module_name)
            imports_by_category[category] += 1
            imports_by_module[module_name] += 1

            if category == "legacy":
                legacy_patterns.append(f"{py_file}: {module_name}")

    # Get top imports
    top_imports = imports_by_module.most_common(50)

    # Count legacy imports by pattern
    legacy_by_pattern: dict[str, int] = defaultdict(int)
    for pattern in legacy_patterns:
        module = pattern.split(": ")[1] if ": " in pattern else ""
        if module.startswith("core."):
            legacy_by_pattern["core.*"] += 1
        elif module.startswith("ai."):
            legacy_by_pattern["ai.*"] += 1
        elif module.startswith("obs."):
            legacy_by_pattern["obs.*"] += 1
        elif module.startswith("ingest."):
            legacy_by_pattern["ingest.*"] += 1
        elif module.startswith("analysis."):
            legacy_by_pattern["analysis.*"] += 1
        elif module.startswith("memory."):
            legacy_by_pattern["memory.*"] += 1

    return {
        "total_files": total_files,
        "total_imports": len(all_imports),
        "unique_imports": len(imports_by_module),
        "imports_by_category": dict(imports_by_category),
        "legacy_by_pattern": dict(legacy_by_pattern),
        "top_50_imports": [{"module": mod, "count": count} for mod, count in top_imports],
        "legacy_imports_count": len(legacy_patterns),
        "legacy_imports_sample": legacy_patterns[:100],  # First 100 for reference
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze imports across Python files")
    parser.add_argument("directory", type=str, nargs="?", help="Directory to analyze (default: src/)")
    parser.add_argument("--baseline", type=str, help="Generate baseline report for directory")

    args = parser.parse_args()

    target_dir = Path(args.baseline) if args.baseline else Path(args.directory or "src/")

    if not target_dir.exists():
        print(f"Error: Directory does not exist: {target_dir}")
        return 1

    results = analyze_directory(target_dir)

    print("\n" + "=" * 60)
    print("Import Analysis Results")
    print("=" * 60)
    print(f"Total Python files: {results['total_files']}")
    print(f"Total imports: {results['total_imports']}")
    print(f"Unique imports: {results['unique_imports']}")
    print("\nImports by category:")
    for category, count in sorted(results["imports_by_category"].items()):
        print(f"  {category}: {count}")

    if results["legacy_by_pattern"]:
        print("\nLegacy imports by pattern:")
        for pattern, count in sorted(results["legacy_by_pattern"].items(), key=lambda x: -x[1]):
            print(f"  {pattern}: {count}")

    print("\n" + "=" * 60)

    # Output JSON
    print(json.dumps(results, indent=2))

    return 0


if __name__ == "__main__":
    exit(main())
