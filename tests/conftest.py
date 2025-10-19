from __future__ import annotations

import importlib
import importlib.util as _ilu
import os
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

# Ensure developer .env does not leak into tests; disable dotenv loading globally
os.environ.setdefault("CREW_DISABLE_DOTENV", "1")


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
    # Skip root-level heavy/integration tests by default to avoid hangs.
    # These files often exercise end-to-end workflows (Discord, yt-dlp, network),
    # which are not suitable for the fast unit test sweep. Enable with FULL_STACK_TEST=1.
    try:
        repo_root = Path(__file__).resolve().parents[1]
        # collection_path can be a string-like; normalize to Path
        p = Path(str(collection_path))
        if (
            os.getenv("FULL_STACK_TEST") != "1"
            and p.parent == repo_root
            and p.name.startswith("test_")
            and p.suffix == ".py"
        ):
            return True
    except Exception:
        # Be conservative: if any error arises determining the path, do not skip
        # collection (avoids false positives masking issues).
        pass
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

    # Default to disabling Settings() env overlay to keep most tests deterministic,
    # but allow specific modules to re-enable it (see pytest_runtest_setup).
    os.environ.setdefault("DISABLE_SETTINGS_ENV_OVERLAY", "1")
    # Default to disabling transcript memory writes so E2E expects a single
    # memory.run call. Specific tests can re-enable by unsetting this env.
    os.environ.setdefault("DISABLE_TRANSCRIPT_MEMORY", "1")
    for key in [
        "RETRY_MAX_ATTEMPTS",  # affects http retry precedence tests
        "OPENROUTER_REFERER",  # affects header assertions
        "OPENROUTER_TITLE",
        "ARCHIVE_API_TOKEN",  # secrets baseline should be None
        "DISCORD_BOT_TOKEN",
        "ENABLE_INGEST_STRICT",  # avoid strict-mode failures unless test enables it
        "ENABLE_RL_GLOBAL",  # keep RL disabled unless test enables it
        "ENABLE_RL_ROUTING",
    ]:
        os.environ.pop(key, None)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):  # noqa: D401
    """Clear lightweight guard when test explicitly requests fullstack.

    If a test is marked with @pytest.mark.fullstack we remove the
    LIGHTWEIGHT_IMPORT flag prior to its import/fixture setup so module level
    imports behave as in production.
    """
    if item.get_closest_marker("fullstack") is not None:
        os.environ.pop("LIGHTWEIGHT_IMPORT", None)
    # Re-enable settings env overlay for the overlay-specific test module
    try:
        modname = getattr(getattr(item, "module", None), "__name__", "")
        if modname.endswith("test_settings_env_overlay"):
            os.environ.pop("DISABLE_SETTINGS_ENV_OVERLAY", None)
        # Re-enable transcript memory for the pipeline unit tests that
        # assert two memory writes (transcript + analysis).
        if modname.endswith("test_pipeline"):
            os.environ.pop("DISABLE_TRANSCRIPT_MEMORY", None)
    except Exception:
        pass


# Shared async fixtures for testing
@pytest.fixture
async def async_test_helper():
    """Provide async test helper utilities."""
    from tests.utils import AsyncTestHelper

    return AsyncTestHelper()


@pytest.fixture
def mock_builder():
    """Provide mock builder utilities."""
    from tests.utils import MockBuilder

    return MockBuilder()


@pytest.fixture
def test_data_generator():
    """Provide test data generator utilities."""
    from tests.utils import TestDataGenerator

    return TestDataGenerator()


@pytest.fixture
def performance_helper():
    """Provide performance testing utilities."""
    from tests.utils import PerformanceTestHelper

    return PerformanceTestHelper()


@pytest.fixture
def assertion_helper():
    """Provide custom assertion utilities."""
    from tests.utils import TestAssertionHelper

    return TestAssertionHelper()


@pytest.fixture
def sample_tenants():
    """Provide sample tenant data for testing."""
    return [
        {"tenant": "tenant_a", "workspace": "workspace_a"},
        {"tenant": "tenant_b", "workspace": "workspace_b"},
        {"tenant": "tenant_c", "workspace": "workspace_c"},
    ]


@pytest.fixture
def sample_urls():
    """Provide sample URLs for testing."""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.twitch.tv/videos/123456789",
        "https://www.tiktok.com/@user/video/123456789",
        "https://www.reddit.com/r/technology/comments/abc123",
        "https://www.linkedin.com/posts/activity-123456789",
    ]


@pytest.fixture
async def mock_vector_store():
    """Provide a mock vector store for testing."""
    mock_store = Mock()
    mock_store.store = AsyncMock(return_value={"success": True, "data": {"stored": True}})
    mock_store.retrieve = AsyncMock(return_value={"success": True, "data": {"content": "retrieved"}})
    mock_store.search = AsyncMock(return_value={"success": True, "data": {"results": []}})
    return mock_store


