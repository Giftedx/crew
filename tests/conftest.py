import sys
from pathlib import Path
import types

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.append(str(SRC_DIR))

# Stub heavy external dependencies for tests
sys.modules.setdefault("whisper", types.SimpleNamespace(load_model=lambda *a, **k: None))
sys.modules.setdefault("googleapiclient.discovery", types.SimpleNamespace(build=lambda *a, **k: None))
sys.modules.setdefault("googleapiclient.http", types.SimpleNamespace(MediaFileUpload=object))
sys.modules.setdefault(
    "google.oauth2.service_account",
    types.SimpleNamespace(Credentials=types.SimpleNamespace(from_service_account_file=lambda *a, **k: None)),
)
sys.modules.setdefault("crewai_tools", types.SimpleNamespace(BaseTool=object))
