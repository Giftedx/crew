#!/usr/bin/env python3
"""Generate structured guard violation report from guard output logs.

This script parses guard execution logs and generates a structured JSON report
for CI artifacts and PR comments.

Usage:
    python scripts/generate_guard_report.py --input guards_output.log --output reports/guard_violations.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class GuardViolation:
    """Individual guard violation."""
    guard_name: str
    severity: str  # error, warning, info
    file_path: str | None
    line_number: int | None
    message: str
    suggestion: str | None = None


@dataclass
class GuardResult:
    """Result from a single guard execution."""
    guard_name: str
    status: str  # passed, failed, skipped
    duration_ms: float | None
    violations: list[GuardViolation]
    total_violations: int


@dataclass
class GuardReport:
    """Complete guard execution report."""
    timestamp: str
    total_guards: int
    passed_guards: int
    failed_guards: int
    skipped_guards: int
    total_violations: int
    guards: list[GuardResult]
    summary: str


def parse_guard_output(log_content: str) -> GuardReport:
    """Parse guard output log and extract violations."""
    lines = log_content.split('\n')
    guards: dict[str, GuardResult] = {}
    current_guard: str | None = None
    violations: list[GuardViolation] = []

    # Patterns for parsing
    guard_start_pattern = re.compile(r'\[(\w+[-_]\w+)\]|\b(validate_\w+|deprecated_directories_guard|metrics_instrumentation_guard)\.py\b')
    violation_pattern = re.compile(r'(?:ERROR|VIOLATION|WARNING):\s*(.+?)(?:\s+in\s+(.+?):(\d+))?$')
    file_path_pattern = re.compile(r'(src/[^\s:]+\.py):?(\d+)?')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect guard start
        guard_match = guard_start_pattern.search(line)
        if guard_match:
            # Save previous guard if exists
            if current_guard and current_guard in guards:
                guards[current_guard].violations = violations
                guards[current_guard].total_violations = len(violations)

            # Start new guard
            current_guard = guard_match.group(1) or guard_match.group(2) or "unknown"
            if current_guard not in guards:
                guards[current_guard] = GuardResult(
                    guard_name=current_guard,
                    status="running",
                    duration_ms=None,
                    violations=[],
                    total_violations=0
                )
            violations = []
            continue

        # Detect violations
        violation_match = violation_pattern.search(line)
        if violation_match and current_guard:
            message = violation_match.group(1)
            file_path = violation_match.group(2)
            line_num = int(violation_match.group(3)) if violation_match.group(3) else None

            # Extract file path from message if not in regex groups
            if not file_path:
                file_match = file_path_pattern.search(message)
                if file_match:
                    file_path = file_match.group(1)
                    line_num = int(file_match.group(2)) if file_match.group(2) else None

            # Determine severity
            severity = "error"
            if "WARNING" in line.upper():
                severity = "warning"
            elif "INFO" in line.upper():
                severity = "info"

            violations.append(GuardViolation(
                guard_name=current_guard,
                severity=severity,
                file_path=file_path,
                line_number=line_num,
                message=message,
                suggestion=None  # Could be enhanced with pattern matching
            ))

        # Detect guard completion
        if current_guard and any(word in line.lower() for word in ["passed", "failed", "ok", "error", "✓", "✗", "❌", "✅"]):
            if current_guard in guards:
                if any(word in line.lower() for word in ["passed", "ok", "✓", "✅"]):
                    guards[current_guard].status = "passed"
                elif any(word in line.lower() for word in ["failed", "error", "✗", "❌"]):
                    guards[current_guard].status = "failed"

    # Save last guard
    if current_guard and current_guard in guards:
        guards[current_guard].violations = violations
        guards[current_guard].total_violations = len(violations)

    # Generate summary
    guard_results = list(guards.values())
    passed = sum(1 for g in guard_results if g.status == "passed")
    failed = sum(1 for g in guard_results if g.status == "failed")
    skipped = sum(1 for g in guard_results if g.status == "skipped")
    total_violations = sum(g.total_violations for g in guard_results)

    summary_lines = []
    summary_lines.append(f"Total Guards: {len(guard_results)}")
    summary_lines.append(f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}")
    summary_lines.append(f"Total Violations: {total_violations}")
    if failed > 0:
        summary_lines.append("❌ Compliance guards failed - violations must be fixed")
    else:
        summary_lines.append("✅ All compliance guards passed")

    return GuardReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_guards=len(guard_results),
        passed_guards=passed,
        failed_guards=failed,
        skipped_guards=skipped,
        total_violations=total_violations,
        guards=guard_results,
        summary="\n".join(summary_lines)
    )


def dataclass_to_dict(obj: Any) -> Any:
    """Convert dataclass to dict recursively."""
    if hasattr(obj, '__dataclass_fields__'):
        return {k: dataclass_to_dict(v) for k, v in asdict(obj).items()}
    elif isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]
    return obj


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate guard violation report from logs")
    parser.add_argument("--input", required=True, help="Input log file from guard execution")
    parser.add_argument("--output", required=True, help="Output JSON report file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    # Read input log
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1

    log_content = input_path.read_text(encoding="utf-8")

    # Parse report
    report = parse_guard_output(log_content)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_dict = dataclass_to_dict(report)
    indent = 2 if args.pretty else None
    output_path.write_text(json.dumps(report_dict, indent=indent), encoding="utf-8")

    # Print summary
    print(report.summary)
    print(f"\nReport written to: {output_path}")

    return 0 if report.failed_guards == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