@pytest.fixture
async def mock_memory_service():
    """Provide a mock memory service for testing."""
    mock_service = Mock()
    mock_service.store_content = AsyncMock(return_value={"success": True, "data": {"stored": True}})
    mock_service.retrieve_content = AsyncMock(return_value={"success": True, "data": {"content": "retrieved"}})
    mock_service.search_content = AsyncMock(return_value={"success": True, "data": {"results": []}})
    return mock_service


@pytest.fixture
async def mock_llm_client():
    """Provide a mock LLM client for testing."""
    mock_client = Mock()
    mock_client.generate = AsyncMock(return_value={"success": True, "data": {"text": "Generated response"}})
    mock_client.embed = AsyncMock(return_value={"success": True, "data": {"embeddings": [0.1, 0.2, 0.3]}})
    return mock_client


@pytest.fixture
async def mock_discord_bot():
    """Provide a mock Discord bot for testing."""
    mock_bot = Mock()
    mock_bot.send_message = AsyncMock(return_value={"success": True, "data": {"sent": True}})
    mock_bot.get_channel = AsyncMock(return_value=Mock())
    mock_bot.get_user = AsyncMock(return_value=Mock())
    return mock_bot


@pytest.fixture
def mock_redis_client():
    """Provide a mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    mock_redis.delete = Mock(return_value=1)
    mock_redis.exists = Mock(return_value=False)
    return mock_redis


@pytest.fixture
def mock_database():
    """Provide a mock database for testing."""
    mock_db = Mock()
    mock_db.execute = Mock(return_value=[])
    mock_db.fetchall = Mock(return_value=[])
    mock_db.fetchone = Mock(return_value=None)
    return mock_db


@pytest.fixture
def mock_file_system():
    """Provide a mock file system for testing."""
    mock_fs = Mock()
    mock_fs.read_file = Mock(return_value="")
    mock_fs.write_file = Mock(return_value=True)
    mock_fs.file_exists = Mock(return_value=False)
    return mock_fs


@pytest.fixture
def mock_http_client():
    """Provide a mock HTTP client for testing."""
    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=Mock(status_code=200, json=lambda: {"success": True}))
    mock_client.post = AsyncMock(return_value=Mock(status_code=201, json=lambda: {"created": True}))
    mock_client.put = AsyncMock(return_value=Mock(status_code=200, json=lambda: {"updated": True}))
    mock_client.delete = AsyncMock(return_value=Mock(status_code=204, json=lambda: {"deleted": True}))
    return mock_client


@pytest.fixture
def mock_rate_limiter():
    """Provide a mock rate limiter for testing."""
    mock_limiter = Mock()
    mock_limiter.check_rate_limit = AsyncMock(return_value={"success": True, "data": {"allowed": True}})
    mock_limiter.get_remaining_requests = Mock(return_value=100)
    mock_limiter.reset_rate_limit = AsyncMock(return_value={"success": True})
    return mock_limiter


@pytest.fixture
def mock_audit_logger():
    """Provide a mock audit logger for testing."""
    mock_logger = Mock()
    mock_logger.log_operation = AsyncMock(return_value={"success": True, "data": {"logged": True}})
    mock_logger.log_authentication = AsyncMock(return_value={"success": True, "data": {"logged": True}})
    mock_logger.log_data_access = AsyncMock(return_value={"success": True, "data": {"logged": True}})
    mock_logger.log_data_modification = AsyncMock(return_value={"success": True, "data": {"logged": True}})
    mock_logger.log_admin_action = AsyncMock(return_value={"success": True, "data": {"logged": True}})
    return mock_logger


@pytest.fixture
def mock_pii_detector():
    """Provide a mock PII detector for testing."""
    mock_detector = Mock()
    mock_detector.detect_emails = Mock(return_value=[])
    mock_detector.detect_phones = Mock(return_value=[])
    mock_detector.detect_ssns = Mock(return_value=[])
    mock_detector.detect_credit_cards = Mock(return_value=[])
    mock_detector.detect_addresses = Mock(return_value=[])
    mock_detector.detect_names = Mock(return_value=[])
    mock_detector.detect_ip_addresses = Mock(return_value=[])
    mock_detector.detect_urls = Mock(return_value=[])
    mock_detector.redact_pii = Mock(return_value="Redacted text")
    mock_detector.detect_all_pii = Mock(return_value={"emails": [], "phones": [], "ssns": []})
    return mock_detector


# StepResult factory fixtures
@pytest.fixture
def stepresult_factory():
    """Provide StepResult factory for testing."""
    from tests.factories import StepResultFactory

    return StepResultFactory()


@pytest.fixture
def transcript_factory():
    """Provide Transcript factory for testing."""
    from tests.factories import TranscriptFactory

    return TranscriptFactory()


@pytest.fixture
def analysis_factory():
    """Provide Analysis factory for testing."""
    from tests.factories import AnalysisFactory

    return AnalysisFactory()


@pytest.fixture
def mock_factory():
    """Provide Mock factory for testing."""
    from tests.factories import MockFactory

    return MockFactory()


@pytest.fixture
def test_data_factory():
    """Provide TestData factory for testing."""
    from tests.factories import TestDataFactory

    return TestDataFactory()
