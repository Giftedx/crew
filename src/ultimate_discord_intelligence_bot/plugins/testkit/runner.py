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
from typing import Any, Dict

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


def _load_manifest(plugin: str) -> Dict[str, Any]:
    module = importlib.import_module(plugin)
    manifest_path = Path(module.__file__).parent / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def run(plugin: str) -> Dict[str, Any]:
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
                passed = True
                reason = None
                if "must_include" in expected:
                    predicate = scorers.must_include(expected["must_include"])
                    if not predicate(str(output)):
                        passed = False
                        reason = "must_include failed"
                results.append(ScenarioResult(scenario["name"], passed, reason))
            except Exception as exc:  # pragma: no cover - exercised in tests
                results.append(ScenarioResult(scenario["name"], False, str(exc)))

    return {
        "plugin": manifest["name"],
        "results": [r.__dict__ for r in results],
    }
