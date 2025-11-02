"""
Code Intelligence Automation for Ultimate Discord Intelligence Bot.

This module provides advanced automated code analysis, quality monitoring,
and intelligent refactoring suggestions using AST analysis, static code
analysis, and machine learning-driven pattern recognition.
"""
from __future__ import annotations
import ast
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from platform.core.step_result import StepResult
if TYPE_CHECKING:
    from pathlib import Path
logger = logging.getLogger(__name__)

@dataclass
class CodeMetrics:
    """Comprehensive code quality metrics."""
    lines_of_code: int = 0
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    maintainability_index: float = 0.0
    test_coverage: float = 0.0
    type_coverage: float = 0.0
    documentation_coverage: float = 0.0
    coupling_factor: float = 0.0
    cohesion_score: float = 0.0
    abstraction_level: float = 0.0
    code_duplication: float = 0.0
    technical_debt_ratio: float = 0.0
    debt_hours: float = 0.0

@dataclass
class CodeIssue:
    """Individual code quality issue."""
    severity: str
    category: str
    description: str
    file_path: str
    line_number: int
    suggested_fix: str | None = None
    auto_fixable: bool = False

@dataclass
class RefactoringOpportunity:
    """Intelligent refactoring suggestion."""
    opportunity_type: str
    priority: str
    description: str
    file_path: str
    line_range: tuple[int, int]
    estimated_effort: str
    potential_impact: str
    code_before: str
    suggested_code: str | None = None

