"""Facade for archiving files to Discord's CDN-backed storage."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Optional

from . import compress, limits, manifest, router, uploader, cleanup, policy, rehydrate
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from fastapi.responses import JSONResponse
import asyncio
import json
import tempfile

ENABLE_ARCHIVER = os.environ.get("ENABLE_DISCORD_ARCHIVER", "1") != "0"
ALLOW_WEBHOOK = os.environ.get("ARCHIVER_ALLOW_WEBHOOK_FALLBACK", "0") == "1"


def archive_file(
    path: str | Path,
    meta: Optional[Dict] = None,
    *,
    tenant: str | None = None,
    keep_local: bool = False,
) -> Dict:
    """Archive ``path`` to Discord and return manifest metadata.

    This function performs routing, compression, upload, manifest write, and optional
    cleanup. It raises ``RuntimeError`` if archiving is disabled via feature flag.
    """
    if not ENABLE_ARCHIVER:
        raise RuntimeError("discord archiver disabled")

    meta = meta or {}
    allowed, reasons = policy.check(path, meta)
    if not allowed:
        raise RuntimeError("policy denied: " + ";".join(reasons))
    visibility = meta.get("visibility", "public")
    channel_id, _thread = router.pick_channel(path, meta, tenant, visibility)
    limit = limits.detect(None)
    kind = meta.get("kind") or router.kind_from_path(Path(path))
    fitted_path, stats = compress.fit_to_limit(path, limit, kind)
    sha256 = manifest.compute_hash(fitted_path)
    existing = manifest.lookup(sha256)
    if existing:
        existing["tags"] = existing.get("tags", "").split(",") if existing.get("tags") else []
        existing["content_hash"] = sha256
        if not keep_local:
            cleanup.delete(path)
            if Path(fitted_path) != Path(path):
                cleanup.delete(fitted_path)
        return existing
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN not configured")
    upload_resp = uploader.upload_file_sync(fitted_path, channel_id, token=token)
    record = {
        "message_id": str(upload_resp.get("id", "0")),
        "channel_id": channel_id,
        "attachment_id": str(upload_resp.get("attachments", [{}])[0].get("id", "0")),
        "filename": Path(fitted_path).name,
        "size": stats["final_size"],
        "sha256": sha256,
        "tenant": tenant,
        "workspace": meta.get("workspace"),
        "media_type": kind,
        "visibility": visibility,
        "tags": meta.get("tags", []),
    }
    manifest.record(sha256, record)
    if not keep_local:
        cleanup.delete(path)
        if Path(fitted_path) != Path(path):
            cleanup.delete(fitted_path)
    record["content_hash"] = sha256
    return record


api_router = APIRouter(prefix="/api/archive")


def _auth(token: str | None = Header(None)):
    expected = os.environ.get("ARCHIVE_API_TOKEN")
    if expected and token != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


@api_router.post("/")
async def archive_endpoint(
    file: UploadFile = File(...),
    meta: str = Form("{}"),
    x_api_token: str | None = Header(None, alias="X-API-TOKEN"),
):
    _auth(x_api_token)
    meta_dict = json.loads(meta or "{}")
    suffix = Path(file.filename or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        record = await asyncio.to_thread(
            archive_file, tmp_path, meta_dict, tenant=meta_dict.get("tenant")
        )
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return JSONResponse(record)


@api_router.get("/{content_hash}")
async def rehydrate_endpoint(content_hash: str, x_api_token: str | None = Header(None, alias="X-API-TOKEN")):
    _auth(x_api_token)
    rec = manifest.lookup(content_hash)
    if not rec:
        raise HTTPException(status_code=404, detail="not found")
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    att = await rehydrate.fetch_attachment(rec["message_id"], rec["channel_id"], token=token)
    return {"url": att.get("url"), "filename": rec["filename"]}


@api_router.get("/search")
def search_endpoint(tag: str, x_api_token: str | None = Header(None, alias="X-API-TOKEN")):
    _auth(x_api_token)
    return manifest.search_tag(tag)

__all__ = ["archive_file", "api_router"]
