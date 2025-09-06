#!/usr/bin/env python3
"""Check tools directory against documentation coverage.

This script compares the concrete tool Python modules that exist under
``src/ultimate_discord_intelligence_bot/tools`` with the entries present in
``docs/tools_reference.md``. It reports:
    * missing documentation (tool file exists but not listed)
    * documented tools whose files do not exist
    * documented sections without a file reference
    * class naming convention issues (file snake_case -> CamelCase class)

Exit status is non‑zero when there are undocumented tools so it can be used in
CI to enforce coverage.
"""

import re
import sys
from pathlib import Path


def get_actual_tools() -> set[str]:
    """Get list of actual Python tool files."""
    tools_dir = Path("/home/crew/src/ultimate_discord_intelligence_bot/tools")
    tool_files = [f.stem for f in tools_dir.glob("*.py") if f.name != "__init__.py"]

    # Remove backup files
    tool_files = [t for t in tool_files if not t.endswith("_backup")]

    return set(tool_files)


def get_documented_tools() -> set[str]:
    """Get list of tools mentioned in documentation."""
    docs_path = Path("/home/crew/docs/tools_reference.md")

    with open(docs_path, encoding="utf-8") as f:
        content = f.read()

    # Extract tool names from file references e.g.:
    #   src/ultimate_discord_intelligence_bot/tools/logical_fallacy_tool.py
    file_pattern = r"src/ultimate_discord_intelligence_bot/tools/([^/]+)\.py"
    tool_files = re.findall(file_pattern, content)

    return set(tool_files)


def get_tool_descriptions() -> list[tuple]:
    """Get documented tools with their descriptions."""
    docs_path = Path("/home/crew/docs/tools_reference.md")

    with open(docs_path, encoding="utf-8") as f:
        content = f.read()

    # Extract ### headers and file references
    sections = re.split(r"^### ", content, flags=re.MULTILINE)[1:]  # Skip content before first ###

    tool_info = []
    for section in sections:
        lines = section.strip().split("\n")
        if not lines:
            continue

        title = lines[0].strip()

        # Find file reference in the section
        file_match = None
        for line in lines[1:]:
            match = re.search(r"src/ultimate_discord_intelligence_bot/tools/([^/]+)\.py", line)
            if match:
                file_match = match.group(1)
                break

        if file_match:
            tool_info.append((file_match, title))
        else:
            tool_info.append((None, title))

    return tool_info


def check_tool_class_names():
    """Check if tool class names follow conventions."""
    tools_dir = Path("/home/crew/src/ultimate_discord_intelligence_bot/tools")
    issues = []

    for tool_file in tools_dir.glob("*.py"):
        if tool_file.name == "__init__.py":
            continue

        expected_class = "".join(word.capitalize() for word in tool_file.stem.split("_"))

        try:
            with open(tool_file, encoding="utf-8") as f:
                content = f.read()

            # Look for class definitions
            class_matches = re.findall(r"^class (\w+)", content, re.MULTILINE)

            # Check if expected class exists
            if expected_class not in class_matches:
                # Keep message components short per line for lint (E501)
                msg = f"{tool_file.name}: Expected class '{expected_class}' not found. Found: {class_matches}"
                issues.append(msg)

        except Exception as e:
            issues.append(f"{tool_file.name}: Error reading file - {e}")

    return issues


def main():
    """Main check function."""
    print("🔧 Tool Documentation Coverage Check")
    print("=" * 50)

    actual_tools = get_actual_tools()
    documented_tools = get_documented_tools()
    tool_descriptions = get_tool_descriptions()

    print(f"📁 Found {len(actual_tools)} tool files")
    print(f"📚 Found {len(documented_tools)} documented tools")
    print(f"📖 Found {len(tool_descriptions)} tool descriptions")

    # Check for missing documentation
    missing_docs = actual_tools - documented_tools
    if missing_docs:
        print(f"\n❌ Tools missing documentation ({len(missing_docs)}):")
        for tool in sorted(missing_docs):
            print(f"  • {tool}.py")

    # Check for documented tools that don't exist
    missing_files = documented_tools - actual_tools
    if missing_files:
        print(f"\n⚠️  Documented tools that don't exist ({len(missing_files)}):")
        for tool in sorted(missing_files):
            print(f"  • {tool}.py")

    # Check for orphaned descriptions (no file reference)
    orphaned = [desc for tool, desc in tool_descriptions if tool is None]
    if orphaned:
        print(f"\n🔍 Tool descriptions without file references ({len(orphaned)}):")
        for desc in orphaned:
            print(f"  • {desc}")

    # Check class naming conventions
    class_issues = check_tool_class_names()
    if class_issues:
        print(f"\n⚠️  Class naming issues ({len(class_issues)}):")
        for issue in class_issues:
            print(f"  • {issue}")

    # Summary
    coverage = (len(documented_tools) / len(actual_tools)) * 100 if actual_tools else 0
    print(f"\n📊 Documentation Coverage: {coverage:.1f}% ({len(documented_tools)}/{len(actual_tools)})")

    if missing_docs:
        print("\n💡 Recommendation: Add documentation for missing tools")
        return 1
    else:
        print("\n✅ All tools are documented!")
        return 0


if __name__ == "__main__":
    # Use sys.exit so Ruff (PLR1722) does not complain about bare exit().
    sys.exit(main())
