from __future__ import annotations

import importlib
import importlib.util as _ilu
import os
import sys
import types
from pathlib import Path

import pytest


def pytest_ignore_collect(collection_path: Path, config) -> bool:  # type: ignore[override]
    """Conditionally ignore tests that require optional heavy dependencies.

    If importing 'crewai' fails for any reason (missing extras or platform wheels),
    skip collecting tests that depend on it to keep the fast test subset stable.
    """
    basename = os.path.basename(str(collection_path))
    if basename == "test_crewai_enhancements.py":
        try:
            importlib.import_module("crewai")
            return False
        except Exception:
            return True
    return False


# Ensure repository root (for 'scripts' package) and src/ are on sys.path.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))


# Stub heavy external dependencies for tests
def _stub_module(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    return mod


whisper_mod = _stub_module("whisper")
whisper_mod.load_model = lambda *a, **k: None  # type: ignore[attr-defined]
sys.modules.setdefault("whisper", whisper_mod)

gdisc_mod = _stub_module("googleapiclient.discovery")
gdisc_mod.build = lambda *a, **k: None  # type: ignore[attr-defined]
sys.modules.setdefault("googleapiclient.discovery", gdisc_mod)

ghttp_mod = _stub_module("googleapiclient.http")
ghttp_mod.MediaFileUpload = object  # type: ignore[attr-defined]
sys.modules.setdefault("googleapiclient.http", ghttp_mod)

gsa_mod = _stub_module("google.oauth2.service_account")
creds_cls = types.SimpleNamespace(from_service_account_file=lambda *a, **k: None)
gsa_mod.Credentials = creds_cls  # type: ignore[attr-defined]
sys.modules.setdefault("google.oauth2.service_account", gsa_mod)

crewai_tools_mod = _stub_module("crewai_tools")
crewai_tools_mod.BaseTool = object  # type: ignore[attr-defined]
sys.modules.setdefault("crewai_tools", crewai_tools_mod)

# Stub instructor to avoid import issues
instructor_mod = _stub_module("instructor")
instructor_mod.from_openai = lambda *a, **k: None  # type: ignore[attr-defined]
sys.modules.setdefault("instructor", instructor_mod)

# Provide fallback for crewai.tools.BaseTool if crewai not installed or import side-effects undesired.
try:  # pragma: no cover - protective shim
    pass
except Exception:  # broad catch acceptable in test shim
    crewai_pkg = types.ModuleType("crewai")
    tools_mod = types.ModuleType("crewai.tools")

    class _BaseTool:  # minimal interface used in tests
        pass

    tools_mod.BaseTool = _BaseTool  # type: ignore[attr-defined]
    sys.modules.setdefault("crewai", crewai_pkg)
    sys.modules.setdefault("crewai.tools", tools_mod)

# Provide lightweight stub for python-dotenv only if truly missing. The pydantic-settings
# provider imports dotenv_values; supply it so import does not fail. Avoid overwriting the
# real package when installed to prevent 'unknown location' import errors.
if _ilu.find_spec("dotenv") is None and "dotenv" not in sys.modules:  # pragma: no cover
    dotenv_mod = types.ModuleType("dotenv")

    def _load_dotenv(*a, **k):  # pragma: no cover
        return True

    def _dotenv_values(*a, **k):  # pragma: no cover
        return {}

    dotenv_mod.load_dotenv = _load_dotenv  # type: ignore[attr-defined]
    dotenv_mod.dotenv_values = _dotenv_values  # type: ignore[attr-defined]
    sys.modules["dotenv"] = dotenv_mod


def pytest_configure(config):  # noqa: D401
    """Register custom markers and set default lightweight mode early.

    We default to LIGHTWEIGHT_IMPORT=1 so that importing heavy Discord / FastAPI
    stacks is avoided for the majority of unit tests. Tests that require real
    integrations can declare @pytest.mark.fullstack or set env
    FULL_STACK_TEST=1 to disable the guard.
    """
    config.addinivalue_line("markers", "fullstack: enable full dependency imports (discord, fastapi, etc.)")
    if os.getenv("FULL_STACK_TEST") != "1":
        os.environ.setdefault("LIGHTWEIGHT_IMPORT", "1")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):  # noqa: D401
    """Clear lightweight guard when test explicitly requests fullstack.

    If a test is marked with @pytest.mark.fullstack we remove the
    LIGHTWEIGHT_IMPORT flag prior to its import/fixture setup so module level
    imports behave as in production.
    """
    if item.get_closest_marker("fullstack") is not None:
        os.environ.pop("LIGHTWEIGHT_IMPORT", None)
