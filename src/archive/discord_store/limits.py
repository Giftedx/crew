"""Upload limit detection utilities.

Discord applies an effective 10 MiB default per attachment when no boosted
limits are present, though the ceiling may be higher for Nitro or boosted
servers. :contentReference[oaicite:0]{index=0}
"""

from __future__ import annotations

import os


# Default per-attachment limit in bytes when guild tier is unknown.
# https://support.discord.com/hc/en-us/articles/213247207--My-files-are-too-powerful-
_DEFAULT_LIMIT = 10 * 1024 * 1024


def detect(guild_id: int | None = None, use_bot: bool = True) -> int:
    """Return the effective upload limit in bytes.

    Parameters can override the default via environment variables:

    ``DISCORD_UPLOAD_LIMIT_BYTES`` – global override for bot uploads.
    ``DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES`` – global override for webhooks.
    ``DISCORD_UPLOAD_LIMIT_GUILD_<id>`` – per‑guild override (bot uploads).
    ``DISCORD_UPLOAD_LIMIT_WEBHOOK_GUILD_<id>`` – per‑guild override for
    webhook uploads.

    When no overrides are found the function defaults to 10 MiB per
    attachment. Webhooks often have lower ceilings; callers can set
    ``DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES`` to reflect that.
    """
    if guild_id is not None:
        if use_bot:
            specific = os.getenv(f"DISCORD_UPLOAD_LIMIT_GUILD_{guild_id}")
        else:
            specific = os.getenv(f"DISCORD_UPLOAD_LIMIT_WEBHOOK_GUILD_{guild_id}")
        if specific and specific.isdigit():
            return int(specific)

    if not use_bot:
        webhook_override = os.getenv("DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES")
        if webhook_override and webhook_override.isdigit():
            return int(webhook_override)

    global_override = os.getenv("DISCORD_UPLOAD_LIMIT_BYTES")
    if global_override and global_override.isdigit():
        return int(global_override)

    return _DEFAULT_LIMIT


__all__ = ["detect"]
