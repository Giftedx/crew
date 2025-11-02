from datetime import UTC, datetime, timedelta
from platform.security.secret_rotation import list_entries, promote, register, verify_ref


def test_verify_ref_accepts_current_and_previous_within_grace():
    register("webhook", "WEBHOOK:v1", activated_at=datetime.now(UTC) - timedelta(hours=1))
    promote("webhook", "WEBHOOK:v2")
    assert verify_ref("webhook", "WEBHOOK:v2") is True
    assert verify_ref("webhook", "WEBHOOK:v1") is True


def test_verify_ref_rejects_previous_after_grace(monkeypatch):
    register("token", "TOKEN:v1", activated_at=datetime.now(UTC) - timedelta(hours=50))
    promote("token", "TOKEN:v2")
    for entry in list_entries():
        if entry.logical == "token":
            entry.activated_at = datetime.now(UTC) - timedelta(hours=50)
    assert verify_ref("token", "TOKEN:v1") is False
    assert verify_ref("token", "TOKEN:v2") is True
