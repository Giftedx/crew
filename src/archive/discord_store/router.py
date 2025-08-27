"""Channel router for Discord CDN archiver."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Tuple
import yaml

_CONFIG_PATH = Path(os.environ.get("ARCHIVE_ROUTES_PATH", "config/archive_routes.yaml"))

class RouteConfigError(RuntimeError):
    """Raised when the routing configuration is missing or invalid."""


def _load_config() -> Dict:
    if not _CONFIG_PATH.exists():
        raise RouteConfigError(f"missing routes config at {_CONFIG_PATH}")
    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)

_CONFIG = _load_config()

_EXT_MAP = {
    "images": {".png", ".jpg", ".jpeg", ".webp"},
    "videos": {".mp4", ".webm", ".mov"},
    "audio": {".mp3", ".m4a", ".opus", ".wav"},
    "docs": {".pdf", ".csv", ".json", ".md"},
}


def kind_from_path(path: Path) -> str:
    """Return the file *kind* based on extension."""
    ext = path.suffix.lower()
    for kind, exts in _EXT_MAP.items():
        if ext in exts:
            return kind
    return "blobs"


def pick_channel(
    path: str | Path,
    meta: Dict | None = None,
    tenant: str | None = None,
    visibility: str = "public",
) -> Tuple[str, str | None]:
    """Return `(channel_id, thread_id)` for the given file.

    Parameters
    ----------
    path:
        File path to inspect.
    meta:
        Optional metadata for future routing rules.
    tenant:
        Optional tenant slug for overrides.
    """
    cfg = _CONFIG
    kind = kind_from_path(Path(path))
    if tenant:
        overrides = cfg.get("per_tenant_overrides", {}).get(tenant, {})
        if kind in overrides and visibility in overrides[kind]:
            route = overrides[kind][visibility]
            return route["channel_id"], route.get("thread_id")
    route_group = cfg["routes"].get(kind)
    if not route_group or visibility not in route_group:
        raise RouteConfigError(f"no route for kind {kind} visibility {visibility}")
    route = route_group[visibility]
    return route["channel_id"], route.get("thread_id")

__all__ = ["pick_channel", "kind_from_path", "RouteConfigError"]
