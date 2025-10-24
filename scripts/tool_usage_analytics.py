#!/usr/bin/env python3
"""Tool Usage Analytics Script

Analyzes tool usage patterns across the codebase to identify:
- Underutilized tools (<5% usage)
- Redundant tools with overlapping functionality
- Deprecated tools that should be removed
- High-impact tools that need optimization

Usage:
    python scripts/tool_usage_analytics.py [--output-format json|csv|html]
"""

import ast
import json
import logging
import os
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ultimate_discord_intelligence_bot.tools import MAPPING


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ToolUsageStats:
    """Statistics for a single tool."""

    name: str
    file_path: str
    import_count: int
    instantiation_count: int
    method_call_count: int
    agent_assignments: int
    test_coverage: bool
    documentation_quality: str
    last_modified: str
    lines_of_code: int
    complexity_score: int
    dependencies: list[str]
    category: str


@dataclass
class ToolConsolidationCandidate:
    """A tool that could be consolidated with others."""

    primary_tool: str
    redundant_tools: list[str]
    overlap_percentage: float
    consolidation_effort: str
    migration_path: str


class ToolUsageAnalyzer:
    """Analyzes tool usage patterns across the codebase."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tool_mapping = MAPPING
        self.usage_stats: dict[str, ToolUsageStats] = {}
        self.consolidation_candidates: list[ToolConsolidationCandidate] = []

    def analyze_tool_usage(self) -> dict[str, Any]:
        """Main analysis method."""
        logger.info("Starting tool usage analysis...")

        # 1. Scan for tool imports and usage
        self._scan_tool_imports()

        # 2. Analyze agent assignments
        self._analyze_agent_assignments()

        # 3. Check test coverage
        self._check_test_coverage()

        # 4. Analyze documentation quality
        self._analyze_documentation()

        # 5. Calculate complexity scores
        self._calculate_complexity_scores()

        # 6. Identify consolidation candidates
        self._identify_consolidation_candidates()

        # 7. Generate recommendations
        recommendations = self._generate_recommendations()

        return {
            "tool_stats": {name: asdict(stats) for name, stats in self.usage_stats.items()},
            "consolidation_candidates": [asdict(candidate) for candidate in self.consolidation_candidates],
            "recommendations": recommendations,
            "summary": self._generate_summary(),
        }

    def _scan_tool_imports(self) -> None:
        """Scan codebase for tool imports and usage."""
        logger.info("Scanning for tool imports and usage...")

        # Patterns to search for
        import_patterns = [
            r"from.*tools.*import.*(\w+Tool)",
            r"import.*(\w+Tool)",
            r"(\w+Tool)\(\s*\)",  # Instantiation
            r"(\w+Tool)\.(\w+)\(",  # Method calls
        ]

        for tool_name, tool_path in self.tool_mapping.items():
            stats = ToolUsageStats(
                name=tool_name,
                file_path=tool_path,
                import_count=0,
                instantiation_count=0,
                method_call_count=0,
                agent_assignments=0,
                test_coverage=False,
                documentation_quality="unknown",
                last_modified="unknown",
                lines_of_code=0,
                complexity_score=0,
                dependencies=[],
                category=self._categorize_tool(tool_name),
            )

            # Count usage across codebase
            for pattern in import_patterns:
                count = self._count_pattern_usage(pattern, tool_name)
                if "Tool)(" in pattern:
                    stats.instantiation_count += count
                elif r"Tool)\.(" in pattern:
                    stats.method_call_count += count
                else:
                    stats.import_count += count

            # Get file stats
            tool_file = self.project_root / "src" / "ultimate_discord_intelligence_bot" / tool_path.lstrip(".")
            if tool_file.exists():
                stats.lines_of_code = len(tool_file.read_text().splitlines())
                stats.last_modified = str(tool_file.stat().st_mtime)
                stats.complexity_score = self._calculate_file_complexity(tool_file)

            self.usage_stats[tool_name] = stats

    def _count_pattern_usage(self, pattern: str, tool_name: str) -> int:
        """Count occurrences of a pattern in the codebase."""
        count = 0
        for root, dirs, files in os.walk(self.project_root / "src"):
            # Skip __pycache__ and test directories for now
            dirs[:] = [d for d in dirs if not d.startswith("__pycache__")]

            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text()
                        matches = re.findall(pattern, content)
                        count += len([m for m in matches if tool_name in str(m)])
                    except Exception as e:
                        logger.debug(f"Error reading {file_path}: {e}")
        return count

    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool based on its name."""
        if "Download" in tool_name or "Acquisition" in tool_name:
            return "acquisition"
        elif "Analysis" in tool_name or "Sentiment" in tool_name or "Trend" in tool_name:
            return "analysis"
        elif "Verification" in tool_name or "Fact" in tool_name or "Truth" in tool_name:
            return "verification"
        elif "Memory" in tool_name or "RAG" in tool_name or "Vector" in tool_name:
            return "memory"
        elif "Performance" in tool_name or "Analytics" in tool_name or "Monitoring" in tool_name:
            return "observability"
        else:
            return "other"

    def _analyze_agent_assignments(self) -> None:
        """Analyze which agents use which tools."""
        logger.info("Analyzing agent assignments...")

        # Scan agent files
        agent_files = [
            "src/ultimate_discord_intelligence_bot/agents/analysis.py",
            "src/ultimate_discord_intelligence_bot/agents/executive_supervisor.py",
            "src/ultimate_discord_intelligence_bot/agents/intelligence.py",
            "src/ultimate_discord_intelligence_bot/agents/observability.py",
            "src/ultimate_discord_intelligence_bot/agents/workflow_manager.py",
        ]

        for agent_file in agent_files:
            file_path = self.project_root / agent_file
            if file_path.exists():
                content = file_path.read_text()
                for tool_name in self.tool_mapping.keys():
                    if tool_name in content:
                        self.usage_stats[tool_name].agent_assignments += 1

    def _check_test_coverage(self) -> None:
        """Check if tools have test coverage."""
        logger.info("Checking test coverage...")

        for tool_name, stats in self.usage_stats.items():
            # Look for test files
            test_patterns = [
                f"test_{tool_name.lower()}.py",
                f"test_{tool_name.lower().replace('tool', '')}.py",
                f"test_{stats.category}_{tool_name.lower()}.py",
            ]

            test_found = False
            for pattern in test_patterns:
                for root, dirs, files in os.walk(self.project_root / "tests"):
                    if pattern in files:
                        test_found = True
                        break
                if test_found:
                    break

            stats.test_coverage = test_found

    def _analyze_documentation(self) -> None:
        """Analyze documentation quality for tools."""
        logger.info("Analyzing documentation quality...")

        for tool_name, stats in self.usage_stats.items():
            tool_file = self.project_root / "src" / "ultimate_discord_intelligence_bot" / stats.file_path.lstrip(".")

            if tool_file.exists():
                content = tool_file.read_text()

                # Simple heuristics for documentation quality
                has_docstring = '"""' in content or "'''" in content
                has_type_hints = "->" in content and "def " in content
                has_examples = "Example:" in content or "Usage:" in content

                if has_docstring and has_type_hints and has_examples:
                    quality = "excellent"
                elif has_docstring and has_type_hints:
                    quality = "good"
                elif has_docstring:
                    quality = "basic"
                else:
                    quality = "poor"

                stats.documentation_quality = quality

    def _calculate_file_complexity(self, file_path: Path) -> int:
        """Calculate cyclomatic complexity of a file."""
        try:
            with open(file_path) as f:
                tree = ast.parse(f.read())

            complexity = 1  # Base complexity
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)) or isinstance(node, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            return complexity
        except Exception:
            return 0

    def _calculate_complexity_scores(self) -> None:
        """Calculate complexity scores for all tools."""
        # Already calculated in _scan_tool_imports

    def _identify_consolidation_candidates(self) -> None:
        """Identify tools that could be consolidated."""
        logger.info("Identifying consolidation candidates...")

        # Group tools by category
        category_groups = defaultdict(list)
        for tool_name, stats in self.usage_stats.items():
            category_groups[stats.category].append((tool_name, stats))

        # Look for overlapping functionality within categories
        for category, tools in category_groups.items():
            if len(tools) < 2:
                continue

            # Simple heuristic: tools with similar names and low usage
            for i, (name1, stats1) in enumerate(tools):
                for j, (name2, stats2) in enumerate(tools[i + 1 :], i + 1):
                    # Check for name similarity
                    name1_words = set(name1.lower().split())
                    name2_words = set(name2.lower().split())
                    overlap = len(name1_words.intersection(name2_words)) / len(name1_words.union(name2_words))

                    if overlap > 0.3:  # 30% name overlap
                        # Determine which tool to keep (higher usage)
                        if (
                            stats1.import_count + stats1.instantiation_count
                            > stats2.import_count + stats2.instantiation_count
                        ):
                            primary, redundant = name1, name2
                        else:
                            primary, redundant = name2, name1

                        candidate = ToolConsolidationCandidate(
                            primary_tool=primary,
                            redundant_tools=[redundant],
                            overlap_percentage=overlap * 100,
                            consolidation_effort="medium",
                            migration_path=f"Replace {redundant} with {primary} in all usages",
                        )
                        self.consolidation_candidates.append(candidate)

    def _generate_recommendations(self) -> dict[str, list[str]]:
        """Generate recommendations based on analysis."""
        recommendations = {"deprecate": [], "consolidate": [], "optimize": [], "document": [], "test": []}

        total_tools = len(self.usage_stats)

        for tool_name, stats in self.usage_stats.items():
            usage_score = stats.import_count + stats.instantiation_count + stats.method_call_count

            # Deprecation candidates (very low usage)
            if usage_score < 2 and stats.agent_assignments == 0:
                recommendations["deprecate"].append(f"{tool_name} (usage: {usage_score})")

            # Documentation improvements
            if stats.documentation_quality in ["poor", "basic"]:
                recommendations["document"].append(f"{tool_name} ({stats.documentation_quality})")

            # Test coverage improvements
            if not stats.test_coverage:
                recommendations["test"].append(tool_name)

            # Optimization candidates (high complexity, low usage)
            if stats.complexity_score > 10 and usage_score < 5:
                recommendations["optimize"].append(f"{tool_name} (complexity: {stats.complexity_score})")

        # Add consolidation recommendations
        for candidate in self.consolidation_candidates:
            recommendations["consolidate"].append(
                f"Consolidate {candidate.redundant_tools} into {candidate.primary_tool} "
                f"(overlap: {candidate.overlap_percentage:.1f}%)"
            )

        return recommendations

    def _generate_summary(self) -> dict[str, Any]:
        """Generate analysis summary."""
        total_tools = len(self.usage_stats)
        tools_with_tests = sum(1 for stats in self.usage_stats.values() if stats.test_coverage)
        tools_with_good_docs = sum(
            1 for stats in self.usage_stats.values() if stats.documentation_quality in ["good", "excellent"]
        )

        # Calculate usage distribution
        usage_scores = [
            stats.import_count + stats.instantiation_count + stats.method_call_count
            for stats in self.usage_stats.values()
        ]

        return {
            "total_tools": total_tools,
            "test_coverage_percentage": (tools_with_tests / total_tools) * 100 if total_tools > 0 else 0,
            "documentation_quality_percentage": (tools_with_good_docs / total_tools) * 100 if total_tools > 0 else 0,
            "average_usage": sum(usage_scores) / len(usage_scores) if usage_scores else 0,
            "low_usage_tools": len([score for score in usage_scores if score < 2]),
            "consolidation_candidates": len(self.consolidation_candidates),
            "category_breakdown": {
                category: len([t for t in self.usage_stats.values() if t.category == category])
                for category in set(stats.category for stats in self.usage_stats.values())
            },
        }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze tool usage patterns")
    parser.add_argument(
        "--output-format", choices=["json", "csv", "html"], default="json", help="Output format for results"
    )
    parser.add_argument("--output-file", help="Output file path (default: stdout)")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    analyzer = ToolUsageAnalyzer(project_root)

    results = analyzer.analyze_tool_usage()

    if args.output_format == "json":
        output = json.dumps(results, indent=2)
    elif args.output_format == "csv":
        # Convert to CSV format
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Tool Name", "Category", "Usage Score", "Test Coverage", "Doc Quality", "Complexity"])

        # Write data
        for tool_name, stats in results["tool_stats"].items():
            usage_score = stats["import_count"] + stats["instantiation_count"] + stats["method_call_count"]
            writer.writerow(
                [
                    tool_name,
                    stats["category"],
                    usage_score,
                    stats["test_coverage"],
                    stats["documentation_quality"],
                    stats["complexity_score"],
                ]
            )

        output = output.getvalue()
    else:  # html
        # Simple HTML output
        output = f"""
        <html>
        <head><title>Tool Usage Analysis</title></head>
        <body>
        <h1>Tool Usage Analysis Summary</h1>
        <p>Total Tools: {results["summary"]["total_tools"]}</p>
        <p>Test Coverage: {results["summary"]["test_coverage_percentage"]:.1f}%</p>
        <p>Documentation Quality: {results["summary"]["documentation_quality_percentage"]:.1f}%</p>
        <p>Low Usage Tools: {results["summary"]["low_usage_tools"]}</p>
        <p>Consolidation Candidates: {results["summary"]["consolidation_candidates"]}</p>
        </body>
        </html>
        """

    if args.output_file:
        with open(args.output_file, "w") as f:
            f.write(output)
        logger.info(f"Results written to {args.output_file}")
    else:
        print(output)


if __name__ == "__main__":
    main()
