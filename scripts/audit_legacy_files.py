"""Audit script to verify legacy directories are true duplicates of platform/domains.

This script compares legacy directories against their new locations to confirm
all unique files have been migrated and no stragglers remain.
"""

from pathlib import Path
import difflib

LEGACY_TO_NEW = {
    "src/core": "src/platform/core",
    "src/ai": "src/platform/rl",
    "src/obs": "src/platform/observability",
    "src/ingest": "src/domains/ingestion",
    "src/analysis": "src/domains/intelligence/analysis",
}


def audit_directory_pair(legacy_path: Path, new_path: Path):
    """Compare legacy and new directories for missing files.

    Returns dict with missing files, unique files, and content differences.
    """
    legacy_files = {f.name: f for f in legacy_path.rglob("*.py") if f.is_file()}
    new_files = {f.name: f for f in new_path.rglob("*.py") if f.is_file()}

    missing_in_new = set(legacy_files.keys()) - set(new_files.keys())
    only_in_new = set(new_files.keys()) - set(legacy_files.keys())

    # Check content similarity for common files
    common = set(legacy_files.keys()) & set(new_files.keys())
    content_diffs = []

    for filename in common:
        legacy_content = legacy_files[filename].read_text()
        new_content = new_files[filename].read_text()

        if legacy_content != new_content:
            similarity = difflib.SequenceMatcher(None, legacy_content, new_content).ratio()
            if similarity < 0.95:  # Significant difference
                content_diffs.append((filename, similarity))

    return {
        "missing_in_new": missing_in_new,
        "only_in_new": only_in_new,
        "content_diffs": content_diffs
    }


def main():
    """Run audit across all legacy directory pairs."""
    print("🔍 Auditing Legacy Directories vs New Structure")
    print("=" * 60)

    total_missing = 0
    total_diffs = 0

    for legacy, new in LEGACY_TO_NEW.items():
        legacy_path = Path(legacy)
        new_path = Path(new)

        if not legacy_path.exists():
            print(f"\n✓ {legacy} already deleted")
            continue

        if not new_path.exists():
            print(f"\n⚠ WARNING: {new} doesn't exist but {legacy} does!")
            print(f"   This indicates a consolidation issue.")
            continue

        results = audit_directory_pair(legacy_path, new_path)

        print(f"\n=== {legacy} vs {new} ===")
        print(f"Files only in legacy: {len(results['missing_in_new'])}")
        print(f"Files only in new: {len(results['only_in_new'])}")
        print(f"Content differences: {len(results['content_diffs'])}")

        if results['missing_in_new']:
            total_missing += len(results['missing_in_new'])
            print("\n⚠ Missing files in new location (need manual review):")
            for f in sorted(results['missing_in_new'])[:10]:
                print(f"  - {f}")
            if len(results['missing_in_new']) > 10:
                print(f"  ... and {len(results['missing_in_new']) - 10} more")

        if results['content_diffs']:
            total_diffs += len(results['content_diffs'])
            print("\n⚠ Content differences (potential updates):")
            for f, sim in sorted(results['content_diffs'])[:5]:
                print(f"  - {f} (similarity: {sim:.2%})")
            if len(results['content_diffs']) > 5:
                print(f"  ... and {len(results['content_diffs']) - 5} more")

        if not results['missing_in_new'] and not results['content_diffs']:
            print("✓ All files accounted for and content matches")

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total missing files: {total_missing}")
    print(f"Total content differences: {total_diffs}")

    if total_missing == 0 and total_diffs == 0:
        print("\n✅ ALL FILES VERIFIED - Safe to delete legacy directories")
        return 0
    else:
        print("\n⚠️  ISSUES FOUND - Manual review required before deletion")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
