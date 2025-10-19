import os
from pathlib import Path

# Ensure .env is only loaded once so tests that delete env vars can observe the
# absence on subsequent reloads (importlib.reload). Without this, load_dotenv()
# would re-populate deleted variables, preventing override-clearing tests.
_DOTENV_LOADED = globals().get("_DOTENV_LOADED", False)
_DISABLE_DOTENV = os.getenv("CREW_DISABLE_DOTENV") == "1" or (
    os.getenv("PYTEST_CURRENT_TEST") is not None
)
if not _DOTENV_LOADED and not _DISABLE_DOTENV:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass  # dotenv is optional
    _DOTENV_LOADED = True

# In CI/tests where a committed .env may exist, honor the sentinel to prevent reloading on module reloads.
globals()["_DOTENV_LOADED"] = _DOTENV_LOADED

REPO_ROOT = Path(__file__).resolve().parents[2]


# Lazy-loaded configuration to avoid circular imports
def _get_config():
    try:
        from core.secure_config import (
            get_config,  # noqa: E402, PLC0415 - intentional lazy import to avoid cycles
        )

        return get_config()
    except ImportError:
        return None


_ENABLE_SECURE_PATH_FALLBACK = os.getenv("CREW_ENABLE_SECURE_PATH_FALLBACK") == "1"


def _get_path_setting(key: str, default_path: Path) -> Path:
    """Get path setting preferring environment variable, then secure config.

    Tests and CLI expect that explicit environment variables take precedence
    over values that may be provided by the secure configuration layer. This
    function therefore checks the environment first, then consults secure
    config, finally falling back to the provided default.
    """
    # Highest priority: direct environment variable override
    env_value = os.getenv(key.upper())
    if env_value:
        return Path(env_value).expanduser()

    # Next: optional secure config (only if explicitly enabled to avoid sticky defaults in tests)
    if _ENABLE_SECURE_PATH_FALLBACK:
        config = _get_config()
        if config:
            value = config.get_setting(key, None)
            if value:
                return Path(value).expanduser()

    # Default
    return default_path.expanduser()


def _get_setting(key: str, default: str = "") -> str:
    """Get string setting preferring environment variable, then secure config.

    Tests rely on environment taking precedence over any secure-config defaults.
    """
    # Highest priority: environment variable
    env_val = os.getenv(key.upper())
    if env_val is not None:
        return env_val
    # Fallback: optional secure config
    config = _get_config()
    if config:
        return config.get_setting(key, default)
    return default


# Base directories (computed lazily)
BASE_DIR = _get_path_setting("crewai_base_dir", Path.home() / "crew_data")
DOWNLOADS_DIR = _get_path_setting("crewai_downloads_dir", BASE_DIR / "Downloads")
CONFIG_DIR = _get_path_setting("crewai_config_dir", BASE_DIR / "Config")
LOGS_DIR = _get_path_setting("crewai_logs_dir", BASE_DIR / "Logs")
PROCESSING_DIR = _get_path_setting("crewai_processing_dir", BASE_DIR / "Processing")

# yt-dlp paths
YTDLP_DIR = _get_path_setting("crewai_ytdlp_dir", REPO_ROOT / "yt-dlp")
YTDLP_CONFIG = _get_path_setting(
    "crewai_ytdlp_config", YTDLP_DIR / "config" / "crewai-system.conf"
)
YTDLP_ARCHIVE = _get_path_setting(
    "crewai_ytdlp_archive", YTDLP_DIR / "archives" / "crewai_downloads.txt"
)
TEMP_DIR = _get_path_setting("crewai_temp_dir", DOWNLOADS_DIR / "temp")

GOOGLE_CREDENTIALS = _get_path_setting(
    "google_credentials", CONFIG_DIR / "google-credentials.json"
)
DISCORD_WEBHOOK = _get_setting("discord_webhook")
DISCORD_PRIVATE_WEBHOOK = _get_setting("discord_private_webhook")

# Vector database settings
# Precedence (highest first):
#   1. Explicit environment variable (QDRANT_URL / QDRANT_API_KEY)
#   2. Optional secure config (when CREW_ENABLE_SECURE_QDRANT_FALLBACK=1)
#   3. Empty string default
# Tests rely on being able to clear the env var and get an empty string, so the
# fallback is gated by an opt-in flag and thus inert during tests unless set.
_qdrant_env_url = os.getenv("QDRANT_URL", "")
_qdrant_env_key = os.getenv("QDRANT_API_KEY", "")
_enable_secure_qdrant_fallback = os.getenv("CREW_ENABLE_SECURE_QDRANT_FALLBACK") == "1"
_test_secure_qdrant_url = os.getenv("CREW_QDRANT_SECURE_TEST_URL")  # test seam
if _qdrant_env_url:
    QDRANT_URL = _qdrant_env_url
elif _enable_secure_qdrant_fallback:
    # Allow tests to inject a deterministic secure-config URL without patching internals.
    if _test_secure_qdrant_url:
        QDRANT_URL = _test_secure_qdrant_url
    else:
        _cfg = _get_config()
        QDRANT_URL = _cfg.qdrant_url if _cfg else ""
else:
    QDRANT_URL = ""

if _qdrant_env_key:
    QDRANT_API_KEY = _qdrant_env_key
elif _enable_secure_qdrant_fallback:
    _cfg = _get_config()
    QDRANT_API_KEY = _cfg.qdrant_api_key if _cfg and _cfg.qdrant_api_key else ""
else:
    QDRANT_API_KEY = ""

