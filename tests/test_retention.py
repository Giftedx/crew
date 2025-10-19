from datetime import UTC, datetime, timedelta

from ultimate_discord_intelligence_bot.core.privacy import retention
from ingest import models


def test_retention_sweep(tmp_path):
    db = tmp_path / "r.db"
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
    deleted = retention.sweep(conn, now=datetime.now(UTC))
    assert deleted == 1
