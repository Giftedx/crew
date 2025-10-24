#!/usr/bin/env python3
"""Script to add comprehensive type hints to service layer files."""

import re
from pathlib import Path


def add_type_hints_to_service_file(file_path: str) -> bool:
    """Add comprehensive type hints to a service file."""
    try:
        with open(file_path) as f:
            content = f.read()

        # Add __future__ import if not present
        if "from __future__ import annotations" not in content:
            lines = content.split("\n")
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith(("import ", "from ")):
                    import_end = i + 1

            lines.insert(import_end, "from __future__ import annotations")
            content = "\n".join(lines)

        # Add typing imports if not present
        typing_imports = [
            "from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic",
            "from collections.abc import Mapping, Sequence",
        ]

        for typing_import in typing_imports:
            if typing_import.split()[2] not in content:
                lines = content.split("\n")
                import_end = 0
                for i, line in enumerate(lines):
                    if line.startswith(("import ", "from ")):
                        import_end = i + 1

                lines.insert(import_end, typing_import)
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

        # Update method signatures to include proper type hints
        # Pattern: def method_name(self, ...) -> Any:
        pattern = r"def (\w+)\(self, ([^)]*)\) -> [^:]*:"
        replacement = r"def \1(self, \2) -> StepResult:"
        content = re.sub(pattern, replacement, content)

        # Update class method signatures
        pattern = r"def (\w+)\(cls, ([^)]*)\) -> [^:]*:"
        replacement = r"def \1(cls, \2) -> StepResult:"
        content = re.sub(pattern, replacement, content)

        # Update static method signatures
        pattern = r"def (\w+)\(([^)]*)\) -> [^:]*:"
        replacement = r"def \1(\2) -> StepResult:"
        content = re.sub(pattern, replacement, content)

        # Write back to file
        with open(file_path, "w") as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to add type hints to service files."""
    services_dir = Path("/home/crew/src/ultimate_discord_intelligence_bot/services")

    if not services_dir.exists():
        print("Services directory not found!")
        return

    total_processed = 0
    total_errors = 0

    # Process all service files
    for service_file in services_dir.glob("*.py"):
        if service_file.name.startswith("__"):
            continue

        if add_type_hints_to_service_file(str(service_file)):
            total_processed += 1
            print(f"Added type hints to {service_file}")
        else:
            total_errors += 1

    print("\nService type hints addition complete!")
    print(f"Processed: {total_processed} files")
    print(f"Errors: {total_errors} files")


if __name__ == "__main__":
    main()
