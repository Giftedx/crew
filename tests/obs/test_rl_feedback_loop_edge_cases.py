import sys
import types

import pytest

from obs.enhanced_monitoring import EnhancedMonitoringSystem


class _NoRouterModule(types.ModuleType):
    def get_rl_model_router(self, create_if_missing: bool = False):
        return None


@pytest.fixture(autouse=True)
def _cleanup_registry_modules():
    # Ensure clean import state between tests
    yield
    for name in list(sys.modules.keys()):
        if name.startswith("ultimate_discord_intelligence_bot.services.rl_router_registry"):
            sys.modules.pop(name, None)


def test_flag_enabled_but_no_router(monkeypatch):
    # Enable feedback loop
    monkeypatch.setenv("ENABLE_TRAJECTORY_FEEDBACK_LOOP", "1")

    # Install a registry module that returns None
    mod_name = "ultimate_discord_intelligence_bot.services.rl_router_registry"
    sys.modules[mod_name] = _NoRouterModule(mod_name)

    ems = EnhancedMonitoringSystem()
    summary = ems.process_rl_feedback_once()

    assert summary["processed"] == 0
    assert summary["failed"] == 0
    assert summary["queue_depth"] == 0


def test_registry_import_failure(monkeypatch):
    # Enable feedback loop
    monkeypatch.setenv("ENABLE_TRAJECTORY_FEEDBACK_LOOP", "1")

    # Force an import error for the registry module
    class _FailImporter(types.ModuleType):
        def __getattr__(self, name):  # pragma: no cover - defensive
            raise ImportError("boom")

    mod_name = "ultimate_discord_intelligence_bot.services"
    pkg = types.ModuleType(mod_name)
    pkg.__path__ = []
    sys.modules[mod_name] = pkg

    # Ensure that importing submodule raises ImportError at access time
    def _find_spec(*_a, **_k):  # pragma: no cover - guard
        raise ImportError("boom")

    # Simulate that accessing the attribute will raise
    pkg.__getattr__ = lambda *_a, **_k: (_ for _ in ()).throw(ImportError("boom"))  # type: ignore[attr-defined]

    ems = EnhancedMonitoringSystem()
    summary = ems.process_rl_feedback_once()

    assert summary["processed"] == 0
    assert summary["failed"] == 0
    assert summary["queue_depth"] == 0
