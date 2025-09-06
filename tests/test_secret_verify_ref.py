from datetime import UTC, datetime, timedelta

from src.security.secret_rotation import list_entries, promote, register, verify_ref


def test_verify_ref_accepts_current_and_previous_within_grace():
    register("webhook", "WEBHOOK:v1", activated_at=datetime.now(UTC) - timedelta(hours=1))
    promote("webhook", "WEBHOOK:v2")
    assert verify_ref("webhook", "WEBHOOK:v2") is True  # current
    assert verify_ref("webhook", "WEBHOOK:v1") is True  # previous within grace


def test_verify_ref_rejects_previous_after_grace(monkeypatch):
    # Register and promote, then artificially age activation to exceed grace
    register("token", "TOKEN:v1", activated_at=datetime.now(UTC) - timedelta(hours=50))
    promote("token", "TOKEN:v2")
    # Simulate grace elapsed by rewinding activated_at to long ago so previous is older than grace
    # list_entries returns dataclasses; find our entry and backdate activated_at far enough
    for entry in list_entries():
        if entry.logical == "token":
            # previous is v1; set activated_at to now so grace applies to new current only
            entry.activated_at = datetime.now(UTC) - timedelta(hours=50)
    # default grace 24h -> previous should now be expired
    assert verify_ref("token", "TOKEN:v1") is False
    assert verify_ref("token", "TOKEN:v2") is True
