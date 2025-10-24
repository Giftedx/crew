from datetime import datetime, timedelta, UTC  # noqa: I001

from src.security.secret_rotation import (
    register,
    promote,
    retire_previous,
    get_current,
    get_previous,
    previous_available,
    validate_grace,
)


def test_register_and_promote():
    register("api_key", "API_KEY:v1", activated_at=datetime.now(UTC) - timedelta(hours=2))
    assert get_current("api_key") == "API_KEY:v1"
    assert get_previous("api_key") is None
    promote("api_key", "API_KEY:v2")
    assert get_current("api_key") == "API_KEY:v2"
    assert get_previous("api_key") == "API_KEY:v1"


def test_previous_available_and_retire_blocked():
    register("svc", "SVC:v1")
    promote("svc", "SVC:v2")
    # Immediately after promote, previous should be within grace (default 24h)
    assert previous_available("svc") is True
    # Attempt retire before grace -> blocked
    assert retire_previous("svc") is False
    # Force ignore grace
    assert retire_previous("svc", ignore_grace=True) is True
    assert get_previous("svc") is None


def test_validate_grace_violation():
    # simulate old activation so grace elapsed
    past = datetime.now(UTC) - timedelta(hours=30)
    register("rotate_me", "ROTATE:v1", activated_at=past)
    promote("rotate_me", "ROTATE:v2")
    # move activation further in past for previous (already set above)
    # sleep not required; we rely on old timestamp of previous (v1) relative to new activation
    # Fast-forward by adjusting internal registry timestamp for testing
    # (Simplest: directly set entry to older activation before promotion, done above.)
    # Grace should not yet have elapsed for new current, but previous was old.
    assert validate_grace("rotate_me") is True
