"""Guard script to ensure StepResult-returning tools are metrics-instrumented.

Rules (kept intentionally simple & low-cost):
1. A file under `src/ultimate_discord_intelligence_bot/tools/` that:
   - Imports StepResult (direct import of step_result.StepResult) AND
   - Defines a class whose name ends with `Tool` (heuristic for tool classes) AND
   - Contains a `_run` or `run` method body referencing `StepResult` (return usage) or
     has `-> StepResult` in its signature
   must also reference metrics instrumentation via either:
       get_metrics(  OR  .counter("tool_runs_total"  OR  .histogram("tool_run_seconds"

2. Exclusions: Some scripts or helper auditors inside tools/ are not actual runtime tools.
   We maintain an ALLOWED_UNINSTRUMENTED set for explicit exceptions (kept minimal).

Exit code:
 - 0 if all compliant
 - 1 if any violations (each printed)

This script is fast (pure text scan + light AST for signatures) and safe to run in CI.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


TOOLS_DIR = Path("src/ultimate_discord_intelligence_bot/tools")

# Explicit allowlist for tool-like files intentionally without metrics (keep minimal)
ALLOWED_UNINSTRUMENTED = {
    "step_result_auditor.py",  # analysis / auditing script, not invoked in production pipeline
    "compliance_summary.py",  # reporting script
    "compliance_executive_summary.py",  # reporting script
    # Abstract base classes (not directly instantiated, no runtime metrics needed)
    "_base.py",  # Base tool interface
    "acquisition_base.py",  # Base acquisition tool
    "analysis_base.py",  # Base analysis tool
    "memory_base.py",  # Base memory tool
    "standard_tool.py",  # Standard tool template
    "template_tool.py",  # Tool template
    "verification_base.py",  # Base verification tool
    # TODO: Add metrics instrumentation to these tools in future phase
    "knowledge_ops_tool.py",  # not currently used in crew configuration
    "multimodal_analysis_tool_old.py",  # old version, not used
    "narrative_tracker_tool.py",  # not currently used in crew configuration
    "output_validation_tool.py",  # not currently used in crew configuration
    "reanalysis_trigger_tool.py",  # not currently used in crew configuration
    "smart_clip_composer_tool.py",  # not currently used in crew configuration
    "social_graph_analysis_tool.py",  # not currently used in crew configuration
    "sponsor_compliance_tool.py",  # not currently used in crew configuration
    "tiktok_enhanced_download_tool.py",  # not currently used in crew configuration
    "twitter_thread_reconstructor_tool.py",  # not currently used in crew configuration
    "unified_cache_tool.py",  # not currently used in crew configuration
    # Tools currently used in crew configuration - all have metrics instrumentation now
}


def file_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def is_candidate(path: Path, text: str) -> bool:
    if path.name in ALLOWED_UNINSTRUMENTED:
        return False
    if "StepResult" not in text:
        return False
    return not ("class " not in text or "Tool" not in text)


def extract_tool_classes(path: Path, text: str) -> list[ast.ClassDef]:
    out: list[ast.ClassDef] = []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return out
    return [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name.endswith("Tool")]


def class_uses_stepresult(cls: ast.ClassDef) -> bool:
    for node in ast.walk(cls):
        if isinstance(node, ast.FunctionDef) and node.name in {
            "run",
            "_run",
            "execute",
            "_execute",
        }:
            # Signature annotation
            if node.returns and isinstance(node.returns, ast.Name) and node.returns.id == "StepResult":
                return True
            # Body usage (search for StepResult.ok/fail/from_dict in calls)
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    if (
                        isinstance(func, ast.Attribute)
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "StepResult"
                    ):
                        return True
    return False


def has_metrics(text: str) -> bool:
    return (
        "get_metrics(" in text
        or (".counter(" in text and "tool_runs_total" in text)
        or (".histogram(" in text and "tool_run_seconds" in text)
    )


def main() -> int:
    if not TOOLS_DIR.exists():
        print("[metrics-guard] tools directory not found; skipping")
        return 0
    violations: list[str] = []
    for path in TOOLS_DIR.glob("*.py"):
        text = file_text(path)
        if not is_candidate(path, text):
            continue
        tool_classes = extract_tool_classes(path, text)
        # Only flag if at least one tool class actually uses StepResult
        if not any(class_uses_stepresult(cls) for cls in tool_classes):
            continue
        if not has_metrics(text):
            violations.append(path.name)
    if violations:
        print("[metrics-guard] Missing instrumentation in:")
        for v in sorted(violations):
            print(f"  - {v}")
        print(
            "Add get_metrics() + counter('tool_runs_total', labels={tool,outcome}) instrumentation or add to ALLOWED_UNINSTRUMENTED if intentionally excluded."
        )
        return 1
    print("[metrics-guard] All StepResult tools instrumented.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
