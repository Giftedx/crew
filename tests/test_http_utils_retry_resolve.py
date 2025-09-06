from __future__ import annotations

from types import SimpleNamespace

from core import http_utils as hu


def test_resolve_retry_attempts_explicit_wins(monkeypatch):
    # Even with config/env present, explicit call_arg is highest precedence
    monkeypatch.setattr(hu, "_load_retry_config", lambda: {"max_attempts": 5})
    monkeypatch.setattr(hu, "_config", SimpleNamespace(retry_max_attempts=4))
    assert hu.resolve_retry_attempts(call_arg=7) == 7


def test_resolve_retry_attempts_config_over_env(monkeypatch):
    # Config file value takes precedence over env when call_arg is None
    monkeypatch.setattr(hu, "_load_retry_config", lambda: {"max_attempts": 6})
    monkeypatch.setattr(hu, "_config", SimpleNamespace(retry_max_attempts=4))
    assert hu.resolve_retry_attempts(call_arg=None) == 6


def test_resolve_retry_attempts_env_over_default(monkeypatch):
    # When config has no value, env-driven (secure config) value is used
    monkeypatch.setattr(hu, "_load_retry_config", lambda: {"max_attempts": None})
    monkeypatch.setattr(hu, "_config", SimpleNamespace(retry_max_attempts=4))
    assert hu.resolve_retry_attempts(call_arg=None) == 4


def test_resolve_retry_attempts_default(monkeypatch):
    # Fallback to library default when no other source provides a valid value
    monkeypatch.setattr(hu, "_load_retry_config", lambda: {"max_attempts": None})
    monkeypatch.setattr(hu, "_config", None)
    assert hu.resolve_retry_attempts(call_arg=None) == hu.DEFAULT_HTTP_RETRY_ATTEMPTS


def test_resolve_retry_attempts_sanitizes_out_of_range(monkeypatch):
    # Out-of-range explicit value should be ignored and next source used
    monkeypatch.setattr(hu, "_load_retry_config", lambda: {"max_attempts": 8})
    monkeypatch.setattr(hu, "_config", SimpleNamespace(retry_max_attempts=2))
    assert hu.resolve_retry_attempts(call_arg=999) == 8

