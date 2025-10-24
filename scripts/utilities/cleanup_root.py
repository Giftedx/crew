#!/usr/bin/env python3
"""
Root directory cleanup script to maintain organization.

This script helps prevent accumulation of clutter in the root directory
by automatically moving files to appropriate archive locations.
"""

import glob
import os
import shutil
from datetime import datetime
from pathlib import Path


def ensure_archive_dirs():
    """Ensure archive directories exist."""
    dirs = [
        "archive/demos",
        "archive/results",
        "archive/experimental",
        "archive/logs",
        "docs/history",
        "scripts",
        "tests",
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)


def move_demo_files():
    """Move demo files to archive/demos/."""
    patterns = ["demo_*.py", "*_demo.py", "*_demo_*.py"]
    moved = []
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            dest = f"archive/demos/{os.path.basename(file_path)}"
            shutil.move(file_path, dest)
            moved.append(file_path)
    return moved


def move_result_files():
    """Move result files to archive/results/."""
    patterns = ["*_results*.json", "*_20[0-9][0-9]*.json", "*_snapshot.json"]
    moved = []
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            dest = f"archive/results/{os.path.basename(file_path)}"
            shutil.move(file_path, dest)
            moved.append(file_path)
    return moved


def move_experimental_files():
    """Move experimental files to archive/experimental/."""
    patterns = [
        "*_engine.py",
        "*_optimizer.py",
        "*_orchestrator.py",
        "*_benchmark*.py",
        "*_integration*.py",
    ]
    moved = []
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            dest = f"archive/experimental/{os.path.basename(file_path)}"
            shutil.move(file_path, dest)
            moved.append(file_path)
    return moved


def move_completion_docs():
    """Move completion documentation to docs/history/."""
    patterns = [
        "PHASE_*_COMPLETE*.md",
        "ADVANCED_*_COMPLETE*.md",
        "COMPREHENSIVE_*.md",
        "COMPLETE_*.md",
        "*_COMPLETION*.md",
        "FINAL_*.md",
        "*_COMPLETE*.md",
    ]
    moved = []
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            dest = f"docs/history/{os.path.basename(file_path)}"
            # If destination already exists (previously moved), remove source to keep root clean
            if os.path.exists(dest):
                os.remove(file_path)
            else:
                shutil.move(file_path, dest)
            moved.append(file_path)
    return moved


def move_phase_guides():
    """Move phase guide markdown files to docs/history/.

    Examples:
    - PHASE5_PRODUCTION_OPERATIONS_GUIDE.md
    - PHASE*_OPERATIONS_GUIDE.md
    """
    patterns = [
        "PHASE*_PRODUCTION_*GUIDE.md",
        "PHASE*_OPERATIONS_*GUIDE.md",
        "PHASE*_*GUIDE.md",
    ]
    moved = []
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            dest = f"docs/history/{os.path.basename(file_path)}"
            shutil.move(file_path, dest)
            moved.append(file_path)
    return moved


def move_log_files():
    """Move log files to archive/logs/."""
    patterns = ["*.log"]
    moved = []
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            dest = f"archive/logs/{os.path.basename(file_path)}"
            shutil.move(file_path, dest)
            moved.append(file_path)
    return moved


def move_utility_files():
    """Move utility scripts and test files to appropriate directories."""
    moved = []
    # Move utility scripts to scripts/
    for pattern in ["fix_*.py", "*_util.py", "*_script.py"]:
        for file_path in glob.glob(pattern):
            dest = f"scripts/{os.path.basename(file_path)}"
            shutil.move(file_path, dest)
            moved.append(file_path)

    # Move test files to tests/
    for pattern in ["test_*.py", "*_test.py"]:
        for file_path in glob.glob(pattern):
            dest = f"tests/{os.path.basename(file_path)}"
            shutil.move(file_path, dest)
            moved.append(file_path)
    return moved


def main():
    """Run cleanup process."""
    print(f"🧹 Running root directory cleanup at {datetime.now()}")

    # Change to repo root
    repo_root = Path(__file__).parent.parent
    os.chdir(repo_root)

    ensure_archive_dirs()

    all_moved = []

    # Run cleanup functions
    moved_demos = move_demo_files()
    moved_results = move_result_files()
    moved_experimental = move_experimental_files()
    moved_docs = move_completion_docs()
    moved_phase_guides = move_phase_guides()
    moved_logs = move_log_files()
    moved_utilities = move_utility_files()

    all_moved.extend(moved_demos)
    all_moved.extend(moved_results)
    all_moved.extend(moved_experimental)
    all_moved.extend(moved_docs)
    all_moved.extend(moved_phase_guides)
    all_moved.extend(moved_logs)
    all_moved.extend(moved_utilities)

    if all_moved:
        print(f"✅ Moved {len(all_moved)} files:")
        for file_path in all_moved:
            print(f"  📁 {file_path}")
    else:
        print("✅ Root directory is already clean!")

    print("\n📋 Root directory organization maintained.")


if __name__ == "__main__":
    main()
