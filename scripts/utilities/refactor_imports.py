import glob
import os


def refactor_imports_in_file(file_path):
    """
    Refactors import statements in a single Python file.
    """
    with open(file_path, "r") as f:
        content = f.read()

    new_content = content.replace(
        "from ultimate_discord_intelligence_bot.core",
        "from ultimate_discord_intelligence_bot.core",
    )
    new_content = new_content.replace(
        "from ultimate_discord_intelligence_bot.core.",
        "from ultimate_discord_intelligence_bot.core.",
    )
    new_content = new_content.replace(
        "from ultimate_discord_intelligence_bot.obs.",
        "from ultimate_discord_intelligence_bot.obs.",
    )
    new_content = new_content.replace(
        "from ultimate_discord_intelligence_bot.server.",
        "from ultimate_discord_intelligence_bot.server.",
    )
    # Add other replacements as needed...

    if new_content != content:
        print(f"Refactoring imports in: {file_path}")
        with open(file_path, "w") as f:
            f.write(new_content)
        return True
    return False


def refactor_all_imports(start_dir):
    """
    Recursively finds all Python files in a directory and refactors their imports.
    """
    refactored_count = 0
    for filepath in glob.iglob(os.path.join(start_dir, "**", "*.py"), recursive=True):
        if refactor_imports_in_file(filepath):
            refactored_count += 1

    print(f"\nRefactored {refactored_count} files.")


if __name__ == "__main__":
    print("Starting import refactoring for tests and scripts...")
    refactor_all_imports("tests")
    refactor_all_imports("scripts")
    print("Import refactoring complete.")
