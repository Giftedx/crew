#!/usr/bin/env python3
"""Script to migrate tools from legacy dict returns to StepResult pattern.

This script converts tools that return dictionaries with "status" keys to use
the StepResult dataclass for consistent error handling across the pipeline.
"""

import re
import sys
from pathlib import Path


def convert_tool_returns(content: str) -> tuple[str, int]:
    """Convert legacy dict returns to StepResult pattern.

    Returns:
        Tuple of (converted_content, number_of_conversions)
    """
    conversions = 0

    # Pattern 1: {"status": "success", "key": value, ...} -> StepResult.ok(key=value, ...)
    def replace_success(match):
        nonlocal conversions
        conversions += 1
        dict_content = match.group(1)

        # Parse the dictionary content to extract key-value pairs
        # Skip the status key
        pairs = []
        # Simple parsing - look for "key": value patterns
        kv_pattern = r'"(\w+)"\s*:\s*([^,}]+)'
        for kv_match in re.finditer(kv_pattern, dict_content):
            key, value = kv_match.groups()
            if key != "status":
                # Clean up the value (remove trailing commas)
                value = value.rstrip(", ")
                pairs.append(f"{key}={value}")

        if pairs:
            return f"StepResult.ok({', '.join(pairs)})"
        else:
            return "StepResult.ok()"

    # Pattern 2: {"status": "error", "error": message, ...} -> StepResult.fail(message, ...)
    def replace_error(match):
        nonlocal conversions
        conversions += 1
        dict_content = match.group(1)

        # Extract error message
        error_pattern = r'"error"\s*:\s*([^,}]+)'
        error_match = re.search(error_pattern, dict_content)
        error_msg = error_match.group(1) if error_match else '"Unknown error"'
        error_msg = error_msg.rstrip(", ")

        # Extract additional data (non-status, non-error keys)
        pairs = []
        kv_pattern = r'"(\w+)"\s*:\s*([^,}]+)'
        for kv_match in re.finditer(kv_pattern, dict_content):
            key, value = kv_match.groups()
            if key not in ("status", "error"):
                value = value.rstrip(", ")
                pairs.append(f"{key}={value}")

        if pairs:
            return f"StepResult.fail({error_msg}, {', '.join(pairs)})"
        else:
            return f"StepResult.fail({error_msg})"

    # Apply patterns
    content = re.sub(r'{\s*"status"\s*:\s*"success"\s*,([^}]+)}', replace_success, content)

    content = re.sub(r'{\s*"status"\s*:\s*"error"\s*,([^}]+)}', replace_error, content)

    # Handle simple cases
    content = re.sub(r'{\s*"status"\s*:\s*"success"\s*}', "StepResult.ok()", content)
    content = re.sub(r'{\s*"status"\s*:\s*"error"\s*}', 'StepResult.fail("Unknown error")', content)

    return content, conversions


def add_stepresult_import(content: str) -> str:
    """Add StepResult import if not present."""
    if "from ultimate_discord_intelligence_bot.step_result import StepResult" in content:
        return content

    # Find the right place to add the import
    lines = content.split("\n")

    # Look for existing imports from ultimate_discord_intelligence_bot
    for i, line in enumerate(lines):
        if "from ultimate_discord_intelligence_bot." in line:
            # Insert before this import
            lines.insert(
                i,
                "from ultimate_discord_intelligence_bot.step_result import StepResult",
            )
            return "\n".join(lines)

    # Look for other tool imports
    for i, line in enumerate(lines):
        if "from ._base import BaseTool" in line:
            # Insert after this import
            lines.insert(
                i + 1,
                "from ultimate_discord_intelligence_bot.step_result import StepResult",
            )
            return "\n".join(lines)

    # Fallback: add after the last import
    for i, line in enumerate(lines):
        if line.startswith(("from ", "import ")):
            continue
        else:
            # Found first non-import line
            lines.insert(
                i,
                "from ultimate_discord_intelligence_bot.step_result import StepResult",
            )
            lines.insert(i + 1, "")
            return "\n".join(lines)

    return content


def migrate_tool_file(file_path: Path) -> bool:
    """Migrate a single tool file to use StepResult.

    Returns:
        True if the file was modified, False otherwise.
    """
    try:
        content = file_path.read_text()

        # Skip if already uses StepResult
        if "StepResult.ok(" in content or "StepResult.fail(" in content:
            return False

        # Skip base classes and non-tool files
        if file_path.name in ("_base.py", "__init__.py"):
            return False

        # Convert returns
        new_content, conversions = convert_tool_returns(content)

        if conversions > 0:
            # Add import if needed
            new_content = add_stepresult_import(new_content)

            # Write back
            file_path.write_text(new_content)
            print(f"✅ Migrated {file_path.name}: {conversions} conversions")
            return True
        else:
            print(f"⏭️  Skipped {file_path.name}: no conversions needed")
            return False

    except Exception as e:
        print(f"❌ Error migrating {file_path}: {e}")
        return False


def main():
    """Main migration function."""
    tools_dir = Path("src/ultimate_discord_intelligence_bot/tools")

    if not tools_dir.exists():
        print(f"Tools directory not found: {tools_dir}")
        sys.exit(1)

    tool_files = list(tools_dir.glob("*.py"))
    tool_files = [f for f in tool_files if f.name not in ("_base.py", "__init__.py")]

    print(f"Found {len(tool_files)} tool files to process")
    print()

    modified_count = 0
    for tool_file in sorted(tool_files):
        if migrate_tool_file(tool_file):
            modified_count += 1

    print()
    print(f"Migration complete: {modified_count}/{len(tool_files)} files modified")


if __name__ == "__main__":
    main()
