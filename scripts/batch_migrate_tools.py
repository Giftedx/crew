#!/usr/bin/env python3
"""Batch tool migration script to standardize tool architecture.

This script migrates multiple tools at once to use standardized patterns.
"""

import os
import re
from pathlib import Path
from typing import Any


def migrate_tool_file(file_path: Path, dry_run: bool = True) -> dict[str, Any]:
    """Migrate a single tool file to use standardized patterns."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    changes_made = []

    # Add future annotations import if missing
    if "from __future__ import annotations" not in content:
        if content.startswith(('"""', "'''")):
            # Find end of docstring
            end_quote = '"""' if content.startswith('"""') else "'''"
            docstring_end = content.find(end_quote, 3)
            if docstring_end != -1:
                insert_pos = docstring_end + 3
                if content[insert_pos : insert_pos + 1] == "\n":
                    insert_pos += 1
                content = content[:insert_pos] + "from __future__ import annotations\n\n" + content[insert_pos:]
                changes_made.append("Added future annotations import")
        else:
            content = "from __future__ import annotations\n\n" + content
            changes_made.append("Added future annotations import")

    # Determine tool type based on directory
    tool_type = None
    if "acquisition" in str(file_path):
        tool_type = "acquisition"
    elif "analysis" in str(file_path):
        tool_type = "analysis"

    # Update base class imports
    if tool_type and "from ._base import BaseTool" in content:
        if tool_type == "acquisition":
            content = content.replace("from ._base import BaseTool", "from ._base import AcquisitionTool")
            changes_made.append("Updated import to AcquisitionTool")
        elif tool_type == "analysis":
            content = content.replace("from ._base import BaseTool", "from ._base import AnalysisTool")
            changes_made.append("Updated import to AnalysisTool")

    # Update class inheritance
    if tool_type and "BaseTool[StepResult]" in content:
        if tool_type == "acquisition":
            content = content.replace("BaseTool[StepResult]", "AcquisitionTool")
            changes_made.append("Updated inheritance to AcquisitionTool")
        elif tool_type == "analysis":
            content = content.replace("BaseTool[StepResult]", "AnalysisTool")
            changes_made.append("Updated inheritance to AnalysisTool")

    # Update method signatures to include tenant and workspace
    if "def _run(" in content and "tenant" not in content:
        # Find _run method and add tenant/workspace parameters
        run_pattern = r"(def _run\([^)]*)\)"
        match = re.search(run_pattern, content)
        if match:
            old_signature = match.group(1)
            # Add tenant and workspace parameters
            new_signature = old_signature + ', tenant: str = "default", workspace: str = "default")'
            content = content.replace(old_signature + ")", new_signature)
            changes_made.append("Added tenant and workspace parameters to _run method")

    # Update return statements to use StepResult.ok
    if "return {" in content and "StepResult.ok" not in content:
        # This is a complex transformation, so we'll just note it
        changes_made.append("TODO: Update return statements to use StepResult.ok")

    # Write changes if not dry run
    if not dry_run and changes_made:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    return {
        "file": str(file_path),
        "changes_made": changes_made,
        "has_changes": len(changes_made) > 0,
        "dry_run": dry_run,
    }


def main() -> None:
    """Main function to run batch migration."""
    tools_dir = Path("src/ultimate_discord_intelligence_bot/tools")

    if not tools_dir.exists():
        print(f"Tools directory not found: {tools_dir}")
        return

    # Find all tool files
    tool_files = []
    for root, _dirs, files in os.walk(tools_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__") and not file.startswith("_base"):
                tool_files.append(Path(root) / file)

    print(f"Found {len(tool_files)} tool files to analyze")

    # Run migration analysis (dry run first)
    print("\n=== DRY RUN ANALYSIS ===")
    results = []
    for tool_file in tool_files[:10]:  # Limit to first 10 for demo
        result = migrate_tool_file(tool_file, dry_run=True)
        if result["has_changes"]:
            results.append(result)

    # Print results
    for result in results:
        print(f"\n{result['file']}:")
        for change in result["changes_made"]:
            print(f"  - {change}")

    print(f"\nTotal files with changes: {len(results)}")

    # Ask if user wants to apply changes
    if results:
        response = input("\nApply these changes? (y/N): ")
        if response.lower() == "y":
            print("\n=== APPLYING CHANGES ===")
            for result in results:
                file_path = Path(result["file"])
                apply_result = migrate_tool_file(file_path, dry_run=False)
                print(f"Updated {file_path}: {len(apply_result['changes_made'])} changes")
            print("Migration complete!")
        else:
            print("Migration cancelled.")


if __name__ == "__main__":
    main()
