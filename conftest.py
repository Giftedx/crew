"""Root-level pytest configuration for this repo.

We enable asyncio support explicitly when the optional dependency is present.
In CI or minimal environments where pytest-asyncio isn't installed, tests that
don't require asyncio can still run by skipping the plugin.
"""

import importlib
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    """Inject the project's ``src`` directory into ``sys.path`` for tests.

    Pytest spawns from the repository root where ``src`` isn't automatically
    discoverable. Adding it manually ensures imports like ``eval.langsmith``
    resolve without relying on environment variables.
    """

    project_root = Path(__file__).resolve().parent
    src_path = project_root / "src"
    if src_path.exists():
        src_str = str(src_path)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_ensure_src_on_path()


def _prefer_local_opentelemetry() -> None:
    """Ensure the in-repo OpenTelemetry shim is imported ahead of site packages."""

    project_root = Path(__file__).resolve().parent
    local_pkg_prefix = str(project_root / "src" / "opentelemetry")

    existing = sys.modules.get("opentelemetry")
    if existing:
        module_path = getattr(existing, "__file__", "") or ""
        if module_path.startswith(local_pkg_prefix):
            return
        for name in list(sys.modules):
            if name == "opentelemetry" or name.startswith("opentelemetry."):
                sys.modules.pop(name, None)

    try:
        module = importlib.import_module("opentelemetry")
    except Exception:  # pragma: no cover - shim opt-in only when available
        return

    module_path = getattr(module, "__file__", "") or ""
    if module_path.startswith(local_pkg_prefix):
        sys.modules["opentelemetry"] = module


_prefer_local_opentelemetry()


try:  # Optional: only enable if available
    import pytest_asyncio  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover - environment dependent
    pytest_plugins: list[str] = []
else:
    pytest_plugins = ["pytest_asyncio"]
