import importlib.util as _ilu
import sys
import types
from pathlib import Path

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
