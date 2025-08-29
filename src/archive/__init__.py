"""Archive package exposing a Discord CDN-backed file store."""

from .discord_store.api import archive_file  # re-export

__all__ = ["archive_file"]
