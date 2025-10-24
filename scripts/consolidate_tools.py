#!/usr/bin/env python3
"""Tool consolidation script for the Ultimate Discord Intelligence Bot.

This script analyzes the tool codebase, identifies duplicates and consolidation
opportunities, and provides recommendations for reducing tool count.
"""

import ast
import os
from collections import defaultdict
from pathlib import Path


class ToolAnalyzer:
    """Analyzes tools for consolidation opportunities."""

    def __init__(self, tools_dir: str):
        """Initialize analyzer with tools directory."""
        self.tools_dir = Path(tools_dir)
        self.tools: dict[str, dict] = {}
        self.duplicates: list[tuple[str, str]] = []
        self.similar_tools: list[tuple[str, str, float]] = []

    def analyze_tools(self) -> None:
        """Analyze all tools in the directory."""
        print("🔍 Analyzing tools for consolidation opportunities...")

        for tool_file in self.tools_dir.rglob("*.py"):
            if tool_file.name.startswith("__") or tool_file.name == "_base.py":
                continue

            try:
                tool_info = self._analyze_tool_file(tool_file)
                if tool_info:
                    self.tools[tool_file.stem] = tool_info
            except Exception as e:
                print(f"⚠️  Error analyzing {tool_file}: {e}")

        print(f"📊 Found {len(self.tools)} tools to analyze")

    def _analyze_tool_file(self, tool_file: Path) -> dict:
        """Analyze a single tool file."""
        with open(tool_file, encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return None

        tool_info = {
            "file_path": str(tool_file),
            "class_name": None,
            "base_class": None,
            "methods": [],
            "imports": [],
            "docstring": None,
            "line_count": len(content.splitlines()),
        }

        # Extract class information
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not tool_info["class_name"]:  # First class
                    tool_info["class_name"] = node.name
                    tool_info["docstring"] = ast.get_docstring(node)

                    # Get base classes
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            tool_info["base_class"] = base.id
                        elif isinstance(base, ast.Attribute):
                            tool_info["base_class"] = f"{base.attr}"

                # Get methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        tool_info["methods"].append(item.name)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    tool_info["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    tool_info["imports"].append(node.module)

        return tool_info

    def find_duplicates(self) -> None:
        """Find duplicate tools based on class names and functionality."""
        print("🔍 Finding duplicate tools...")

        # Group by class name
        class_groups = defaultdict(list)
        for tool_name, tool_info in self.tools.items():
            if tool_info["class_name"]:
                class_groups[tool_info["class_name"]].append(tool_name)

        # Find exact duplicates
        for class_name, tool_list in class_groups.items():
            if len(tool_list) > 1:
                self.duplicates.extend([(tool_list[0], tool) for tool in tool_list[1:]])
                print(f"🔄 Duplicate class '{class_name}' found in: {', '.join(tool_list)}")

        # Find similar tools by method overlap
        for tool1_name, tool1_info in self.tools.items():
            for tool2_name, tool2_info in self.tools.items():
                if tool1_name >= tool2_name:  # Avoid duplicates
                    continue

                similarity = self._calculate_similarity(tool1_info, tool2_info)
                if similarity > 0.7:  # 70% similarity threshold
                    self.similar_tools.append((tool1_name, tool2_name, similarity))

    def _calculate_similarity(self, tool1: dict, tool2: dict) -> float:
        """Calculate similarity between two tools."""
        if not tool1["class_name"] or not tool2["class_name"]:
            return 0.0

        # Method overlap
        methods1 = set(tool1["methods"])
        methods2 = set(tool2["methods"])

        if not methods1 or not methods2:
            return 0.0

        method_overlap = len(methods1.intersection(methods2)) / len(methods1.union(methods2))

        # Base class similarity
        base_similarity = 1.0 if tool1["base_class"] == tool2["base_class"] else 0.0

        # Weighted similarity
        return 0.7 * method_overlap + 0.3 * base_similarity

    def find_consolidation_opportunities(self) -> None:
        """Find specific consolidation opportunities."""
        print("🎯 Finding consolidation opportunities...")

        opportunities = []

        # YouTube download tools
        youtube_tools = [
            name for name, info in self.tools.items() if "youtube" in name.lower() and "download" in name.lower()
        ]
        if len(youtube_tools) > 1:
            opportunities.append(
                {
                    "category": "YouTube Download Tools",
                    "tools": youtube_tools,
                    "recommendation": "Keep MultiPlatformDownloadTool, remove legacy wrappers",
                }
            )

        # Analysis tools
        analysis_tools = [
            name
            for name, info in self.tools.items()
            if "analysis" in name.lower() and info["base_class"] == "AnalysisTool"
        ]
        if len(analysis_tools) > 3:
            opportunities.append(
                {
                    "category": "Analysis Tools",
                    "tools": analysis_tools,
                    "recommendation": "Merge text/timeline/trend analysis into EnhancedAnalysisTool",
                }
            )

        # Memory tools
        memory_tools = [name for name, info in self.tools.items() if "memory" in name.lower() or "rag" in name.lower()]
        if len(memory_tools) > 5:
            opportunities.append(
                {
                    "category": "Memory Tools",
                    "tools": memory_tools,
                    "recommendation": "Consolidate RAG tools, merge graph memory into primary storage",
                }
            )

        return opportunities

    def generate_consolidation_plan(self) -> str:
        """Generate a detailed consolidation plan."""
        plan = []
        plan.append("# Tool Consolidation Plan")
        plan.append("")
        plan.append("## Current Status")
        plan.append(f"- Total tools: {len(self.tools)}")
        plan.append(f"- Duplicates found: {len(self.duplicates)}")
        plan.append(f"- Similar tools: {len(self.similar_tools)}")
        plan.append("")

        if self.duplicates:
            plan.append("## Duplicate Tools to Remove")
            for tool1, tool2 in self.duplicates:
                plan.append(f"- {tool2} (duplicate of {tool1})")
            plan.append("")

        if self.similar_tools:
            plan.append("## Similar Tools to Consolidate")
            for tool1, tool2, similarity in sorted(self.similar_tools, key=lambda x: x[2], reverse=True):
                plan.append(f"- {tool1} + {tool2} (similarity: {similarity:.1%})")
            plan.append("")

        # Tool count by category
        categories = defaultdict(int)
        for tool_info in self.tools.values():
            if tool_info["file_path"]:
                category = Path(tool_info["file_path"]).parent.name
                categories[category] += 1

        plan.append("## Tool Count by Category")
        for category, count in sorted(categories.items()):
            plan.append(f"- {category}: {count} tools")

        return "\n".join(plan)

    def run_analysis(self) -> None:
        """Run complete tool analysis."""
        print("🚀 Starting tool consolidation analysis...")

        self.analyze_tools()
        self.find_duplicates()

        print("✅ Analysis complete!")
        print(f"📊 Found {len(self.tools)} tools")
        print(f"🔄 Found {len(self.duplicates)} duplicates")
        print(f"🔗 Found {len(self.similar_tools)} similar tools")

        # Generate consolidation plan
        plan = self.generate_consolidation_plan()

        # Save plan to file
        plan_file = Path("tool_consolidation_plan.md")
        with open(plan_file, "w", encoding="utf-8") as f:
            f.write(plan)

        print(f"📝 Consolidation plan saved to: {plan_file}")


def main():
    """Main function."""
    tools_dir = "src/ultimate_discord_intelligence_bot/tools"

    if not os.path.exists(tools_dir):
        print(f"❌ Tools directory not found: {tools_dir}")
        return

    analyzer = ToolAnalyzer(tools_dir)
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
