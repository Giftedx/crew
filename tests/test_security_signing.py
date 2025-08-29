import time

from security import signing
from security.signing import (
    build_signature_headers,
    sign_message,
    verify_signature,
    verify_signature_headers,
)


def test_sign_and_verify():
    secret = "s3cr3t"
    payload = b"payload"
    ts = int(time.time())
    nonce = "abc"
    sig = sign_message(payload, secret, ts, nonce)
    assert verify_signature(payload, secret, sig, ts, nonce)


def test_replay_and_tamper():
    secret = "s3cr3t"
    payload = b"data"
    ts = int(time.time())
    nonce = "n1"
    sig = sign_message(payload, secret, ts, nonce)
    assert verify_signature(payload, secret, sig, ts, nonce)
    assert not verify_signature(payload, secret, sig, ts, nonce)
    ts2 = int(time.time())
    nonce2 = "n2"
    sig2 = sign_message(payload, secret, ts2, nonce2)
    assert not verify_signature(b"other", secret, sig2, ts2, nonce2)
    old_ts = ts2 - 1000
    sig3 = sign_message(payload, secret, old_ts, "n3")
    assert not verify_signature(payload, secret, sig3, old_ts, "n3", tolerance=10)


def test_header_helpers():
    secret = "s3cr3t"
    payload = b"data"
    headers = build_signature_headers(payload, secret)
    assert verify_signature_headers(payload, secret, headers)
    # missing header -> fail
    bad = headers.copy()
    bad.pop("X-Signature")
    assert not verify_signature_headers(payload, secret, bad)


def test_nonce_cache_bounded(monkeypatch):
    secret = "s3cr3t"
    payload = b"x"
    signing._seen_nonces.clear()
    monkeypatch.setattr(signing, "MAX_NONCES", 3)
    base_ts = int(time.time())
    for i in range(5):
        nonce = f"n{i}"
        sig = sign_message(payload, secret, base_ts + i, nonce)
        assert verify_signature(payload, secret, sig, base_ts + i, nonce)
    assert len(signing._seen_nonces) <= 3
