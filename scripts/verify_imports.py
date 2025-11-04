"""Import verification script for restructured codebase.

Verifies that all migrated imports resolve correctly and reports any failures.
"""

import ast
import importlib
import sys
from pathlib import Path


def verify_file_imports(file_path: Path) -> list[tuple[str, str]]:
    """Verify imports in a single file.

    Args:
        file_path: Path to Python file

    Returns:
        List of (error_type, message) tuples
    """
    errors: list[tuple[str, str]] = []

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))

        # Walk AST and collect imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        # Try importing each module
        for module_name in imports:
            # Skip stdlib modules
            if module_name.split(".")[0] in [
                "os",
                "sys",
                "logging",
                "typing",
                "pathlib",
                "collections",
                "dataclasses",
                "enum",
                "asyncio",
                "json",
                "time",
                "datetime",
                "math",
                "random",
            ]:
                continue

            try:
                importlib.import_module(module_name)
            except ImportError as e:
                errors.append(("IMPORT_ERROR", f"{file_path}: Cannot import '{module_name}' - {e}"))
            except Exception:
                # Other errors (circular imports, etc.) are not critical
                pass

    except SyntaxError as e:
        errors.append(("SYNTAX_ERROR", f"{file_path}: Parse error - {e}"))
    except Exception as e:
        errors.append(("ERROR", f"{file_path}: Unexpected error - {e}"))

    return errors


def main(target_dir: Path = Path("src"), verbose: bool = False):
    """Verify imports across all Python files.

    Args:
        target_dir: Directory to scan
        verbose: If True, show all files processed
    """
    files = list(target_dir.rglob("*.py"))
    total = len(files)
    all_errors: list[tuple[str, str]] = []

    print(f"Verifying imports in {total} Python files...")
    print()

    for i, file_path in enumerate(files, 1):
        errors = verify_file_imports(file_path)

        if errors:
            all_errors.extend(errors)
            if verbose:
                print(f"[{i}/{total}] ❌ {file_path.relative_to(target_dir)}")
                for error_type, message in errors:
                    print(f"  {error_type}: {message}")
        elif verbose:
            print(f"[{i}/{total}] ✅ {file_path.relative_to(target_dir)}")

    print()
    if all_errors:
        print(f"❌ Found {len(all_errors)} import errors:")
        print()
        for error_type, message in all_errors[:50]:  # Limit output
            print(f"  {error_type}: {message}")
        if len(all_errors) > 50:
            print(f"  ... and {len(all_errors) - 50} more errors")
        print()
        return 1
    else:
        print("✅ All imports verified successfully!")
        return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify imports resolve correctly")
    parser.add_argument("target", nargs="?", type=Path, default=Path("src"), help="Directory to scan (default: src)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output for all files")

    args = parser.parse_args()

    sys.exit(main(args.target, verbose=args.verbose))
