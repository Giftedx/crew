from datetime import UTC, datetime

from ultimate_discord_intelligence_bot.core.time import default_utc_now, ensure_utc


def test_default_utc_now_is_timezone_aware_utc():
    now = default_utc_now()
    assert isinstance(now, datetime)
    assert now.tzinfo is not None
    assert now.tzinfo == UTC


def test_ensure_utc_attaches_utc_to_naive():
    naive = datetime(2025, 1, 2, 3, 4, 5)  # naive
    fixed = ensure_utc(naive)
    assert fixed.tzinfo == UTC
    # semantics: same wall time with attached tzinfo
    assert fixed.year == naive.year and fixed.hour == naive.hour


def test_ensure_utc_preserves_aware():
    aware = datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)
    roundtrip = ensure_utc(aware)
    assert roundtrip is aware or roundtrip == aware
