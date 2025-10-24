#!/usr/bin/env python3
"""Script to add comprehensive type hints to all tools."""

import re
from pathlib import Path


def add_type_hints_to_file(file_path: str) -> bool:
    """Add type hints to a tool file."""
    try:
        with open(file_path) as f:
            content = f.read()

        # Check if file already has proper type hints
        if "def _run(self, " in content and "-> StepResult:" in content:
            return False  # Already has type hints

        # Add imports if not present
        if "from __future__ import annotations" not in content:
            # Add after existing imports
            lines = content.split("\n")
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith(("import ", "from ")):
                    import_end = i + 1

            lines.insert(import_end, "from __future__ import annotations")
            content = "\n".join(lines)

        # Add StepResult import if not present
        if "from ultimate_discord_intelligence_bot.step_result import StepResult" not in content:
            lines = content.split("\n")
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith(("import ", "from ")):
                    import_end = i + 1

            lines.insert(import_end, "from ultimate_discord_intelligence_bot.step_result import StepResult")
            content = "\n".join(lines)

        # Update _run method signature
        # Pattern: def _run(self, ...) -> Any:
        pattern = r"def _run\(self, ([^)]*)\) -> [^:]*:"
        replacement = r"def _run(self, \1) -> StepResult:"
        content = re.sub(pattern, replacement, content)

        # Update run method signature
        # Pattern: def run(self, ...) -> Any:
        pattern = r"def run\(self, ([^)]*)\) -> [^:]*:"
        replacement = r"def run(self, \1) -> StepResult:"
        content = re.sub(pattern, replacement, content)

        # Write back to file
        with open(file_path, "w") as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def process_tool_directory(directory: str) -> tuple[int, int]:
    """Process all tool files in a directory."""
    tool_dir = Path(directory)
    if not tool_dir.exists():
        return 0, 0

    processed = 0
    errors = 0

    for tool_file in tool_dir.glob("*.py"):
        if tool_file.name.startswith("__"):
            continue

        if add_type_hints_to_file(str(tool_file)):
            processed += 1
            print(f"Added type hints to {tool_file}")
        else:
            errors += 1

    return processed, errors


def main():
    """Main function to add type hints to all tools."""
    tools_dir = Path("/home/crew/src/ultimate_discord_intelligence_bot/tools")

    if not tools_dir.exists():
        print("Tools directory not found!")
        return

    total_processed = 0
    total_errors = 0

    # Process all tool files
    for tool_file in tools_dir.glob("*.py"):
        if tool_file.name.startswith("__"):
            continue

        if add_type_hints_to_file(str(tool_file)):
            total_processed += 1
            print(f"Added type hints to {tool_file}")
        else:
            total_errors += 1

    print("\nType hints addition complete!")
    print(f"Processed: {total_processed} files")
    print(f"Errors: {total_errors} files")


if __name__ == "__main__":
    main()
