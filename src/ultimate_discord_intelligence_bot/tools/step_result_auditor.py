"""StepResult compliance auditor.

This tool audits the codebase for proper StepResult usage patterns.
"""

import sys
from pathlib import Path

from ultimate_discord_intelligence_bot.step_result import StepResult


def audit_codebase(base_dir: Path) -> StepResult:
    """Audit the codebase for StepResult compliance.

    Args:
        base_dir: Root directory to audit

    Returns:
        StepResult indicating audit status
    """
    tools_dir = base_dir / "src" / "ultimate_discord_intelligence_bot" / "tools"

    if not tools_dir.exists():
        return StepResult.fail(
            f"Tools directory not found: {tools_dir}",
            error_category="validation_error",
        )

    # Collect all tool Python files
    tool_files = list(tools_dir.glob("*.py"))
    tool_files = [f for f in tool_files if f.name not in ("__init__.py", "_base.py")]

    total_tools = len(tool_files)
    compliant_tools = []
    non_compliant_tools = []

    for tool_file in tool_files:
        content = tool_file.read_text()
        # Check if tool returns StepResult
        if "-> StepResult" in content or "StepResult." in content:
            compliant_tools.append(tool_file.name)
        else:
            non_compliant_tools.append(tool_file.name)

    compliance_rate = len(compliant_tools) / total_tools * 100 if total_tools > 0 else 0

    return StepResult.ok(
        total_tools=total_tools,
        compliant_tools=len(compliant_tools),
        non_compliant_tools=len(non_compliant_tools),
        compliance_rate=compliance_rate,
        non_compliant_list=non_compliant_tools,
    )


def main() -> int:
    """Run StepResult compliance audit."""
    print("=" * 60)
    print("StepResult Compliance Audit")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent.parent.parent
    result = audit_codebase(base_dir)

    if result.success:
        data = result.data
        print(f"📊 Total tools: {data['total_tools']}")
        print(f"✅ Compliant: {data['compliant_tools']} ({data['compliance_rate']:.1f}%)")
        print(f"❌ Non-compliant: {data['non_compliant_tools']}")

        if data["non_compliant_list"]:
            print("\nNon-compliant tools:")
            for tool in data["non_compliant_list"]:
                print(f"  - {tool}")
        print()
        return 0
    else:
        print(f"❌ Audit failed: {result.error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
