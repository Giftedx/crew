from datetime import UTC, datetime, timedelta

from discord import commands
from ingest import models
from policy import policy_engine


def test_ops_privacy_commands(tmp_path):
    events = [{"type": "redaction", "count": 2}, {"type": "block", "count": 1}]
    status = commands.ops_privacy_status(events, policy_version="v1")
    assert status["events"] == {"redaction": 2, "block": 1}
    assert status["policy_version"] == "v1"

    report = {"found": [], "redacted_by_type": {"email": 1}, "decisions": []}
    assert commands.ops_privacy_show(report) == report

    db = tmp_path / "p.db"
    conn = models.connect(str(db))
    old = datetime.now(UTC) - timedelta(days=40)
    conn.execute(
        (
            "INSERT INTO provenance (content_id, source_url, source_type, retrieved_at, license, terms_url, "
            "consent_flags, checksum_sha256, creator_id, episode_id) VALUES (?,?,?,?,?,?,?,?,?,?)"
        ),
        ("1", "u", "yt", old.isoformat(), "", None, None, "x", None, None),
    )
    conn.commit()
    sweep = commands.ops_privacy_sweep(conn, now=datetime.now(UTC))
    assert sweep["deleted"] == 1


def test_policy_override_applied():
    base = policy_engine.load_policy()
    assert "custom" not in base.allowed_sources
    overridden = policy_engine.load_policy("default")
    assert "custom" in overridden.allowed_sources
