"""Tests for retry attempt precedence (production implementation).

Precedence enforced by ``core.http_utils.resolve_retry_attempts``:
  1. Explicit call argument (sanity-checked range)
  2. config/retry.yaml (key: max_attempts)
  3. Environment variable RETRY_MAX_ATTEMPTS
  4. DEFAULT_HTTP_RETRY_ATTEMPTS constant
"""

from pathlib import Path

from core import http_utils


def _reset_retry_config_cache():
    # Clear module-level cache to ensure fresh parse per test
    if hasattr(http_utils, "_RETRY_CONFIG_CACHE"):
        http_utils._RETRY_CONFIG_CACHE = None  # noqa: SLF001 - test reaching into module cache


def test_retry_precedence_call_arg_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "9")
    cfg_dir = Path("config")
    cfg_dir.mkdir(exist_ok=True)
    (cfg_dir / "retry.yaml").write_text("max_attempts: 6\n", encoding="utf-8")
    _reset_retry_config_cache()
    assert http_utils.resolve_retry_attempts(call_arg=2) == 2


def test_retry_precedence_config_over_env(monkeypatch, tmp_path):
    monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "11")
    cfg_dir = Path("config")
    cfg_dir.mkdir(exist_ok=True)
    (cfg_dir / "retry.yaml").write_text("max_attempts: 5\n", encoding="utf-8")
    _reset_retry_config_cache()
    assert http_utils.resolve_retry_attempts() == 5


def test_retry_precedence_env_over_default(monkeypatch, tmp_path):
    cfg_dir = Path("config")
    cfg_dir.mkdir(exist_ok=True)
    retry_cfg = cfg_dir / "retry.yaml"
    if retry_cfg.exists():
        retry_cfg.unlink()
    monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "7")
    _reset_retry_config_cache()
    assert http_utils.resolve_retry_attempts() == 7


def test_retry_precedence_fallback(monkeypatch, tmp_path):
    cfg_dir = Path("config")
    cfg_dir.mkdir(exist_ok=True)
    retry_cfg = cfg_dir / "retry.yaml"
    if retry_cfg.exists():
        retry_cfg.unlink()
    monkeypatch.delenv("RETRY_MAX_ATTEMPTS", raising=False)
    _reset_retry_config_cache()
    assert http_utils.resolve_retry_attempts() == http_utils.DEFAULT_HTTP_RETRY_ATTEMPTS


def test_retry_invalid_sources_fall_back(monkeypatch, tmp_path):
    # Invalid explicit call arg -> look at config
    cfg_dir = Path("config")
    cfg_dir.mkdir(exist_ok=True)
    (cfg_dir / "retry.yaml").write_text("max_attempts: 4\n", encoding="utf-8")
    monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "not-an-int")
    _reset_retry_config_cache()
    assert http_utils.resolve_retry_attempts(call_arg=0) == 4  # 0 invalid, config wins

    # Corrupt config -> env -> fallback
    (cfg_dir / "retry.yaml").write_text("max_attempts: notnum\n", encoding="utf-8")
    monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "25")  # beyond reasonable cap (max 20) -> reject
    _reset_retry_config_cache()
    assert http_utils.resolve_retry_attempts() == http_utils.DEFAULT_HTTP_RETRY_ATTEMPTS
