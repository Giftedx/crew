#!/usr/bin/env python3
"""Validate that all tools are importable and all Tool classes are exported.

Checks:
1) Import all names from ultimate_discord_intelligence_bot.tools.__all__ without raising.
    Tools with optional deps may resolve to stubs; that's OK.
2) Static coverage: any class in tools/ that subclasses BaseTool (and endswith "Tool")
    must appear in tools.__all__. This prevents un-exported Tool classes.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import os
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    sys.path.insert(0, "src")
    mod = importlib.import_module("ultimate_discord_intelligence_bot.tools")
    ok: list[str] = []
    stubs: list[str] = []
    failures: list[tuple[str, str]] = []
    for name in getattr(mod, "__all__", []):
        try:
            obj = getattr(mod, name)
            if inspect.isclass(obj) and obj.__module__ == "ultimate_discord_intelligence_bot.tools.__init__":
                stubs.append(name)
            else:
                ok.append(name)
        except Exception as e:  # pragma: no cover - simple guard
            failures.append((name, f"{type(e).__name__}: {e}"))
    print(f"[tools-validate] OK={len(ok)} STUBS={len(stubs)} FAILURES={len(failures)}")
    if failures:
        for n, err in failures:
            print(f" - FAIL {n}: {err}")
        return 2

    # Static coverage: ensure every BaseTool subclass is exported via __all__
    missing_exports: list[str] = []
    tools_root = Path("src/ultimate_discord_intelligence_bot/tools")
    exported = set(getattr(mod, "__all__", []))

    # Allowlist for tool-like classes intentionally not exported via tools.__all__
    # These include abstract bases, internal wrappers, or experimental tools.
    ALLOWED_MISSING_EXPORTS: set[str] = {
        # Base/abstract classes and templates
        "MemoryBaseTool",
        "AnalysisBaseTool",
        "VerificationBaseTool",
        "AcquisitionBaseTool",
        "AnalysisTool",
        "AcquisitionTool",
        "TranscriptionTool",
        "StandardTool",
        "TemplateTool",
        # MCP wrappers and internal tools
        "WebSearchTool",
        "DataAnalysisTool",
        "CodeReviewTool",
        # Observability/Cache/Router internal tools (not exported at top-level)
        "CacheV2Tool",
        "CostTrackingTool",
        "RouterStatusTool",
        "MCPResourceTool",
        "CacheOptimizationTool",
        "CacheStatusTool",
        "TaskManagementTool",
        "OrchestrationStatusTool",
        # Memory tools that are not exposed at top-level
        "UnifiedMemoryStoreTool",
        "UnifiedContextTool",
        "MemoryV2Tool",
        # Analysis tools
        "MultiModalAnalysisTool",
        "OpenAIEnhancedAnalysisTool",
        # Lazy-load stub placeholder
        "StubTool",
    }

    def _is_tool_class(node: ast.ClassDef) -> bool:
        # Name heuristic first
        if not node.name.endswith("Tool") or node.name.startswith("_"):
            return False
        # Base class heuristic: BaseTool or BaseTool[...]
        for b in node.bases:
            if isinstance(b, ast.Name) and b.id == "BaseTool":
                return True
            if isinstance(b, ast.Subscript) and isinstance(b.value, ast.Name) and b.value.id == "BaseTool":
                return True
        return False

    for py in tools_root.rglob("*.py"):
        # Skip package init and golden examples directory
        if py.name == "__init__.py" or os.sep + "golden" + os.sep in str(py):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except Exception:
            continue  # non-fatal; import-based check above should catch runtime issues
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and _is_tool_class(node):
                if node.name in exported or node.name in ALLOWED_MISSING_EXPORTS:
                    continue
                missing_exports.append(f"{node.name} (in {py.relative_to(tools_root)})")

    if missing_exports:
        print("[tools-validate] Missing exports for BaseTool subclasses:")
        for m in missing_exports:
            print(f" - {m}")
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
