#!/usr/bin/env python
"""Enhanced Deprecation Reporting Dashboard.

Provides comprehensive visibility into the deprecation lifecycle, migration status,
and timeline compliance across the codebase.

Features:
- Integration with existing deprecation validation tools
- Migration progress tracking for each deprecated feature
- Timeline compliance monitoring
- Actionable recommendations for next steps
- Multiple output formats (console, JSON, HTML)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json as _json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEP_FILE = ROOT / "config" / "deprecations.yaml"
MIGRATION_SCRIPTS = {
    "ENABLE_HTTP_RETRY": "scripts/migrate_http_retry_flag.py",
    "core.learning_engine.LearningEngine": "scripts/migrate_learning_engine.py",
}

# Health score thresholds
HEALTH_GOOD = 80
HEALTH_WARNING = 60


class DeprecationDashboard:
    """Enhanced deprecation reporting dashboard."""

    def __init__(self):
        self.today = dt.date.today()
        self.deprecations = self._load_deprecations()
        self.migration_status = self._check_migration_status()

    def _load_deprecations(self) -> list[dict[str, Any]]:
        """Load deprecation configuration."""
        try:
            with open(DEP_FILE, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return data.get("flags", [])
        except Exception as e:
            print(f"Error loading deprecations: {e}", file=sys.stderr)
            return []

    def _check_migration_status(self) -> dict[str, dict[str, Any]]:
        """Check migration status for each deprecated feature."""
        status = {}

        for dep in self.deprecations:
            name = dep["name"]
            script_path = MIGRATION_SCRIPTS.get(name)

            if script_path and Path(ROOT / script_path).exists():
                # Run migration script in dry-run mode to get current status
                try:
                    result = subprocess.run(
                        [sys.executable, script_path, "--dry-run", "--report-only"],
                        check=False,
                        capture_output=True,
                        text=True,
                        cwd=ROOT,
                        timeout=30,
                    )
                    if result.returncode == 1:  # Script found migrations needed
                        status[name] = {
                            "migration_available": True,
                            "pending_migrations": True,
                            "script_path": script_path,
                            "last_check": self.today.isoformat(),
                        }
                    else:
                        status[name] = {
                            "migration_available": True,
                            "pending_migrations": False,
                            "script_path": script_path,
                            "last_check": self.today.isoformat(),
                        }
                except Exception as e:
                    status[name] = {
                        "migration_available": True,
                        "error": str(e),
                        "script_path": script_path,
                        "last_check": self.today.isoformat(),
                    }
            else:
                status[name] = {
                    "migration_available": False,
                    "pending_migrations": None,  # Unknown
                    "script_path": None,
                    "last_check": self.today.isoformat(),
                }

        return status

    def _run_deprecation_scan(self) -> dict[str, Any]:
        """Run the existing deprecation scanner and return results."""
        try:
            result = subprocess.run(
                [sys.executable, "scripts/check_deprecations.py", "--json"],
                check=False,
                capture_output=True,
                text=True,
                cwd=ROOT,
                timeout=30,
            )
            if result.returncode in [0, 1]:  # Success or violations found
                return _json.loads(result.stdout)
            else:
                return {"error": f"Scan failed with code {result.returncode}"}
        except Exception as e:
            return {"error": str(e)}

    def _calculate_health_score(self, scan_results: dict[str, Any]) -> float:
        """Calculate overall deprecation health score (0-100)."""
        if "error" in scan_results:
            return 0.0

        results = scan_results.get("results", [])
        if not results:
            return 100.0

        violation_weight = sum(1 for r in results if r.get("violation", False))
        overdue_weight = sum(1 for r in results if r.get("past_deadline", False))

        # Heavier penalty for violations and overdue items
        score = 100 - (violation_weight * 30 + overdue_weight * 20)
        return max(0.0, min(100.0, score))

    def _get_recommendations(self, scan_results: dict[str, Any]) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if "error" in scan_results:
            recommendations.append("❌ Fix deprecation scanner error")
            return recommendations

        results = scan_results.get("results", [])

        # Check for violations
        violations = [r for r in results if r.get("violation", False)]
        if violations:
            recommendations.append(f"🚨 Address {len(violations)} critical violations immediately")

        # Check for upcoming deadlines
        upcoming = scan_results.get("upcoming", [])
        if upcoming:
            recommendations.append(
                f"⚠️  {len(upcoming)} deprecations due within {scan_results.get('upcoming_window_days', 120)} days"
            )

        # Check migration status
        for name, status in self.migration_status.items():
            if status.get("pending_migrations"):
                script = status.get("script_path", "migration script")
                recommendations.append(f"🔧 Run {script} to migrate {name}")

        # General recommendations
        if not violations and not upcoming:
            recommendations.append("✅ All deprecations are on track")

        if not any(s.get("migration_available") for s in self.migration_status.values()):
            recommendations.append("📝 Consider creating migration scripts for remaining deprecated features")

        return recommendations

    def generate_report(self, format_type: str = "console") -> str:
        """Generate the dashboard report."""
        scan_results = self._run_deprecation_scan()
        health_score = self._calculate_health_score(scan_results)
        recommendations = self._get_recommendations(scan_results)

        if format_type == "json":
            return self._generate_json_report(scan_results, health_score, recommendations)
        elif format_type == "html":
            return self._generate_html_report(scan_results, health_score, recommendations)
        else:
            return self._generate_console_report(scan_results, health_score, recommendations)

    def _generate_console_report(
        self, scan_results: dict[str, Any], health_score: float, recommendations: list[str]
    ) -> str:
        """Generate console-formatted report."""
        lines = []
        lines.append("╔══════════════════════════════════════════════════════════════════════════════╗")
        lines.append("║                        DEPRECATION DASHBOARD                              ║")
        lines.append("╚══════════════════════════════════════════════════════════════════════════════╝")
        lines.append("")

        # Health Score
        health_icon = "🟢" if health_score >= HEALTH_GOOD else "🟡" if health_score >= HEALTH_WARNING else "🔴"
        lines.append(f"Health Score: {health_icon} {health_score:.1f}/100")
        lines.append("")

        # Summary
        if "error" not in scan_results:
            results = scan_results.get("results", [])
            violations = sum(1 for r in results if r.get("violation", False))
            upcoming = len(scan_results.get("upcoming", []))
            total = len(results)

            lines.append("📊 Summary:")
            lines.append(f"   Total deprecated features: {total}")
            lines.append(f"   Critical violations: {violations}")
            lines.append(f"   Upcoming deadlines: {upcoming}")
            lines.append("")

        # Migration Status
        lines.append("🔧 Migration Status:")
        for name, status in self.migration_status.items():
            if status.get("migration_available"):
                if status.get("pending_migrations"):
                    lines.append(f"   ❌ {name}: Migrations pending")
                else:
                    lines.append(f"   ✅ {name}: Fully migrated")
            else:
                lines.append(f"   ❓ {name}: No migration script available")
        lines.append("")

        # Recommendations
        lines.append("💡 Recommendations:")
        lines.extend([f"   {rec}" for rec in recommendations])
        lines.append("")

        # Detailed Results
        if "error" not in scan_results:
            lines.append("📋 Detailed Results:")
            results = scan_results.get("results", [])
            for result in results:
                status_icon = "❌" if result.get("violation") else "⚠️" if result.get("past_deadline") else "✅"
                days = result.get("days_until_removal", 0)
                deadline_status = f" ({days} days)" if days >= 0 else " (OVERDUE)"
                lines.append(f"   {status_icon} {result['name']}: {result['stage']}{deadline_status}")

        return "\n".join(lines)

    def _generate_json_report(
        self, scan_results: dict[str, Any], health_score: float, recommendations: list[str]
    ) -> str:
        """Generate JSON-formatted report."""
        report = {
            "timestamp": self.today.isoformat(),
            "health_score": health_score,
            "scan_results": scan_results,
            "migration_status": self.migration_status,
            "recommendations": recommendations,
        }
        return _json.dumps(report, indent=2)

    def _generate_html_report(
        self, scan_results: dict[str, Any], health_score: float, recommendations: list[str]
    ) -> str:
        """Generate HTML-formatted report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Deprecation Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .health {{ font-size: 24px; font-weight: bold; }}
        .section {{ margin: 20px 0; }}
        .recommendation {{ background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .violation {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .success {{ color: #28a745; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Deprecation Dashboard</h1>
        <div class="health">Health Score: {health_score:.1f}/100</div>
        <div>Generated: {self.today.isoformat()}</div>
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        {"".join(f'<div class="recommendation">{rec}</div>' for rec in recommendations)}
    </div>

    <div class="section">
        <h2>Migration Status</h2>
        <table>
            <tr><th>Feature</th><th>Status</th><th>Migration Available</th></tr>
            {
            "".join(
                f'''
            <tr>
                <td>{name}</td>
                <td class="{"violation" if status.get("pending_migrations") else "success"}">
                    {"Pending" if status.get("pending_migrations") else "Complete"}
                </td>
                <td>{"✅" if status.get("migration_available") else "❌"}</td>
            </tr>
            '''
                for name, status in self.migration_status.items()
            )
        }
        </table>
    </div>
</body>
</html>
"""
        return html


def main():
    parser = argparse.ArgumentParser(description="Enhanced Deprecation Reporting Dashboard")
    parser.add_argument("--format", "-f", choices=["console", "json", "html"], default="console", help="Output format")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    args = parser.parse_args()

    dashboard = DeprecationDashboard()
    report = dashboard.generate_report(args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
