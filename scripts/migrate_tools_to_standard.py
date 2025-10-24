#!/usr/bin/env python3
"""Tool migration script to standardize tool architecture.

This script helps migrate existing tools to use the standardized patterns:
- Inherit from appropriate base classes (AcquisitionTool, AnalysisTool, etc.)
- Use consistent StepResult patterns
- Add proper type annotations
- Include input validation
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class ToolMigrationAnalyzer:
    """Analyzes tools and suggests migration improvements."""

    def __init__(self, tools_dir: Path) -> None:
        self.tools_dir = tools_dir
        self.issues_found: list[dict[str, Any]] = []

    def analyze_tool_file(self, file_path: Path) -> dict[str, Any]:
        """Analyze a single tool file for migration issues."""
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        issues = {"file": str(file_path), "issues": [], "suggestions": []}

        # Check for BaseTool[StepResult] inheritance
        if "BaseTool[StepResult]" in content:
            issues["issues"].append("Uses generic BaseTool[StepResult] instead of specialized base class")
            issues["suggestions"].append("Inherit from AcquisitionTool, AnalysisTool, or other specialized base class")

        # Check for missing type hints
        if "def _run(" in content and "-> StepResult" not in content:
            issues["issues"].append("Missing return type annotation on _run method")
            issues["suggestions"].append("Add -> StepResult return type annotation")

        # Check for missing input validation
        if "def _run(" in content and "validation" not in content.lower():
            issues["issues"].append("No input validation found")
            issues["suggestions"].append("Add input validation using validate_url, validate_content, etc.")

        # Check for inconsistent error handling
        if "return {" in content and "StepResult" not in content:
            issues["issues"].append("Returns raw dict instead of StepResult")
            issues["suggestions"].append("Use StepResult.ok(data=...) instead of raw dict returns")

        # Check for missing tenant/workspace parameters
        if "def _run(" in content and ("tenant" not in content or "workspace" not in content):
            issues["issues"].append("Missing tenant/workspace parameters")
            issues["suggestions"].append("Add tenant: str, workspace: str parameters to _run method")

        # Check for missing __future__ import
        if "from __future__ import annotations" not in content:
            issues["issues"].append("Missing future annotations import")
            issues["suggestions"].append("Add 'from __future__ import annotations' at the top")

        return issues

    def analyze_all_tools(self) -> list[dict[str, Any]]:
        """Analyze all tool files in the directory."""
        results = []

        for root, _dirs, files in os.walk(self.tools_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__") and not file.startswith("_base"):
                    file_path = Path(root) / file
                    result = self.analyze_tool_file(file_path)
                    if result["issues"]:
                        results.append(result)

        return results

    def generate_migration_report(self, results: list[dict[str, Any]]) -> str:
        """Generate a migration report."""
        report = []
        report.append("# Tool Migration Analysis Report")
        report.append("")
        report.append(f"Analyzed {len(results)} tool files with issues.")
        report.append("")

        for result in results:
            report.append(f"## {result['file']}")
            report.append("")

            if result["issues"]:
                report.append("### Issues Found:")
                for issue in result["issues"]:
                    report.append(f"- {issue}")
                report.append("")

                report.append("### Suggestions:")
                for suggestion in result["suggestions"]:
                    report.append(f"- {suggestion}")
                report.append("")

        return "\n".join(report)

    def generate_migration_template(self, tool_type: str) -> str:
        """Generate a migration template for a specific tool type."""
        templates = {
            "acquisition": '''
"""Migrated acquisition tool with standardized patterns."""

from __future__ import annotations

from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.acquisition._base import AcquisitionTool


class YourAcquisitionTool(AcquisitionTool):
    """Your tool description here."""

    name: str = "Your Tool Name"
    description: str = "Your tool description"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def run(self, url: str, tenant: str = "default", workspace: str = "default", **kwargs: Any) -> StepResult:
        """Execute the tool with proper error handling and validation.

        Args:
            url: The URL to process
            tenant: Tenant identifier for data isolation
            workspace: Workspace identifier for organization
            **kwargs: Additional tool-specific parameters

        Returns:
            StepResult with processed data or error information
        """
        try:
            # Input validation
            validation_result = self.validate_url(url)
            if not validation_result.success:
                return validation_result

            # Your tool logic here
            result = self._process_url(url, tenant, workspace, **kwargs)

            return StepResult.ok(data=result)

        except Exception as e:
            return StepResult.fail(f"Tool execution failed: {str(e)}")

    def _process_url(self, url: str, tenant: str, workspace: str, **kwargs: Any) -> dict[str, Any]:
        """Process the URL and return results."""
        # Your implementation here
        return {"processed": True, "url": url}
''',
            "analysis": '''
"""Migrated analysis tool with standardized patterns."""

from __future__ import annotations

from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.analysis._base import AnalysisTool


class YourAnalysisTool(AnalysisTool):
    """Your tool description here."""

    name: str = "Your Tool Name"
    description: str = "Your tool description"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def run(self, content: str, tenant: str = "default", workspace: str = "default", **kwargs: Any) -> StepResult:
        """Execute the tool with proper error handling and validation.

        Args:
            content: The content to analyze
            tenant: Tenant identifier for data isolation
            workspace: Workspace identifier for organization
            **kwargs: Additional tool-specific parameters

        Returns:
            StepResult with processed data or error information
        """
        try:
            # Input validation
            validation_result = self.validate_content(content)
            if not validation_result.success:
                return validation_result

            # Your tool logic here
            result = self._process_content(content, tenant, workspace, **kwargs)

            return StepResult.ok(data=result)

        except Exception as e:
            return StepResult.fail(f"Tool execution failed: {str(e)}")

    def _process_content(self, content: str, tenant: str, workspace: str, **kwargs: Any) -> dict[str, Any]:
        """Process the content and return analysis results."""
        # Your implementation here
        return {"analyzed": True, "content_length": len(content)}
''',
        }

        return templates.get(tool_type, "Template not found")


def main() -> None:
    """Main function to run the migration analysis."""
    tools_dir = Path("src/ultimate_discord_intelligence_bot/tools")

    if not tools_dir.exists():
        print(f"Tools directory not found: {tools_dir}")
        return

    analyzer = ToolMigrationAnalyzer(tools_dir)
    results = analyzer.analyze_all_tools()

    # Generate and save report
    report = analyzer.generate_migration_report(results)

    with open("tool_migration_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Migration analysis complete. Found issues in {len(results)} files.")
    print("Report saved to tool_migration_report.md")

    # Print summary
    total_issues = sum(len(result["issues"]) for result in results)
    print(f"Total issues found: {total_issues}")

    if results:
        print("\nTop issues:")
        issue_counts = {}
        for result in results:
            for issue in result["issues"]:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {issue}: {count} files")


if __name__ == "__main__":
    main()
