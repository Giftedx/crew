"""File policy checks for Discord archiver."""

from __future__ import annotations

import os
from pathlib import Path

from policy import policy_engine

# Basic allowlist for file extensions per kind
_ALLOWLIST = {
    "images": {".png", ".jpg", ".jpeg", ".webp"},
    "videos": {".mp4", ".webm", ".mov"},
    "audio": {".mp3", ".m4a", ".opus", ".wav"},
    "docs": {".pdf", ".csv", ".json", ".md"},
}
# Deny potentially dangerous types
_DENY_EXTS = {".exe", ".bat", ".cmd"}

_MAX_SIZE = int(os.environ.get("ARCHIVER_POLICY_MAX_SIZE", 100 * 1024 * 1024))
_POLICY = policy_engine.load_policy()


class PolicyError(RuntimeError):
    """Raised when a file fails policy checks."""


def check(path: str | Path, meta: dict) -> tuple[bool, list[str]]:
    """Return (allowed, reasons) for ``path`` given ``meta``."""
    reasons: list[str] = []
    p = Path(path)
    ext = p.suffix.lower()
    if meta.get("do_not_archive"):
        reasons.append("do_not_archive flag set")
    if ext in _DENY_EXTS:
        reasons.append("extension not allowed")
    if not any(ext in exts for exts in _ALLOWLIST.values()):
        reasons.append("unknown file type")
    dec = policy_engine.check_payload("", {"media_type": meta.get("kind")}, _POLICY)
    if dec.decision == "block":
        reasons.extend(dec.reasons)
    size = p.stat().st_size
    limit = int(meta.get("size_limit", _MAX_SIZE))
    if size > limit:
        reasons.append("file exceeds policy size limit")
    return not reasons, reasons


__all__ = ["check", "PolicyError"]
