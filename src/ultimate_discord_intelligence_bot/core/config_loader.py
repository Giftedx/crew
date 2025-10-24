from __future__ import annotations

from pathlib import Path
from typing import Any


class ConfigValidationError(ValueError):
    """Raised when configuration files fail validation."""


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import importlib

        yaml = importlib.import_module("yaml")
    except Exception as e:  # pragma: no cover - yaml optional for runtime, tests can install
        raise ConfigValidationError("PyYAML not installed; cannot load YAML configs") from e
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                raise ConfigValidationError(f"Invalid YAML structure in {path}")
            return data
    except FileNotFoundError as e:
        raise ConfigValidationError(f"Configuration file not found: {path}") from e
    except Exception as e:  # yaml.YAMLError and others
        raise ConfigValidationError(f"Invalid YAML in {path}: {e}") from e


def load_agents_config(config_path: str | Path) -> dict[str, Any]:
    """Load and minimally validate agents YAML.

    Required keys per agent: role, goal, backstory.
    """
    data = _load_yaml(Path(config_path))
    agents = data.get("agents") or data
    if not isinstance(agents, dict):
        raise ConfigValidationError("agents.yaml must contain a mapping of agents")

    for name, cfg in agents.items():
        if not isinstance(cfg, dict):
            raise ConfigValidationError(f"Agent '{name}' must be a mapping")
        for key in ("role", "goal", "backstory"):
            if not cfg.get(key):
                raise ConfigValidationError(f"Agent '{name}' missing required field: {key}")
    return agents


def load_tasks_config(config_path: str | Path) -> dict[str, Any]:
    """Load and minimally validate tasks YAML.

    Required keys per task: description, expected_output.
    """
    data = _load_yaml(Path(config_path))
    tasks = data.get("tasks") or data
    if not isinstance(tasks, dict):
        raise ConfigValidationError("tasks.yaml must contain a mapping of tasks")

    for name, cfg in tasks.items():
        if not isinstance(cfg, dict):
            raise ConfigValidationError(f"Task '{name}' must be a mapping")
        for key in ("description", "expected_output"):
            if not cfg.get(key):
                raise ConfigValidationError(f"Task '{name}' missing required field: {key}")
    return tasks


__all__ = [
    "ConfigValidationError",
    "load_agents_config",
    "load_tasks_config",
]
