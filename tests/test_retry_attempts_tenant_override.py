from __future__ import annotations

from pathlib import Path

import yaml

from core.http_utils import resolve_retry_attempts
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_tenant_retry_yaml_overrides_global(tmp_path: Path, monkeypatch) -> None:
    # Place tenant retry.yaml with strict attempts
    (tmp_path / "acme").mkdir(parents=True, exist_ok=True)
    (tmp_path / "acme" / "retry.yaml").write_text("max_attempts: 2\n", encoding="utf-8")
    # Place global retry.yaml with higher attempts
    root = Path(__file__).resolve().parents[1]
    global_cfg = root / "config" / "retry.yaml"
    global_cfg.parent.mkdir(parents=True, exist_ok=True)
    global_cfg.write_text("max_attempts: 5\n", encoding="utf-8")

    # Monkeypatch project root resolution to our tmp tenant dir
    # We can't easily patch Path.parents; instead, temporarily symlink tenants dir
    tenants_dir = root / "tenants" / "acme"
    tenants_dir.parent.mkdir(parents=True, exist_ok=True)
    # Write tenant file into real tenants dir for the tested loader
    (tenants_dir / "retry.yaml").write_text("max_attempts: 2\n", encoding="utf-8")

    with with_tenant(TenantContext("acme", "main")):
        assert resolve_retry_attempts() == 2