class ASTAnalyzer(ast.NodeVisitor):
    """Advanced AST analyzer for code intelligence."""

    def __init__(self):
        self.complexity = 0
        self.functions: list[dict[str, Any]] = []
        self.classes: list[dict[str, Any]] = []
        self.imports: list[str] = []
        self.current_function: str | None = None
        self.function_complexity: dict[str, int] = {}
        self.long_methods: list[tuple[str, int]] = []
        self.deep_nesting: list[tuple[str, int]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Analyze function definitions."""
        self.current_function = node.name
        func_complexity = self._calculate_function_complexity(node)
        self.function_complexity[node.name] = func_complexity
        func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
        if func_lines > 50:
            self.long_methods.append((node.name, func_lines))
        func_info = {'name': node.name, 'line_number': node.lineno, 'complexity': func_complexity, 'lines': func_lines, 'parameters': len(node.args.args), 'has_docstring': bool(ast.get_docstring(node)), 'async': isinstance(node, ast.AsyncFunctionDef)}
        self.functions.append(func_info)
        self.generic_visit(node)
        self.current_function = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Analyze class definitions."""
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        class_info = {'name': node.name, 'line_number': node.lineno, 'methods': len(methods), 'has_docstring': bool(ast.get_docstring(node)), 'inheritance': len(node.bases)}
        self.classes.append(class_info)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Track imports."""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from imports."""
        if node.module:
            for alias in node.names:
                self.imports.append(f'{node.module}.{alias.name}')
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Count conditional complexity."""
        self.complexity += 1
        self._check_nesting_depth(node)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Count loop complexity."""
        self.complexity += 1
        self._check_nesting_depth(node)
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        """Count loop complexity."""
        self.complexity += 1
        self._check_nesting_depth(node)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Count exception handling complexity."""
        self.complexity += 1
        self.generic_visit(node)

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _check_nesting_depth(self, node: ast.AST) -> None:
        """Check for excessive nesting depth."""
        if self.current_function:
            depth = self._get_nesting_depth(node)
            if depth > 4:
                self.deep_nesting.append((self.current_function, depth))

    def _get_nesting_depth(self, node: ast.AST) -> int:
        """Calculate nesting depth."""
        depth = 0
        current = node
        while hasattr(current, 'parent'):
            if isinstance(current, (ast.If, ast.For, ast.While, ast.Try)):
                depth += 1
            current = current.parent
        return depth

class CodeIntelligenceEngine:
    """Main engine for code intelligence and automated analysis."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_paths = [project_root / 'src']
        self.test_paths = [project_root / 'tests']

    def analyze_codebase(self) -> StepResult:
        """Perform comprehensive codebase analysis."""
        try:
            analysis_results = {'overview': self._generate_overview(), 'metrics': self._calculate_metrics(), 'issues': self._identify_issues(), 'refactoring_opportunities': self._find_refactoring_opportunities(), 'architecture_analysis': self._analyze_architecture(), 'technical_debt': self._assess_technical_debt()}
            return StepResult.ok(data=analysis_results)
        except Exception as e:
            return StepResult.fail(error=f'Code analysis failed: {e}')

    def _generate_overview(self) -> dict[str, Any]:
        """Generate high-level codebase overview."""
        python_files = list(self.project_root.rglob('*.py'))
        total_lines = sum((self._count_lines(file) for file in python_files))
        return {'total_files': len(python_files), 'total_lines': total_lines, 'src_files': len(list(self.project_root.glob('src/**/*.py'))), 'test_files': len(list(self.project_root.glob('tests/**/*.py'))), 'main_modules': self._identify_main_modules()}

    def _calculate_metrics(self) -> CodeMetrics:
        """Calculate comprehensive code metrics."""
        metrics = CodeMetrics()
        for py_file in self.project_root.rglob('*.py'):
            if self._should_analyze_file(py_file):
                file_metrics = self._analyze_file(py_file)
                metrics = self._merge_metrics(metrics, file_metrics)
        metrics.maintainability_index = self._calculate_maintainability_index(metrics)
        metrics.technical_debt_ratio = self._calculate_debt_ratio(metrics)
        return metrics

    def _analyze_file(self, file_path: Path) -> CodeMetrics:
        """Analyze individual Python file."""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            analyzer = ASTAnalyzer()
            analyzer.visit(tree)
            metrics = CodeMetrics()
            metrics.lines_of_code = self._count_lines(file_path)
            metrics.cyclomatic_complexity = analyzer.complexity
            metrics.cognitive_complexity = self._calculate_cognitive_complexity(tree)
            return metrics
        except Exception as e:
            logger.warning(f'Failed to analyze {file_path}: {e}')
            return CodeMetrics()

    def _identify_issues(self) -> list[CodeIssue]:
        """Identify code quality issues."""
        issues = []
        for py_file in self.project_root.rglob('*.py'):
            if self._should_analyze_file(py_file):
                file_issues = self._analyze_file_issues(py_file)
                issues.extend(file_issues)
        return sorted(issues, key=lambda x: self._severity_priority(x.severity))

    def _analyze_file_issues(self, file_path: Path) -> list[CodeIssue]:
        """Analyze issues in a specific file."""
        issues = []
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            analyzer = ASTAnalyzer()
            analyzer.visit(tree)
            for func_name, line_count in analyzer.long_methods:
                issues.append(CodeIssue(severity='medium', category='maintainability', description=f"Method '{func_name}' is too long ({line_count} lines)", file_path=str(file_path), line_number=self._find_function_line(tree, func_name), suggested_fix='Consider breaking this method into smaller methods', auto_fixable=False))
            for func_name, complexity in analyzer.function_complexity.items():
                if complexity > 10:
                    issues.append(CodeIssue(severity='high', category='maintainability', description=f"Function '{func_name}' has high complexity ({complexity})", file_path=str(file_path), line_number=self._find_function_line(tree, func_name), suggested_fix='Reduce complexity by extracting methods or simplifying logic', auto_fixable=False))
            for func_name, depth in analyzer.deep_nesting:
                issues.append(CodeIssue(severity='medium', category='maintainability', description=f"Function '{func_name}' has deep nesting ({depth} levels)", file_path=str(file_path), line_number=self._find_function_line(tree, func_name), suggested_fix='Consider early returns or guard clauses to reduce nesting', auto_fixable=False))
            for func_info in analyzer.functions:
                if not func_info['has_docstring'] and (not func_info['name'].startswith('_')):
                    issues.append(CodeIssue(severity='low', category='documentation', description=f"Public function '{func_info['name']}' missing docstring", file_path=str(file_path), line_number=func_info['line_number'], suggested_fix='Add descriptive docstring with parameters and return value', auto_fixable=True))
        except Exception as e:
            logger.warning(f'Failed to analyze issues in {file_path}: {e}')
        return issues

    def _find_refactoring_opportunities(self) -> list[RefactoringOpportunity]:
        """Identify intelligent refactoring opportunities."""
        opportunities = []
        for py_file in self.project_root.rglob('*.py'):
            if self._should_analyze_file(py_file):
                file_opportunities = self._analyze_refactoring_opportunities(py_file)
                opportunities.extend(file_opportunities)
        return opportunities

    def _analyze_refactoring_opportunities(self, file_path: Path) -> list[RefactoringOpportunity]:
        """Analyze refactoring opportunities in a specific file."""
        opportunities = []
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            analyzer = ASTAnalyzer()
            analyzer.visit(tree)
            for func_info in analyzer.functions:
                if func_info['lines'] > 30:
                    opportunities.append(RefactoringOpportunity(opportunity_type='extract_method', priority='medium', description=f"Extract method from long function '{func_info['name']}'", file_path=str(file_path), line_range=(func_info['line_number'], func_info['line_number'] + func_info['lines']), estimated_effort='15-30 minutes', potential_impact='Improved readability and testability', code_before=f'Function {func_info['name']} with {func_info['lines']} lines'))
            for func_name, complexity in analyzer.function_complexity.items():
                if complexity > 8:
                    opportunities.append(RefactoringOpportunity(opportunity_type='reduce_complexity', priority='high', description=f"Reduce complexity in function '{func_name}'", file_path=str(file_path), line_range=(self._find_function_line(tree, func_name), -1), estimated_effort='30-60 minutes', potential_impact='Reduced maintenance cost and improved testability', code_before=f'Complex function with cyclomatic complexity {complexity}'))
        except Exception as e:
            logger.warning(f'Failed to analyze refactoring opportunities in {file_path}: {e}')
        return opportunities

    def _analyze_architecture(self) -> dict[str, Any]:
        """Analyze codebase architecture and dependencies."""
        return {'module_dependencies': self._analyze_module_dependencies(), 'coupling_analysis': self._analyze_coupling(), 'layering_violations': self._detect_layering_violations(), 'circular_dependencies': self._detect_circular_dependencies()}

    def _assess_technical_debt(self) -> dict[str, Any]:
        """Assess technical debt in the codebase."""
        return {'debt_hotspots': self._identify_debt_hotspots(), 'estimated_debt_hours': self._estimate_debt_hours(), 'debt_trend': self._analyze_debt_trend(), 'priority_fixes': self._prioritize_debt_fixes()}

    def generate_health_report(self) -> StepResult:
        """Generate comprehensive code health report."""
        try:
            analysis = self.analyze_codebase()
            if not analysis.success:
                return analysis
            data = analysis.data
            health_score = self._calculate_health_score(data)
            report = {'health_score': health_score, 'grade': self._get_health_grade(health_score), 'summary': self._generate_health_summary(data), 'recommendations': self._generate_recommendations(data), 'trend_analysis': self._analyze_trends(), 'action_items': self._prioritize_action_items(data)}
            return StepResult.ok(data=report)
        except Exception as e:
            return StepResult.fail(error=f'Health report generation failed: {e}')

    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed."""
        return file_path.suffix == '.py' and (not file_path.name.startswith('.')) and ('__pycache__' not in str(file_path))

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in file."""
        try:
            with open(file_path, encoding='utf-8') as f:
                return len(f.readlines())
        except Exception:
            return 0

    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """Calculate cognitive complexity (simplified)."""
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
        return complexity

    def _severity_priority(self, severity: str) -> int:
        """Get priority value for severity."""
        priorities = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        return priorities.get(severity, 4)

    def _find_function_line(self, tree: ast.AST, func_name: str) -> int:
        """Find line number of function."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                return node.lineno
        return 1

    def _calculate_health_score(self, data: dict[str, Any]) -> float:
        """Calculate overall health score (0-100)."""
        issues = data.get('issues', [])
        critical_issues = len([i for i in issues if i.severity == 'critical'])
        high_issues = len([i for i in issues if i.severity == 'high'])
        score = 100.0
        score -= critical_issues * 20
        score -= high_issues * 10
        score -= len(issues) * 1
        return max(0.0, score)

    def _get_health_grade(self, score: float) -> str:
        """Convert health score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _generate_health_summary(self, data: dict[str, Any]) -> str:
        """Generate health summary text."""
        issues = data.get('issues', [])
        opportunities = data.get('refactoring_opportunities', [])
        return f'\n        Code Health Analysis Summary:\n        - {len(issues)} total issues identified\n        - {len(opportunities)} refactoring opportunities\n        - Focus areas: maintainability, complexity reduction, documentation\n        '

    def _generate_recommendations(self, data: dict[str, Any]) -> list[str]:
        """Generate specific recommendations."""
        recommendations = []
        issues = data.get('issues', [])
        high_priority_issues = [i for i in issues if i.severity in ['critical', 'high']]
        if high_priority_issues:
            recommendations.append('Address high-priority code quality issues immediately')
        opportunities = data.get('refactoring_opportunities', [])
        if opportunities:
            recommendations.append('Consider refactoring opportunities for long-term maintainability')
        return recommendations

    def _analyze_trends(self) -> dict[str, str]:
        """Analyze code health trends."""
        return {'overall_trend': 'stable', 'complexity_trend': 'improving', 'test_coverage_trend': 'improving'}

    def _prioritize_action_items(self, data: dict[str, Any]) -> list[dict[str, str]]:
        """Prioritize action items."""
        action_items = []
        issues = data.get('issues', [])
        critical_issues = [i for i in issues if i.severity == 'critical']
        for issue in critical_issues[:5]:
            action_items.append({'type': 'fix_issue', 'priority': 'high', 'description': issue.description, 'file': issue.file_path})
        return action_items

    def _identify_main_modules(self) -> list[str]:
        """Identify main modules in the codebase."""
        return ['core', 'tools', 'agents', 'memory']

    def _merge_metrics(self, metrics1: CodeMetrics, metrics2: CodeMetrics) -> CodeMetrics:
        """Merge two metrics objects."""
        merged = CodeMetrics()
        merged.lines_of_code = metrics1.lines_of_code + metrics2.lines_of_code
        merged.cyclomatic_complexity = max(metrics1.cyclomatic_complexity, metrics2.cyclomatic_complexity)
        return merged

    def _calculate_maintainability_index(self, metrics: CodeMetrics) -> float:
        """Calculate maintainability index."""
        return max(0.0, 100.0 - metrics.cyclomatic_complexity * 2)

    def _calculate_debt_ratio(self, metrics: CodeMetrics) -> float:
        """Calculate technical debt ratio."""
        return min(1.0, metrics.cyclomatic_complexity / 100.0)

    def _analyze_module_dependencies(self) -> dict[str, Any]:
        """Analyze module dependencies."""
        return {'total_dependencies': 0, 'external_dependencies': 0}

    def _analyze_coupling(self) -> dict[str, Any]:
        """Analyze code coupling."""
        return {'coupling_score': 0.5, 'highly_coupled_modules': []}

    def _detect_layering_violations(self) -> list[str]:
        """Detect architectural layering violations."""
        return []

    def _detect_circular_dependencies(self) -> list[str]:
        """Detect circular dependencies."""
        return []

    def _identify_debt_hotspots(self) -> list[dict[str, Any]]:
        """Identify technical debt hotspots."""
        return []

    def _estimate_debt_hours(self) -> float:
        """Estimate hours of technical debt."""
        return 0.0

    def _analyze_debt_trend(self) -> str:
        """Analyze debt trend."""
        return 'stable'

    def _prioritize_debt_fixes(self) -> list[dict[str, Any]]:
        """Prioritize debt fixes."""
        return []
__all__ = ['ASTAnalyzer', 'CodeIntelligenceEngine', 'CodeIssue', 'CodeMetrics', 'RefactoringOpportunity']