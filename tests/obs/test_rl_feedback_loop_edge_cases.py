import sys
import types

import pytest

from ultimate_discord_intelligence_bot.obs.enhanced_monitoring import EnhancedMonitoringSystem


class _NoRouterModule(types.ModuleType):
    def get_rl_model_router(self, create_if_missing: bool = False):
        return None


@pytest.fixture(autouse=True)
def _cleanup_registry_modules():
    yield
    for name in list(sys.modules.keys()):
        if name.startswith("ultimate_discord_intelligence_bot.services.rl_router_registry"):
            sys.modules.pop(name, None)


def test_flag_enabled_but_no_router(monkeypatch):
    monkeypatch.setenv("ENABLE_TRAJECTORY_FEEDBACK_LOOP", "1")
    mod_name = "ultimate_discord_intelligence_bot.services.rl_router_registry"
    sys.modules[mod_name] = _NoRouterModule(mod_name)
    ems = EnhancedMonitoringSystem()
    summary = ems.process_rl_feedback_once()
    assert summary["processed"] == 0
    assert summary["failed"] == 0
    assert summary["queue_depth"] == 0


def test_registry_import_failure(monkeypatch):
    monkeypatch.setenv("ENABLE_TRAJECTORY_FEEDBACK_LOOP", "1")

    class _FailImporter(types.ModuleType):
        def __getattr__(self, name):
            raise ImportError("boom")

    mod_name = "ultimate_discord_intelligence_bot.services"
    pkg = types.ModuleType(mod_name)
    pkg.__path__ = []
    sys.modules[mod_name] = pkg

    def _find_spec(*_a, **_k):
        raise ImportError("boom")

    pkg.__getattr__ = lambda *_a, **_k: (_ for _ in ()).throw(ImportError("boom"))
    ems = EnhancedMonitoringSystem()
    summary = ems.process_rl_feedback_once()
    assert summary["processed"] == 0
    assert summary["failed"] == 0
    assert summary["queue_depth"] == 0
