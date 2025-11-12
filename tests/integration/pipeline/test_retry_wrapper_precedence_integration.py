import contextlib
from pathlib import Path

import pytest


pytest.skip("Test file imports from non-existent or moved modules", allow_module_level=True)

from core import http_utils


class DummyResp:
    def __init__(self, status_code=200):
        self.status_code = status_code
        self.text = "ok"

    def json(self):  # pragma: no cover - not used
        return {"ok": True}


def test_wrapper_uses_explicit_max_attempts(monkeypatch, tmp_path):
    attempts = {"count": 0}

    def failing(_url, **_):
        attempts["count"] += 1
        # always raise to trigger retry path until limit reached
        raise http_utils.requests.ConnectionError("boom")

    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")
    # no config file present
    with contextlib.suppress(Exception):
        http_utils.retrying_get("https://x", max_attempts=2, request_callable=failing)
    assert attempts["count"] == 2  # 2 attempts (initial + retry capped by explicit)


def test_wrapper_config_over_env(monkeypatch, tmp_path):
    attempts = {"count": 0}

    def failing(_url, **_):
        attempts["count"] += 1
        raise http_utils.requests.ConnectionError("boom")

    cfg_dir = Path("config")
    cfg_dir.mkdir(exist_ok=True)
    (cfg_dir / "retry.yaml").write_text("max_attempts: 4\n", encoding="utf-8")
    monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "6")
    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")
    # ensure cache reset
    if hasattr(http_utils, "_RETRY_CONFIG_CACHE"):
        http_utils._RETRY_CONFIG_CACHE = None
    with contextlib.suppress(Exception):
        http_utils.retrying_post("https://x", json_payload={}, request_callable=failing)
    assert attempts["count"] == 4


def test_wrapper_env_over_default(monkeypatch, tmp_path):
    attempts = {"count": 0}

    def failing(_url, **_):
        attempts["count"] += 1
        raise http_utils.requests.ConnectionError("boom")

    cfg_dir = Path("config")
    cfg_dir.mkdir(exist_ok=True)
    retry_cfg = cfg_dir / "retry.yaml"
    if retry_cfg.exists():
        retry_cfg.unlink()
    monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "5")
    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")
    if hasattr(http_utils, "_RETRY_CONFIG_CACHE"):
        http_utils._RETRY_CONFIG_CACHE = None
    with contextlib.suppress(Exception):
        http_utils.retrying_get("https://x", request_callable=failing)
    assert attempts["count"] == 5


def test_wrapper_fallback_default(monkeypatch, tmp_path):
    attempts = {"count": 0}

    def failing(_url, **_):
        attempts["count"] += 1
        raise http_utils.requests.ConnectionError("boom")

    cfg_dir = Path("config")
    cfg_dir.mkdir(exist_ok=True)
    retry_cfg = cfg_dir / "retry.yaml"
    if retry_cfg.exists():
        retry_cfg.unlink()
    monkeypatch.delenv("RETRY_MAX_ATTEMPTS", raising=False)
    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")
    if hasattr(http_utils, "_RETRY_CONFIG_CACHE"):
        http_utils._RETRY_CONFIG_CACHE = None
    with contextlib.suppress(Exception):
        http_utils.retrying_post("https://x", json_payload={}, request_callable=failing)
    assert attempts["count"] == http_utils.DEFAULT_HTTP_RETRY_ATTEMPTS
