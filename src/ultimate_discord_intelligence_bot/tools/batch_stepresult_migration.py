"""Batch migration script to update tools to use StepResult pattern."""

import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ultimate_discord_intelligence_bot.step_result import StepResult


class BatchStepResultMigration:
    """Batch migrate tools to StepResult pattern per Copilot instruction #3."""

    def __init__(self):
        self.tools_dir = Path(__file__).parent
        self.updated_files = []
        self.failed_files = []

    def migrate_all(self) -> StepResult:
        """Migrate all tool files to StepResult pattern."""
        tool_files = [
            f
            for f in self.tools_dir.glob("*.py")
            if not f.name.startswith("test_")
            and f.name != "__init__.py"
            and not f.name.endswith("_auditor.py")  # Skip auditor scripts
            and not f.name.endswith("_migration.py")  # Skip migration scripts
        ]

        print(f"🔄 Attempting to migrate {len(tool_files)} tool files...")

        for tool_file in tool_files:
            if self._migrate_file(tool_file):
                self.updated_files.append(tool_file.name)
            else:
                self.failed_files.append(tool_file.name)

        if self.updated_files:
            print(f"\n✅ Successfully updated {len(self.updated_files)} files")
            for f in self.updated_files[:10]:
                print(f"   - {f}")
            if len(self.updated_files) > 10:
                print(f"   ... and {len(self.updated_files) - 10} more")

        if self.failed_files:
            print(f"\n⚠️  Could not auto-migrate {len(self.failed_files)} files (manual update needed)")
            for f in self.failed_files[:5]:
                print(f"   - {f}")

        return StepResult.ok(
            data={"updated": len(self.updated_files), "failed": len(self.failed_files), "total": len(tool_files)}
        )

    def _migrate_file(self, file_path: Path) -> bool:
        """Attempt to migrate a single file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Check if already has StepResult import
            has_stepresult = "from ultimate_discord_intelligence_bot.step_result import StepResult" in content

            # Add import if missing
            if not has_stepresult:
                # Find the right place to add import (after other imports)
                lines = content.split("\n")
                insert_pos = 0

                for i, line in enumerate(lines):
                    if line.startswith("from ") or line.startswith("import "):
                        insert_pos = i + 1
                    elif insert_pos > 0 and not line.strip().startswith("#") and line.strip():
                        # Found non-import, non-comment line after imports
                        break

                # Add the import
                lines.insert(insert_pos, "from ultimate_discord_intelligence_bot.step_result import StepResult")
                content = "\n".join(lines)

            # Simple pattern replacements for common cases
            replacements = [
                # Dict returns with success key
                (
                    r'return\s+\{\s*["\']success["\']\s*:\s*True\s*,\s*["\']data["\']\s*:\s*([^}]+)\s*\}',
                    r"return StepResult.ok(data=\1)",
                ),
                # Dict returns with error key
                (
                    r'return\s+\{\s*["\']success["\']\s*:\s*False\s*,\s*["\']error["\']\s*:\s*([^}]+)\s*\}',
                    r"return StepResult.fail(error=\1)",
                ),
                # Simple dict return
                (r'return\s+\{\s*["\']result["\']\s*:\s*([^}]+)\s*\}', r'return StepResult.ok(data={"result": \1})'),
            ]

            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)

            # Only write if we made changes
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return True

            return False

        except Exception as e:
            print(f"   Error migrating {file_path.name}: {e}")
            return False


def main():
    """Run batch migration."""
    print("=" * 60)
    print("Batch StepResult Migration")
    print("=" * 60)
    print("Per Copilot instruction #3: Every tool should return StepResult.ok|fail|skip\n")

    migrator = BatchStepResultMigration()
    result = migrator.migrate_all()

    print("\n📊 Migration Summary:")
    print(f"   Total files: {result.data.get('total', 0)}")
    print(f"   Updated: {result.data.get('updated', 0)}")
    print(f"   Need manual update: {result.data.get('failed', 0)}")

    print("\n💡 Next steps:")
    print("   1. Review the updated files with 'git diff'")
    print("   2. Run step_result_auditor.py to check remaining issues")
    print("   3. Manually update complex cases that couldn't be auto-migrated")
    print("   4. Run 'make test-fast' to verify changes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
