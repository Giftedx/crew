from datetime import UTC
from pathlib import Path

from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry


def test_tenant_created_at_is_utc(tmp_path: Path):
    tdir = tmp_path / "tenants" / "t1"
    tdir.mkdir(parents=True)
    # Write naive ISO timestamp and verify normalization
    (tdir / "tenant.yaml").write_text(
        "id: 1\nname: T1\ncreated_at: 2024-01-01T12:00:00\nworkspaces:\n  main: {}\n",
        encoding="utf-8",
    )
    reg = TenantRegistry(tmp_path / "tenants")
    reg.load()
    cfg = reg.get_tenant("t1")
    assert cfg is not None
    assert cfg.tenant.created_at.tzinfo == UTC
