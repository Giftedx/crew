import sys
import types

import pytest

from obs.enhanced_monitoring import EnhancedMonitoringSystem
from ultimate_discord_intelligence_bot.step_result import StepResult


class _FakeRouter:
    def __init__(self, initial_items: int = 0):
        self.trajectory_feedback_queue = [object()] * int(initial_items)

    def process_trajectory_feedback(self, batch_size: int = 10):
        take = min(batch_size, len(self.trajectory_feedback_queue))
        # Drain
        self.trajectory_feedback_queue = self.trajectory_feedback_queue[take:]
        return StepResult.ok(processed=take, failed=0, remaining_queue_size=len(self.trajectory_feedback_queue))


def _install_registry_stub(router: _FakeRouter) -> None:
    """Install a stubbed rl_router_registry module to avoid importing heavy deps."""
    pkg_name = "ultimate_discord_intelligence_bot.services"
    mod_name = pkg_name + ".rl_router_registry"

    # Create parent package stub if missing
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = []  # mark as package
        sys.modules[pkg_name] = pkg

    # Install/replace the registry module stub
    stub = types.ModuleType(mod_name)
    # store router on module for closure-free access
    stub._router = router  # type: ignore[attr-defined]

    def get_rl_model_router(create_if_missing: bool = False):
        return getattr(stub, "_router", None)

    def set_rl_model_router(new_router):
        stub._router = new_router  # type: ignore[attr-defined]

    stub.get_rl_model_router = get_rl_model_router  # type: ignore[attr-defined]
    stub.set_rl_model_router = set_rl_model_router  # type: ignore[attr-defined]
    sys.modules[mod_name] = stub


@pytest.fixture(autouse=True)
def _cleanup_registry_modules():
    # Ensure clean import state between tests
    yield
    for name in list(sys.modules.keys()):
        if name.startswith("ultimate_discord_intelligence_bot.services.rl_router_registry"):
            sys.modules.pop(name, None)


def test_process_once_flag_disabled(monkeypatch):
    # Ensure flag is off
    monkeypatch.setenv("ENABLE_TRAJECTORY_FEEDBACK_LOOP", "0")

    # Register a router with items to ensure it would have work (but flag disables it)
    router = _FakeRouter(initial_items=3)
    _install_registry_stub(router)

    ems = EnhancedMonitoringSystem()
    summary = ems.process_rl_feedback_once()

    assert summary["processed"] == 0
    assert summary["failed"] == 0
    # Queue should remain untouched when disabled
    assert summary["queue_depth"] == 3
    assert len(router.trajectory_feedback_queue) == 3


def test_process_once_happy_path(monkeypatch):
    # Enable feedback loop
    monkeypatch.setenv("ENABLE_TRAJECTORY_FEEDBACK_LOOP", "1")

    # Router with 5 items, batch size is 25 in the helper so all should drain
    router = _FakeRouter(initial_items=5)
    _install_registry_stub(router)

    ems = EnhancedMonitoringSystem()
    summary = ems.process_rl_feedback_once()

    assert summary["processed"] == 5
    assert summary["failed"] == 0
    assert summary["queue_depth"] == 0
    assert len(router.trajectory_feedback_queue) == 0
