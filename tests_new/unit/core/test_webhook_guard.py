import time

import pytest

from src.security.signing import build_signature_headers
from src.security.webhook_guard import SecurityError, verify_incoming


SECRET = "TEST_SECRET"


def _headers(body: bytes, secret: str = SECRET, ts: int | None = None, nonce: str | None = None):
    return build_signature_headers(body, secret, timestamp=ts, nonce=nonce)


def test_verify_valid(monkeypatch, tmp_path):
    # Prepare config file with secret
    cfg = tmp_path / "security.yaml"
    cfg.write_text(
        """
webhooks:
  secrets:
    default: TEST_SECRET
  clock_skew_seconds: 300
"""
    )
    body = b"hello"
    hdrs = _headers(body)
    assert verify_incoming(body, hdrs, config_path=cfg)


def test_verify_missing_headers(tmp_path):
    cfg = tmp_path / "security.yaml"
    cfg.write_text(
        """
webhooks:
  secrets:
    default: TEST_SECRET
"""
    )
    body = b"body"
    with pytest.raises(SecurityError):
        verify_incoming(body, {}, config_path=cfg)


def test_verify_bad_timestamp(tmp_path):
    cfg = tmp_path / "security.yaml"
    cfg.write_text(
        """
webhooks:
  secrets:
    default: TEST_SECRET
"""
    )
    body = b"body"
    hdrs = _headers(body)
    hdrs["X-Timestamp"] = "notint"
    with pytest.raises(SecurityError):
        verify_incoming(body, hdrs, config_path=cfg)


def test_verify_skew(tmp_path):
    cfg = tmp_path / "security.yaml"
    cfg.write_text(
        """
webhooks:
  secrets:
    default: TEST_SECRET
  clock_skew_seconds: 5
"""
    )
    body = b"body"
    past = int(time.time()) - 999
    hdrs = _headers(body, ts=past)
    with pytest.raises(SecurityError):
        verify_incoming(body, hdrs, config_path=cfg)


def test_verify_invalid_signature(tmp_path):
    cfg = tmp_path / "security.yaml"
    cfg.write_text(
        """
webhooks:
  secrets:
    default: TEST_SECRET
"""
    )
    body = b"body"
    hdrs = _headers(body)
    # Modify body to invalidate signature
    with pytest.raises(SecurityError):
        verify_incoming(b"tampered", hdrs, config_path=cfg)


def test_verify_replay(tmp_path):
    cfg = tmp_path / "security.yaml"
    cfg.write_text(
        """
webhooks:
  secrets:
    default: TEST_SECRET
"""
    )
    body = b"body"
    ts = int(time.time())
    hdrs = _headers(body, ts=ts, nonce="abc123")
    assert verify_incoming(body, hdrs, config_path=cfg)
    with pytest.raises(SecurityError):  # replay same nonce+timestamp
        verify_incoming(body, hdrs, config_path=cfg)
