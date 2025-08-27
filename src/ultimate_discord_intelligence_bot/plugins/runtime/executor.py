from __future__ import annotations

import importlib
import json
import multiprocessing as mp
import pathlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import jsonschema

from .perm_guard import PermissionGuard, PermissionError


@dataclass
class PluginResult:
    success: bool
    output: Any = None
    error: Optional[str] = None


def _plugin_entry(entrypoint: str, adapters: Dict[str, Any], args: Dict[str, Any], queue: mp.Queue) -> None:
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

    def _load_manifest(self, plugin_dir: pathlib.Path) -> Dict[str, Any]:
        manifest_file = plugin_dir / "manifest.json"
        with manifest_file.open("r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        jsonschema.validate(manifest, self._schema)
        return manifest

    def run(
        self,
        plugin_dir: str | pathlib.Path,
        granted_scopes: Iterable[str],
        adapters: Dict[str, Any],
        args: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0,
    ) -> PluginResult:
        plugin_path = pathlib.Path(plugin_dir)
        manifest = self._load_manifest(plugin_path)
        guard = PermissionGuard(granted_scopes)
        try:
            guard.require(manifest.get("capabilities", []))
        except PermissionError as exc:
            return PluginResult(success=False, error=str(exc))

        entrypoint = manifest["entrypoint"]
        queue: mp.Queue = mp.Queue()
        proc = mp.Process(
            target=_plugin_entry,
            args=(entrypoint, adapters, args or {}, queue),
        )
        proc.start()
        proc.join(timeout)
        if proc.is_alive():
            proc.kill()
            return PluginResult(success=False, error="timeout")
        return queue.get() if not queue.empty() else PluginResult(success=False, error="no result")
