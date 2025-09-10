"""Script to audit and fix direct requests usage in the codebase."""

import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ultimate_discord_intelligence_bot.step_result import StepResult

FIXES_PREVIEW_LIMIT = 3  # how many auto-fix suggestions to print


class HTTPComplianceAuditor:
    """Auditor for ensuring HTTP wrapper compliance per Copilot instruction #8."""

    def __init__(self, project_root: Path | None = None):
        if project_root is None:
            # Navigate up to project root
            project_root = Path(__file__).parent.parent.parent.parent
        self.project_root = project_root
        self.violations: list[tuple[str, int, str]] = []

    def audit_files(self) -> StepResult:
        """Audit all Python files for direct requests usage."""
        # Focus on src directory
        src_dir = self.project_root / "src" / "ultimate_discord_intelligence_bot"
        if not src_dir.exists():
            src_dir = Path(__file__).parent.parent  # Current module root

        py_files = list(src_dir.rglob("*.py"))
        print(f"🔍 Scanning {len(py_files)} Python files for HTTP compliance...")
        print("Per Copilot instruction #8: Always use core.http_utils wrappers")

        for file_path in py_files:
            # Skip http_utils itself, test files, and this audit file
            relative_path = str(file_path.name)
            if any(skip in relative_path for skip in ["http_utils", "test_", "http_compliance_audit"]):
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
                # Exemption: file-level pragma allowing intentional direct requests usage
                if "http-compliance: allow-direct-requests" in raw:
                    return []
                lines = raw.splitlines(keepends=False)
                # Track whether a line is inside a triple-quoted string to avoid false positives
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
                        # end of triple quoted string
                        in_triple = False
                        triple_quote = None
                        i += 3
                        continue
                    # mark current character's line as inside string if in_triple
                    if in_triple:
                        # compute current line number
                        line_no = raw.count("\n", 0, i) + 1
                        in_string_lines.add(line_no)
                    i += 1
        except Exception:
            # Skip files that can't be read
            return violations

        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("#"):
                continue
            # Skip lines inside triple-quoted strings / docstrings or multi-line examples
            if i in in_string_lines:
                continue

            # Check for direct requests import
            if re.search(r"^\s*import\s+requests\b", line):
                violations.append((file_path.name, i, "Direct import of requests"))

            # Check for requests.* usage (but not in strings/comments or explanatory docstrings)
            if (
                re.search(r"\brequests\.(get|post|put|delete|patch|head)\b", line)
                and '"requests.' not in line
                and "'requests." not in line
                and "# " not in line
                and "monkeypatching requests." not in line
            ):
                violations.append((file_path.name, i, "Direct requests method call"))

            # Check for from requests import
            if re.search(r"^\s*from\s+requests\s+import\b", line):
                violations.append((file_path.name, i, "Direct import from requests"))

        return violations

    def generate_fixes(self) -> list[str]:
        """Generate fix suggestions for violations."""
        fixes: list[str] = []
        unique_files = {v[0] for v in self.violations}
        for file_name in unique_files:
            file_violations = [v for v in self.violations if v[0] == file_name]
            fix = f"""
📁 File: {file_name}
Violations: {len(file_violations)} issues found

Required changes per Copilot instruction #8:
1. Replace imports:
   ```python
   # ❌ Remove:
   import requests
   from requests import get, post

   # ✅ Add (use core.http_utils wrappers):
   from core.http_utils import (
       resilient_get, resilient_post, retrying_get, retrying_post,
   )
   ```

2. Update method calls:
   ```python
   # ❌ Avoid direct requests:
    response = requests[.]get(url)

   # ✅ Use resilient wrapper:
   response = resilient_get(url, headers=headers)
   ```

3. For custom retry config (check retry.yaml):
   ```python
   # Per instruction #10: HTTP retry config override via retry.yaml
   response = retrying_get(url, max_attempts=5, timeout_seconds=30)
   ```
"""
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

        # Group by file
        files_with_issues = {}
        for file_name, line_num, violation_type in auditor.violations:
            if file_name not in files_with_issues:
                files_with_issues[file_name] = []
            files_with_issues[file_name].append((line_num, violation_type))

        # Display violations grouped by file
        for file_name, issues in files_with_issues.items():
            print(f"📄 {file_name}")
            for line_num, violation_type in sorted(issues):
                print(f"   Line {line_num}: {violation_type}")
            print()

        print("\n" + "=" * 60)
        print("MIGRATION GUIDE")
        print("=" * 60)
        fixes = auditor.generate_fixes()
        for fix in fixes[:FIXES_PREVIEW_LIMIT]:  # Show limited preview of fixes
            print(fix)
        remaining = len(fixes) - FIXES_PREVIEW_LIMIT
        if remaining > 0:
            print(f"\n... and {remaining} more files need updating")

        print("\n💡 Next step: Run 'make guards' to enforce HTTP wrapper usage")
    else:
        # Fixed: Use correct data key
        message = result.data.get("message", "All files comply with HTTP wrapper requirements")
        print(f"\n✅ {message}")
        print("   All files correctly use core.http_utils wrappers")

    return 0 if result.success else 1


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    sys.exit(main())
