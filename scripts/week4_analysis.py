#!/usr/bin/env python3
"""
Week 4 Results Analysis Script

Analyzes benchmark results from Week 4 testing and generates:
- Performance comparison vs baseline
- Configuration recommendations
- Quality vs speed tradeoffs
- Production deployment recommendations
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


class Week4Analyzer:
    """Analyze Week 4 benchmark results and generate recommendations."""

    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir)
        self.results_files = list(self.results_dir.glob("week4_results_*.json"))
        self.validation_files = list(self.results_dir.glob("week4_direct_validation_*.json"))

    def load_results(self) -> list[dict[str, Any]]:
        """Load all results files."""
        all_results = []

        for file in self.results_files:
            with open(file) as f:
                data = json.load(f)
                all_results.append(data)

        for file in self.validation_files:
            with open(file) as f:
                data = json.load(f)
                all_results.append(data)

        return all_results

    def analyze_performance(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze performance across all tests."""
        analysis = defaultdict(
            lambda: {
                "iterations": 0,
                "total_time": 0,
                "min_time": float("inf"),
                "max_time": 0,
                "improvements": [],
                "baseline": None,
            }
        )

        for result in results:
            # Extract test statistics
            if "test_statistics" in result:
                for test_name, stats in result["test_statistics"].items():
                    analysis[test_name]["iterations"] += stats.get("successful_iterations", 0)
                    analysis[test_name]["total_time"] += stats["mean_seconds"]
                    analysis[test_name]["min_time"] = min(
                        analysis[test_name]["min_time"], stats.get("min_seconds", float("inf"))
                    )
                    analysis[test_name]["max_time"] = max(analysis[test_name]["max_time"], stats.get("max_seconds", 0))

            # Extract baseline comparison
            if "baseline_comparison" in result:
                for test_name, comparison in result["baseline_comparison"].items():
                    improvement = abs(comparison.get("vs_baseline_percent", 0))
                    analysis[test_name]["improvements"].append(improvement)
                    if analysis[test_name]["baseline"] is None:
                        baseline_min = result.get("benchmark_info", {}).get("baseline_minutes")
                        if baseline_min:
                            analysis[test_name]["baseline"] = baseline_min * 60

            # Extract validation data
            if "performance_summary" in result:
                summary = result["performance_summary"]
                for key, value in summary.items():
                    if "_avg" in key:
                        test_name = key.replace("_avg", "")
                        analysis[test_name]["improvements"].append(value)

        return dict(analysis)

    def generate_recommendations(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate configuration recommendations based on analysis."""
        recommendations = {"deploy": [], "tune": [], "investigate": []}

        for test_name, stats in analysis.items():
            if not stats["improvements"]:
                continue

            avg_improvement = sum(stats["improvements"]) / len(stats["improvements"])

            # Determine recommendation
            if avg_improvement >= 50:
                recommendations["deploy"].append(
                    {
                        "test": test_name,
                        "improvement": avg_improvement,
                        "reason": f"Excellent performance ({avg_improvement:.1f}% improvement)",
                    }
                )
            elif avg_improvement >= 20:
                recommendations["tune"].append(
                    {
                        "test": test_name,
                        "improvement": avg_improvement,
                        "reason": f"Good performance ({avg_improvement:.1f}%), tune for optimization",
                    }
                )
            else:
                recommendations["investigate"].append(
                    {
                        "test": test_name,
                        "improvement": avg_improvement,
                        "reason": f"Low impact ({avg_improvement:.1f}%), investigate configuration",
                    }
                )

        return recommendations

    def calculate_combined_impact(self, analysis: dict[str, Any]) -> dict[str, float]:
        """Calculate projected combined impact of all optimizations."""
        # Get individual improvements
        quality_improvement = 0
        routing_improvement = 0
        exit_improvement = 0
        combined_improvement = 0

        for test_name, stats in analysis.items():
            if not stats["improvements"]:
                continue
            avg = sum(stats["improvements"]) / len(stats["improvements"])

            if "quality" in test_name.lower():
                quality_improvement = max(quality_improvement, avg)
            elif "routing" in test_name.lower() or "content" in test_name.lower():
                routing_improvement = max(routing_improvement, avg)
            elif "exit" in test_name.lower():
                exit_improvement = max(exit_improvement, avg)
            elif "combined" in test_name.lower():
                combined_improvement = max(combined_improvement, avg)

        # Calculate realistic combined (account for overlap)
        if combined_improvement > 0:
            realistic = combined_improvement
        else:
            # Conservative: Take max + half of second + third of third
            sorted_improvements = sorted([quality_improvement, routing_improvement, exit_improvement], reverse=True)
            realistic = sorted_improvements[0] + sorted_improvements[1] * 0.5 + sorted_improvements[2] * 0.33

        return {
            "quality_filtering": quality_improvement,
            "content_routing": routing_improvement,
            "early_exit": exit_improvement,
            "combined_measured": combined_improvement,
            "combined_realistic": realistic,
            "combined_optimistic": quality_improvement + routing_improvement + exit_improvement,
        }

    def generate_report(self) -> str:
        """Generate comprehensive analysis report."""
        results = self.load_results()
        analysis = self.analyze_performance(results)
        recommendations = self.generate_recommendations(analysis)
        combined = self.calculate_combined_impact(analysis)

        report = []
        report.append("# Week 4 Analysis Report")
        report.append("")
        report.append(f"**Generated**: {datetime.now().isoformat()}")
        report.append(f"**Results Directory**: {self.results_dir}")
        report.append(f"**Files Analyzed**: {len(self.results_files) + len(self.validation_files)}")
        report.append("")
        report.append("---")
        report.append("")

        # Performance Summary
        report.append("## Performance Summary")
        report.append("")
        report.append("| Optimization | Iterations | Avg Improvement | Range |")
        report.append("|-------------|-----------|----------------|--------|")

        for test_name, stats in sorted(analysis.items()):
            if not stats["improvements"]:
                continue
            avg = sum(stats["improvements"]) / len(stats["improvements"])
            min_imp = min(stats["improvements"])
            max_imp = max(stats["improvements"])
            report.append(f"| {test_name} | {stats['iterations']} | {avg:.1f}% | {min_imp:.1f}% - {max_imp:.1f}% |")

        report.append("")

        # Combined Impact
        report.append("## Combined Impact Analysis")
        report.append("")
        report.append("| Metric | Value |")
        report.append("|--------|-------|")
        report.append(f"| Quality Filtering Alone | {combined['quality_filtering']:.1f}% |")
        report.append(f"| Content Routing Alone | {combined['content_routing']:.1f}% |")
        report.append(f"| Early Exit Alone | {combined['early_exit']:.1f}% |")
        report.append(f"| **Combined (Measured)** | **{combined['combined_measured']:.1f}%** |")
        report.append(f"| **Combined (Realistic)** | **{combined['combined_realistic']:.1f}%** |")
        report.append(f"| Combined (Optimistic) | {combined['combined_optimistic']:.1f}% |")
        report.append("")

        # Recommendations
        report.append("## Recommendations")
        report.append("")

        if recommendations["deploy"]:
            report.append("### ✅ Ready for Production")
            report.append("")
            for rec in recommendations["deploy"]:
                report.append(f"- **{rec['test']}**: {rec['reason']}")
            report.append("")

        if recommendations["tune"]:
            report.append("### 🔧 Tune for Optimization")
            report.append("")
            for rec in recommendations["tune"]:
                report.append(f"- **{rec['test']}**: {rec['reason']}")
            report.append("")

        if recommendations["investigate"]:
            report.append("### 🔍 Investigate Further")
            report.append("")
            for rec in recommendations["investigate"]:
                report.append(f"- **{rec['test']}**: {rec['reason']}")
            report.append("")

        # Configuration Guidance
        report.append("## Configuration Guidance")
        report.append("")

        if combined["quality_filtering"] >= 60:
            report.append("### Quality Filtering")
            report.append("")
            report.append("**Status**: ✅ Excellent performance")
            report.append("")
            report.append("**Current Config**:")
            report.append("```yaml")
            report.append("thresholds:")
            report.append("  min_overall: 0.65")
            report.append("  min_coherence: 0.60")
            report.append("```")
            report.append("")
            report.append("**Recommendation**: Deploy with current settings")
            report.append("")

        if combined["combined_measured"] >= 65 or combined["combined_realistic"] >= 65:
            report.append("### Combined Optimization")
            report.append("")
            report.append("**Status**: ✅ Target achieved (65-80%)")
            report.append("")
            report.append("**Deployment Command**:")
            report.append("```bash")
            report.append("export ENABLE_QUALITY_FILTERING=1")
            report.append("export ENABLE_CONTENT_ROUTING=1")
            report.append("export ENABLE_EARLY_EXIT=1")
            report.append("```")
            report.append("")

        # Next Steps
        report.append("## Next Steps")
        report.append("")
        report.append("1. Review detailed logs in results directory")
        report.append("2. Validate quality scores (target: > 0.70)")
        report.append("3. Test with multiple content types")
        report.append("4. Run A/B testing (conservative vs aggressive)")
        report.append("5. Configure dashboard monitoring")
        report.append("6. Deploy to production")
        report.append("")

        return "\n".join(report)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python week4_analysis.py <results_directory>")
        print("")
        print("Examples:")
        print("  python scripts/week4_analysis.py benchmarks/")
        print("  python scripts/week4_analysis.py benchmarks/week4_full_test_20251006_120000/")
        sys.exit(1)

    results_dir = sys.argv[1]

    if not Path(results_dir).exists():
        print(f"Error: Directory not found: {results_dir}")
        sys.exit(1)

    analyzer = Week4Analyzer(results_dir)
    report = analyzer.generate_report()

    # Print report
    print(report)

    # Save report
    output_file = Path(results_dir) / "ANALYSIS.md"
    with open(output_file, "w") as f:
        f.write(report)

    print(f"\n✅ Report saved: {output_file}")


if __name__ == "__main__":
    main()
