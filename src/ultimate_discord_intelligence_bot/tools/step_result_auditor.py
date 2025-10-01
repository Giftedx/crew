"""Tool to audit and ensure StepResult pattern compliance in all tools.

Enhancements:
    - Differentiates between hard errors (non-compliance) and advisories (legacy dict pattern allowed temporarily)
    - Provides --strict flag to escalate advisories to errors (CI enforcement ready)
    - Outputs structured summary counts for errors vs advisories
"""

import ast
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ultimate_discord_intelligence_bot.step_result import StepResult

LEGACY_DICT_MSG = (
    "Method {method} in {cls} uses legacy dict return - wrap with StepResult.from_dict or migrate to StepResult.ok/fail"
)


class StepResultAuditor:
    """Auditor for StepResult pattern compliance in tools per Copilot instruction #3."""

    def __init__(self, strict: bool = False):
        self.tools_dir = Path(__file__).parent
        # Hard errors (must fix)
        self.error_tools: list[dict] = []
        # Advisory warnings (legacy dict usage accepted temporarily)
        self.advisory_tools: list[dict] = []
        self.strict = strict

    def audit_tools(self) -> StepResult:
        """Audit all tool files for StepResult compliance.

        Returns StepResult.ok unless hard errors exist. Advisories are included in data.
        When strict mode is enabled (--strict), advisories are escalated to errors.
        """
        tool_files = [
            f
            for f in self.tools_dir.glob("*.py")
            if not f.name.startswith("test_")
            and f.name != "__init__.py"
            and f.name != "step_result_auditor.py"  # Skip self
            and f.name != "_base.py"  # Skip typing shim (doesn't itself produce StepResult)
            and not f.name.endswith("_migration.py")  # Skip migration scripts
        ]

        print(f"🔍 Scanning {len(tool_files)} tool files for StepResult compliance...")
        print("Per Copilot instruction #3: Every tool should return StepResult.ok|fail|skip")
        print()

        for tool_file in tool_files:
            result = self._check_tool_file(tool_file)
            if result["errors"]:
                self.error_tools.append(result)
            elif result["advisories"]:
                self.advisory_tools.append(result)

        escalated = self.strict and self.advisory_tools
        if self.error_tools or escalated:
            total_errors = len(self.error_tools) + (len(self.advisory_tools) if escalated else 0)
            return StepResult.fail(
                error=(
                    f"Found {total_errors} non-compliant tools (errors={len(self.error_tools)}, "
                    f"advisories_escalated={len(self.advisory_tools) if escalated else 0})"
                ),
                errors=self.error_tools,
                advisories=self.advisory_tools,
                strict=self.strict,
            )
        # Success path
        return StepResult.ok(
            message=f"All {len(tool_files)} tools pass hard error checks",
            errors=len(self.error_tools),
            advisories=len(self.advisory_tools),
            strict=self.strict,
        )

    def _check_tool_file(self, file_path: Path) -> dict:
        """Check if a tool file properly implements StepResult pattern.

        Returns dict with separate lists: errors (hard) and advisories (legacy).
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {
                "file": file_path.name,
                "errors": [f"Failed to read file: {e}"],
                "advisories": [],
                "tool_classes": [],
            }

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {
                "file": file_path.name,
                "errors": [f"Failed to parse file: {e}"],
                "advisories": [],
                "tool_classes": [],
            }
        errors = []
        advisories = []
        has_stepresult_import = False
        tool_classes = []

        for node in ast.walk(tree):
            # Check for StepResult import
            if isinstance(node, ast.ImportFrom):
                if node.module and "step_result" in node.module:
                    has_stepresult_import = True
                    for alias in node.names:
                        if isinstance(alias, ast.alias) and alias.name == "StepResult":
                            has_stepresult_import = True
                            break

            # Find tool classes (per project pattern)
            if isinstance(node, ast.ClassDef):
                # Tools typically end with Tool or Agent
                if "Tool" in node.name or node.name.endswith("Agent"):
                    tool_classes.append(node.name)

                    # Check run methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name in ["run", "_run", "execute", "_execute"]:
                            if not self._returns_stepresult(item):
                                if self._method_uses_legacy_pattern(item):
                                    advisories.append(LEGACY_DICT_MSG.format(method=item.name, cls=node.name))
                                else:
                                    errors.append(f"Method {item.name} in {node.name} doesn't return StepResult")

        # Only flag missing import if there are actual tool classes
        if tool_classes and not has_stepresult_import:
            # If only advisories so far, escalate missing import to error; import absent blocks migration
            if advisories and not errors:
                errors.append("Tool file doesn't import StepResult (required before migration)")
            elif not errors:
                # No legacy usage detected yet but missing import—treat as error
                errors.append("Tool file doesn't import StepResult")

        return {
            "file": file_path.name,
            "errors": errors,
            "advisories": advisories,
            "tool_classes": tool_classes,
        }

    def _returns_stepresult(self, func_node: ast.FunctionDef) -> bool:
        """Check if function returns StepResult."""
        # Check for explicit return type annotation
        if func_node.returns:
            if isinstance(func_node.returns, ast.Name):
                if func_node.returns.id == "StepResult":
                    return True

        # Check for StepResult.ok/fail/skip in return statements
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                if node.value:
                    # Check if it's a StepResult call
                    if isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Attribute):
                            if isinstance(node.value.func.value, ast.Name):
                                if node.value.func.value.id == "StepResult":
                                    return True

        return False

    def _method_uses_legacy_pattern(self, func_node: ast.FunctionDef) -> bool:
        """Check if method uses legacy dict return pattern."""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                if node.value and isinstance(node.value, ast.Dict):
                    # Check if dict has success/error keys
                    for key in node.value.keys:
                        if isinstance(key, ast.Constant):
                            if key.value in ["success", "error", "data"]:
                                return True
        return False

    def generate_migration_guide(self) -> str:
        """Generate migration guide for non-compliant tools (errors + advisories)."""
        if not (self.error_tools or self.advisory_tools):
            return "All tools are compliant!"

        guide = "# StepResult Migration Guide\n"
        guide += "Per Copilot instruction #3: Every external/system step should yield StepResult.ok|fail (skips via StepResult.skip(...)).\n\n"

        sample = (self.error_tools + self.advisory_tools)[:5]
        for tool_info in sample:  # Show first 5 as examples
            guide += f"## 📁 {tool_info['file']}\n"
            if tool_info.get("tool_classes"):
                guide += f"**Classes:** {', '.join(tool_info['tool_classes'])}\n"
            if tool_info.get("errors"):
                guide += "**Errors:**\n"
                for err in tool_info.get("errors", []):
                    guide += f"- {err}\n"
            if tool_info.get("advisories"):
                guide += "**Advisories (legacy accepted short-term):**\n"
                for adv in tool_info.get("advisories", []):
                    guide += f"- {adv}\n"
            guide += "\n"

        guide += "### Required Changes (Hard Errors)\n"
        guide += "Errors must be fixed immediately to maintain compliance.\n\n"
        guide += "### Advisory Changes (Legacy Dict Returns)\n"
        guide += "Advisories should be migrated; they become errors under --strict.\n\n"
        guide += "### Migration Steps\n"
        guide += """
