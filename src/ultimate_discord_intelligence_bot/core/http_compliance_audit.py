"""Script to audit and fix direct requests usage in the codebase."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from platform.core.step_result import StepResult

FIXES_PREVIEW_LIMIT = 3


class HTTPComplianceAuditor:
    """Auditor for ensuring HTTP wrapper compliance per Copilot instruction #8."""

    def __init__(self, project_root: Path | None = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent.parent
        self.project_root = project_root
        self.violations: list[tuple[str, int, str]] = []

    def audit_files(self) -> StepResult:
        """Audit all Python files for direct requests usage."""
        src_dir = self.project_root / "src" / "ultimate_discord_intelligence_bot"
        if not src_dir.exists():
            src_dir = Path(__file__).parent.parent
        py_files = list(src_dir.rglob("*.py"))
        print(f"🔍 Scanning {len(py_files)} Python files for HTTP compliance...")
        print("Per Copilot instruction #8: Always use core.http_utils wrappers")
        for file_path in py_files:
            relative_path = str(file_path.name)
            if any((skip in relative_path for skip in ["http_utils", "test_", "http_compliance_audit"])):
                continue
            violations = self._check_file(file_path)
            if violations:
                self.violations.extend(violations)
        if self.violations:
            return StepResult.fail(
                error=f"Found {len(self.violations)} HTTP compliance violations", data={"violations": self.violations}
            )
        return StepResult.ok(data={"message": "All files comply with HTTP wrapper requirements"})

    def _check_file(self, file_path: Path) -> list[tuple[str, int, str]]:
        """Check a single file for violations."""
        violations: list[tuple[str, int, str]] = []
        try:
            with open(file_path, encoding="utf-8") as f:
                raw = f.read()
                if "http-compliance: allow-direct-requests" in raw:
                    return []
                lines = raw.splitlines(keepends=False)
                in_triple = False
                triple_quote: str | None = None
                in_string_lines: set[int] = set()
                i = 0
                while i < len(raw):
                    nxt2 = raw[i : i + 3]
                    if not in_triple and nxt2 in ("'''", '"""'):
                        in_triple = True
                        triple_quote = nxt2
                        i += 3
                        continue
                    if in_triple and nxt2 == triple_quote:
                        in_triple = False
                        triple_quote = None
                        i += 3
                        continue
                    if in_triple:
                        line_no = raw.count("\n", 0, i) + 1
                        in_string_lines.add(line_no)
                    i += 1
        except Exception:
            return violations
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue
            if i in in_string_lines:
                continue
            if re.search("^\\s*import\\s+requests\\b", line):
                violations.append((file_path.name, i, "Direct import of requests"))
            if (
                re.search("\\brequests\\.(get|post|put|delete|patch|head)\\b", line)
                and '"requests.' not in line
                and ("'requests." not in line)
                and ("# " not in line)
                and ("monkeypatching requests." not in line)
            ):
                violations.append((file_path.name, i, "Direct requests method call"))
            if re.search("^\\s*from\\s+requests\\s+import\\b", line):
                violations.append((file_path.name, i, "Direct import from requests"))
        return violations

    def generate_fixes(self) -> list[str]:
        """Generate fix suggestions for violations."""
        fixes: list[str] = []
        unique_files = {v[0] for v in self.violations}
        for file_name in unique_files:
            file_violations = [v for v in self.violations if v[0] == file_name]
            fix = f"\n📁 File: {file_name}\nViolations: {len(file_violations)} issues found\n\nRequired changes per Copilot instruction #8:\n1. Replace imports:\n   ```python\n   # ❌ Remove:\n   import requests\n   from requests import get, post\n\n   # ✅ Add (use core.http_utils wrappers):\n   from core.http_utils import (\n       resilient_get, resilient_post, retrying_get, retrying_post,\n   )\n   ```\n\n2. Update method calls:\n   ```python\n   # ❌ Avoid direct requests:\n    response = requests[.]get(url)\n\n   # ✅ Use resilient wrapper:\n   response = resilient_get(url, headers=headers)\n   ```\n\n3. For custom retry config (check retry.yaml):\n   ```python\n   # Per instruction #10: HTTP retry config override via retry.yaml\n   response = retrying_get(url, max_attempts=5, timeout_seconds=30)\n   ```\n"
            fixes.append(fix)
        return fixes


def main():
    """Run the HTTP compliance audit."""
    auditor = HTTPComplianceAuditor()
    print("=" * 60)
    print("HTTP Compliance Audit")
    print("=" * 60)
    result = auditor.audit_files()
    if not result.success:
        print(f"\n❌ Found {len(auditor.violations)} violations of Copilot instruction #8")
        print("   (Always use core.http_utils wrappers, not direct requests.*)\n")
        files_with_issues = {}
        for file_name, line_num, violation_type in auditor.violations:
            if file_name not in files_with_issues:
                files_with_issues[file_name] = []
            files_with_issues[file_name].append((line_num, violation_type))
        for file_name, issues in files_with_issues.items():
            print(f"📄 {file_name}")
            for line_num, violation_type in sorted(issues):
                print(f"   Line {line_num}: {violation_type}")
            print()
        print("\n" + "=" * 60)
        print("MIGRATION GUIDE")
        print("=" * 60)
        fixes = auditor.generate_fixes()
        for fix in fixes[:FIXES_PREVIEW_LIMIT]:
            print(fix)
        remaining = len(fixes) - FIXES_PREVIEW_LIMIT
        if remaining > 0:
            print(f"\n... and {remaining} more files need updating")
        print("\n💡 Next step: Run 'make guards' to enforce HTTP wrapper usage")
    else:
        message = result.data.get("message", "All files comply with HTTP wrapper requirements")
        print(f"\n✅ {message}")
        print("   All files correctly use core.http_utils wrappers")
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