# Ensure directories exist
for path in [
    DOWNLOADS_DIR,
    CONFIG_DIR,
    LOGS_DIR,
    PROCESSING_DIR,
    TEMP_DIR,
    YTDLP_ARCHIVE.parent,
]:
    path.mkdir(parents=True, exist_ok=True)


# ========================================
# PHASE 1 ENHANCEMENT FLAGS
# ========================================

ENABLE_MEM0_MEMORY = str(_get_setting("ENABLE_MEM0_MEMORY", "false")).lower() in (
    "true",
    "1",
    "yes",
)
ENABLE_DSPY_OPTIMIZATION = str(
    _get_setting("ENABLE_DSPY_OPTIMIZATION", "false")
).lower() in ("true", "1", "yes")

# Configuration for DSPy (placeholders)
DSPY_OPTIMIZATION_LEVEL = _get_setting("DSPY_OPTIMIZATION_LEVEL", "medium")

# LangGraph pipeline flag (sqlite checkpointer with memory fallback in code)
ENABLE_LANGGRAPH_PIPELINE = str(
    _get_setting("ENABLE_LANGGRAPH_PIPELINE", "false")
).lower() in ("true", "1", "yes")

# ========================================
# PHASE 2 ENHANCEMENT FLAGS
# ========================================

ENABLE_HIERARCHICAL_ORCHESTRATION = str(
    _get_setting("ENABLE_HIERARCHICAL_ORCHESTRATION", "false")
).lower() in ("true", "1", "yes")

ENABLE_RL_MODEL_ROUTING = str(
    _get_setting("ENABLE_RL_MODEL_ROUTING", "false")
).lower() in ("true", "1", "yes")

ENABLE_WEBSOCKET_UPDATES = str(
    _get_setting("ENABLE_WEBSOCKET_UPDATES", "false")
).lower() in ("true", "1", "yes")

ENABLE_ENTERPRISE_TENANT_MANAGEMENT = str(
    _get_setting("ENABLE_ENTERPRISE_TENANT_MANAGEMENT", "false")
).lower() in ("true", "1", "yes")

# ========================================
# UNIFIED KNOWLEDGE LAYER FLAGS
# ========================================

ENABLE_UNIFIED_KNOWLEDGE = str(
    _get_setting("ENABLE_UNIFIED_KNOWLEDGE", "false")
).lower() in ("true", "1", "yes")

ENABLE_UNIFIED_CACHE = str(_get_setting("ENABLE_UNIFIED_CACHE", "false")).lower() in (
    "true",
    "1",
    "yes",
)

ENABLE_UNIFIED_ROUTER = str(_get_setting("ENABLE_UNIFIED_ROUTER", "false")).lower() in (
    "true",
    "1",
    "yes",
)

ENABLE_UNIFIED_ORCHESTRATION = str(
    _get_setting("ENABLE_UNIFIED_ORCHESTRATION", "false")
).lower() in ("true", "1", "yes")

# ========================================
# UNIFIED ROUTER SYSTEM FLAGS
# ========================================

ENABLE_UNIFIED_COST_TRACKING = str(
    _get_setting("ENABLE_UNIFIED_COST_TRACKING", "false")
).lower() in (
    "true",
    "1",
    "yes",
)

# ========================================
# UNIFIED CACHE SYSTEM FLAGS
# ========================================

ENABLE_UNIFIED_CACHE = str(_get_setting("ENABLE_UNIFIED_CACHE", "false")).lower() in (
    "true",
    "1",
    "yes",
)

ENABLE_CACHE_OPTIMIZATION = str(
    _get_setting("ENABLE_CACHE_OPTIMIZATION", "false")
).lower() in (
    "true",
    "1",
    "yes",
)

# ========================================
# UNIFIED ORCHESTRATION SYSTEM FLAGS
# ========================================

ENABLE_UNIFIED_ORCHESTRATION = str(
    _get_setting("ENABLE_UNIFIED_ORCHESTRATION", "false")
).lower() in (
    "true",
    "1",
    "yes",
)

ENABLE_TASK_MANAGEMENT = str(
    _get_setting("ENABLE_TASK_MANAGEMENT", "false")
).lower() in (
    "true",
    "1",
    "yes",
)

# ========================================
# AGENT BRIDGE SYSTEM FLAGS
# ========================================

ENABLE_AGENT_BRIDGE = str(_get_setting("ENABLE_AGENT_BRIDGE", "false")).lower() in (
    "true",
    "1",
    "yes",
)

ENABLE_KNOWLEDGE_SHARING = str(
    _get_setting("ENABLE_KNOWLEDGE_SHARING", "false")
).lower() in (
    "true",
    "1",
    "yes",
)

ENABLE_CROSS_AGENT_LEARNING = str(
    _get_setting("ENABLE_CROSS_AGENT_LEARNING", "false")
).lower() in (
    "true",
    "1",
    "yes",
)

ENABLE_COLLECTIVE_INTELLIGENCE = str(
    _get_setting("ENABLE_COLLECTIVE_INTELLIGENCE", "false")
).lower() in (
    "true",
    "1",
    "yes",
)

# ========================================
# OBSERVABILITY SYSTEM FLAGS
# ========================================

ENABLE_UNIFIED_METRICS = str(
    _get_setting("ENABLE_UNIFIED_METRICS", "false")
).lower() in (
    "true",
    "1",
    "yes",
)

ENABLE_INTELLIGENT_ALERTING = str(
    _get_setting("ENABLE_INTELLIGENT_ALERTING", "false")
).lower() in (
    "true",
    "1",
    "yes",
)

ENABLE_DASHBOARD_INTEGRATION = str(
    _get_setting("ENABLE_DASHBOARD_INTEGRATION", "false")
).lower() in (
    "true",
    "1",
    "yes",
)
