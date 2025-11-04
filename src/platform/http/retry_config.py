"""Retry attempts configuration resolution.

Splits out precedence logic from the legacy ``core.http_utils`` module.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from .config import DEFAULT_HTTP_RETRY_ATTEMPTS


try:
    from ultimate_discord_intelligence_bot.tenancy.context import current_tenant
except Exception:

    def current_tenant() -> Any:
        return None


_RETRY_CONFIG_CACHE: dict[str, dict[str, int | None]] | None = {}
_MAX_REASONABLE_HTTP_RETRY_ATTEMPTS = 20


def _load_retry_config() -> dict[str, int | None]:
    global _RETRY_CONFIG_CACHE
    try:
        ctx = current_tenant()
    except Exception:
        ctx = None
    tenant_id = getattr(ctx, "tenant_id", None) or "global"
    cache = _RETRY_CONFIG_CACHE or {}
    if tenant_id in cache:
        return cache[tenant_id]
    root = Path(__file__).resolve().parents[2]
    cfg_paths: list[Path] = []
    if ctx and getattr(ctx, "tenant_id", None):
        cfg_paths.append(root / "tenants" / ctx.tenant_id / "retry.yaml")
    cfg_paths.append(root / "config" / "retry.yaml")
    max_attempts: int | None = None
    try:
        for cfg_path in cfg_paths:
            if cfg_path.exists():
                for line in cfg_path.read_text(encoding="utf-8").splitlines():
                    if "max_attempts:" in line:
                        try:
                            cand = int(line.split(":", 1)[1].strip())
                            if 1 <= cand <= _MAX_REASONABLE_HTTP_RETRY_ATTEMPTS:
                                max_attempts = cand
                        except ValueError:
                            pass
                        break
            if max_attempts is not None:
                break
    except Exception:
        max_attempts = None
    if _RETRY_CONFIG_CACHE is None:
        _RETRY_CONFIG_CACHE = {}
    _RETRY_CONFIG_CACHE[tenant_id] = {"max_attempts": max_attempts}
    return _RETRY_CONFIG_CACHE[tenant_id]


def resolve_retry_attempts(call_arg: int | None = None) -> int:
    """Resolve effective retry attempts with explicit precedence.

    1) Explicit call_arg (if valid)
    2) config/tenants retry.yaml
    3) Environment RETRY_MAX_ATTEMPTS (if not equal to library default)
    4) Secure config value (via core.secure_config)
    5) DEFAULT_HTTP_RETRY_ATTEMPTS
    """
    if call_arg is not None:
        if 1 <= call_arg <= _MAX_REASONABLE_HTTP_RETRY_ATTEMPTS:
            return call_arg
        logging.getLogger(__name__).warning(
            "Ignoring out-of-range explicit retry attempts (%s); falling back.", call_arg
        )
    cfg = _load_retry_config()
    cfg_val = cfg.get("max_attempts") if cfg else None
    if isinstance(cfg_val, int) and 1 <= cfg_val <= _MAX_REASONABLE_HTTP_RETRY_ATTEMPTS:
        return cfg_val
    raw_env = os.getenv("RETRY_MAX_ATTEMPTS")
    if raw_env is not None and raw_env.strip():
        try:
            cand = int(raw_env)
            if 1 <= cand <= _MAX_REASONABLE_HTTP_RETRY_ATTEMPTS and cand != DEFAULT_HTTP_RETRY_ATTEMPTS:
                return cand
        except ValueError:
            logging.getLogger(__name__).warning("Invalid RETRY_MAX_ATTEMPTS=%s; falling back to defaults", raw_env)
    _config: Any | None = None
    try:
        from platform.config.configuration import get_config  # project's "platform" package, not stdlib

        _config = get_config()
    except Exception:
        _config = None
    env_val = getattr(_config, "retry_max_attempts", None) if _config else None
    if env_val is not None:
        try:
            cand = int(env_val)
            if 1 <= cand <= _MAX_REASONABLE_HTTP_RETRY_ATTEMPTS:
                return cand
        except ValueError:
            pass
    return DEFAULT_HTTP_RETRY_ATTEMPTS


def reset_retry_config_cache() -> None:
    global _RETRY_CONFIG_CACHE
    _RETRY_CONFIG_CACHE = {}


__all__ = ["reset_retry_config_cache", "resolve_retry_attempts"]
