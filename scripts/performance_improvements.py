#!/usr/bin/env python3
"""
Automated Performance Improvement Script

This script applies safe, automated performance improvements to the codebase
using ruff's PERF rules and provides detailed reporting.

Usage:
    python scripts/performance_improvements.py --check    # Check only, no fixes
    python scripts/performance_improvements.py --fix      # Apply fixes
    python scripts/performance_improvements.py --report   # Generate detailed report
"""

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


class PerformanceImprover:
    """Manages automated performance improvements."""

    def __init__(self, root_dir: Path = Path(".")):
        self.root_dir = root_dir
        self.src_dir = root_dir / "src"

    def run_ruff_check(self, auto_fix: bool = False) -> dict[str, Any]:
        """Run ruff performance checks and optionally apply fixes."""
        cmd = ["python3", "-m", "ruff", "check", str(self.src_dir), "--select", "PERF", "--output-format", "json"]

        if auto_fix:
            cmd.append("--fix")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.stdout:
                return json.loads(result.stdout)
            return []
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Error running ruff: {e}", file=sys.stderr)
            return []

    def categorize_issues(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """Categorize and analyze performance issues."""
        if not issues:
            return {
                "total": 0,
                "by_code": {},
                "by_file": {},
                "by_severity": {},
            }

        # Count by code
        by_code = Counter(issue["code"] for issue in issues)

        # Count by file
        by_file = Counter(issue["filename"] for issue in issues)

        # Group by file and code
        file_code_map = defaultdict(lambda: defaultdict(list))
        for issue in issues:
            file_code_map[issue["filename"]][issue["code"]].append(
                {
                    "line": issue["location"]["row"],
                    "message": issue["message"],
                    "url": issue["url"],
                }
            )

        # Severity mapping
        severity_map = {
            "PERF203": "High",  # try-except in loop
            "PERF401": "Medium",  # list comprehension
            "PERF102": "Medium",  # dict iteration
            "PERF403": "Medium",  # dict comprehension
            "PERF402": "Low",  # manual list copy
        }

        by_severity = defaultdict(int)
        for code, count in by_code.items():
            severity = severity_map.get(code, "Unknown")
            by_severity[severity] += count

        return {
            "total": len(issues),
            "by_code": dict(by_code),
            "by_file": dict(by_file),
            "by_severity": dict(by_severity),
            "file_details": dict(file_code_map),
        }

    def generate_report(self, issues: list[dict[str, Any]], output_file: Path | None = None) -> str:
        """Generate a detailed performance improvement report."""
        analysis = self.categorize_issues(issues)

        report_lines = [
            "=" * 80,
            "PERFORMANCE ANALYSIS REPORT",
            "=" * 80,
            "",
            f"Total Issues Found: {analysis['total']}",
            "",
            "Issues by Type:",
            "-" * 80,
        ]

        # Issue descriptions
        descriptions = {
            "PERF203": "Try-except in loop (High Impact - 30-50% overhead)",
            "PERF401": "Inefficient list building (Medium Impact - 20-40% slower)",
            "PERF102": "Inefficient dict iteration (Medium Impact - 10-20% overhead)",
            "PERF403": "Inefficient dict building (Medium Impact - 15-30% slower)",
            "PERF402": "Manual list copy (Low Impact - 5-10% slower)",
        }

        for code, count in sorted(analysis["by_code"].items(), key=lambda x: -x[1]):
            desc = descriptions.get(code, "Unknown issue")
            report_lines.append(f"  {code}: {count:3d} - {desc}")

        report_lines.extend(
            [
                "",
                "Issues by Severity:",
                "-" * 80,
            ]
        )

        for severity, count in sorted(analysis["by_severity"].items()):
            report_lines.append(f"  {severity:10s}: {count:3d}")

        report_lines.extend(
            [
                "",
                "Top 10 Files with Most Issues:",
                "-" * 80,
            ]
        )

        top_files = sorted(analysis["by_file"].items(), key=lambda x: -x[1])[:10]
        for filepath, count in top_files:
            # Make path relative and shorter
            try:
                rel_path = Path(filepath).relative_to(self.root_dir.resolve())
            except ValueError:
                # If not relative, try to make it shorter
                rel_path = Path(filepath).relative_to(Path.cwd()) if Path.cwd() in Path(filepath).parents else Path(filepath)
            report_lines.append(f"  {count:2d} issues: {rel_path}")

        report_lines.extend(
            [
                "",
                "=" * 80,
                "RECOMMENDED ACTIONS",
                "=" * 80,
                "",
                "Priority 1 - Safe Auto-Fixes (Can apply immediately):",
                "  1. Run: python3 -m ruff check --select PERF401 --fix src/",
                "     → Fixes inefficient list building with comprehensions",
                "",
                "  2. Run: python3 -m ruff check --select PERF403 --fix src/",
                "     → Fixes inefficient dict building with comprehensions",
                "",
                "  3. Run: python3 -m ruff check --select PERF102 --fix src/",
                "     → Fixes inefficient dict iteration",
                "",
                "Priority 2 - Requires Manual Review:",
                "  1. PERF203 (try-except in loops) - Requires case-by-case analysis",
                "     → Review each instance to maintain error handling behavior",
                "     → Consider refactoring to use StepResult pattern",
                "",
                "After applying fixes:",
                "  - Run test suite: make test-fast",
                "  - Run benchmarks: python3 benchmarks/performance_benchmarks.py",
                "  - Compare with baselines in memory_profiling_results.json",
                "",
                "=" * 80,
            ]
        )

        report = "\n".join(report_lines)

        if output_file:
            output_file.write_text(report)
            print(f"Report saved to: {output_file}")

        return report

    def apply_safe_fixes(self, dry_run: bool = True) -> dict[str, Any]:
        """Apply safe automated fixes."""
        safe_codes = ["PERF401", "PERF403", "PERF102", "PERF402"]

        results = {}
        for code in safe_codes:
            print(f"{'[DRY RUN] ' if dry_run else ''}Processing {code}...")

            if not dry_run:
                cmd = ["python3", "-m", "ruff", "check", str(self.src_dir), "--select", code, "--fix"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                results[code] = {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            else:
                # Just check without fixing
                issues = self.run_ruff_check(auto_fix=False)
                code_issues = [i for i in issues if i["code"] == code]
                results[code] = {
                    "issues_found": len(code_issues),
                    "dry_run": True,
                }
                print(f"  Found {len(code_issues)} issues for {code}")

        return results

    def check_baseline_performance(self) -> dict[str, Any]:
        """Load and display baseline performance metrics."""
        baseline_files = [
            "memory_profiling_results.json",
            "pipeline_profiling_results.json",
            "benchmarks/baselines.json",
        ]

        baselines = {}
        for filename in baseline_files:
            filepath = self.root_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, encoding="utf-8") as f:
                        baselines[filename] = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not load {filename}: {e}")

        return baselines


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Automated Performance Improvement Tool")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check for performance issues without fixing",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply safe automated fixes",
    )
    parser.add_argument(
        "--fix-dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed performance report",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for report",
    )
    parser.add_argument(
        "--baselines",
        action="store_true",
        help="Show current performance baselines",
    )

    args = parser.parse_args()

    # Default to check if no action specified
    if not any([args.check, args.fix, args.fix_dry_run, args.report, args.baselines]):
        args.check = True

    improver = PerformanceImprover()

    if args.baselines:
        print("Current Performance Baselines:")
        print("=" * 80)
        baselines = improver.check_baseline_performance()
        for filename, data in baselines.items():
            print(f"\n{filename}:")
            print(json.dumps(data, indent=2)[:500])  # First 500 chars
            print("...")
        return

    if args.check or args.report:
        print("Analyzing performance issues...")
        issues = improver.run_ruff_check(auto_fix=False)
        report = improver.generate_report(issues, args.output)
        print(report)

    if args.fix_dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN - Checking what would be fixed...")
        print("=" * 80 + "\n")
        results = improver.apply_safe_fixes(dry_run=True)
        print("\nNo changes were made (dry run)")

    if args.fix:
        print("\n" + "=" * 80)
        print("Applying safe automated fixes...")
        print("=" * 80 + "\n")

        # Confirm before proceeding
        response = input("This will modify files. Continue? [y/N]: ")
        if response.lower() != "y":
            print("Cancelled.")
            return

        results = improver.apply_safe_fixes(dry_run=False)

        print("\nFixes Applied:")
        for code, result in results.items():
            if result.get("returncode") == 0:
                print(f"  ✓ {code}: Success")
            else:
                print(f"  ✗ {code}: Failed")
                if result.get("stderr"):
                    print(f"    Error: {result['stderr'][:200]}")

        print("\nNext steps:")
        print("  1. Review changes: git diff")
        print("  2. Run tests: make test-fast")
        print("  3. Run benchmarks: python3 benchmarks/performance_benchmarks.py")


if __name__ == "__main__":
    main()
