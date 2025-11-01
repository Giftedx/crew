#!/usr/bin/env python3
"""Simple StepResult compliance checker for tools."""

import ast
import sys
from pathlib import Path


def check_stepresult_compliance(file_path: Path) -> dict:
    """Check if a tool file properly implements StepResult pattern."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        has_stepresult_import = False
        has_stepresult_returns = False
        tool_classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "step_result" in node.module:
                    for alias in node.names:
                        if alias.name == "StepResult":
                            has_stepresult_import = True
                            break

            elif isinstance(node, ast.ClassDef) and "Tool" in node.name:
                tool_classes.append(node.name)

                # Check methods in the class
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name in ["_run", "run"]:
                        # Check return type annotation
                        if item.returns and hasattr(item.returns, "id") and item.returns.id == "StepResult":
                            has_stepresult_returns = True

                        # Check for StepResult.ok/fail/skip in return statements
                        for stmt in item.body:
                            if (
                                isinstance(stmt, ast.Return)
                                and stmt.value
                                and isinstance(stmt.value, ast.Call)
                                and (
                                    (
                                        hasattr(stmt.value.func, "attr")
                                        and stmt.value.func.attr in ["ok", "fail", "skip"]
                                    )
                                    or (
                                        hasattr(stmt.value.func, "value")
                                        and hasattr(stmt.value.func.value, "id")
                                        and stmt.value.func.value.id == "StepResult"
                                    )
                                )
                            ):
                                has_stepresult_returns = True

        return {
            "file": str(file_path),
            "has_import": has_stepresult_import,
            "has_returns": has_stepresult_returns,
            "tool_classes": tool_classes,
            "compliant": has_stepresult_import and has_stepresult_returns,
        }

    except Exception as e:
        return {"file": str(file_path), "error": str(e), "compliant": False}


def main():
    """Run StepResult compliance check on all tools."""
    tools_dir = Path("src/ultimate_discord_intelligence_bot/tools")

    if not tools_dir.exists():
        print("❌ Tools directory not found")
        return 1

    compliant_count = 0
    total_count = 0
    non_compliant = []

    print("🔍 Checking StepResult compliance in tools...")

    for tool_file in tools_dir.rglob("*.py"):
        if tool_file.name.startswith("_") or tool_file.name == "__init__.py" or "test" in tool_file.name.lower():
            continue

        # Skip utility modules that aren't tools
        if tool_file.name in ["tenancy.py", "settings.py", "lazy_tools.py", "lazy_loader.py"]:
            continue

        result = check_stepresult_compliance(tool_file)
        total_count += 1

        if result.get("compliant", False):
            compliant_count += 1
            print(f"✅ {result['file']}")
        else:
            non_compliant.append(result)
            print(f"❌ {result['file']}")
            if "error" in result:
                print(f"   Error: {result['error']}")
            else:
                issues = []
                if not result.get("has_import", False):
                    issues.append("missing StepResult import")
                if not result.get("has_returns", False):
                    issues.append("missing StepResult returns")
                print(f"   Issues: {', '.join(issues)}")

    compliance_rate = (compliant_count / total_count * 100) if total_count > 0 else 0

    print("\n📊 Compliance Summary:")
    print(f"   Total tools: {total_count}")
    print(f"   Compliant: {compliant_count}")
    print(f"   Non-compliant: {len(non_compliant)}")
    print(f"   Compliance rate: {compliance_rate:.1f}%")

    if non_compliant:
        print("\n❌ Non-compliant tools:")
        for result in non_compliant:
            print(f"   - {result['file']}")

    return 0 if compliance_rate >= 98 else 1


if __name__ == "__main__":
    sys.exit(main())
