import importlib.util
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / 'src'
sys.path.append(str(SRC_DIR))

# Map package name with underscores to directory with spaces
pkg_path = SRC_DIR / 'Ultimate Discord Intelligence Bot - Complete Social Media Analysis & Fact-Checking System'
spec = importlib.util.spec_from_file_location(
    'ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system',
    pkg_path / '__init__.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.modules['ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system'] = module

# Stub heavy external dependencies for tests
import types

sys.modules.setdefault('whisper', types.SimpleNamespace(load_model=lambda *a, **k: None))
sys.modules.setdefault('googleapiclient.discovery', types.SimpleNamespace(build=lambda *a, **k: None))
sys.modules.setdefault('googleapiclient.http', types.SimpleNamespace(MediaFileUpload=object))
sys.modules.setdefault('google.oauth2.service_account', types.SimpleNamespace(Credentials=types.SimpleNamespace(from_service_account_file=lambda *a, **k: None)))
sys.modules.setdefault('instagrapi', types.SimpleNamespace(Client=object))
sys.modules.setdefault('pyktok', types.SimpleNamespace(specify_browser=lambda *a, **k: None, save_tiktok=lambda *a, **k: None))
sys.modules.setdefault('crewai_tools', types.SimpleNamespace(BaseTool=object))

# Stub heavy external dependencies for tests
import types

sys.modules.setdefault('whisper', types.SimpleNamespace(load_model=lambda *a, **k: None))
sys.modules.setdefault('googleapiclient.discovery', types.SimpleNamespace(build=lambda *a, **k: None))
sys.modules.setdefault('googleapiclient.http', types.SimpleNamespace(MediaFileUpload=object))
sys.modules.setdefault('google.oauth2.service_account', types.SimpleNamespace(Credentials=types.SimpleNamespace(from_service_account_file=lambda *a, **k: None)))
sys.modules.setdefault('instagrapi', types.SimpleNamespace(Client=object))
sys.modules.setdefault('pyktok', types.SimpleNamespace(specify_browser=lambda *a, **k: None, save_tiktok=lambda *a, **k: None))
