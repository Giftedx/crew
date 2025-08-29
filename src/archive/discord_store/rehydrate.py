"""Helpers to re-fetch attachments when CDN links expire.

Discord's CDN links are temporary and signed, so long-term access requires
re-fetching attachment metadata via the API to obtain a fresh URL.
https://discord.com/developers/docs/reference#cdn-endpoints
"""

from __future__ import annotations

import aiohttp

API_BASE = "https://discord.com/api/v10"


async def fetch_attachment(
    message_id: str,
    channel_id: str,
    *,
    token: str,
    attachment_id: str | None = None,
) -> dict:
    """Return attachment metadata for ``attachment_id``.

    If ``attachment_id`` is not provided the first attachment is returned. This
    helper is used to obtain a fresh signed URL whenever a stored CDN link
    expires.
    """
    headers = {"Authorization": f"Bot {token}"}
    url = f"{API_BASE}/channels/{channel_id}/messages/{message_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
    attachments = data.get("attachments", [])
    if attachment_id is None:
        return attachments[0] if attachments else {}
    for att in attachments:
        if str(att.get("id")) == str(attachment_id):
            return att
    raise KeyError("attachment not found")


__all__ = ["fetch_attachment"]
