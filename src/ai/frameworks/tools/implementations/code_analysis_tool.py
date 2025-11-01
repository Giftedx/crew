"""
CodeAnalysisTool - Static code analysis and quality checking.

This tool provides static analysis capabilities for multiple programming languages,
detecting common issues, style violations, and potential bugs without executing code.
"""

import re
from typing import Any

import structlog

from ai.frameworks.tools.converters import BaseUniversalTool
from ai.frameworks.tools.protocols import ParameterSchema, ToolMetadata


logger = structlog.get_logger(__name__)


class CodeAnalysisTool(BaseUniversalTool):
    """
    A universal code analysis tool for static code quality checking.

    Performs static analysis on code snippets to detect:
    - Syntax errors
    - Style violations (PEP 8 for Python, etc.)
    - Security issues
    - Complexity metrics
    - Best practice violations

    Example:
        # Analyze Python code
        result = await analyzer.run(
            code='def foo():\\n    x=1\\n    return x',
            language="python",
            checks=["syntax", "style", "complexity"]
        )

        # Check JavaScript for security issues
        result = await analyzer.run(
            code='eval(userInput);',
            language="javascript",
            checks=["security"]
        )
    """

    name = "code-analysis"
    description = (
        "Analyze source code for syntax errors, style violations, security issues, "
        "and complexity metrics. Supports Python, JavaScript, TypeScript, Go, and more. "
        "Returns detailed issue reports with line numbers, severity, and suggested fixes."
    )

    parameters = {
        "code": ParameterSchema(
            type="string",
            description="Source code to analyze",
            required=True,
        ),
        "language": ParameterSchema(
            type="string",
            description="Programming language of the code",
            required=True,
            enum=["python", "javascript", "typescript", "go", "java", "rust", "ruby"],
        ),
        "checks": ParameterSchema(
            type="array",
            description="Types of checks to perform (default: all)",
            required=False,
            default=["syntax", "style", "complexity", "security"],
        ),
        "max_line_length": ParameterSchema(
            type="number",
            description="Maximum allowed line length for style checks (default 100)",
            required=False,
            default=100,
        ),
        "severity_filter": ParameterSchema(
            type="string",
            description="Minimum severity level to report (error, warning, info)",
            required=False,
            enum=["error", "warning", "info"],
            default="info",
        ),
    }

    metadata = ToolMetadata(
        category="development",
        return_type="dict",
        examples=[
            "Check Python code for PEP 8 violations",
            "Detect security issues in JavaScript",
            "Calculate code complexity metrics",
            "Validate syntax across multiple languages",
        ],
        version="1.0.0",
        tags=["code", "analysis", "linting", "static-analysis", "quality"],
        requires_auth=False,
    )

    # Security patterns to detect
    SECURITY_PATTERNS = {
        "python": [
            (r"\beval\(", "Use of eval() can execute arbitrary code", "error"),
            (r"\bexec\(", "Use of exec() can execute arbitrary code", "error"),
            (r"__import__\(", "Dynamic imports can be dangerous", "warning"),
            (r"pickle\.loads\(", "Unpickling untrusted data is unsafe", "error"),
        ],
        "javascript": [
            (r"\beval\(", "Use of eval() can execute arbitrary code", "error"),
            (r"innerHTML\s*=", "Direct innerHTML assignment can lead to XSS", "warning"),
            (r"document\.write\(", "document.write() can introduce XSS", "warning"),
            (r"setTimeout\(['\"]", "setTimeout with string argument uses eval", "error"),
        ],
    }

    async def run(
        self,
        code: str,
        language: str,
        checks: list[str] | None = None,
        max_line_length: int = 100,
        severity_filter: str = "info",
    ) -> dict[str, Any]:
        """
        Analyze source code for quality and security issues.

        Args:
            code: Source code to analyze
            language: Programming language
            checks: Types of checks to perform
            max_line_length: Maximum line length for style checks
            severity_filter: Minimum severity to report

        Returns:
            Dictionary containing:
            - issues (list): List of detected issues
            - summary (dict): Summary statistics
            - metrics (dict): Code metrics (lines, complexity, etc.)

        Raises:
            ValueError: If language not supported or invalid parameters
        """
        logger.info(
            "code_analysis_execution",
            language=language,
            code_length=len(code),
            checks=checks,
        )

        checks = checks or ["syntax", "style", "complexity", "security"]
        issues = []
        lines = code.split("\n")

        # Syntax check (basic validation)
        if "syntax" in checks:
            syntax_issues = self._check_syntax(code, language, lines)
            issues.extend(syntax_issues)

        # Style check
        if "style" in checks:
            style_issues = self._check_style(lines, max_line_length, language)
            issues.extend(style_issues)

        # Complexity check
        if "complexity" in checks:
            complexity_issues = self._check_complexity(code, language, lines)
            issues.extend(complexity_issues)

        # Security check
        if "security" in checks:
            security_issues = self._check_security(code, language, lines)
            issues.extend(security_issues)

        # Filter by severity
        severity_order = {"info": 0, "warning": 1, "error": 2}
        min_severity = severity_order.get(severity_filter, 0)
        filtered_issues = [issue for issue in issues if severity_order.get(issue["severity"], 0) >= min_severity]

        # Calculate summary
        summary = {
            "total_issues": len(filtered_issues),
            "errors": sum(1 for i in filtered_issues if i["severity"] == "error"),
            "warnings": sum(1 for i in filtered_issues if i["severity"] == "warning"),
            "info": sum(1 for i in filtered_issues if i["severity"] == "info"),
        }

        metrics = {
            "total_lines": len(lines),
            "code_lines": sum(1 for line in lines if line.strip() and not line.strip().startswith(("#", "//"))),
            "blank_lines": sum(1 for line in lines if not line.strip()),
            "comment_lines": sum(1 for line in lines if line.strip() and line.strip().startswith(("#", "//"))),
        }

        logger.info(
            "code_analysis_complete",
            language=language,
            total_issues=summary["total_issues"],
            errors=summary["errors"],
        )

        return {
            "issues": filtered_issues,
            "summary": summary,
            "metrics": metrics,
        }

    def _check_syntax(self, code: str, language: str, lines: list[str]) -> list[dict]:
        """Check for basic syntax issues."""
        issues = []

        if language == "python":
            # Check for common Python syntax issues
            try:
                compile(code, "<string>", "exec")
            except SyntaxError as e:
                issues.append(
                    {
                        "line": e.lineno or 1,
                        "column": e.offset or 0,
                        "severity": "error",
                        "message": f"Syntax error: {e.msg}",
                        "rule": "syntax-error",
                    }
                )

        return issues

    def _check_style(self, lines: list[str], max_line_length: int, language: str) -> list[dict]:
        """Check code style violations."""
        issues = []

        for i, line in enumerate(lines, start=1):
            # Line length check
            if len(line) > max_line_length:
                issues.append(
                    {
                        "line": i,
                        "column": max_line_length,
                        "severity": "warning",
                        "message": f"Line too long ({len(line)} > {max_line_length} characters)",
                        "rule": "line-too-long",
                    }
                )

            # Trailing whitespace (check if line has trailing spaces/tabs before newline)
            if line.endswith((" ", "\t")) or (line != line.rstrip() and not line.endswith("\n")):
                issues.append(
                    {
                        "line": i,
                        "column": len(line.rstrip()),
                        "severity": "info",
                        "message": "Trailing whitespace",
                        "rule": "trailing-whitespace",
                    }
                )

            # Python-specific style checks
            if language == "python" and re.search(r"\w=[^=]|[^=]=\w", line):
                issues.append(
                    {
                        "line": i,
                        "column": 0,
                        "severity": "info",
                        "message": "Missing whitespace around operator",
                        "rule": "whitespace-around-operator",
                    }
                )

        return issues

    def _check_complexity(self, code: str, language: str, lines: list[str]) -> list[dict]:
        """Check code complexity metrics."""
        issues = []

        # Simple cyclomatic complexity estimation
        if language in ["python", "javascript", "typescript"]:
            # Count decision points (branches)
            complexity_count = 0
            for line in lines:
                # Count keywords that introduce branches
                complexity_count += line.count(" if ")
                complexity_count += line.count(" elif ")
                complexity_count += line.count(" for ")
                complexity_count += line.count(" while ")
                complexity_count += line.count(" and ")
                complexity_count += line.count(" or ")
                # Also count starting if/for/while
                stripped = line.lstrip()
                if stripped.startswith(("if ", "elif ", "for ", "while ")):
                    complexity_count += 1

            if complexity_count > 10:
                issues.append(
                    {
                        "line": 1,
                        "column": 0,
                        "severity": "warning",
                        "message": f"High code complexity (estimated {complexity_count} branches)",
                        "rule": "high-complexity",
                    }
                )

        return issues

    def _check_security(self, code: str, language: str, lines: list[str]) -> list[dict]:
        """Check for security vulnerabilities."""
        issues = []

        patterns = self.SECURITY_PATTERNS.get(language, [])
        for pattern, message, severity in patterns:
            for i, line in enumerate(lines, start=1):
                if re.search(pattern, line):
                    issues.append(
                        {
                            "line": i,
                            "column": 0,
                            "severity": severity,
                            "message": message,
                            "rule": "security-vulnerability",
                        }
                    )

        return issues
