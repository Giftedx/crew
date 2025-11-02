#!/usr/bin/env python3
"""MD5 hash-based duplicate file verification tool.

This script compares files byte-for-byte using MD5 hashes to identify
identical duplicate files (not just same names - actual identical content).

Usage:
    python scripts/verify_duplicates.py --source src/dir1 --target src/dir2 --output report.json
    python scripts/verify_duplicates.py --test  # Test on sample files
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def compute_md5(file_path: Path) -> str:
    """Compute MD5 hash of file contents.

    Args:
        file_path: Path to file

    Returns:
        MD5 hash as hexadecimal string
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        raise ValueError(f"Failed to compute MD5 for {file_path}: {e}") from e


def find_python_files(directory: Path) -> dict[str, Path]:
    """Find all Python files in directory recursively.

    Args:
        directory: Root directory to search

    Returns:
        Dictionary mapping filename to full path
    """
    files: dict[str, Path] = {}
    for py_file in directory.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue  # Skip __init__.py files
        files[py_file.name] = py_file
    return files


def verify_duplicates(source_dir: Path, target_dir: Path) -> list[dict[str, Any]]:
    """Verify duplicate files between source and target directories.

    Args:
        source_dir: Source directory to check
        target_dir: Target directory to check against

    Returns:
        List of duplicate file records
    """
    source_files = find_python_files(source_dir)
    target_files = find_python_files(target_dir)

    duplicates: list[dict[str, Any]] = []

    for filename, source_path in source_files.items():
        if filename not in target_files:
            continue  # File doesn't exist in target

        target_path = target_files[filename]

        # Compute MD5 hashes
        try:
            source_hash = compute_md5(source_path)
            target_hash = compute_md5(target_path)
        except Exception as e:
            print(f"Warning: Failed to hash {filename}: {e}")
            continue

        # Get file sizes
        source_size = source_path.stat().st_size
        target_size = target_path.stat().st_size

        is_identical = source_hash == target_hash and source_size == target_size

        duplicates.append(
            {
                "filename": filename,
                "source_path": str(source_path.relative_to(source_dir.parent.parent)),
                "target_path": str(target_path.relative_to(target_dir.parent.parent)),
                "md5_hash": source_hash,
                "target_hash": target_hash,
                "file_size": source_size,
                "target_size": target_size,
                "verified_identical": is_identical,
            }
        )

    return duplicates


def test_verification() -> None:
    """Test the verification tool on sample files."""
    print("Testing duplicate verification tool...")
    # Create test files
    test_dir = Path("/tmp/verify_duplicates_test")
    test_dir.mkdir(exist_ok=True)

    source_dir = test_dir / "source"
    target_dir = test_dir / "target"
    source_dir.mkdir(exist_ok=True)
    target_dir.mkdir(exist_ok=True)

    # Create identical file
    (source_dir / "identical.py").write_text("print('identical')")
    (target_dir / "identical.py").write_text("print('identical')")

    # Create different file with same name
    (source_dir / "different.py").write_text("print('source')")
    (target_dir / "different.py").write_text("print('target')")

    # Create unique file
    (source_dir / "unique.py").write_text("print('unique')")

    duplicates = verify_duplicates(source_dir, target_dir)

    assert len(duplicates) == 2, f"Expected 2 duplicates, got {len(duplicates)}"

    # Find identical and different files (order may vary)
    identical = [d for d in duplicates if d["verified_identical"]]
    different = [d for d in duplicates if not d["verified_identical"]]

    assert len(identical) == 1, f"Expected 1 identical file, got {len(identical)}"
    assert len(different) == 1, f"Expected 1 different file, got {len(different)}"
    assert identical[0]["filename"] == "identical.py", "identical.py should be identical"
    assert different[0]["filename"] == "different.py", "different.py should not be identical"

    print("✅ Verification tool test passed!")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Verify duplicate files using MD5 hash comparison")
    parser.add_argument("--source", type=str, help="Source directory to check")
    parser.add_argument("--target", type=str, help="Target directory to check against")
    parser.add_argument("--output", type=str, help="Output JSON report file")
    parser.add_argument("--test", action="store_true", help="Run test verification")

    args = parser.parse_args()

    if args.test:
        test_verification()
        return 0

    if not args.source or not args.target:
        parser.error("--source and --target are required (or use --test)")

    source_dir = Path(args.source)
    target_dir = Path(args.target)

    if not source_dir.exists():
        print(f"Error: Source directory does not exist: {source_dir}")
        return 1

    if not target_dir.exists():
        print(f"Error: Target directory does not exist: {target_dir}")
        return 1

    print(f"Verifying duplicates between {source_dir} and {target_dir}...")
    duplicates = verify_duplicates(source_dir, target_dir)

    identical_count = sum(1 for d in duplicates if d["verified_identical"])
    different_count = len(duplicates) - identical_count

    print(f"\nFound {len(duplicates)} files with matching names:")
    print(f"  - {identical_count} identical (same MD5 hash)")
    print(f"  - {different_count} different implementations")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(
                {
                    "source_directory": str(source_dir),
                    "target_directory": str(target_dir),
                    "total_matching_names": len(duplicates),
                    "identical_files": identical_count,
                    "different_implementations": different_count,
                    "duplicates": duplicates,
                },
                f,
                indent=2,
            )
        print(f"\nReport saved to: {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())
