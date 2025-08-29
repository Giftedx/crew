import sys
import types
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.append(str(SRC_DIR))

# Stub heavy external dependencies for tests
sys.modules.setdefault("whisper", types.SimpleNamespace(load_model=lambda *a, **k: None))
sys.modules.setdefault(
    "googleapiclient.discovery", types.SimpleNamespace(build=lambda *a, **k: None)
)
sys.modules.setdefault("googleapiclient.http", types.SimpleNamespace(MediaFileUpload=object))
sys.modules.setdefault(
    "google.oauth2.service_account",
    types.SimpleNamespace(
        Credentials=types.SimpleNamespace(from_service_account_file=lambda *a, **k: None)
    ),
)
sys.modules.setdefault("crewai_tools", types.SimpleNamespace(BaseTool=object))
# Provide fallback for crewai.tools.BaseTool if crewai not installed or import side-effects undesired.
try:  # pragma: no cover - protective shim
    pass  # type: ignore
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
import importlib.util as _ilu
if _ilu.find_spec("dotenv") is None and "dotenv" not in sys.modules:  # pragma: no cover
    dotenv_mod = types.ModuleType("dotenv")

    def _load_dotenv(*a, **k):  # pragma: no cover
        return True

    def _dotenv_values(*a, **k):  # pragma: no cover
        return {}

    dotenv_mod.load_dotenv = _load_dotenv  # type: ignore[attr-defined]
    dotenv_mod.dotenv_values = _dotenv_values  # type: ignore[attr-defined]
    sys.modules["dotenv"] = dotenv_mod
