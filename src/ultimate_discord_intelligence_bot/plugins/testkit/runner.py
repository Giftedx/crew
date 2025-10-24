"""Lightweight plugin test runner.

The runner loads a plugin's manifest, executes its self-test entrypoint
and then iterates through the declared capability scenarios.  Each
scenario invokes the plugin's entrypoint with stubbed adapters and the
provided inputs, asserting that expected predicates hold.
"""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from . import scorers


class DummyLLM:
    """Minimal stub used for plugin tests."""

    def generate(self, _prompt: str) -> str:  # pragma: no cover - trivial
        return "stubbed summary"


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    reason: str | None = None


def _load_manifest(plugin: str) -> dict[str, Any]:
    module = importlib.import_module(plugin)
    module_file = getattr(module, "__file__", None)
    if module_file is None:
        raise RuntimeError(f"Plugin module {plugin} has no __file__ attribute")
    manifest_path = Path(cast("str", module_file)).parent / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise RuntimeError("manifest.json must contain an object")
    # manifest shape is heterogeneous; we retain Dict[str, Any]
    return data


def run(plugin: str) -> dict[str, Any]:
    """Execute the plugin's capability scenarios.

    Parameters
    ----------
    plugin:
        Import path of the plugin package.

    Returns
    -------
    Dict[str, Any]
        Summary report including scenario results.
    """

    manifest = _load_manifest(plugin)
    tests = manifest.get("tests")
    if not tests:
        raise RuntimeError("manifest is missing 'tests' block")

    # Self-test
    module_name, func_name = tests["selftest_entrypoint"].split(":")
    self_fn = getattr(importlib.import_module(module_name), func_name)
    if not self_fn():
        raise RuntimeError("self-test failed")

    # Entrypoint
    ent_mod, ent_func = manifest["entrypoint"].split(":")
    entry_fn = getattr(importlib.import_module(ent_mod), ent_func)

    results: list[ScenarioResult] = []
    for matrix in tests.get("capability_matrix", []):
        for scenario in matrix.get("scenarios", []):
            adapters = {"svc_llm": DummyLLM()}
            try:
                output = entry_fn(adapters, **scenario.get("inputs", {}))
                expected = scenario.get("expected", {})
                checks: list[tuple[str, bool]] = []
                out_str = str(output)
                if "must_include" in expected:
                    checks.append(
                        (
                            "must_include",
                            scorers.must_include(expected["must_include"])(out_str),
                        )
                    )
                if "forbidden" in expected:
                    checks.append(("forbidden", scorers.forbidden(expected["forbidden"])(out_str)))
                if "must_link" in expected:
                    checks.append(("must_link", scorers.must_link(expected["must_link"])(out_str)))
                if "status_ok" in expected:
                    checks.append(("status_ok", scorers.status_ok()(output)))
                failing = next((name for name, ok in checks if not ok), None)
                results.append(
                    ScenarioResult(
                        scenario["name"],
                        failing is None,
                        f"{failing} failed" if failing else None,
                    )
                )
            except Exception as exc:  # pragma: no cover - exercised in tests
                results.append(ScenarioResult(scenario["name"], False, str(exc)))

    return {
        "plugin": manifest["name"],
        "results": [r.__dict__ for r in results],
    }