1. **Add StepResult import:**
   ```python
   from ultimate_discord_intelligence_bot.step_result import StepResult
   ```

2. **Update return statements (per instruction #3):**
   ```python
   # ❌ Legacy dict pattern:
    return {"success": True, "data": result}

   # ✅ StepResult pattern:
    return StepResult.ok(data=result)

   # For errors (don't raise for recoverable):
    return StepResult.fail(error="Error message", data={"details": ...})

   # For skipped operations:
        return StepResult.skip(reason="Not applicable")
   ```

3. **Exception handling (per instruction #3):**
   ```python
   try:
       result = perform_operation()
       return StepResult.ok(data=result)
   except RecoverableError as e:
       # Known/expected errors - don't raise
       return StepResult.fail(error=str(e))
   except Exception as e:
       # Unexpected exceptions - increment metrics then raise
       metrics.increment_failure()
       raise
   ```

4. **Legacy dict compatibility (per instruction #3):**
   ```python
   # If working with legacy dict returns:
   legacy_result = {"success": True, "data": {...}}
   return StepResult.from_dict(legacy_result)
   ```
"""

        return guide


def main():
    """Run the StepResult compliance audit."""
    print("=" * 60)
    print("StepResult Pattern Compliance Audit")
    print("=" * 60)

    strict = "--strict" in sys.argv
    auditor = StepResultAuditor(strict=strict)
    result = auditor.audit_tools()

    if result.success:
        print(f"\n✅ {result.data['message']}")
        if result.data.get("advisories"):
            print(
                f"   Note: {result.data['advisories']} advisory tool(s) still using legacy dict pattern (run with --strict to fail)."
            )
    else:
        print("\n❌ Non-compliance detected")
        errors = result.data.get("errors", [])
        advisories = result.data.get("advisories", [])
        if errors:
            print(f"   Hard Errors: {len(errors)} (must fix)")
            for tool in errors[:10]:
                print(f"📁 {tool['file']}")
                if tool.get("tool_classes"):
                    print(f"   Classes: {', '.join(tool['tool_classes'])}")
                for err in tool.get("errors", []):
                    print(f"   - ERROR: {err}")
                for adv in tool.get("advisories", []):
                    print(f"   - ADVISORY: {adv}")
                print()
            if len(errors) > 10:
                print(f"... {len(errors) - 10} more error tool(s) omitted for brevity\n")
        if advisories and not strict:
            print(f"\n⚠️ Advisories: {len(advisories)} (not failing without --strict)")
            for tool in advisories[:10]:
                print(f"📁 {tool['file']}")
                if tool.get("tool_classes"):
                    print(f"   Classes: {', '.join(tool['tool_classes'])}")
                for adv in tool.get("advisories", []):
                    print(f"   - ADVISORY: {adv}")
                print()
            if len(advisories) > 10:
                print(f"... {len(advisories) - 10} more advisory tool(s) omitted for brevity\n")

        print("\n" + "=" * 60)
        print("MIGRATION GUIDE")
        print("=" * 60)
        print(auditor.generate_migration_guide())

        print("\n💡 Next steps:")
        if errors:
            print("   * Fix ERROR tools immediately (they block compliance)")
        if advisories:
            print("   * Migrate ADVISORY tools to StepResult (will fail under --strict)")
        print("   * Run 'make guards' and tests once fixed")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
