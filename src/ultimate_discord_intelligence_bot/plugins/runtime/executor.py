from __future__ import annotations

import importlib
import json
import multiprocessing as mp
import pathlib
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

try:  # Support different jsonschema versions
    from jsonschema import validate as _js_validate
except Exception:  # pragma: no cover - fallback when jsonschema missing or API changed
    _js_validate = None

from core import learn
from core.rl import registry as rl_registry

from .perm_guard import PermissionError, PermissionGuard


@dataclass
class PluginResult:
    success: bool
    output: Any = None
    error: str | None = None


def _plugin_entry(entrypoint: str, adapters: dict[str, Any], args: dict[str, Any], queue: mp.Queue) -> None:
    """Load the plugin entrypoint and execute it."""
    try:
        module_name, func_name = entrypoint.split(":")
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
        result = func(adapters=adapters, **args)
        queue.put(PluginResult(success=True, output=result))
    except Exception as exc:  # pragma: no cover - bubble up for logging
        queue.put(PluginResult(success=False, error=str(exc)))


class PluginExecutor:
    """Validate a plugin manifest and run the entrypoint in a sandboxed process."""

    def __init__(self, manifest_schema: pathlib.Path | str):
        self._schema_path = pathlib.Path(manifest_schema)
        with self._schema_path.open("r", encoding="utf-8") as fh:
            self._schema = json.load(fh)

    def _load_manifest(self, plugin_dir: pathlib.Path) -> dict[str, Any]:
        manifest_file = plugin_dir / "manifest.json"
        with manifest_file.open("r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        if _js_validate is not None:
            _js_validate(manifest, self._schema)
        else:  # pragma: no cover - degraded validation path
            # Minimal structural checks as fallback
            if not isinstance(manifest, dict):  # noqa: TRY301
                raise ValueError("Invalid manifest structure")
            required = self._schema.get("required", []) if isinstance(self._schema, dict) else []
            missing = [k for k in required if k not in manifest]
            if missing:
                raise ValueError(f"Manifest missing required fields: {missing}")
        return manifest

    def run(  # noqa: PLR0913 - parameters mirror sandbox policy + execution knobs; **kwargs would obscure contract
        self,
        plugin_dir: str | pathlib.Path,
        granted_scopes: Iterable[str],
        adapters: dict[str, Any],
        args: dict[str, Any] | None = None,
        timeout: float = 10.0,
        *,
        policy_registry: rl_registry.PolicyRegistry | None = None,
    ) -> PluginResult:
        plugin_path = pathlib.Path(plugin_dir)
        manifest = self._load_manifest(plugin_path)
        guard = PermissionGuard(granted_scopes)
        try:
            guard.require(manifest.get("capabilities", []))
        except PermissionError as exc:
            return PluginResult(success=False, error=str(exc))

        entrypoint = manifest["entrypoint"]

        result_holder: dict[str, PluginResult] = {}

        def act(chosen_timeout: float):
            start = time.perf_counter()
            queue: mp.Queue = mp.Queue()
            proc = mp.Process(
                target=_plugin_entry,
                args=(entrypoint, adapters, args or {}, queue),
            )
            proc.start()
            proc.join(chosen_timeout)
            if proc.is_alive():
                proc.kill()
                res = PluginResult(success=False, error="timeout")
            else:
                res = queue.get() if not queue.empty() else PluginResult(success=False, error="no result")
            elapsed = (time.perf_counter() - start) * 1000
            result_holder["res"] = res
            outcome = {"cost_usd": 0.0, "latency_ms": elapsed}
            signals = {"quality": 1.0 if res.success else 0.0}
            return outcome, signals

        candidates = [timeout, max(1.0, timeout / 2.0)]
        learn.learn(
            "plugin",
            {"name": manifest.get("name", plugin_path.name)},
            candidates,
            act,
            policy_registry=policy_registry,
        )
        return result_holder.get("res", PluginResult(success=False, error="no result"))
