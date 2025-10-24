#!/usr/bin/env python3
"""
Archive maintenance script for periodic cleanup and organization.

This script helps maintain the archive directory by:
- Removing very old files (configurable age)
- Compressing large result files
- Generating inventory reports
"""

import gzip
import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path


def compress_old_results(archive_path: Path, days_old: int = 30):
    """Compress JSON result files older than specified days."""
    results_dir = archive_path / "results"
    if not results_dir.exists():
        return []

    compressed = []
    cutoff_date = datetime.now() - timedelta(days=days_old)

    for json_file in results_dir.glob("*.json"):
        # Skip already compressed files
        if json_file.name.endswith(".gz"):
            continue

        # Check file age
        file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
        if file_time < cutoff_date:
            # Compress the file
            compressed_path = json_file.with_suffix(".json.gz")
            with open(json_file, "rb") as f_in, gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

            # Remove original if compression successful
            if compressed_path.exists():
                json_file.unlink()
                compressed.append(str(json_file.relative_to(archive_path)))

    return compressed


def generate_archive_inventory(archive_path: Path):
    """Generate an inventory report of the archive."""
    inventory = {
        "generated_at": datetime.now().isoformat(),
        "directories": {},
        "summary": {},
    }

    for subdir in ["demos", "results", "experimental", "logs"]:
        dir_path = archive_path / subdir
        if dir_path.exists():
            files = list(dir_path.glob("*"))
            inventory["directories"][subdir] = {
                "count": len(files),
                "files": [f.name for f in files[:10]],  # First 10 files
                "total_size_mb": sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024),
            }
            if len(files) > 10:
                inventory["directories"][subdir]["files"].append(f"... and {len(files) - 10} more")

    # Summary
    total_files = sum(d["count"] for d in inventory["directories"].values())
    total_size = sum(d["total_size_mb"] for d in inventory["directories"].values())

    inventory["summary"] = {
        "total_files": total_files,
        "total_size_mb": round(total_size, 2),
        "directories": len(inventory["directories"]),
    }

    return inventory


def clean_very_old_files(archive_path: Path, days_old: int = 90):
    """Remove files older than specified days from logs directory."""
    logs_dir = archive_path / "logs"
    if not logs_dir.exists():
        return []

    removed = []
    cutoff_date = datetime.now() - timedelta(days=days_old)

    for log_file in logs_dir.glob("*.log"):
        file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
        if file_time < cutoff_date:
            log_file.unlink()
            removed.append(str(log_file.relative_to(archive_path)))

    return removed


def main():
    """Run archive maintenance."""
    print(f"🗂️ Running archive maintenance at {datetime.now()}")

    # Change to repo root
    repo_root = Path(__file__).parent.parent
    os.chdir(repo_root)
    archive_path = Path("archive")

    if not archive_path.exists():
        print("No archive directory found. Nothing to maintain.")
        return

    # Compress old results
    compressed = compress_old_results(archive_path, days_old=30)
    if compressed:
        print(f"📦 Compressed {len(compressed)} old result files")

    # Clean very old logs
    removed = clean_very_old_files(archive_path, days_old=90)
    if removed:
        print(f"🗑️ Removed {len(removed)} very old log files")

    # Generate inventory
    inventory = generate_archive_inventory(archive_path)
    inventory_file = archive_path / "inventory.json"
    with open(inventory_file, "w") as f:
        json.dump(inventory, f, indent=2)

    print(f"📋 Archive inventory updated: {inventory_file}")
    print(f"   Total: {inventory['summary']['total_files']} files, {inventory['summary']['total_size_mb']} MB")

    if not compressed and not removed:
        print("✅ Archive is already well-maintained!")


if __name__ == "__main__":
    main()
