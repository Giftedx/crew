from __future__ import annotations

from core.settings import get_settings


def _reset_cache():
    # Reset the lru_cache for get_settings between tests
    get_settings.cache_clear()  # type: ignore[attr-defined]


def test_env_overlay_basic_override(monkeypatch):
    monkeypatch.setenv("SERVICE_NAME", "prod-service")
    _reset_cache()
    s = get_settings()
    assert s.service_name == "prod-service"


def test_env_overlay_bool_flag(monkeypatch):
    monkeypatch.setenv("ENABLE_API", "true")
    _reset_cache()
    s = get_settings()
    assert s.enable_api is True


def test_env_overlay_int_and_float(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_RPS", "25")
    monkeypatch.setenv("REWARD_COST_WEIGHT", "0.9")  # float
    _reset_cache()
    s = get_settings()
    assert s.rate_limit_rps == 25
    assert abs(s.reward_cost_weight - 0.9) < 1e-9


def test_env_overlay_disable(monkeypatch):
    monkeypatch.setenv("SERVICE_NAME", "will-not-apply")
    monkeypatch.setenv("DISABLE_SETTINGS_ENV_OVERLAY", "1")
    _reset_cache()
    s = get_settings()
    assert s.service_name != "will-not-apply"  # overlay disabled


def test_env_overlay_unrecognized_does_not_add(monkeypatch):
    monkeypatch.setenv("SOME_UNKNOWN_SETTING", "value")
    _reset_cache()
    s = get_settings()
    assert not hasattr(s, "some_unknown_setting")
