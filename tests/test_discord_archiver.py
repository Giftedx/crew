import os
from pathlib import Path

from fastapi.testclient import TestClient

from archive.discord_store import api, limits, manifest, policy, router

ROUTES_YAML = (
    "routes:\n"
    "  images:\n"
    "    public:\n"
    "      channel_id: '123'\n"
    "    private:\n"
    "      channel_id: '456'\n"
    "per_tenant_overrides: {}\n"
)


def test_router_basic(tmp_path):
    cfg_path = tmp_path / "routes.yaml"
    cfg_path.write_text(ROUTES_YAML)
    os.environ["ARCHIVE_ROUTES_PATH"] = str(cfg_path)
    import importlib

    importlib.reload(router)
    channel, thread = router.pick_channel("foo.png", visibility="public")
    assert channel == "123"
    assert thread is None


def test_limit_detection_default():
    assert limits.detect() == 10 * 1024 * 1024


def test_limit_detection_env_override(monkeypatch):
    monkeypatch.setenv("DISCORD_UPLOAD_LIMIT_BYTES", "2048")
    assert limits.detect() == 2048


def test_limit_detection_webhook_override(monkeypatch):
    monkeypatch.setenv("DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES", "4096")
    assert limits.detect(use_bot=False) == 4096


def test_limit_detection_guild_override(monkeypatch):
    monkeypatch.setenv("DISCORD_UPLOAD_LIMIT_GUILD_42", "8192")
    assert limits.detect(guild_id=42) == 8192


def test_limit_detection_webhook_guild_override(monkeypatch):
    monkeypatch.setenv("DISCORD_UPLOAD_LIMIT_WEBHOOK_GUILD_99", "1024")
    assert limits.detect(guild_id=99, use_bot=False) == 1024


def test_archive_file_records_manifest(monkeypatch, tmp_path):
    db = tmp_path / "manifest.db"
    os.environ["ARCHIVE_DB_PATH"] = str(db)
    monkeypatch.setenv("ENABLE_DISCORD_ARCHIVER", "1")
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "dummy")
    # dummy routes
    cfg_path = tmp_path / "routes.yaml"
    cfg_path.write_text(ROUTES_YAML)
    monkeypatch.setenv("ARCHIVE_ROUTES_PATH", str(cfg_path))
    import importlib

    importlib.reload(router)
    # create small file
    f = tmp_path / "foo.png"
    import base64

    f.write_bytes(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAgMBAQAAAAABJRU5ErkJggg=="
        )
    )

    # stub uploader
    def _fake_upload(path, channel_id, token):
        assert Path(path).exists()
        return {"id": "1", "attachments": [{"id": "2"}]}

    monkeypatch.setattr(api.compress, "Image", None)
    monkeypatch.setattr(api.uploader, "upload_file_sync", _fake_upload)
    res = api.archive_file(f, {"kind": "images", "visibility": "public"})
    assert res["channel_id"] == "123"
    assert res["attachment_ids"] == ["2"]
    look = manifest.lookup(res["content_hash"])
    assert look is not None
    assert look["attachment_ids"] == ["2"]
    assert "final_size" in look["compression"]
    assert not f.exists()


def test_dedup_short_circuits_upload(monkeypatch, tmp_path):
    db = tmp_path / "manifest.db"
    os.environ["ARCHIVE_DB_PATH"] = str(db)
    monkeypatch.setenv("ENABLE_DISCORD_ARCHIVER", "1")
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "dummy")
    cfg_path = tmp_path / "routes.yaml"
    cfg_path.write_text(ROUTES_YAML)
    monkeypatch.setenv("ARCHIVE_ROUTES_PATH", str(cfg_path))
    import importlib

    importlib.reload(router)
    importlib.reload(manifest)
    importlib.reload(api)

    f = tmp_path / "foo.png"
    import base64

    f.write_bytes(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAgMBAQAAAAABJRU5ErkJggg=="
        )
    )

    calls = []

    def _fake_upload(path, channel_id, token):
        calls.append(1)
        return {"id": "1", "attachments": [{"id": "2"}]}

    monkeypatch.setattr(api.uploader, "upload_file_sync", _fake_upload)
    monkeypatch.setattr(api.compress, "Image", None)
    # keep_local so we can attempt second archive
    rec1 = api.archive_file(f, {"kind": "images", "visibility": "public"}, keep_local=True)
    rec2 = api.archive_file(f, {"kind": "images", "visibility": "public"}, keep_local=True)
    assert rec1["content_hash"] == rec2["content_hash"]
    assert len(calls) == 1


def test_policy_denies(monkeypatch, tmp_path):
    p = tmp_path / "bad.exe"
    p.write_bytes(b"bad")
    allowed, reasons = policy.check(p, {})
    assert not allowed
    assert "extension not allowed" in reasons


def test_rest_api(monkeypatch, tmp_path):
    db = tmp_path / "manifest.db"
    os.environ["ARCHIVE_DB_PATH"] = str(db)
    monkeypatch.setenv("ENABLE_DISCORD_ARCHIVER", "1")
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "dummy")
    monkeypatch.setenv("ARCHIVE_API_TOKEN", "secret")
    cfg_path = tmp_path / "routes.yaml"
    cfg_path.write_text(ROUTES_YAML)
    monkeypatch.setenv("ARCHIVE_ROUTES_PATH", str(cfg_path))
    import importlib

    importlib.reload(router)
    importlib.reload(api)
    # create small file
    f = tmp_path / "foo.png"
    import base64

    f.write_bytes(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAgMBAQAAAAABJRU5ErkJggg=="
        )
    )

    def _fake_upload(path, channel_id, token):
        return {"id": "1", "attachments": [{"id": "2", "url": "https://temp"}]}

    monkeypatch.setattr(api.uploader, "upload_file_sync", _fake_upload)
    monkeypatch.setattr(api.compress, "Image", None)
    client = TestClient(api.api_router)
    with f.open("rb") as fh:
        resp = client.post(
            "/api/archive/",
            files={"file": ("foo.png", fh, "image/png")},
            data={"meta": '{"kind": "images", "visibility": "public"}'},
            headers={"X-API-TOKEN": "secret"},
        )
    assert resp.status_code == 200
    content_hash = resp.json()["content_hash"]

    # rehydrate endpoint
    async def _fake_fetch(message_id, channel_id, *, token, attachment_id=None):
        return {"url": "https://fresh"}

    monkeypatch.setattr(api.rehydrate, "fetch_attachment", _fake_fetch)
    resp2 = client.get(f"/api/archive/{content_hash}", headers={"X-API-TOKEN": "secret"})
    assert resp2.json()["url"] == "https://fresh"
